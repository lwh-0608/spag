#!/usr/bin/env python3
"""英语角反馈问卷 — DataFusion 的一个独立板块。

职责：活动**反馈问卷**的记录持久化与统计聚合。与签到（checkin.py）分开存储、
互不影响；两者共用同一套「原子写 + 容错读 + 白名单清洗」范式。

  内容来源（2026-11-24 起）：《JFC 商业英语角｜活动反馈问卷》腾讯问卷
  `https://wj.qq.com/s2/28393446/v1z5/` 的 6 道题，一字不改搬进自建页，
  与签到并成「一个二维码 · 签到 / 反馈两个可切换部分」（见 templates/checkin.html）。

  存储结构（feedback_records.json）：
    {
      "records": [
        {"id": "<uuid4 hex>", "session": "2026-11-24",
         "satisfaction": "4",                            # 整体满意度 1–5
         "enjoyed": ["商务主题讨论", "自由交流、认识同行"],   # 多选
         "helpfulness": "有一点帮助",                     # 单选题
         "topics": ["报价、议价、订单谈判"],               # 多选：后续想多排的主题
         "nickname": "Amy",                              # 选填
         "comments": "希望多一点角色扮演",                # 开放留言
         "ts": "2026-11-24T19:03:11"}
      ]
    }
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
RECORDS_FILE = ROOT / "feedback_records.json"


def current_session() -> str:
    """当前场次 = 当天日期。

    与 checkin.py 同理：场次写死会导致参与者二次扫码时直接命中本机旧记录，
    看到「感谢你的反馈」问卷根本不出现。
    """
    return datetime.now().strftime("%Y-%m-%d")


def __getattr__(name):
    """让 feedback.DEFAULT_SESSION 每次取属性都算当天，无需改 DF 的 app.py。"""
    if name == "DEFAULT_SESSION":
        return current_session()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 单值字段长度上限
FIELD_LIMITS = {
    "session": 32,
    "satisfaction": 4,
    "helpfulness": 40,
    "nickname": 40,
    "comments": 1000,
}

# 量表范围
SATISFACTION_RANGE = (1, 5)

# 选项白名单（与前端按钮一致，顺序也照腾讯问卷原卷）
ENJOYED = [
    "商务主题讨论",
    "情景角色扮演（展会 / 谈判 / 电话）",
    "导师纠正发音、表达纠错",
    "小组配对练习",
    "案例 / 范文拆解",
    "自由交流、认识同行",
    "其他",
]

HELPFULNESS = [
    "收获很大，学到实用表达",
    "有一点帮助",
    "帮助不大",
    "几乎没有帮助",
]

TOPICS = [
    "展会接待、客户开发",
    "报价、议价、订单谈判",
    "商务邮件、消息撰写",
    "线上英文会议、汇报",
    "客户跟进、维护客情",
    "面试英文、职场自我介绍",
    "跨文化沟通、海外礼仪",
    "其他",
]

# 腾讯问卷原卷六题都勾了「必填」；昵称题自己写着「可不填」，故唯一选填。
# 必填项由前端先拦一次、后端再拦一次（防止绕过前端直接 POST）。
REQUIRED_FIELDS = ("satisfaction", "enjoyed", "helpfulness", "topics", "comments")
FIELD_LABELS = {
    "session": "场次",
    "satisfaction": "整体满意度",
    "enjoyed": "喜欢的部分",
    "helpfulness": "帮助程度",
    "topics": "后续想多安排的主题",
    "nickname": "昵称",
    "comments": "其他建议",
}

# 场次：客户端提交的 session 必须是真实日期，且落在本场次前后一年内。
# 不校验的话，"test"/"1900-01-01" 这类值会污染按场次统计。
RE_SESSION = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SESSION_MAX_AGE_DAYS = 366

# 不可见字符（零宽空格/连接符、BOM、方向控制符、软连字符）：既不算内容，
# 落盘前也应清掉 —— 否则只填「看不见的字符」也能混过必填校验。
RE_INVISIBLE = re.compile("[\u00ad\u061c\u180e\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")

# 「其他建议」的占位/敷衍词表（归一化后比较）：写「无」「没有」「test」
# 等于这一题没答，必填就被绕过了。
JUNK_COMMENTS = {
    "无", "没有", "暂无", "无建议", "没有建议", "暂无建议", "无意见", "没有意见",
    "没什么", "没啥", "不知道", "不清楚", "略", "同上", "无想法", "没想法",
    "暂无想法", "不用", "否", "无异议",
    "na", "none", "null", "nil", "test", "testing", "ok", "okay",
    "123", "1234", "1", "asdf", "qwer",
}

# 昵称是原卷唯一选填题，但仍然不能是占位词（emoji 昵称放行，不要求含字母）。
JUNK_NICKNAME = {"无", "没有", "暂无", "匿名", "na", "none", "null", "nil", "test", "testing"}


MAX_RECORDS = 5000

_lock = threading.Lock()


def _clean(value, limit: int) -> str:
    """转字符串 + 去首尾空白 + 去不可见字符 + 截断。非标量返回空串。"""
    if value is None or isinstance(value, (list, dict, bool)):
        return ""
    if not isinstance(value, (str, int, float)):
        return ""
    return RE_INVISIBLE.sub("", str(value).strip())[:limit]


def _junk_key(value: str) -> str:
    """占位值归一化：去空白、常见分隔符与标点，再转小写。"""
    return re.sub(r"[\s\-_/·.,，。、;；:：!！?？'\"“”‘’()（）\[\]【】]+", "", value).lower()


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


def _comment_is_fake(value: str) -> bool:
    """「其他建议」是不是敷衍填写：占位词、纯数字、纯标点、单字符反复。"""
    visible = (value or "").strip()
    if len(visible) < 2:
        return True
    if len(set(visible)) == 1:                  # 。。。 / 哈哈哈 / 111
        return True
    if visible.isdigit():
        return True
    if not any(ch.isalnum() for ch in visible):
        return True
    key = _junk_key(visible)
    return not key or key in JUNK_COMMENTS


def _nickname_is_fake(value: str) -> bool:
    """昵称选填；填了就不能是「无」「test」这类占位（emoji 昵称不受影响）。"""
    return _junk_key(value) in JUNK_NICKNAME


def _clean_multi(value, allowed: list) -> list:
    """多选字段：接受 list 或逗号分隔字符串，逐项过白名单并去重。"""
    if isinstance(value, str):
        items = [p.strip() for p in value.split(",")]
    elif isinstance(value, list):
        items = [p if isinstance(p, str) else "" for p in value]
    else:
        return []
    seen, out = set(), []
    for it in items:
        if it in allowed and it not in seen:
            seen.add(it)
            out.append(it)
    return out


def load_records() -> list:
    """加载全部反馈记录。文件缺失/损坏时返回空列表，不抛异常。"""
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


def _missing_message(missing: list) -> str:
    return "请完成：" + "、".join(FIELD_LABELS.get(f, f) for f in missing)


def validate(payload) -> tuple:
    """校验并清洗反馈 payload。返回 (cleaned, error)。"""
    if not isinstance(payload, dict):
        return None, "invalid body"

    # 文本题必须是字符串：数字/布尔/对象一律拒绝，
    # 防止用 123、true 这类值蒙混过「已填写」的检查。
    for field in ("comments", "nickname"):
        raw = payload.get(field)
        if raw is not None and not isinstance(raw, str):
            return None, "请用文字填写：" + FIELD_LABELS.get(field, field)

    cleaned = {k: _clean(payload.get(k), lim) for k, lim in FIELD_LIMITS.items()}
    # 必须调函数：模块内的全局名查找不看 __getattr__，写 DEFAULT_SESSION 会 NameError
    session = _normalize_session(cleaned["session"])
    if session is None:
        return None, "session 取值非法：需为 YYYY-MM-DD 且在本场次前后一年内"
    cleaned["session"] = session
    cleaned["enjoyed"] = _clean_multi(payload.get("enjoyed"), ENJOYED)
    cleaned["topics"] = _clean_multi(payload.get("topics"), TOPICS)

    # 原卷六题全标必填（昵称题自注「可不填」除外）：必填项缺失直接打回。
    missing = [f for f in REQUIRED_FIELDS if not cleaned[f]]
    if missing:
        return None, _missing_message(missing)

    # 必填题「填了也算没填」的占位值同样打回（无 / 没有 / test / 。。。）。
    if _comment_is_fake(cleaned["comments"]):
        return None, "其他建议请写具体一些，不要只填「无」「没有」「test」这类占位"
    if cleaned["nickname"] and _nickname_is_fake(cleaned["nickname"]):
        return None, "昵称像占位值，请填你希望我们称呼你的名字"

    try:
        n = int(cleaned["satisfaction"])
    except (TypeError, ValueError):
        return None, "satisfaction 取值非法"
    if not (SATISFACTION_RANGE[0] <= n <= SATISFACTION_RANGE[1]):
        return None, "satisfaction 超出 1–5"
    cleaned["satisfaction"] = str(n)

    if cleaned["helpfulness"] not in HELPFULNESS:
        return None, "helpfulness 取值非法"

    return cleaned, ""


def add_record(payload) -> tuple:
    """校验并追加一条反馈。返回 (record, error)。"""
    cleaned, error = validate(payload)
    if error:
        return None, error

    record = dict(cleaned)
    record["id"] = uuid.uuid4().hex
    record["ts"] = datetime.now().isoformat(timespec="seconds")

    with _lock:
        records = load_records()
        if len(records) >= MAX_RECORDS:
            return None, "反馈记录已达上限"
        records.append(record)
        _write(records)
    return record, ""


def delete_record(record_id: str) -> bool:
    with _lock:
        records = load_records()
        kept = [r for r in records if r.get("id") != record_id]
        if len(kept) == len(records):
            return False
        _write(kept)
    return True


def summarize(records: list) -> dict:
    """聚合：份数 / 平均满意度 / 各维度分布 / 留言与昵称条数。"""
    total = len(records)
    satisfaction, enjoyed, helpfulness, topics, sessions = {}, {}, {}, {}, {}
    satisfaction_vals = []
    comments_cnt = nickname_cnt = 0

    for r in records:
        c = r.get("satisfaction")
        if c:
            try:
                satisfaction_vals.append(int(c))
            except (TypeError, ValueError):
                pass
            satisfaction[c] = satisfaction.get(c, 0) + 1
        if r.get("helpfulness"):
            k = r["helpfulness"]; helpfulness[k] = helpfulness.get(k, 0) + 1
        for s in (r.get("enjoyed") or []):
            enjoyed[s] = enjoyed.get(s, 0) + 1
        for t in (r.get("topics") or []):
            topics[t] = topics.get(t, 0) + 1
        session = r.get("session") or "(未填)"
        sessions[session] = sessions.get(session, 0) + 1
        if (r.get("comments") or "").strip():
            comments_cnt += 1
        if (r.get("nickname") or "").strip():
            nickname_cnt += 1

    return {
        "total": total,
        "satisfaction_avg": (round(sum(satisfaction_vals) / len(satisfaction_vals), 1)
                             if satisfaction_vals else None),
        "satisfaction_count": len(satisfaction_vals),
        "by_satisfaction": satisfaction,
        "by_helpfulness": helpfulness,
        "by_enjoyed": enjoyed,
        "by_topics": topics,
        "by_session": sessions,
        "comments_count": comments_cnt,
        "nickname_count": nickname_cnt,
    }


CSV_HEADERS = ["提交时间", "场次", "整体满意度(1-5)", "喜欢的部分", "帮助程度",
               "想多安排的主题", "昵称", "其他建议"]


def to_csv(records: list) -> str:
    """导出 CSV（UTF-8 BOM，Excel/WPS 直接双击不乱码）。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    for r in records:
        writer.writerow([
            r.get("ts", ""), r.get("session", ""), r.get("satisfaction", ""),
            "、".join(r.get("enjoyed") or []), r.get("helpfulness", ""),
            "、".join(r.get("topics") or []), r.get("nickname", ""),
            r.get("comments", ""),
        ])
    return "\ufeff" + buf.getvalue()
