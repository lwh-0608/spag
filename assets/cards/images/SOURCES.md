# 图片来源清单 · SOURCES

JFC / CSCV 可打印卡片（A6 竖版 105×148mm，见 `CARD-SPEC.md §4`）照片带用图。

- 下载日期：**2026-11-25**（Asia/Shanghai）
- 查找方式：Ego 浏览器（Chromium）→ Bing 图片搜索（限定 `site:unsplash.com` / `site:pexels.com`）→ 打开图片详情页提取原图 URL 与作者/授权 → `node fetch` 下载原图（非缩略图）
- 文件位置：`assets/cards/images/`
- 用途：C1–C5 五张卡片的 111×50mm 照片带（CSS `object-fit: cover` 中心裁切；模板内做灰度 + 双色调处理）

## 授权总述

全部图片（现行 C1–C5 五张 + C3/C5 备选各 1 张）均来自 **Pexels License** 或 **Unsplash License**：可免费用于商业用途、可修改、**无需署名**（本清单保留作者与来源以便追溯，建议印厂/法务存档）。两种授权均**不允许**把未修改的原图本身作为图库素材转售/分发。图片中人物仅作出镜模特，不代表对本公司服务的背书。

- Pexels License：https://www.pexels.com/license/
- Unsplash License：https://unsplash.com/license

## 清单

| 文件 | 卡片 | 画面 | 像素（长边） | 来源页 URL | 作者 | 授权 | 原始下载 URL |
|---|---|---|---|---|---|---|---|
| `img1_city.jpg` | C1 公司介绍 | 广州珠江新城 / 珠江天际线，日落薄雾，克制干净 | 10350×5822（≥2000 ✔） | https://www.pexels.com/photo/waterfront-view-of-guangzhou-china-25865508/ | jiahua zhou | Pexels License | `https://images.pexels.com/photos/25865508/pexels-photo-25865508/free-photo-of-waterfront-view-of-guangzhou-china.jpeg` |
| `img2_factory.jpg` | C2 CSCV 服务 | 现代工厂/车间内部，产线设备与货架长透视 | 6000×4000（✔） | https://www.pexels.com/photo/modern-industrial-warehouse-interior-with-machinery-34207364/ | Freek Wolsink | Pexels License | `https://images.pexels.com/photos/34207364/pexels-photo-34207364.jpeg` |
| `img3_inspection.jpg` | C3 核验流程与证据（**备选**，现行用 v2 见下节） | 仓库现场核验：反光背心 + 记录板/平板，对照货架抽查（两位人物面孔明显） | 6046×4024（✔） | https://www.pexels.com/photo/employees-looking-at-the-clipboard-while-standing-near-metal-shelves-13804490/ | Centre for Ageing Better | Pexels License | `https://images.pexels.com/photos/13804490/pexels-photo-13804490.jpeg` |
| `img4_team.jpg` | C4 SME 业务 | 中小企业团队会议/共创，真实办公场景，成员多样 | 6396×4264（✔） | https://www.pexels.com/photo/diverse-team-meeting-in-modern-office-space-29267520/ | Matheus Bertelli | Pexels License | `https://images.pexels.com/photos/29267520/pexels-photo-29267520.jpeg` |
| `img5_port.jpg` | C5 转介绍 / 货代（**备选**，现行用 v2 见下节；原图船体有可读 MSC / MSC MARTA PANAMA 与 EUROGATE 标牌，已弃用） | 黄昏集装箱码头，岸桥与堆场，暗调 | 5472×3648（✔） | https://unsplash.com/photos/ship-cV99JK3dWXk | Bernd Dittrich（@hdbernd，Waltershof, Hamburg） | Unsplash License | `https://images.unsplash.com/photo-1561475699-1e4fdac1e4e2` |

## IMG3 替换版 v2（2026-11-25 追加）

按 C3 卡片语境（中国供应商核验，「七步核验 / 一份可审计的证据」）替换原 IMG3：原图 `img3_inspection.jpg` 为两位西方面孔员工看记录板的特写，面孔过强、语境不贴。v2 要求：**无明显人物面孔**（仅背影/侧影/手部），画面有「现场、证据、检查」语义，暗调或中性调，可商用免费授权。其余 4 张保留不变。

| 文件 | 卡片 | 画面 | 像素（长边） | 来源页 URL | 作者 | 授权 | 原始下载 URL |
|---|---|---|---|---|---|---|---|
| `img3_inspection_v2.jpg` | C3 核验流程与证据 | 侧背影人员手持检查清单 + 红笔，在仓库货架前逐项记录；画面无面孔（仅肩背/手部），右侧为货架与文件箱，暗调剪影 | 6000×4000（≥2000 ✔） | https://www.pexels.com/photo/close-up-shot-of-a-person-doing-a-checklist-12234106/ | Daniel Andraski | Pexels License | `https://images.pexels.com/photos/12234106/pexels-photo-12234106.jpeg` |

- 授权/来源：Pexels License（https://www.pexels.com/license/），作者 Daniel Andraski；下载日期 2026-11-25。
- **无人物面孔**；清单表格线在 111×50mm 照片带内不可辨，无可见文字 / 水印 / 品牌 logo。
- 中性偏暗调；中心裁切带内为「手 + 记录板 + 货架」，可直接用于纸面卡 C3 照片带。
- 原 `img3_inspection.jpg` 保留在本目录作为备选（如需人物出镜版本可回切）。

**v2 备选（未采用，供替换）**

| 画面 | 来源页 | 作者 · 授权 · 像素 | 说明 |
|---|---|---|---|
| 暗调仓库货架 + 剪影人员持记录板 | https://www.pexels.com/photo/person-with-clipboard-in-warehouse-12234107/ | Daniel Andraski · Pexels License · 5678×3785 | 更「工业/暗调」，但记录板细节小、偏氛围 |
| 仓库背影点货（蓝帽、手持单据，无面孔） | https://www.pexels.com/photo/a-back-view-of-a-woman-in-blue-cap-counting-boxes-in-the-warehouse-8069576/ | Lagos Food Bank Initiative · Pexels License · 3120×2080 | 完全背影 + 点货语义；暖色纸箱、偏「志愿者」气质，非工厂 |
| 手部 + 记录板 + 笔填写表格特写 | https://www.pexels.com/photo/a-person-filling-up-a-form-on-a-clipboard-6169648/ | Tima Miroshnichenko · Pexels License · 6000×4000 | 手部特写、无面孔；背景偏办公，工厂语义弱 |

**v2 排除**：Pexels «Checklist on a Clipboard»（8293635）画面含可读英文「HOME INSPECTION Checklist」文字，与「无文字」硬要求冲突，未采用。

## C5 替换版 v2（2026-11-25 追加）

按印刷 QA 反馈替换原 C5 图：`img5_port.jpg`（Bernd Dittrich，Waltershof, Hamburg）画面中船体有可读「MSC / MSC MARTA PANAMA」大字、岸桥有「EUROGATE」标牌，违反「无可读品牌文字/logo」规范，且 `object-fit: cover` 只能垂直裁、无法裁掉。v2 要求：夜色/黄昏集装箱码头（岸桥、堆场、货代感），**画面中不得有任何可读的航运公司名 / 船名 / 箱号大字 / 码头运营商 logo**，暗调或中性调适合深底卡橙色双色调，长边 ≥2000px，可商用免费授权，无水印。其余 4 张保留不变。

| 文件 | 卡片 | 画面 | 像素（长边） | 来源页 URL | 作者 | 授权 | 原始下载 URL |
|---|---|---|---|---|---|---|---|
| `img5_port_v2.jpg` | C5 转介绍 / 货代 | 夜景集装箱码头：跨海大桥红色桥塔与灯带 + 岸桥 / 集装箱堆场 + 水面倒影；集装箱仅为色块，无可读文字 | 2221×1000（按现行 111×50mm 照片带预裁；原图 2221×3948，长边 ≥2000 ✔） | https://www.pexels.com/photo/view-of-a-port-at-night-13337017/ | Fatih Turan | Pexels License | `https://images.pexels.com/photos/13337017/pexels-photo-13337017.jpeg` |

- 授权/来源：Pexels License（https://www.pexels.com/license/），作者 Fatih Turan；下载日期 2026-11-25。
- **交付说明**：模板照片带现为 111×50mm（2.22:1）。本图为 Pexels 原图（2221×3948）按 2.22:1 纵向截取的 2221×1000 条带（仅裁切，未做局部修图/擦除），`object-fit: cover` 无需再裁；若需原幅图可回退 Pexels 原图。
- **文字确认（逐区 100% 像素复核）**：跨海大桥、岸桥、集装箱堆场均为夜景灯光/色块；船体、岸桥机房、箱体、建筑上均无可读字母或数字；无人物；无平台水印。集装箱在成品 300dpi（111mm 宽）下更小，仅呈色块。
- 原 `img5_port.jpg` 保留在本目录作为备选（欧洲港口、船名/船公司标识清晰，不再用于印刷）。

**v2 排除（均因画面含可读文字/标识）**

| 画面 | 来源页 | 作者 · 授权 | 排除原因 |
|---|---|---|---|
| HIT 码头夜班岸桥特写 | https://www.pexels.com/photo/busy-port-during-night-time-4297388/ | JMC · Pexels License | 岸桥机房多处可读「HIT」运营商 logo；船名「BAL PEACE」、箱体 T.S.LINES 等 |
| Hamburg Burchardkai 夜岸桥 | https://www.pexels.com/photo/vibrant-night-view-of-cargo-port-with-ships-30705550/ | Katja B · Pexels License | 岸桥吊臂整排可读「TERMINAL BURCHARDKAI」+「HHLA」 |
| Hamburg 黄昏集装箱船 | https://www.pexels.com/photo/loaded-container-ships-in-the-harbor-at-dusk-20313499/ | Wolfgang Weiser · Pexels License | 「TERMINAL BURCHARDKAI」「EUROGATE」「COSCO」/ Hapag 等可读 |
| 深圳/香港集装箱码头夜景 | https://www.pexels.com/photo/night-view-of-illuminated-industrial-port-34947063/ | ainc T · Pexels License | 粮仓中文厂名、「BULK CARGO TERMINAL」、右侧 Evergreen 等箱标可读 |
| 黄昏码头剪影（asvaport 岸桥） | https://www.pexels.com/photo/silhouette-of-sea-freight-and-container-port-during-evening-13409734/ | Engin Akyurt · Pexels License | 岸桥机房亮灯牌可读「asvaport」运营商标 |
| Rotterdam 集装箱码头夜景 | https://www.pexels.com/photo/port-of-rotterdam-cargo-container-terminal-at-twilight-32399137/ | Freek Wolsink · Pexels License | 船体巨型 SHIPPING/COSCO 字样（旧候选同源） |
| 香港葵青码头航拍（白天） | https://www.pexels.com/photo/port-of-hong-kong-container-terminals-and-stonecutters-bridge-from-birds-eye-view-10778273/ | SimplyArt4794 · Pexels License | 白天亮调且箱体/路牌文字可读，不适合深底卡 |

## 印刷可用性核对

- **有效分辨率**：照片带成品 111×50mm，300dpi 需 1311×591px；现行 5 张原图中最小为 `img5_port_v2.jpg` 的 2221×1000（约 508dpi）；其余更宽裕。✔
- **无水印**：均为 Pexels / Unsplash 原图（非浏览页截图、非缩略图），无平台水印。✔
- **无文字 / 无醒目品牌 logo**：已对 111×50mm 照片带做逐区 100% 像素复核——C1 纯城市天际线；C2 车间设备无醒目标识；C3（v2）为货架前记录动作、清单文字不可辨；C4 画面内有两处极小的 Apple 标记（成品约 2.5–3mm，非主体、不构成背书；300dpi 下可辨，介意的印厂可忽略或要求换图）；C5（v2）夜色集装箱码头为 2.22:1 预裁条带，船体/岸桥/箱体均无可读字母或数字（集装箱仅呈色块），大桥与码头无运营商标牌；原 `img5_port.jpg` 因船体可读「MSC / MSC MARTA PANAMA」与岸桥「EUROGATE」标牌已弃用。✔
- **人物**：未使用摆拍式白人家庭合照；C3（v2）为**侧背影/手部、无人物面孔**（按 2026-11-25 替换要求）；C3 原图为仓库作业人员（备选）；C4 为多元团队真实会议；C5（v2）无人物。✔
- **建议裁切**：`object-fit: cover` 默认中心裁切即可；C1 建议垂直裁切略偏下（保留楼体+江面倒影）；C5（v2）已按 2.22:1 预裁，无需再裁。

## 备选（未采用，供替换）

| 需求 | 备选来源 | 说明 |
|---|---|---|
| C1 城市（白天明亮） | https://unsplash.com/photos/city-skyline-under-blue-sky-during-daytime-hgmP2Vhm1XE · Jason Sung · Unsplash License · 6432×2383 | 广州荔湾区白天蓝天天际线；更“老城”，不如珠江新城有“连接世界”气质 |
| C3 现场（硬安全帽） | https://www.pexels.com/photo/man-in-yellow-safety-reflective-vest-with-hard-hat-doing-house-inspection-8293667/ · RDNE Stock project · Pexels License · 4500×3000 | 有黄色安全帽 + 记录板，但场景为住宅门窗验收，非工厂/仓库 |
| C2 工厂（暗调 B&W） | https://www.pexels.com/photo/interior-of-a-warehouse-16029880/ · Jonathan Lusilva · Pexels License · 2984×3984 | 黑白空仓顶棚，质感好但偏“闲置仓库”，不体现产能 |
| C5 港口（航拍亮调） | https://www.pexels.com/photo/a-cargo-ship-docked-on-a-port-3848793/ · Tom Fisk · Pexels License · 5412×3608 | 雅加达货柜码头航拍；亮调、色彩多，适合纸面卡而非深底卡 |

## 已排除的不可用候选

- **Unsplash+（付费订阅）图片**：如 `plus.unsplash.com/premium_photo-...`（含 “Photo on Unsplash+” 标识）——不属于免费商用授权，已全部剔除。
- **带大字样/品牌的图**：如 Pexels “Port of Rotterdam ... twilight”（画面含巨型 SHIPPING/COSCO 字样）、“Large gantry crane ... SK oceanplant 标志”等，均因“醒目品牌 logo/文字”排除。
- **纯插画/水印图/列表页缩略图**：未采用。

## 复现命令（可选）

Ego 浏览器（CLI `~/.local/bin/ego-browser`）内用 Bing 图片搜索取 `a.iusc` 的 `m` JSON（`murl`/`purl`），再 `page.goto(purl)` 提取 `meta[property=og:image]` / JSON-LD `contentUrl`，最后用 `node fetch` 下载去掉压缩参数的原始 URL（本清单“原始下载 URL”列）。
