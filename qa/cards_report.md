# QA 验收报告 · JFC / CSCV 可打印卡片（A6 双面 ×9，5 版式族）

- **结论：PASS — 可以通过，交付印刷。必须修复项：0。**（3 项建议见 §六，均不影响印刷/交付）
- 验收人：print-qa（独立印刷 QA；另写 `qa/cards_check.py` 复核，不复用 Lead 的 `cards/print_check.py`）
- 验收日期：2026-11-25
- 共享任务：task-7（本报告为最终版）
- 依据：`CARD-SPEC.md` §0/§1/§2/§3/§4/§6、`content/01_front.md` 第〇节事实表、task-7 验收清单、`deliverables/cards/PRINT-SPEC.md`、`assets/cards/images/SOURCES.md`
- 方法：① 独立脚本 82 项自动检查（PyMuPDF + Pillow：尺寸/页数/字体嵌入/有效 dpi/logo 识别/安全边/基线碰撞/局部对比度/内容 ↔ data.json/事实白名单/授权/预览一致性/哈希留档）；② 18 面 ×150dpi 预览逐面目视（`read_image`），照片带放大到 250–300dpi 复核品牌字与渐变；③ PDF 文本/几何抽样复核。

---

## 一、验收对象快照（最终版，2026-11-25 12:42–12:45 渲染）

| 文件 | 规格 | 哈希 | mtime |
|---|---|---|---|
| `cards/data.json`（冻结文案） | 9 卡 CN/EN；C3→`img3_inspection_v2.jpg`、C5→`img5_port_v2.jpg` | sha256 `7be272f61a05f648e13fe092846f12cc4a937915f165ba0a364e571942cc982b` | 12:40:56 |
| `deliverables/cards/print/C1_front.pdf` … `C9_back.pdf` | 18 个单面，111.17×154.18mm，3mm 出血 | 见 `qa/cards_check_summary.json` | 12:42:20–24 |
| `deliverables/cards/print/CSCV_FieldCards_v1_print.pdf` | 18 页合订（无裁切线，页面=111×154mm） | md5 `c775a2909ef65035c0ece6484f249921` | 12:42:24 |
| `deliverables/cards/print/CSCV_FieldCards_v1_print_marks.pdf` | 18 页，117×160mm，含 105×148 成品裁切线 | md5 `a6f5d5cebe76f2f0f644629128681da2` | 12:44 |
| `deliverables/cards/A4_office_proof.pdf` | 6 页 A4，96% 四拼，纯 ASCII 页眉，无出血 | md5 `450fc10db12adfddebe3d38e43c15b86` | 12:42:26 |
| `deliverables/cards/preview/` | 18×621×875px@150dpi + 3 张拼版 | all_cards `0d4a7c49791485ee4689c0d90473f40f`；all_fronts `f9a576573efbd28456661c3048d83a71`；all_backs `3bd70a9f0308e5151f886cfff00432df` | 12:42 |
| `deliverables/cards/PRINT-SPEC.md` | 5 版式族说明、裁切线文件、纸张/色彩/校对 | sha256 `5e86a81ace82b00e…`（12:45:03 版） | 12:45:03 |
| `assets/cards/images/SOURCES.md` | 现行 5 张（C3/C5 为 v2）+ 备选 + 排除清单 | — | 12:41:45 |

---

## 二、自动检查结果

**汇总：PASS 70 / FAIL 0 / WARN 3 / INFO 10，退出码 0。** 完整输出 `qa/cards_check_output.txt`，机读 `qa/cards_check_summary.json`（含逐项 findings、data.json sha256）。

| 组 | 检查 | 结果 |
|---|---|---|
| A 文件清单 | 18 单面 PDF、合订 PDF、**裁切线 PDF**、A4 试印版、18 预览 + 3 拼版、PRINT-SPEC、SOURCES、5 张现行图、2 logo | PASS |
| B 几何/页序 | 单面 111.17×154.18mm（±0.6mm 内）；合订 18 页、页序 C1 正/背…C9 正/背、与单面逐页文本+像素一致（mean\|Δ\|≤2/255）；裁切线 PDF 18 页 117×160mm、105×148 裁切线、内容与合订一致；A4 6 页、210×297mm、4-up、96%（100.8×142.0mm）、无出血、≈300dpi、FRONT/BACK 纯 ASCII 页眉 | PASS 15 项 |
| C 字体 | 18 面全部嵌入：Type3（PingFang SC，CharProcs 字形程序在 PDF 内）+ Type0/CID 子集（Menlo / Avenir Next Condensed，FontFile2）；`n/a` 仅用于 Type3；18 面文本可抽取 | PASS 6 项 |
| D 图片 | 5 张插图均触达出血边、有效 300.1dpi（logo 1947dpi）；logo 18/18 在页眉带（19.0×6.2mm；侧栏版式在内容列左缘 x=43.9mm，属设计）；纸面 navy / 深底 white 全部正确（逐图与源文件比对识别）；无 MISSING IMAGE；C1–C5 用图 = data.json = SOURCES 记录（与源图中心裁切 mean\|Δ\| 7–38）；C3/C5 为 v2，CARD-SPEC/SOURCES 已同步 | PASS 9 项 |
| E 排版 | 全部文字在 7mm 安全边内（最紧 10.0mm / 143.8mm，文件坐标），无文字进 3mm 出血；无基线碰撞；标题行数合规、无孤字/末行残字；首字母块 27.8mm（spec 28mm）；局部对比度（正文/小字）除 C9 侧栏竖排小字外均达标 | PASS 7 项 |
| F 内容 | 18 面 data.json 文案全部命中（大小写/空白不敏感，含侧栏版式的分栏页脚与短系列行）；C7/C8/C9 方括号占位与 C9「不得原样发布」提示保留；无客户名；「认证/担保」仅是否定句；无绝对化用语/感叹号；价格仅 1,800–3,000 / 3,200–4,500 元；5 & 7–10 工作日、8–12 页、100% 预付、电话/邮箱/地址、五条承诺、七步交付全部命中；无「建塔/建滔」 | PASS 11 项 |
| G data.json | 9 卡、C1–C9 顺序、5 版式映射、每面 3 要点、CN/EN 字数上限（C2 两条要点 24 字符=合规上限）、页脚逐字一致、员工卡字段齐全、photo 映射、C9 提示 | PASS 3 项 |
| H 文档 | PRINT-SPEC 与实际一致（111×154/105×148/3mm、18 页、裁切线文件 117×160、300–350g、CMYK、96% 四拼、SOURCES 引用、页序）；SOURCES 5 张现行图 + 备选均有文件/来源页/作者/授权/像素且像素与文件一致，photo 带 111mm 宽与渲染一致；Lead `PRINT-CHECK.txt`=PASS、`overflow-report.txt`=OK | PASS 14 项 |
| I 预览 | 18 张 621×875px@150dpi 与 PDF 裁切渲染一致（mean\|Δ\|≤3）；3 张拼版尺寸/构图正确 | PASS 4 项 |
| Z 留档 | data.json sha256、合订/A4/PRINT-SPEC 哈希+mtime、文件稳定性 | INFO 3 项 |

---

## 三、逐面视觉检查表（18 面，5 版式族）

图例：✔=通过；△=通过并记录设计约定。预览：`deliverables/cards/preview/Cn_side.png`（正面 CN / 背面 EN）。
渐变融边：5 张插图左侧（或上图下缘）均为柔化渐隐过渡，无硬切边（C1/C3/C4 照片带左缘渐隐、C2 全幅压字左侧暗渐变、C5 顶部照片带下缘融入墨底）；背面统一为「渐变过渡色条」。

| 面 | 版式族 | 标题/孤字 | 安全边 | 对比度 | Logo | 页脚/编号 | 插图/融边 | 结论 |
|---|---|---|---|---|---|---|---|---|
| C1_front | 照片带 + 左缘渐变 | 「从南沙，连接世界」1 行 ✔ | ✔ | 深字纸底 ✔ | navy ✔ | 单行联系行 + `C1 / 09 · NOV 2026` ✔ | 珠江新城天际线，左缘渐隐自然 ✔ | ✔ |
| C1_back | 纸面（渐变条+幽灵卡号） | EN 2 行 ✔ | ✔ | ✔ | navy ✔ | ✔ | 金橙渐变条过渡自然；幽灵 C1 约 5% 极淡 ▲（设计） | ✔ |
| C2_front | 全幅图压字（左侧暗渐变承文） | CN 2 行 ✔ | ✔ | 纸字墨底+左侧暗渐变，可读 ✔ | white ✔ | ✔ | 工厂车间长透视满幅，左侧暗渐变承标题/要点 ✔ | ✔ |
| C2_back | 深底（渐变条） | EN 2 行 ✔ | ✔ | ✔ | white ✔ | ✔ | 渐变条 + 幽灵 C2 ▲ | ✔ |
| C3_front | 高照片带 | CN 2 行 ✔ | ✔ | ✔ | navy ✔ | ✔ | v2：无面孔记录板场景，左缘渐隐；带高 52mm ✔ | ✔ |
| C3_back | 纸面（渐变条） | EN 2 行 ✔ | ✔ | ✔ | navy ✔ | ✔ | 渐变条 ✔ | ✔ |
| C4_front | 矮照片带 + 金色短规则 | CN 2 行 ✔ | ✔ | ✔ | navy ✔ | ✔ | 团队会议，人物完整未切头；带高 36mm，渐隐边 ✔ | ✔ |
| C4_back | 纸面（渐变条） | EN 2 行，无压字 ✔ | ✔ | ✔ | navy ✔ | ✔ | 渐变条 + 引句 ✔ | ✔ |
| C5_front | 顶部照片带（夜景港口 v2） | CN 2 行 ✔ | ✔ | ✔ | white ✔ | ✔ | 夜景港口/跨海大桥，**无可读航运品牌字**（v2 已替换）✔ | ✔ |
| C5_back | 深底（渐变条） | EN 2 行 ✔ | ✔ | ✔ | white ✔ | ✔ | 渐变条 + 引句 ✔ | ✔ |
| C6_front | 员工·墨底居中 | 人名 1 行 ✔ | ✔ | ✔ | white ✔ | ✔ | 无照片；JP 首字母块 27.8mm ✔（+淡色 ghost JP ▲设计） | ✔ |
| C6_back | 同上 | ✔ | ✔ | ✔ | white ✔ | ✔ | — | ✔ |
| C7_front | 员工·墨色侧栏 | `[姓名]` ✔ | ✔（页脚 3 行至 143.8mm，在边内） | ✔ | white（内容列左缘 x=43.9mm，设计） | 分栏 3 行联系 + `C7 / 09 · NOV 2026` ✔ | 左侧 34mm 墨色侧栏竖排系列字 ✔ | ✔ |
| C7_back | 同上 | `[Name]` ✔ | ✔ | ✔ | white ✔ | ✔ | 侧栏 + 幽灵 HV ▲ | ✔ |
| C8_front | 员工·纸面居中 | `[姓名]` ✔ | ✔ | ✔ | navy ✔ | ✔ | CD 首字母块；居中版式 + 幽灵 CD ▲ | ✔ |
| C8_back | 同上 | `[Name]` ✔ | ✔ | ✔ | navy ✔ | ✔ | — | ✔ |
| C9_front | 员工·橙色侧栏 | `[姓名]`/`[职位]` ✔ | ✔ | ✔（侧栏竖排小字见 §六-2） | navy（内容区）✔ | 分栏 3 行联系 + 编号 ✔ | 左侧 34mm 橙色侧栏 + 竖排 `JFC` ✔；含「不得原样发布」提示 | ✔ |
| C9_back | 同上 | `[Name]`/`[ROLE], JFC`（CSS 大写，渲染正确）✔ | ✔ | ✔ | navy ✔ | ✔ | 英文提示保留 ✔ | ✔ |

全部 18 面：文字不越界、不压安全边、无孤字/残字；深底/纸面/图面文字对比可读；logo 颜色随底正确；页脚联系行 + 卡号齐全；照片裁切自然、人物无切头（C4 为多人看镜头的轻摆拍，属素材特征，可接受）。

---

## 四、设计约定（此前告警的判定，均不计 FAIL）

1. **D1 logo 位置（C7/C9 侧栏版式）**：左侧 34mm 为墨色/橙色侧栏，logo 位于右侧内容列左上（x=43.9mm、y=10.1mm，尺寸 19.0×6.2mm）——视觉上仍为内容区左上角，侧栏版式设计如此。PASS。
2. **F1 C7/C9 页脚/系列行**：侧栏版式把联系行拆为 3 行（邮箱 / 电话 / 城市）且系列行缩为 `JFC · FIELD CARDS`；PDF 文本抽取在窄列 + PingFang Type3 下会把分栏行拼成无空格串，但 150dpi 预览目视邮箱/电话/广州南沙与系列字样均完整清晰。PASS。
3. **幽灵卡号/幽灵首字母**：背面 5–7% 透明度大号卡号、员工卡淡色首字母为本次设计语言（Lead 变更摘要第 4 条）；与 CARD-SPEC §2「不出现水印」的边界已由 Lead 确认接受，记为设计约定。
4. **首字母块 28×28mm**：CARD-SPEC §2 已更新，实测描边盒 27.8mm。PASS。
5. **A4 试印版页眉**：已改纯 ASCII `FRONT/BACK`，无替换字形。PASS。
6. **照片带高度因版式而异**（C1 111×44 / C2 111×154 满幅 / C3 111×52 / C4 111×36 / C5 111×44mm）：SOURCES/PRINT-SPEC 以「111×50mm」概括描述；实际按版式族变化，已记录（建议见 §六-3）。

---

## 五、内容与事实核对（PASS）

- **价格**：仅 `RMB 1,800–3,000` / `RMB 3,200–4,500`（CN：1,800–3,000 / 3,200–4,500 元/站），无其他金额；时限 5 / 7–10 个工作日；报告 8–12 页；100% 预付；七步交付；五条承诺（单边收费、不向被核验方收费/返点/礼品、方法不披露、只给时间窗、不认证/不撮合/不担保）；24 小时响应。
- **联系方式**：`JFC.Consulting@outlook.com` · `+86 189 2872 4769` · 广州南沙 / Nansha, Guangzhou，18 面逐字一致（侧栏版式为分栏形式）。
- **合规**：无客户名；「认证/certification」「担保/guarantee」均为否定用法（「不认证…不担保」「No certification…no guarantee」）；无最/第一/唯一/领先/最佳等绝对化用语；无感叹号；无年限/履历虚构；无「建塔/建滔」。
- **占位**：C7/C8 `[姓名]/[Name]`、C9 `[职位]/[Role]/[功能括号]` 保留，C9 双语「不得原样发布」提示在。
- **事实表之外但可溯源**：C1「大湾区中小企业/精品国际咨询」← `source/company_profile.txt`、`source/service_portfolio.txt`；C8「15 分钟·三样信息」← `WORKBRIEF.md §4.2 B3`；C7「广东及周边省份」← B2 职责口径。建议发布前由岗位本人确认（C7/C8）。

---

## 六、建议项（不阻断交付，3 项）

1. **出血最外缘 0.17mm 未印白边（D9，全部 18 面右/下）**：Chromium 将 111×154mm 页盒圆整到整数 CSS px，页面最外缘约 0.17mm 纯白。位于 3mm 出血内、成品裁切即去除，不影响成品；如未来重印，可把背景/色条外扩 0.3mm 或按精确页面盒输出。
2. **C9 橙色侧栏竖排小字对比度（E10）**：`JFC · FIELD CARDS` 竖排 3.4pt 用 `#8C998F`（灰绿），在橙色 `#E4572E` 侧栏上对比约 1.2–1.4:1，实际不可读（C9_front/C9_back 各一处）。若该字样应被看见，建议改纸色 `#F4EFE5` 或深墨 `#0E1A17`（≥3:1）；若刻意做隐藏纹理可保留。其余 3–4pt 微字（卡号、SCOPE 标签、A4 页眉）对比 2.2–4.7:1，属可接受的细字/装饰级。
3. **文档一致性小项**：`SOURCES.md`/`PRINT-SPEC.md` 以 111×50mm 概括照片带，实际按版式族为 36–52mm（C2 满幅）——建议在 PRINT-SPEC 加一行"照片带高度随版式族变化（36–52mm）"；另 `PRINT-SPEC §6` 称「所有卡片内容集中在 cards/data.json」，但 C6–C9 的 quote/skills 仍硬编码在 `cards/templates/layouts.py`（F3），建议迁入 data.json 或改措辞，便于日后维护。

---

## 七、限制与免责

1. 本报告为**屏幕/PDF 与 150dpi 预览校对**，非真机打样：屏幕 RGB 与印厂 CMYK 存在色差；C2/C5/C6 深底大面积实地建议先数码打样 1 张确认墨量与露白；300–350g 白卡/哑粉最终手感未验证。
2. 照片有效分辨率 300.1dpi 为 Chromium 输出上限、**恰好达标**；如印厂要求 350dpi 或需放大，应提高输出分辨率。
3. Type3（PingFang SC）已嵌入且矢量，个别印厂 RIP 对 Type3 兼容性差时可用印厂要求的转曲/CID 方式加固（可选，不是缺陷）。
4. 品牌字/肖像在成品 A6 上的可辨识度：C5 已换无品牌字 v2（已复核无 MSC/EUROGATE 等可读文字）；C4 两处 Apple 标记约 2.5–3mm、非主体，SOURCES 已如实披露。
5. A4 试印版（96%、无出血、纯 ASCII 页眉）仅供内部校对，不能用于成品裁切验收；裁切线版本 `*_marks.pdf` 已单独核验（117×160mm、105×148 裁切线）。
6. 本报告只对 §一 所列哈希版本负责；任何重渲/改图/改文案后须重新验收。

---

## 八、复跑与证据

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 qa/cards_check.py
# → qa/cards_check_output.txt（人读 70 PASS / 0 FAIL / 3 WARN / 10 INFO）
# → qa/cards_check_summary.json（逐项 findings + data.json sha256）
# 只读交付物；脚本只写 qa/ 下文件。退出码 0 = 无 FAIL。
```

- `qa/evidence/C5_front_band_final.png`：C5 新版夜景港口照片带（无品牌字）。
- `qa/evidence/sidebar_layouts_C7_C9.png`：C7 墨色侧栏 / C9 橙色侧栏版式。
- `qa/evidence/C5_front_band_brandmarks_superseded_1233.png`、`C4_front_band_brandmarks_1233.png`：**旧版（12:33）**证据——C5 旧图 MSC/EUROGATE 品牌字问题已在最终版替换 v2 后消除，留存备查。
- `qa/evidence/footer_baselines_superseded_1227.png`、`A4_proof_label_CJK_superseded.png`：旧版问题证据（页脚未对齐、A4 页眉中文缺字），最终版均已修复。

---

**验收判定：PASS。必须修复项：无。** 3 项建议（出血外扩、C9 侧栏小字对比度、文档小项）可在重印或后续版本处理，不影响本次印刷交付。
