# JFC / CSCV · 官方社媒背景横幅模板 / Official Social Banner Template Kit

JFC 公司品牌与 CSCV 视觉品牌的官方社交平台背景横幅模板。覆盖领英（个人主页 / 公司主页）、X、Facebook、YouTube 五种尺寸，每个品牌 5 张、共 10 张可直接上传的 PNG，附可编辑 HTML 源文件、品牌规范、生成与校验脚本。

Official background-banner templates for the JFC company brand and the CSCV visual brand. Five formats per brand — LinkedIn personal profile, LinkedIn company page, X, Facebook and YouTube — ten ready-to-upload PNGs, with editable HTML sources, the brand guide, and build/QA scripts.

| | |
|---|---|
| 品牌 Brand A | **JFC · 机构蓝 / Institutional Blue** — official logo, navy `#0A295B`, ice `#E7F0FD`, logo blue `#2C63E0`, green signal `#2E9D74` |
| 品牌 Brand B | **CSCV · 现场档案 / Field Dossier** — paper `#F1EDE3`, ink `#0A0D10`, signal orange `#FF4D00`, verify green `#37E08A` |
| 尺寸 Formats | `linkedin-personal` 1584×396 · `linkedin-company` 1512×256 · `x-header` 1500×500 · `facebook-cover` 820×360 · `youtube-channel` 2560×1440 |
| 交付 Deliverables | 10 PNG (`banners/<brand>/png/`, 1× + @2×) · 品牌指南 PDF (`guide/`) · 平台示意图与安全区 (`preview/`) · 源文件与脚本 (`banners/`) |

## 快速开始 / Quick start

1. 打开 `guide/JFC_CSCV_Social_Banner_Kit_CN-EN.pdf`，按平台选图版。
2. 上传 `banners/<brand>/png/<format>.png`；平台接受更大图时用同名 `@2x.png`。
3. 需要改文案或改配色：先读 `DESIGN-BRIEF.md` 与 `guide/`，再按下面的命令重新生成。

```bash
PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
$PY banners/kit/tools/build.py      # 生成全部 PNG + QA + 安全区图
$PY banners/kit/tools/preview.py    # 平台 before/after 示意图 + 总览图
$PY guide/build_guide.py            # 生成品牌指南 PDF
```

## 目录 / Layout

```
banners/kit/    共享系统：tokens、批准文案、平台尺寸/安全区、官方 logo、字体、渲染与 QA 工具
banners/jfc/    JFC 机构蓝：src/*.html 源文件、png/ 成品、NOTES.md
banners/cscv/   CSCV 现场档案：src/*.html 源文件、png/ 成品、NOTES.md
preview/        contact-sheet.png、mockups/ before-after 平台示意图、safe-zones/ 安全区图
guide/          品牌指南（PDF + HTML/CSS 源）
qa/             build.py 输出的校验报告
DESIGN-BRIEF.md 设计口径与验收标准
DELIVERY.md     交付说明、验证记录与已知边界
```

## 约束 / Constraints

- 只使用官方 logo、品牌色与冻结文案；不写价格、客户名、认证、保证或未经核实的数字。
- 中英双语成对出现（中文在前，英文紧随），英文使用美式拼写。
- 官方 logo 不重绘、不拉伸、不改色：navy 上用白色版，浅色上用彩色版。
- 字体：Archivo / Inter / JetBrains Mono（SIL OFL 1.1，已内嵌 woff2）；PingFang SC 与 Avenir Next 为 macOS 系统字体，不随模板分发。

更多细节见 `DELIVERY.md` 与 `guide/`。
