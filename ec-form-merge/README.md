# 英语角签到表并入反馈表 —— 一个二维码 · 签到 / 反馈双页切换

> 2026-11-24 · 对应 Feishu 需求：「把此反馈表的内容复制到我的英语角签到表中，将它们归纳为一份二维码，
> 进入二维码后是两个部分，一个签到一个反馈，两部分可切换，风格和设计复用现在签到表即可」。

## 交付了什么

1. **一个二维码一张页面**：`/checkin` 顶部新增「签到 / 反馈」两个切换标签（品牌同一套白底 + 海军蓝 + 金线）。
   - 默认落在「签到」；签到成功后多一个「顺便填一张反馈 →」入口。
   - 「反馈」页直接嵌在同一张页面上，提交成功后回到「感谢反馈」，可「再填一份」或「回到签到」。
2. **反馈内容照搬现行腾讯问卷**：`https://wj.qq.com/s2/28393446/v1z5/`
   《JFC 商业英语角｜活动反馈问卷》2026-11 版 6 题（标题、引导语、题目、选项、必填标记全部按原卷）。
   - 原卷「昵称」题自注「可不填」→ 唯一选填；其余 5 题按原卷必填（前后端各校验一次）。
   - 数据模型随之更新：`satisfaction` / `enjoyed` / `helpfulness` / `topics` / `nickname` / `comments`。
   - 后台统计与 CSV 导出同步改为新字段（平均满意度、满意度分布、帮助程度、喜欢的部分、想多排的主题）。
3. **一张合并二维码（A5 桌卡 + 二维码 PNG/SVG）**：`qr/`，编码 `https://datafusion.a.pinggy.link/checkin`；
   纠错 H、品牌海军蓝、静区 4 模块（沿用 `make_ec_feedback_qr.py` 的既有规格）。
4. **向后兼容**：旧反馈二维码指向的 `/ec-feedback` 保留，打开同一张合并页并默认落在「反馈」标签；
   已打印的签到/反馈桌卡都不作废。`feedback.html` 不再被路由使用（线上文件保留作回滚，可删）。
5. 签到侧（四项必填校验、断网队列、`?desk=1` 现场签到台、手机本地已签记录、管理端口令）行为未变。

## Before / After

| | Before | After |
|---|---|---|
| 扫码进来（签到） | 只有「活动签到」一个表单 | 顶部多「签到 / 反馈」切换；签到表单不变 |
| 反馈 | 另一个二维码 → 独立 `/ec-feedback` 页（旧 7 题） | 同一张页面的「反馈」标签，题目=现行腾讯问卷 6 题 |
| 二维码 | 签到、反馈各一张 | 一张（`/checkin`），反馈旧码仍可用 |

截图（390×844、同主题、同一手机视口）：

- `screenshots/before-checkin-top.png` / `screenshots/after-checkin-top.png`
- `screenshots/before-feedback-top.png` / `screenshots/after-feedback-top.png`（`after-feedback-full.png` 为整页）
- `screenshots/after-checkin-done.png`、`after-feedback-done.png`（提交成功态）
- `screenshots/after-admin-checkin.png`、`after-admin-feedback.png`（后台两个统计子页）

## 文件与落点

本目录是 **JFC 侧（语料/页面）** 的源码留档；DataFusion 仓库把英语角相关文件列在
`df/.git/info/exclude`（「借道部署，不入 DF 仓库历史」），所以改动在这里集中管理。

| 文件 | 部署落点（`~/Desktop/待办事件/df/`） |
|---|---|
| `feedback.py` | `feedback.py`（整文件替换） |
| `templates/checkin.html` | `templates/checkin.html`（整文件替换） |
| `templates/_ec_logo.html` | `templates/_ec_logo.html`（新增：logo data URI 抽成 partial，避免多处副本漂移） |
| `tests/test_feedback.py` | `tests/test_feedback.py`（整文件替换） |
| `tests/test_checkin.py` | `tests/test_checkin.py`（只改了「一张码两段」那条页面断言） |
| `app_ec_routes.diff` | `app.py` 只改 3 处：`/checkin` 与 `/ec-feedback` 两个路由 + 反馈日志行，见 patch |

部署后重启 Flask（守护 `启动DataFusion.command --launchd` 会在 ~30s 内自动拉起），
`/checkin` 与 `/ec-feedback` 都要 200。

## 验证

- 单测：`framework python3 tests/test_feedback.py`（31 项）、`tests/test_checkin.py`（26 项）全绿。
- 端到端（本地 8899 沙箱，真实浏览器 390×844）：
  签到提交 → 成功页 →「顺便填一张反馈」→ 6 题反馈提交（必填缺失会被拦）→ 成功页 →「再填一份」复位；
  `/ec-feedback` 默认落「反馈」标签；管理端「签到统计 / 反馈统计」切换、导出 CSV。
- 线上（`http://localhost:8888` 与本机 pinggy 隧道 `https://datafusion.a.pinggy.link`）：
  `/checkin`、`/ec-feedback` 均为合并页；二维码解码回 `https://datafusion.a.pinggy.link/checkin`。

## 边界与说明

- **反馈内容以腾讯问卷现行版为准**：本项目此前文档里的「现场版 7 题」是旧版，已不再使用；
  本次没有改知识库里的问卷设计文档（如需同步另开一张）。
- 反馈数据仍存 `feedback_records.json`，与签到 `checkin_records.json` 分开；旧 `feedback_records.json` 为空，无迁移。
- 反馈必填严格按腾讯问卷原卷（含「其他建议」必填）。若现场希望「不想写也能交」，把
  `feedback.py` 的 `REQUIRED_FIELDS` 去掉 `comments`、前端 `fbMissing()` 去掉对应一项即可。
- 管理端口令沿用 `.checkin_token`（签到/反馈共用）。

## 复现二维码

```bash
cd ~/Desktop/待办事件
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 make_ec_feedback_qr.py \
  --url "https://datafusion.a.pinggy.link/checkin" \
  --prefix "EC_签到反馈_一码" \
  --title-cn "JFC 英语角 · 签到与反馈" \
  --title-en "JFC English Corner — Check-in & Feedback" \
  --tip-cn "扫码进入 · 先签到，再花 1 分钟填反馈" \
  --tip-en "Scan once — check in, then share your feedback"
```
