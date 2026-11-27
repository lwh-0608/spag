#!/usr/bin/env python3
"""英语角反馈问卷板块的单元测试（unittest，零第三方依赖）。

2026-11-24 起，反馈内容换成《JFC 商业英语角｜活动反馈问卷》腾讯问卷现行版
（6 题，其中昵称题选填），并与签到并进同一张页面（/checkin 的「反馈」标签）。

覆盖两层：
  · feedback.py —— 校验 / 多选清洗 / 统计 / CSV（含损坏文件容错、必填项）
  · app.py 路由 —— /checkin、/ec-feedback、POST /api/ec-feedback、统计与导出、
    共用后台口令鉴权

所有用例都重定向到临时文件，绝不触碰真实的 feedback_records.json。
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
import feedback  # noqa: E402


def valid_payload(**over):
    """一份通过校验的最小反馈（六题按腾讯问卷现行版）。"""
    payload = {
        "session": feedback.current_session(),
        "satisfaction": "4",
        "enjoyed": ["商务主题讨论"],
        "helpfulness": "有一点帮助",
        "topics": ["报价、议价、订单谈判"],
        "nickname": "Amy",
        "comments": "希望多一点角色扮演",
    }
    payload.update(over)
    return payload


class FeedbackStorageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig = feedback.RECORDS_FILE
        feedback.RECORDS_FILE = Path(self._tmp.name) / "feedback_records.json"

    def tearDown(self):
        feedback.RECORDS_FILE = self._orig
        self._tmp.cleanup()

    # ── 校验 ──────────────────────────────────────────────────────────
    def test_full_payload_accepted(self):
        record, err = feedback.add_record(valid_payload())
        self.assertEqual("", err)
        self.assertEqual(feedback.current_session(), record["session"])
        self.assertEqual("4", record["satisfaction"])
        self.assertEqual(["商务主题讨论"], record["enjoyed"])
        self.assertEqual("有一点帮助", record["helpfulness"])
        self.assertEqual(["报价、议价、订单谈判"], record["topics"])
        self.assertEqual("Amy", record["nickname"])
        self.assertEqual("希望多一点角色扮演", record["comments"])
        self.assertTrue(record["id"])
        self.assertTrue(record["ts"])

    def test_default_session_follows_today(self):
        """场次跟着当天走。写死的话，二次扫码的人会命中本机旧记录、看到
        「感谢你的反馈」而问卷不出现 —— 反馈一条都收不到，现场还看不出来。"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(today, feedback.DEFAULT_SESSION)
        self.assertEqual(today, feedback.current_session())

    def test_non_dict_body_rejected(self):
        record, err = feedback.add_record(["nope"])
        self.assertIsNone(record)
        self.assertTrue(err)

    def test_required_questions_enforced(self):
        """腾讯问卷现行版六题都标必填（昵称题自注可不填）：缺一题就打回。"""
        for field in feedback.REQUIRED_FIELDS:
            payload = valid_payload()
            payload.pop(field)
            record, err = feedback.add_record(payload)
            self.assertIsNone(record, f"缺 {field} 应被拒")
            self.assertIn("请完成", err)

    def test_nickname_optional(self):
        payload = valid_payload()
        payload.pop("nickname")
        record, err = feedback.add_record(payload)
        self.assertEqual("", err)
        self.assertEqual("", record["nickname"])

    def test_comments_required(self):
        record, err = feedback.add_record(valid_payload(comments="   "))
        self.assertIsNone(record)
        self.assertIn("其他建议", err)

    # ── 必填护栏：填占位值 = 没填（2026-11-27 加固）──────────────────
    def test_placeholder_comments_rejected(self):
        """「无」「没有」「test」「。。。」这类留言等于这一题没答。"""
        for bad in ("无", "没有", "暂无建议", "没有意见", "test", "ok", "123",
                    "。。。", "\u200b", "好"):
            record, err = feedback.add_record(valid_payload(comments=bad))
            self.assertIsNone(record, f"comments={bad!r} 应被拒")
            self.assertIn("其他建议", err)

    def test_comments_must_be_string(self):
        record, err = feedback.add_record(valid_payload(comments=123))
        self.assertIsNone(record)
        self.assertIn("文字", err)

    def test_nickname_placeholder_rejected(self):
        record, err = feedback.add_record(valid_payload(nickname="无"))
        self.assertIsNone(record)
        self.assertIn("昵称", err)

    def test_nickname_emoji_accepted(self):
        """昵称是选填自由文本，emoji 也算正常昵称（不要求含字母）。"""
        record, err = feedback.add_record(valid_payload(nickname="🐱"))
        self.assertEqual("", err)
        self.assertEqual("🐱", record["nickname"])

    def test_session_must_be_recent_real_date(self):
        for bad in ("test", "1900-01-01", "2026-13-01", "2999-01-01"):
            record, err = feedback.add_record(valid_payload(session=bad))
            self.assertIsNone(record, f"session={bad!r} 应被拒")
            self.assertIn("session", err)
        recent = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        record, err = feedback.add_record(valid_payload(session=recent))
        self.assertEqual("", err)
        self.assertEqual(recent, record["session"])

    def test_satisfaction_range_enforced(self):
        for bad in ("0", "6", "-1", "abc", "9"):
            record, err = feedback.add_record(valid_payload(satisfaction=bad))
            self.assertIsNone(record, f"satisfaction={bad!r} 应被拒")
        record, err = feedback.add_record(valid_payload(satisfaction=5))
        self.assertEqual("", err)
        self.assertEqual("5", record["satisfaction"])

    def test_helpfulness_whitelisted(self):
        record, err = feedback.add_record(valid_payload(helpfulness="外星语"))
        self.assertIsNone(record)
        self.assertIn("helpfulness", err)

    def test_satisfaction_bool_rejected(self):
        record, err = feedback.add_record(valid_payload(satisfaction=True))
        self.assertIsNone(record)
        self.assertTrue(err)

    def test_long_text_truncated(self):
        long_text = "希望多安排一些商务场景的角色扮演和案例分析，尤其是展会和谈判。" * 50
        record, err = feedback.add_record(valid_payload(comments=long_text))
        self.assertEqual("", err)
        self.assertEqual(1000, len(record["comments"]))

    def test_unknown_field_dropped(self):
        record, err = feedback.add_record(valid_payload(evil="x" * 9999))
        self.assertEqual("", err)
        self.assertNotIn("evil", record)

    # ── 多选清洗 ──────────────────────────────────────────────────────
    def test_enjoyed_from_list_whitelisted(self):
        record, _ = feedback.add_record(valid_payload(
            enjoyed=["商务主题讨论", "黑客技能", "自由交流、认识同行"]))
        self.assertEqual(["商务主题讨论", "自由交流、认识同行"], record["enjoyed"])

    def test_topics_deduped(self):
        record, _ = feedback.add_record(valid_payload(
            topics=["跨文化沟通、海外礼仪", "跨文化沟通、海外礼仪", "报价、议价、订单谈判"]))
        self.assertEqual(["跨文化沟通、海外礼仪", "报价、议价、订单谈判"], record["topics"])

    def test_multi_from_comma_string(self):
        record, _ = feedback.add_record(valid_payload(
            enjoyed="商务主题讨论,小组配对练习"))
        self.assertEqual(["商务主题讨论", "小组配对练习"], record["enjoyed"])

    def test_multi_garbage_yields_empty(self):
        record, err = feedback.add_record(valid_payload(enjoyed={"a": 1}))
        self.assertIsNone(record)
        self.assertIn("喜欢的部分", err)

    # ── 读写 ──────────────────────────────────────────────────────────
    def test_roundtrip(self):
        feedback.add_record(valid_payload())
        records = feedback.load_records()
        self.assertEqual(1, len(records))
        self.assertTrue(records[0]["id"])
        self.assertTrue(records[0]["ts"])

    def test_delete_record(self):
        record, _ = feedback.add_record(valid_payload())
        self.assertTrue(feedback.delete_record(record["id"]))
        self.assertEqual([], feedback.load_records())
        self.assertFalse(feedback.delete_record("no-such-id"))

    def test_corrupt_file_returns_empty(self):
        feedback.RECORDS_FILE.write_text("{ broken", encoding="utf-8")
        self.assertEqual([], feedback.load_records())

    def test_wrong_shape_returns_empty(self):
        feedback.RECORDS_FILE.write_text(json.dumps({"records": "nope"}), encoding="utf-8")
        self.assertEqual([], feedback.load_records())

    # ── 统计与导出 ────────────────────────────────────────────────────
    def test_summarize(self):
        feedback.add_record(valid_payload(satisfaction=5, helpfulness="收获很大，学到实用表达",
                                          enjoyed=["商务主题讨论"], topics=["面试英文、职场自我介绍"],
                                          nickname="", comments="希望多安排案例讨论"))
        feedback.add_record(valid_payload(satisfaction=3, helpfulness="有一点帮助",
                                          enjoyed=["商务主题讨论", "小组配对练习"],
                                          topics=["面试英文、职场自我介绍"],
                                          comments="主题可以更聚焦一些"))
        s = feedback.summarize(feedback.load_records())

        self.assertEqual(2, s["total"])
        self.assertEqual(4.0, s["satisfaction_avg"])          # (5+3)/2
        self.assertEqual(2, s["satisfaction_count"])
        self.assertEqual(1, s["by_satisfaction"]["5"])
        self.assertEqual(1, s["by_satisfaction"]["3"])
        self.assertEqual(1, s["by_helpfulness"]["收获很大，学到实用表达"])
        self.assertEqual(1, s["by_helpfulness"]["有一点帮助"])
        self.assertEqual(2, s["by_enjoyed"]["商务主题讨论"])
        self.assertEqual(2, s["by_topics"]["面试英文、职场自我介绍"])
        self.assertEqual(2, s["comments_count"])
        self.assertEqual(1, s["nickname_count"])

    def test_summarize_empty(self):
        s = feedback.summarize([])
        self.assertEqual(0, s["total"])
        self.assertIsNone(s["satisfaction_avg"])

    def test_csv_bom_headers_and_multiselect(self):
        feedback.add_record(valid_payload())
        out = feedback.to_csv(feedback.load_records())
        self.assertTrue(out.startswith("\ufeff"))
        self.assertIn("整体满意度", out)
        self.assertIn("商务主题讨论", out)
        self.assertIn("报价、议价、订单谈判", out)   # 多选以顿号合并


class FeedbackRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app_module.app.test_client()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_file = feedback.RECORDS_FILE
        self._orig_token = app_module.ADMIN_TOKEN_FILE
        feedback.RECORDS_FILE = Path(self._tmp.name) / "feedback_records.json"
        app_module.ADMIN_TOKEN_FILE = Path(self._tmp.name) / ".admin_token"

    def tearDown(self):
        feedback.RECORDS_FILE = self._orig_file
        app_module.ADMIN_TOKEN_FILE = self._orig_token
        self._tmp.cleanup()

    def test_checkin_page_has_both_tabs(self):
        """一个二维码进来，签到 / 反馈两个部分可切换。"""
        resp = self.client.get("/checkin")
        self.assertEqual(200, resp.status_code)
        html = resp.get_data(as_text=True)
        self.assertIn("签到", html)
        self.assertIn("反馈", html)
        self.assertIn('data-tab="feedback"', html)
        self.assertIn("本次活动整体满意度", html)

    def test_feedback_page_defaults_to_feedback_tab(self):
        """旧反馈二维码（/ec-feedback）继续可用，进页直接落在反馈标签。"""
        resp = self.client.get("/ec-feedback")
        self.assertEqual(200, resp.status_code)
        html = resp.get_data(as_text=True)
        self.assertIn('const DEFAULT_TAB = "feedback"', html)

    def test_submit_and_list(self):
        resp = self.client.post("/api/ec-feedback", json=valid_payload())
        self.assertEqual(200, resp.status_code)
        self.assertTrue(resp.get_json()["ok"])

        listing = self.client.get("/api/ec-feedback/list").get_json()
        self.assertEqual(1, listing["stats"]["total"])
        self.assertEqual("希望多一点角色扮演", listing["records"][0]["comments"])

    def test_submit_missing_required_400(self):
        resp = self.client.post("/api/ec-feedback", json={})
        self.assertEqual(400, resp.status_code)
        self.assertFalse(resp.get_json()["ok"])

    def test_submit_placeholder_values_400(self):
        """绕过前端直接 POST 占位值，后端也必须拒（必填不被敷衍填绕过）。"""
        for payload in (
            valid_payload(comments="无"),
            valid_payload(comments="test"),
            valid_payload(nickname="无"),
            valid_payload(session="test"),
        ):
            resp = self.client.post("/api/ec-feedback", json=payload)
            self.assertEqual(400, resp.status_code, payload)
            self.assertFalse(resp.get_json()["ok"])

    def test_submit_invalid_400(self):
        resp = self.client.post("/api/ec-feedback", json=valid_payload(satisfaction=99))
        self.assertEqual(400, resp.status_code)
        self.assertFalse(resp.get_json()["ok"])

    def test_submit_non_json_400(self):
        resp = self.client.post("/api/ec-feedback", data="not json",
                                content_type="text/plain")
        self.assertEqual(400, resp.status_code)

    def test_csv_export(self):
        self.client.post("/api/ec-feedback", json=valid_payload())
        resp = self.client.get("/api/ec-feedback/export")
        self.assertEqual(200, resp.status_code)
        self.assertIn("text/csv", resp.headers["Content-Type"])
        self.assertIn("希望多一点角色扮演", resp.get_data(as_text=True))

    def test_admin_requires_token_when_configured(self):
        app_module.ADMIN_TOKEN_FILE.write_text("s3cret", encoding="utf-8")

        self.assertEqual(401, self.client.get("/api/ec-feedback/list").status_code)
        self.assertEqual(401, self.client.get("/api/ec-feedback/export").status_code)

        ok = self.client.get("/api/ec-feedback/list", headers={"X-Checkin-Token": "s3cret"})
        self.assertEqual(200, ok.status_code)

    def test_public_submit_stays_open_with_token_configured(self):
        """参与者填反馈是公开的：配了口令也不能挡住提交。"""
        app_module.ADMIN_TOKEN_FILE.write_text("s3cret", encoding="utf-8")
        resp = self.client.post("/api/ec-feedback", json=valid_payload())
        self.assertEqual(200, resp.status_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
