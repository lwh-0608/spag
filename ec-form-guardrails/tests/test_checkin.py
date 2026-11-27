#!/usr/bin/env python3
"""英语角签到板块的单元测试（unittest，零第三方依赖）。

覆盖两层：
  · checkin.py —— 存储/校验/统计/CSV（含损坏文件容错）
  · app.py 路由 —— /checkin、POST /api/checkin、统计与导出、token 鉴权

所有用例都重定向到临时文件，绝不触碰真实的 checkin_records.json。
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module  # noqa: E402
import checkin  # noqa: E402
import feedback  # noqa: E402


def valid_payload(**over):
    """当前表单口径的完整 payload —— 四项必填：姓名 / 公司 / 身份 / 联系方式。

    2026-11 表单从 6 项砍到 4 项必填后，只填姓名的 payload 一律被拒；
    这里的基线让每个用例只覆盖自己那一项，其余字段不再成为噪声。
    """
    payload = {"name": "张三", "company": "某公司",
               "role": "企业主 / 创始人", "wechat": "zhangsan"}
    payload.update(over)
    return payload


class CheckinStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig = checkin.RECORDS_FILE
        checkin.RECORDS_FILE = Path(self._tmp.name) / "checkin_records.json"

    def tearDown(self):
        checkin.RECORDS_FILE = self._orig
        self._tmp.cleanup()

    # ── 校验 ──────────────────────────────────────────────────────────
    def test_missing_name_rejected(self):
        record, err = checkin.add_record({"company": "某公司"})
        self.assertIsNone(record)
        self.assertIn("姓名", err)          # 提示走中文字段名，不再回英文 key

    def test_blank_name_rejected(self):
        record, err = checkin.add_record({"name": "   "})
        self.assertIsNone(record)
        self.assertTrue(err)

    def test_invalid_role_rejected(self):
        record, err = checkin.add_record(valid_payload(role="外星人"))
        self.assertIsNone(record)
        self.assertIn("role", err)

    def test_invalid_source_rejected(self):
        record, err = checkin.add_record(valid_payload(source="从天上掉下来"))
        self.assertIsNone(record)
        self.assertIn("source", err)

    def test_bad_contact_rejected(self):
        """联系方式必须是可核实的：11 位手机号，或字母开头的微信 ID。"""
        record, err = checkin.add_record(valid_payload(wechat="zs"))
        self.assertIsNone(record)
        self.assertIn("联系方式", err)

    def test_phone_contact_accepted(self):
        record, err = checkin.add_record(valid_payload(wechat="138-1234-5678"))
        self.assertEqual("", err)
        self.assertEqual("13812345678", record["wechat"])   # 归一去空格/横线

    # ── 必填护栏：填占位值 = 没填（2026-11-27 加固）──────────────────
    def test_placeholder_name_rejected(self):
        """「12」「N/A」「无」「。。」这类值不构成一条可跟进的线索。"""
        for bad in ("12", "N/A", "无", "暂无", "。。", "test", "  ", "\u200b\u200b"):
            record, err = checkin.add_record(valid_payload(name=bad))
            self.assertIsNone(record, f"name={bad!r} 应被拒")
            self.assertIn("姓名", err)

    def test_placeholder_company_rejected(self):
        for bad in ("N/A", "n.a.", "无", "暂无", "保密", "。。", "1234"):
            record, err = checkin.add_record(valid_payload(company=bad))
            self.assertIsNone(record, f"company={bad!r} 应被拒")
            self.assertIn("公司", err)

    def test_fake_contact_rejected(self):
        """格式对、但明显是占位的联系方式也拒：全同字符、测试号、test 字样。"""
        for bad in ("abcdef", "13800138000", "13333333333", "test12345", "Qwerty"):
            record, err = checkin.add_record(valid_payload(wechat=bad))
            self.assertIsNone(record, f"wechat={bad!r} 应被拒")
            self.assertIn("联系方式", err)

    def test_contact_type_must_be_string(self):
        record, err = checkin.add_record(valid_payload(wechat=123))
        self.assertIsNone(record)
        self.assertIn("文字", err)

    def test_session_must_be_recent_real_date(self):
        for bad in ("test", "1900-01-01", "2026-13-01", "2026-02-30", "2999-01-01"):
            record, err = checkin.add_record(valid_payload(session=bad))
            self.assertIsNone(record, f"session={bad!r} 应被拒")
            self.assertIn("session", err)

    def test_non_dict_body_rejected(self):
        record, err = checkin.add_record(["not", "a", "dict"])
        self.assertIsNone(record)
        self.assertTrue(err)

    def test_long_field_truncated_not_fatal(self):
        record, err = checkin.add_record(valid_payload(name="欧阳修文" * 10))
        self.assertEqual("", err)
        self.assertEqual(40, len(record["name"]))

    def test_unknown_field_dropped(self):
        record, err = checkin.add_record(valid_payload(evil="x" * 9999))
        self.assertEqual("", err)
        self.assertNotIn("evil", record)

    # ── 读写 ──────────────────────────────────────────────────────────
    def test_add_then_load_roundtrip(self):
        record, err = checkin.add_record(valid_payload())
        self.assertEqual("", err)
        records = checkin.load_records()
        self.assertEqual(1, len(records))
        self.assertEqual("张三", records[0]["name"])
        self.assertEqual(checkin.current_session(), records[0]["session"])  # 默认场次=当天
        self.assertTrue(records[0]["id"])
        self.assertTrue(records[0]["ts"])

    def test_session_can_be_overridden(self):
        """断网补传会带原来的场次：合法的近期日期仍允许覆盖。"""
        recent = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        record, err = checkin.add_record(valid_payload(name="李四", session=recent))
        self.assertEqual("", err)
        self.assertEqual(recent, record["session"])

    def test_default_session_follows_today(self):
        """场次必须跟着当天走，不能是写死的常量。

        app.py 读的是 checkin.DEFAULT_SESSION（模块属性，每次请求现取）。
        一旦它退回常量，下次活动时老参与者会命中本机旧记录、直接看到「签到成功」，
        表单不出现 —— 静默丢人，且现场看不出来。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(today, checkin.DEFAULT_SESSION)
        self.assertEqual(today, checkin.current_session())
        # 未传 session 的记录也必须落在当天
        record, err = checkin.add_record(valid_payload(name="赵六"))
        self.assertEqual("", err)
        self.assertEqual(today, record["session"])

    def test_delete_record(self):
        record, _ = checkin.add_record(valid_payload(name="王五"))
        self.assertTrue(checkin.delete_record(record["id"]))
        self.assertEqual([], checkin.load_records())
        self.assertFalse(checkin.delete_record("no-such-id"))

    def test_corrupt_file_returns_empty_list(self):
        checkin.RECORDS_FILE.write_text("{ not json", encoding="utf-8")
        self.assertEqual([], checkin.load_records())

    def test_wrong_shape_returns_empty_list(self):
        checkin.RECORDS_FILE.write_text(json.dumps(["nope"]), encoding="utf-8")
        self.assertEqual([], checkin.load_records())

    # ── 统计与导出 ────────────────────────────────────────────────────
    def test_summarize(self):
        checkin.add_record(valid_payload(name="张三", company="甲公司", wechat="zhangsan",
                                         source="朋友或同事推荐", first_time="首次参加"))
        checkin.add_record(valid_payload(name="李四", company="甲公司", role="职场人士",
                                         wechat="lisi6666",
                                         source="微信朋友圈 / 微信群", first_time="参加过"))
        checkin.add_record(valid_payload(name="王五", company="甲公司", role="学生",
                                         wechat="wangwu88", first_time="参加过"))
        s = checkin.summarize(checkin.load_records())

        self.assertEqual(3, s["total"])
        self.assertEqual(1, s["first_time"])
        self.assertEqual(2, s["returning"])
        self.assertEqual(1, s["companies"])          # 甲公司去重
        self.assertEqual(3, s["contacts"])           # 联系方式已是必填，条条可联系
        self.assertEqual(1, s["by_source"]["朋友或同事推荐"])

    def test_summarize_empty(self):
        s = checkin.summarize([])
        self.assertEqual(0, s["total"])
        self.assertEqual({}, s["by_role"])

    def test_csv_has_bom_and_headers(self):
        checkin.add_record(valid_payload())
        out = checkin.to_csv(checkin.load_records())
        self.assertTrue(out.startswith("\ufeff"))     # Excel 打开不乱码
        self.assertIn("姓名", out)
        self.assertIn("张三", out)
        self.assertIn("某公司", out)


class CheckinRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app_module.app.test_client()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_file = checkin.RECORDS_FILE
        self._orig_token = app_module.ADMIN_TOKEN_FILE
        checkin.RECORDS_FILE = Path(self._tmp.name) / "checkin_records.json"
        # 默认不配置 token（开放，便于本地/测试）
        app_module.ADMIN_TOKEN_FILE = Path(self._tmp.name) / ".checkin_token"

    def tearDown(self):
        checkin.RECORDS_FILE = self._orig_file
        app_module.ADMIN_TOKEN_FILE = self._orig_token
        self._tmp.cleanup()

    def test_page_renders(self):
        resp = self.client.get("/checkin")
        self.assertEqual(200, resp.status_code)
        self.assertIn("签到", resp.get_data(as_text=True))

    def test_page_carries_checkin_and_feedback_tabs(self):
        """一张二维码两段：签到 / 反馈可切换，反馈题目照搬腾讯问卷现行版 6 题。

        反馈选项由 feedback.py 注入模板，不是在前端抄一份：两边白名单一旦漂移，
        服务端会整段拒收，现场又看不出来。
        """
        html = self.client.get("/checkin").get_data(as_text=True)
        for marker in ('id="tab-checkin"', 'id="tab-feedback"',
                       'id="checkin-view"', 'id="feedback-view"',
                       'id="fb-done-view"', 'id="fb-form"',
                       "/api/ec-feedback", "本次活动整体满意度"):
            self.assertIn(marker, html)
        for opt in feedback.ENJOYED + feedback.HELPFULNESS + feedback.TOPICS:
            self.assertIn(opt, html)

    def test_submit_and_list(self):
        resp = self.client.post("/api/checkin", json=valid_payload())
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.get_json()["ok"])

        listing = self.client.get("/api/checkin/list").get_json()
        self.assertEqual(1, listing["stats"]["total"])
        self.assertEqual("张三", listing["records"][0]["name"])

    def test_submit_missing_name_400(self):
        resp = self.client.post("/api/checkin", json={"company": "某公司"})
        self.assertEqual(400, resp.status_code)
        self.assertFalse(resp.get_json()["ok"])

    def test_submit_placeholder_values_400(self):
        """绕过前端直接 POST 占位值，后端也必须拒（必填不被敷衍填绕过）。"""
        for payload in (
            valid_payload(name="12"),
            valid_payload(company="N/A"),
            valid_payload(wechat="abcdef"),
        ):
            resp = self.client.post("/api/checkin", json=payload)
            self.assertEqual(400, resp.status_code, payload)
            self.assertFalse(resp.get_json()["ok"])

    def test_submit_non_json_400(self):
        resp = self.client.post("/api/checkin", data="not json",
                                content_type="text/plain")
        self.assertEqual(400, resp.status_code)

    def test_csv_export(self):
        self.client.post("/api/checkin", json=valid_payload())
        resp = self.client.get("/api/checkin/export")
        self.assertEqual(200, resp.status_code)
        self.assertIn("text/csv", resp.headers["Content-Type"])
        self.assertIn("张三", resp.get_data(as_text=True))

    def test_admin_requires_token_when_configured(self):
        app_module.ADMIN_TOKEN_FILE.write_text("s3cret", encoding="utf-8")

        self.assertEqual(401, self.client.get("/api/checkin/list").status_code)
        self.assertEqual(401, self.client.get("/api/checkin/export").status_code)

        ok = self.client.get("/api/checkin/list", headers={"X-Checkin-Token": "s3cret"})
        self.assertEqual(200, ok.status_code)

    def test_public_submit_stays_open_with_token_configured(self):
        """签到是公开的：配了 token 也不能挡住参与者提交。"""
        app_module.ADMIN_TOKEN_FILE.write_text("s3cret", encoding="utf-8")
        resp = self.client.post("/api/checkin", json=valid_payload())
        self.assertEqual(200, resp.status_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
