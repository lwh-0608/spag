#!/usr/bin/env python3
"""英语角签到 — DataFusion 的一个独立板块。

职责：英语角活动的**参与者签到**记录持久化与统计聚合，供现场扫码签到、
后台实时查看与导出使用。

  存储结构（checkin_records.json）：
    {
      "records": [
        {"id": "<uuid4 hex>", "session": "2026-10-08", "name": "张三",
         "company": "某某公司", "role": "企业主 / 创始人", "wechat": "zhangsan",
         "source": "朋友或同事推荐", "first_time": "首次参加", "ts": "2026-10-08T19:03:11"}
      ]
    }

与 DataFusion 产业链分析逻辑完全分离，单独一个文件承载本板块的底层架构；
写法对齐 cognition.py（原子写 + 容错读 + 白名单清洗）。
"""
import csv
import io
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
RECORDS_FILE = ROOT / "checkin_records.json"

def current_session() -> str:
    """当前场次 = 当天日期。

    这里原先是写死的常量（"2026-10-08"），每办一场要人工改一次。漏改的代价不是
    「标签难看」，是静默丢人：前端 localStorage 按场次分键（ec-checkin-<场次>），
    场次不变时，上次来过的参与者再扫码会直接命中旧记录、看到「签到成功」，
    表单根本不出现，人就这么走了。
    """
    return datetime.now().strftime("%Y-%m-%d")


def __getattr__(name):
    """让 checkin.DEFAULT_SESSION 每次取属性都算当天。

    app.py 是 `session=checkin.DEFAULT_SESSION` —— 每次请求现取属性。模块级
    __getattr__（PEP 562）是唯一能在**不碰 app.py** 的前提下让它保持当天的做法，
    而 app.py 属 DataFusion，英语角借道可以、染指不行。
    """
    if name == "DEFAULT_SESSION":
        return current_session()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 字段长度上限——签到是公开接口，必须防止超大/异常 payload 落盘
FIELD_LIMITS = {
    "session": 32,
    "name": 40,
    "company": 80,
    "role": 40,
    "wechat": 60,
    "source": 40,
    "first_time": 20,
}
# 必填四项：姓名 + 公司 + 身份 + 联系方式。
# 2026-11 之前只要求姓名，导出的名单里一半是「只有名字」，构不成可跟进的线索；
# 而留成选填的字段又被随手填成「pie」「GZYY」这类无法核实的值。四项缺一不可。
REQUIRED_FIELDS = ("name", "company", "role", "wechat")

# 联系方式二选一：11 位手机号，或微信 ID（6–20 位、字母开头、可含 - _）
RE_PHONE = re.compile(r"^1[3-9]\d{9}$")
RE_WECHAT = re.compile(r"^[A-Za-z][-_A-Za-z0-9]{5,19}$")

# 场次：客户端提交的 session 必须是真实日期，且落在本场次前后一年内。
# 不校验的话，随手填 "test"/"1900-01-01" 就能污染按场次统计，
# 还能绕开「同场次 + 同联系方式不重复」的去重。
RE_SESSION = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SESSION_MAX_AGE_DAYS = 366

# 不可见字符（零宽空格/连接符、BOM、方向控制符、软连字符）：既不算内容，
# 落盘前也应清掉 —— 否则只填「看不见的字符」也能混过必填校验。
RE_INVISIBLE = re.compile("[\u00ad\u061c\u180e\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")

# 明显不是真实信息的占位值。宁可当场报错让人重填，也不要落一条查无此人的记录。
# 比较前会归一化（去空白、标点、斜杠并转小写），所以这里存归一化后的键：
# 「N/A」「n.a.」「N / A」都会归一成 "na" 命中。
JUNK_VALUES = {
    "无", "没有", "暂无", "未知", "不知道", "不清楚", "保密", "其他", "略",
    "匿名", "无名", "佚名", "同上", "无公司", "暂无公司", "无业", "待定",
    "na", "none", "null", "nil", "test", "testing", "abc", "aaa", "aaaa",
    "asdf", "qwer", "123", "1234", "1", "x", "xx", "xxx",
}

# 明显的假联系方式：真实微信/手机号不会长这样。
FAKE_CONTACTS = {
    "abcdef", "abcdefg", "qwerty", "asdfgh", "zxcvbn", "qazwsx",
    "abc123", "13800138000", "12345678901",
}

# 前端下拉选项（同时也是服务端白名单校验口径）
ROLES = ["企业主 / 创始人", "经理 / 主管", "职场人士", "求职者", "学生", "其他"]
SOURCES = ["微信朋友圈 / 微信群", "朋友或同事推荐", "传单 / 海报", "路过 JFC 办公室", "其他"]
FIRST_TIME = ["首次参加", "参加过"]

MAX_RECORDS = 5000  # 兜底上限，防止单文件无限膨胀

_lock = threading.Lock()


def _clean(value, limit: int) -> str:
    """转字符串 + 去首尾空白 + 去不可见字符 + 截断到上限。非标量返回空串。"""
    if value is None:
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    return RE_INVISIBLE.sub("", str(value).strip())[:limit]


def _junk_key(value: str) -> str:
    """占位值归一化：去空白、常见分隔符与标点，再转小写。"""
    return re.sub(r"[\s\-_/·.,，。、;；:：!！?？'\"“”‘’()（）\[\]【】]+", "", value).lower()


def _looks_fake_text(value: str, min_len: int = 2) -> bool:
    """判断必填文本是不是「敷衍填写」。

    占位词（无 / N/A / test / 保密）、纯数字或纯标点、单个字符反复，
    都不算「填过了」——这些值在导出名单里查无此人，等于必填被绕过。
    """
    visible = (value or "").strip()
    if len(visible) < min_len:
        return True
    if len(set(visible)) == 1:                      # aaa / 111 / 。。。
        return True
    if not any(ch.isalpha() for ch in visible):     # 纯数字/标点：不可核实
        return True
    key = _junk_key(visible)
    return not key or key in JUNK_VALUES


def _normalize_session(raw: str):
    """校验 session：空值落当天；其余必须是近期真实日期，否则返回 None。"""
    s = (raw or "").strip()
    if not s:
        return current_session()
    if not RE_SESSION.match(s):
        return None
    try:
        day = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None
    age = (datetime.now().date() - day).days
    if not (-1 <= age <= SESSION_MAX_AGE_DAYS):
        return None
    return s


def load_records() -> list:
    """加载全部签到记录。文件缺失或损坏时返回空列表（不抛异常）。"""
    if not RECORDS_FILE.exists():
        return []
    try:
        with open(RECORDS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, list):
        return []
    return [r for r in records if isinstance(r, dict)]


def _write(records: list) -> None:
    """原子保存（tmp + os.replace），避免中断留下半截文件。"""
    payload = json.dumps({"records": records}, ensure_ascii=False, indent=2)
    tmp = str(RECORDS_FILE) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(payload)
    os.replace(tmp, str(RECORDS_FILE))


FIELD_LABELS = {"name": "姓名", "company": "公司 / 机构", "role": "身份", "wechat": "微信或手机号"}


def _norm_contact(raw: str) -> str:
    """把联系方式规整成可核实的形式，认不出来返回空串。

    手机可以带空格或横线；微信 ID 本身允许横线，所以先试手机再去掉横线。
    """
    s = (raw or "").strip()
    digits = re.sub(r"[\s-]", "", s)
    if RE_PHONE.match(digits):
        return digits
    if RE_WECHAT.match(s):
        return s
    return ""


def _contact_is_fake(contact: str) -> bool:
    """联系方式格式对、但明显是占位：全同字符、常见测试号、带 test/fake 的假号。"""
    low = (contact or "").lower()
    if not low:
        return True
    if len(set(low)) == 1:                       # aaaaaa / 11111111111
        return True
    if low in FAKE_CONTACTS or _junk_key(low) in JUNK_VALUES:
        return True
    if any(word in low for word in ("test", "fake", "dummy", "example")):
        return True
    # 手机号后十位全相同（如 13333333333）几乎不可能是真号
    if RE_PHONE.match(contact) and len(set(contact[1:])) == 1:
        return True
    return False


def validate(payload) -> tuple:
    """校验并清洗签到 payload。

    返回 (cleaned, error)。error 非空时 cleaned 不可用。
    """
    if not isinstance(payload, dict):
        return None, "invalid body"

    # 文本字段必须是字符串：数字/布尔/对象一律拒绝，
    # 防止用 123、true 这类值蒙混过「已填写」的检查。
    for field in ("name", "company", "wechat"):
        raw = payload.get(field)
        if raw is not None and not isinstance(raw, str):
            return None, "请用文字填写：" + FIELD_LABELS.get(field, field)

    cleaned = {k: _clean(payload.get(k), lim) for k, lim in FIELD_LIMITS.items()}
    # 必须调函数：模块内的全局名查找不看 __getattr__，写 DEFAULT_SESSION 会 NameError
    session = _normalize_session(cleaned["session"])
    if session is None:
        return None, "session 取值非法：需为 YYYY-MM-DD 且在本场次前后一年内"
    cleaned["session"] = session

    # 联系方式先归一再判必填，否则「格式不对」会被误报成「没填」
    raw_contact = cleaned["wechat"]
    cleaned["wechat"] = _norm_contact(raw_contact)
    if raw_contact and not cleaned["wechat"]:
        return None, "联系方式格式不对：手机填 11 位；微信 ID 6 至 20 位、字母开头"
    if cleaned["wechat"] and _contact_is_fake(cleaned["wechat"]):
        return None, "联系方式像占位值，请填真实手机号或微信号"

    missing = [f for f in REQUIRED_FIELDS if not cleaned[f]]
    if missing:
        return None, "请补全：" + "、".join(FIELD_LABELS.get(f, f) for f in missing)

    if _looks_fake_text(cleaned["name"]):
        return None, "姓名不像真实姓名：请填全名，不要填「12」「N/A」「测试」这类占位"
    if _looks_fake_text(cleaned["company"]):
        return None, "公司 / 机构请填全称，不要填「无」「暂无」「N/A」这类占位"

    # 选项类字段做白名单校验（空值放过，视为未填）
    if cleaned["role"] and cleaned["role"] not in ROLES:
        return None, "role 取值非法"
    if cleaned["source"] and cleaned["source"] not in SOURCES:
        return None, "source 取值非法"
    if cleaned["first_time"] and cleaned["first_time"] not in FIRST_TIME:
        return None, "first_time 取值非法"

    return cleaned, ""


def _derive_first_time(cleaned: dict, records: list) -> str:
    """首参不再问客人，改由历史记录判定（2026-11 表单从 6 项砍到 3 项）。

    微信是唯一键（纸质表上就写着这句）；没留微信时退回姓名匹配。
    只跟**其他场次**比 —— 同一场里重复录入不该把自己判成「参加过」。
    """
    if cleaned.get("first_time"):
        return cleaned["first_time"]
    wx = (cleaned.get("wechat") or "").strip().lower()
    nm = (cleaned.get("name") or "").strip().lower()
    for r in records:
        if (r.get("session") or "") == cleaned.get("session"):
            continue
        if wx and (r.get("wechat") or "").strip().lower() == wx:
            return "参加过"
        if not wx and nm and (r.get("name") or "").strip().lower() == nm:
            return "参加过"
    return "首次参加"


def add_record(payload) -> tuple:
    """校验并追加一条签到记录。

    返回 (record, error)。
    """
    cleaned, error = validate(payload)
    if error:
        return None, error

    with _lock:
        records = load_records()
        if len(records) >= MAX_RECORDS:
            return None, "签到记录已达上限"
        # 同一场次、同一联系方式 = 已经在册，不重复落行。
        # 门口最常见的就是同一个人扫了两遍（自己扫一次、工作人员又代录一次），
        # 不拦会让出席人数虚高。
        for r in records:
            if (r.get("session") or "") == cleaned["session"] and \
               (r.get("wechat") or "").lower() == cleaned["wechat"].lower():
                dup = dict(r)
                dup["duplicate"] = True
                return dup, ""
        cleaned["first_time"] = _derive_first_time(cleaned, records)
        record = dict(cleaned)
        record["id"] = uuid.uuid4().hex
        record["ts"] = datetime.now().isoformat(timespec="seconds")
        records.append(record)
        _write(records)
    return record, ""


def delete_record(record_id: str) -> bool:
    """按 id 删除一条记录。返回是否真的删掉了。"""
    with _lock:
        records = load_records()
        kept = [r for r in records if r.get("id") != record_id]
        if len(kept) == len(records):
            return False
        _write(kept)
    return True


def summarize(records: list) -> dict:
    """聚合统计：总数 / 首次占比 / 渠道分布 / 身份分布 / 公司数。"""
    total = len(records)
    roles, sources, sessions = {}, {}, {}
    first_time = 0
    companies = set()

    for r in records:
        role = r.get("role") or "(未填)"
        source = r.get("source") or "(未填)"
        session = r.get("session") or "(未填)"
        roles[role] = roles.get(role, 0) + 1
        sources[source] = sources.get(source, 0) + 1
        sessions[session] = sessions.get(session, 0) + 1
        if r.get("first_time") == "首次参加":
            first_time += 1
        company = (r.get("company") or "").strip()
        if company:
            companies.add(company)

    return {
        "total": total,
        "first_time": first_time,
        "returning": total - first_time,
        "companies": len(companies),
        "contacts": sum(1 for r in records if (r.get("wechat") or "").strip()),
        "by_role": roles,
        "by_source": sources,
        "by_session": sessions,
    }


CSV_HEADERS = ["签到时间", "场次", "姓名", "公司 / 机构", "身份", "微信", "如何得知", "首次参加"]


def to_csv(records: list) -> str:
    """导出 CSV（UTF-8 BOM，Excel/WPS 直接双击不乱码）。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    for r in records:
        writer.writerow([
            r.get("ts", ""), r.get("session", ""), r.get("name", ""),
            r.get("company", ""), r.get("role", ""), r.get("wechat", ""),
            r.get("source", ""), r.get("first_time", ""),
        ])
    return "\ufeff" + buf.getvalue()
