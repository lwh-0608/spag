# 交付说明 · JFC / CSCV 官方社媒背景横幅模板

**Deliverables · Social banner template kit v1.2 · November 2026**

## 1. 这是什么 / What this is

一套可复用、可重新生成的官方社交平台背景横幅模板，覆盖两条品牌线：

- **JFC 公司品牌 · 机构蓝（Institutional Blue）** — 沿用 JFC 公司简介与服务组合的官方视觉：官方 logo、navy `#0A295B`、冰蓝 `#E7F0FD`、官方 logo 蓝 `#2C63E0`、细绿信号线 `#2E9D74`；Avenir Next + PingFang SC。
- **CSCV 视觉品牌 · 现场档案（Field Dossier）** — CSCV 服务线 2026 年 11 月的视觉系统：暖纸 `#F1EDE3`、墨黑 `#0A0D10`、信号橙 `#FF4D00`、核验绿 `#37E08A`；Archivo / Inter / JetBrains Mono + PingFang SC；定位十字、刻度线、证据章、条形码。文案同步至 2026-11-26 最新批准的 CSCV 宣传卡信息（Gordon 修订版）：专为无法亲临现场的买家设计、每一项发现均有可审计的证据支撑、只向买家收费。

每个品牌 5 个平台尺寸，共 **10 张成品 PNG**（1× 与 @2×），另附 HTML 源文件、品牌指南 PDF、平台 before/after 示意图、安全区叠加图与生成/校验脚本。

## 版本记录 / Revision history

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-11-26 | 首版：JFC 机构蓝 + CSCV 现场档案，5 个平台尺寸 × 2 品牌 |
| v1.1 | 2026-11-26 | 按评审把 CSCV 文案「付款之前」改为「采购之前」（英文 before procurement） |
| v1.2 | 2026-11-26 | 按 CSCV 最新信息（Gordon 修订版宣传卡，2026-11-25；USD 价格版正式卡 2026-11-26）同步横幅文案：标题、证据句、只向买家收费；JFC 服务行同步为「专为无法亲临现场的买家设计」 |

## 2. 文件清单 / Files

| 路径 | 内容 |
|---|---|
| `banners/jfc/png/` | JFC 5 张成品（`linkedin-personal.png` … `youtube-channel.png`，含 `@2x`） |
| `banners/cscv/png/` | CSCV 5 张成品（同上） |
| `banners/jfc/src/`、`banners/cscv/src/` | 可编辑 HTML 画板（精确画布尺寸、绝对定位、共用 kit CSS） |
| `banners/kit/` | 共享系统：`tokens.py`（品牌色/字体）、`copydeck.py`（批准文案）、`platform_specs.py`（画布与安全区）、`css/`、`assets/`（官方 logo、叶片、OFL 字体）、`tools/`（render/build/preview） |
| `guide/JFC_CSCV_Social_Banner_Kit_CN-EN.pdf` | 品牌指南（中文在前、英文紧随）：两套品牌、尺寸与安全区、上传方式、修改与再生成、授权 |
| `preview/contact-sheet.png` | 10 张模板总览 |
| `preview/mockups/*.png` | 平台界面示意图（before = 无横幅 / after = 套用模板），领英为主，X/Facebook/YouTube 同法 |
| `preview/safe-zones/*.png` | 每张模板的安全区叠加图（绿虚线 = 必须可见；红斜纹 = 平台 UI 遮挡） |
| `qa/report.md`、`qa/report.json` | 自动校验报告 |
| `DESIGN-BRIEF.md` | 设计口径、品牌规则、验收标准 |
| `build.sh` | 一键重新生成（PNG + 示意图 + 指南） |

## 3. 平台尺寸与安全区 / Formats and safe areas

| slug | 平台 | 画布 Canvas | 安全区 safe (x,y,w,h) | 平台 UI 遮挡 blocked | 依据 |
|---|---|---|---|---|---|
| `linkedin-personal` | 领英 · 个人主页背景 | 1584×396 | 24,24,1536,348 | 头像 40,324,152,72 | Sprout Social / Buffer 2026 |
| `linkedin-company` | 领英 · 公司主页封面 | 1512×256 | 24,24,1464,208 | 公司 logo 30,206,120,50 | LinkedIn Help（Page cover 1512×256） |
| `x-header` | X（Twitter）· 页头 | 1500×500 | 24,40,1452,420 | 头像 0,360,220,140 | Snappa 2026 |
| `facebook-cover` | Facebook · 主页封面 | 820×360 | 90,24,640,312 | 头像 0,270,100,90 | Snappa / SocialBee（桌面 820×312，手机 640×360） |
| `youtube-channel` | YouTube · 频道封面 | 2560×1440 | 507,508,1546,423 | — | Snappa（标准安全区 1546×423） |

安全区 = 所有设备/裁切下必须可见的区域；装饰（网格、十字标记、条形码、出血字）可以越界，文字与 logo 不能。
完整链接与说明见 `banners/kit/platform_specs.py` 与指南第 5 页。

## 4. 验证 / Verification

- **自动检查（`banners/kit/tools/build.py`）**：10/10 通过、0 失败、0 警告。每张横幅检查导出尺寸精确、单画板无页面溢出、关键内容在安全区内且不进入平台 UI 遮挡区、无文字碰撞、所需字体已加载（JFC：Avenir Next + PingFang SC；CSCV：Archivo + Inter + JetBrains Mono + PingFang SC）、中英双语成对、最小字号 ≥ 9.5px（实际最小 10.5px，仅 meta）。结果见 `qa/report.md` / `qa/report.json`。
- **视觉复核**：10 张成品逐张 `read_image` 复核；10 张 `--overlay` 安全区叠加图逐张检查（`preview/safe-zones/`）；10 组平台界面 before/after 示意图（`preview/mockups/`）复核在真实版式中的呈现，并模拟 Facebook 手机裁切、YouTube 桌面/移动安全区切片。
- **指南**：`guide/build_guide.py` 校验 PDF 7 页、22 张引用图片无断链、页面无溢出；指南中文在前、英文紧随，已逐页目检。
- **文案口径**：只用官方 logo、既有对外文案与 CSCV 服务定义 v2 的事实；不含价格、客户名、认证、保证或未经核实的数字（73% 等统计数字不上横幅）。每张横幅在保证可读性的前提下按尺寸取舍二级文案：JFC 四服务定位出现在个人主页与 X 版，公司主页 / Facebook / YouTube 保留品牌主张 + CSCV 服务线；CSCV 版按尺寸省略 three / scope / meta 等次级行。逐版记录见 `banners/*/NOTES.md`。

## 5. 使用与再生成 / Use and regeneration

1. 按平台上传 `banners/<brand>/png/<format>.png`；平台接受更大图时可上传同名 `@2x.png`。不要裁切或拉伸。
2. 改文案：先改 `banners/kit/copydeck.py`（批准文案记录），再改对应 `src/*.html` 文本，然后重新生成——不要只改 PNG。
3. 重新生成：

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/build.py      # 全部 PNG + QA + 安全区图
$PY banners/kit/tools/preview.py    # before/after 示意图 + 总览
$PY guide/build_guide.py            # 指南 PDF
```

## 6. 已知边界 / Limitations

- 未包含微信朋友圈 / 公众号等中国平台尺寸。可按同一系统扩展：新增 `platform_specs.py` 条目与对应的 `src/*.html` 即可。
- 平台会调整版式与裁切规则；上传前若平台已改版，请重新核对尺寸与安全区（本版规格核对于 2026 年 11 月）。
- 平台界面示意图为示意，非真实截图；用于说明横幅在版式中的位置，不代表平台最终呈现。
- 文案为对外口径，发布前仍建议业务/合规最终确认（尤其涉及地址、联系方式）。
- 字体：Archivo / Inter / JetBrains Mono 以 SIL OFL 1.1 内嵌（见 `banners/kit/assets/fonts/OFL-*.txt`）；PingFang SC、Avenir Next 为 macOS 系统字体，未随模板分发，其他系统回退到 Microsoft YaHei / Arial。
- 官方 logo 由 JFC 提供，仅用于 JFC/CSCV 官方物料；不重绘、不拉伸、不改色。
- 本套不使用摄影图，避免版权与裁切问题；如后续需要照片版，应按 CSCV 现场档案规范使用示意图并标注 illustrative。

## 7. 来源与口径 / Sources

- JFC 官方 logo（彩色 / 白色透明底）与公司简介、服务组合的 brand 层。
- CSCV Service Definition v2（2026 年 11 月）与 **2026-11-26 最新批准的 CSCV 宣传卡文案**（Gordon 修订版 DOCX，2026-11-25；正式版宣传卡以 USD 价格发布）：专为无法亲临现场的买家设计、每一项发现均有可审计的证据支撑、只向买家收费、五条铁律、15 年供应链团队 / 美国创始人等。横幅不展示价格；价格口径见宣传卡。
- CSCV 现场档案设计系统：`bizmodel-redesign-8d2bab8a14d8/design/README.md`（2026-11-25）。
- 平台尺寸：LinkedIn Help、Sprout Social、Buffer、Snappa、SocialBee（2026-11 核对，链接在 `platform_specs.py`）。
