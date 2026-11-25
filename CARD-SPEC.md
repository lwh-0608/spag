# CARD-SPEC · JFC / CSCV 可打印介绍卡片（v1）

Levi 2026-11-25 12:11 更正需求后的工作说明。此前的纯文本物料（v2 kit）只作为内容来源；本次交付是**可打印的介绍卡片 + 宣传卡片**：
- 参考 JFC 过往任务卡片（公司介绍卡、SME 问卷卡）的用途与体量；
- 用 Ego 浏览器上网找插图；
- 按内容要求排版，卡片后续要打印。

## 0. 卡片清单（9 张双面卡）

每张卡：正面中文、背面英文（沿用 JFC SME 问卷卡「正面中文 / 背面英文」的做法）。尺寸 A6 竖版 105×148mm。

| 编号 | 卡片 | 布局族 | 正面中文标题（定稿以 data.json 为准） | 图片来源 |
|---|---|---|---|---|
| C1 | JFC 公司介绍卡 | promo-paper | 从南沙，连接世界 | 城市/办公场景 |
| C2 | CSCV 服务卡 | promo-ink | 付款之前，把「能不能生产」变成事实 | 工厂/工业场景 |
| C3 | 核验流程与证据卡 | promo-paper | 七步核验，一份可审计的证据 | 现场核验/记录场景 |
| C4 | JFC SME 业务卡 | promo-paper | 订阅制咨询成果，不增加编制 | 中小企业团队/办公 |
| C5 | 转介绍合作卡 | promo-ink | 你的客户问：这家工厂靠谱吗？ | 港口/货代/物流 |
| C6 | 员工介绍卡 · 创始合伙人 | staff-ink | JFC 创始合伙人 | 无照片（字体+首字母） |
| C7 | 员工介绍卡 · 核验主管 | staff-paper | JFC 核验主管 | 无照片 |
| C8 | 员工介绍卡 · 客户开发负责人 | staff-paper | JFC 客户开发负责人 | 无照片 |
| C9 | 员工介绍卡 · 通用模板 | staff-paper | JFC [职位] | 无照片 |

说明：C6 用已公开的创始人姓名 Jonathan Paets；C7/C8 姓名未知，用 `[姓名]` 占位（打印前由本人填写）；C9 为通用模板，保留方括号并注明不得原样发布。

## 1. 每面内容结构（数据字段）

A6 竖版信息量有限，每面只放：眉标、标题、副题、3 条要点、页脚。

- `eyebrow_cn` / `eyebrow_en`：1 行小字，如“02 / CSCV · 服务”“02 / CSCV · SERVICE”。
- `title_cn` / `title_en`：主标题，中文 ≤ 16 字（2 行内），英文 ≤ 60 字符。
- `sub_cn` / `sub_en`：副题，中文 ≤ 30 字，英文 ≤ 90 字符。
- `points`：3 条，每条 `{num, cn, en}`；中文 ≤ 24 字，英文 ≤ 60 字符（单行或两行）。
- `footer`：固定联系行——`JFC.Consulting@outlook.com · +86 189 2872 4769 · 广州南沙`（英文面 `JFC.Consulting@outlook.com · +86 189 2872 4769 · Nansha, Guangzhou`）。
- 员工卡额外字段：`name_cn`、`name_en`、`role_cn`、`role_en`、`headline_cn`、`headline_en`、`points`。
- 页脚右下统一小字：`JFC · CSCV FIELD CARDS · NOV 2026` + 卡片编号 `C1 … C9`。

事实与措辞边界：只用 `content/01_front.md` 第〇节事实表（价格、时限、承诺、地址、邮箱、电话）。不写客户名称、不写“认证/保证/绝对化用语”，不写无法核实的从业年限。中文自然、英文美式，两版事实一致、不是逐句直译。

## 2. 视觉系统（印刷版）

- 纸色 `#F4EFE5`；墨色 `#0E1A17`；信号橙 `#E4572E`；琥珀 `#F2B544`；灰绿 `#7E9B87`；纸面正文墨 `#14201C`；纸面弱文 `#6B665C`；深底正文纸色 `#F4EFE5`。
- 字体：中文 PingFang SC；英文 Avenir Next；编号/眉标/页脚用 Menlo（等宽，字号小、字距开）。
- 版式：A6 竖版；出血 3mm（成品 105×148 → 文件 111×154）；安全边距 7mm；网格 3 栏逻辑（左对齐主内容 + 右下页脚）。
- 纸面卡：纸底 + 墨字 + 橙色编号 + 金色细线 + 全宽照片带（双色调处理，靠 CSS filter/mix-blend-mode 或预生成处理图）。
- 深底卡：墨底 + 纸字 + 橙色强调 + 照片带（更暗、更强对比）。
- Logo：纸面用深色 logo（`assets/cards/logo_navy.png`）；深底用白色 logo（`assets/cards/logo_white.png`）。Logo 宽约 20mm，左上角。
- 员工卡：无照片；右侧或上方放 28×28mm 的“首字母块”（墨底/纸底方块 + 橙色首字母 + 细线），其余为文字编排。
- 不许出现：emoji、渐变彩虹、描边艺术字、水印、二维码（没有可用落地页，先不放码）。

## 3. 印刷规格与交付

- 单卡成品：A6 竖版 105×148mm；出血 3mm；文件尺寸 111×154mm；图片 ≥300dpi（长边 ≥2000px 原图）。
- 交付：
  - `deliverables/cards/print/C1_front.pdf` … `C9_back.pdf`：每面一个 PDF（111×154mm，含出血，背景铺满）。
  - `deliverables/cards/print/CSCV_FieldCards_v1_print.pdf`：全部 9 张正反面合订（18 页，111×154mm），供印厂整单。
  - `deliverables/cards/preview/*.png`：每面 150dpi RGB 预览图。
  - `deliverables/cards/preview/all_cards_preview.png`：9 张正面 + 背面的拼版总览。
  - `deliverables/cards/A4_office_proof.pdf`：办公室试印版（A4，4 张/页，成品尺寸、无出血，供校对，不用于正式印刷）。
  - `deliverables/cards/PRINT-SPEC.md`：尺寸、出血、纸张建议（300–350g 白卡/哑粉）、双面、颜色（RGB 交付，印厂转 CMYK）、图片版权来源清单、校对注意。
- 生成流程：HTML/CSS（`cards/templates/`）→ Playwright Chromium 打印 PDF（`cards/render.py`）→ PDF 合成/预览（PyMuPDF）。
- 视觉复核：每面渲染 PNG 目视检查文字溢出、边距、logo、照片裁切；出错即修。

## 4. 图片（Ego 浏览器）

需要 5 张印刷级照片（用于 C1–C5 的照片带，纸面/深底各一张）：

| 编号 | 用于 | 画面需求 | 搜索方向 |
|---|---|---|---|
| IMG1 | C1 公司介绍 | 广州/南沙城市或现代办公空间，明亮、克制 | “Guangzhou Nansha skyline”, “modern office workspace” |
| IMG2 | C2 CSCV 服务 | 工厂/车间/工业建筑，暗调有质感 | “factory exterior industrial”, “warehouse interior” |
| IMG3 | C3 流程与证据 | 现场核验：戴安全帽/手持记录板/检查设备 | “factory inspection clipboard hard hat”, “quality inspector warehouse” |
| IMG4 | C4 SME 业务 | 中小企业团队会议/办公协作，真实不摆拍 | “small business team meeting”, “startup office collaboration” |
| IMG5 | C5 转介绍 | 港口集装箱/货代物流，暗调 | “container port crane”, “freight logistics containers” |

要求：Unsplash / Pexels / CC0 等可商用免费授权；长边 ≥2000px；无水印、无文字、无醒目品牌 logo；避免明显白人家庭合照式摆拍；记下来源页 URL、作者、授权类型，写入 `assets/cards/images/SOURCES.md`。下载原图到 `assets/cards/images/`，命名 `img1_city.jpg` 等。找不到合格的就报缺口，不要用低清图凑数。

## 5. 文件与分工

- `CARD-SPEC.md`（本文件）——Lead
- `cards/data.json`——卡片文案（CN/EN），内容写作者
- `cards/templates/style.css`、`cards/templates/*.html`、`cards/render.py`——Lead
- `assets/cards/logo_navy.png`、`logo_white.png`——Lead 从既有品牌素材导出
- `assets/cards/images/*`、`SOURCES.md`——图片侦察员（Ego 浏览器）。C3 使用替换版 `img3_inspection_v2.jpg`（无面孔记录板场景）。
- `deliverables/cards/`——Lead 生成
- `qa/cards_report.md`——印刷 QA 验收员

## 6. 验收

- 9 张卡 × 2 面全部渲染成功，PDF 尺寸 = 111×154mm，图片出血铺满，无文字越界/压边（安全边 7mm 内）。
- 字体全部嵌入（PingFang SC / Avenir Next / Menlo），图片有效分辨率 ≥300dpi。
- data.json 文案事实与事实表逐字一致；中英对应；无违禁表述。
- 每面预览目视通过；A4 试印版拼版正确；SOURCES.md 图片授权可追溯。
