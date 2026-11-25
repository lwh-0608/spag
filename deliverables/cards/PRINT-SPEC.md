# JFC · CSCV FIELD CARDS — 印刷规格与交付说明

本文件是卡片印刷的交接说明。卡片设计文件在 `deliverables/cards/`，源稿与生成脚本在 `cards/`、`assets/cards/`。

## 1. 卡片清单（9 张 · 双面）

| 编号 | 卡片 | 正面 | 背面 | 布局（正面 / 背面） |
|---|---|---|---|---|
| C1 | JFC 公司介绍卡 | 中文 | English | 纸面 + 照片带（左缘渐隐）/ 纸面文字 |
| C2 | CSCV 服务卡 | 中文 | English | 墨底全幅图压字（左侧暗渐变）/ 墨底文字 |
| C3 | 核验流程与证据卡 | 中文 | English | 纸面 + 高照片带（左缘渐隐）/ 纸面文字 |
| C4 | JFC SME 业务卡 | 中文 | English | 纸面 + 矮照片带 + 金色短规则 / 纸面文字 |
| C5 | 转介绍合作卡 | 中文 | English | 墨底 + 顶部照片带（左缘渐隐）/ 墨底文字 |
| C6 | 员工介绍卡 · 创始合伙人 | 中文 | English | 墨底居中 |
| C7 | 员工介绍卡 · 核验主管 | 中文 | English | 纸面 + 墨色侧栏 |
| C8 | 员工介绍卡 · 客户开发负责人 | 中文 | English | 纸面居中 |
| C9 | 员工介绍卡 · 通用模板 | 中文 | English | 纸面 + 橙色侧栏 |

## 1.1 设计说明

- 插图与内容之间为宽渐变过渡（照片左缘向纸色/墨色渐隐），不是硬切边。
- 9 张卡使用 5 种版式族（照片带、全幅压字、顶带、居中、侧栏），避免同一模板重复。
- 背面为文字面：渐变过渡色条 + 幽灵卡号，引句在上、要点贴底，与正面形成层次。
- C5 照片为夜景港口（Pexels 13337017，无任何可读品牌文字）；C3 为无面孔记录板场景（Pexels 12234106）。

## 2. 印刷规格

- 成品尺寸：A6 竖版，105 × 148 mm。
- 裁切线：`CSCV_FieldCards_v1_print_marks.pdf` 为 117×160mm 带四角裁切线版本（成品线 105×148mm）；无裁剪线版本见 `CSCV_FieldCards_v1_print.pdf`，页面即 111×154mm（成品+3mm 出血）。
- 出血：每边 3 mm。单面文件尺寸：111 × 154 mm，背景与照片铺满到出血边。
- 安全边：成品边向内 7 mm 内不放正文（文件边向内 10 mm）。
- 分辨率：照片 ≥ 300 dpi；文字与线条为矢量。
- 字体：PingFang SC、Avenir Next、Menlo（macOS 系统字体），PDF 内已嵌入。
- 颜色：交付 RGB PDF；请印厂按 CMYK 转换。深底墨色 `#0E1A17`、纸色 `#F4EFE5`、信号橙 `#E4572E`、金 `#C8963E`，深底大面积实地建议用专色或高覆盖印刷，避免露白。
- 建议纸张：300–350 g 白卡纸或哑粉纸；深底卡建议哑膜，避免指纹与反光。
- 双面：正面中文、背面英文；按「短边翻转（duplex, flip on short edge）」双面印刷。
- 印后：可选圆角 R3；无需覆膜与烫金。

## 3. 交付文件

| 文件 | 用途 |
|---|---|
| `deliverables/cards/print/C1_front.pdf` … `C9_back.pdf` | 单面印刷文件（111×154 mm，含 3 mm 出血） |
| `deliverables/cards/print/CSCV_FieldCards_v1_print.pdf` | 整单文件：9 张卡 × 正反面，共 18 页，按 C1 正/背、C2 正/背…排序 |
| `deliverables/cards/print/CSCV_FieldCards_v1_print_marks.pdf` | 带裁切线的整单文件：117×160mm 页面，内含 111×154mm 出血盒与 105×148mm 成品裁切线，适合直接送印 |
| `deliverables/cards/A4_office_proof.pdf` | 办公室试印版（A4，96% 缩放，4 张/页），仅供校对，不用于正式印刷 |
| `deliverables/cards/preview/*.png` | 每面 150 dpi 预览图 |
| `deliverables/cards/preview/all_cards_preview.png` | 9 张卡正反面拼版总览 |
| `deliverables/cards/PRINT-CHECK.txt` | 自动打印检查结果（尺寸、页数、字体嵌入、图片有效 dpi） |
| `deliverables/cards/preview/all_cards_preview.png` | 9 张卡正反面总览（评审用） |
| `deliverables/cards/PRINT-SPEC.md` | 本文件 |

## 4. 图片版权来源

正式印刷使用的照片及其授权记录见 `assets/cards/images/SOURCES.md`。图片均为可商用免费授权（Unsplash / Pexels / CC0），已下载原图并记录来源页、作者与授权类型。**印厂不得从其他渠道替换图片。**

## 5. 打印前校对清单

- [ ] 9 张卡正反面文字无误，中英事实一致。
- [ ] 出血与安全边：无正文被裁切线穿过（文件已按 7mm 安全边排版，A4 试印可复核）。
- [ ] 深底卡大面积墨色印刷效果（建议先数码打样一张）。
- [ ] 图片 dpi 与版权：见 `PRINT-CHECK.txt` 与 `SOURCES.md`。
- [ ] C7 / C8 的 `[姓名]`、C9 的 `[职位]` 等方括号字段已由本人填写或删除（模板不得原样印刷）。
- [ ] 联系方式与事实表一致：`JFC.Consulting@outlook.com`、`+86 189 2872 4769`、`广州南沙`。

## 6. 修改与重出

所有卡片内容集中在 `cards/data.json`；版式在 `cards/templates/`。改文案或换图后运行：

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 cards/render.py
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 cards/print_check.py
```

即可重新生成全部印刷文件、预览与 A4 试印版。
