# 每日每餐营养性价比 iOS App —— 可行性评估与 MVP 方案

> 状态：可行性评估 v3（2026-11-24，含 5 项确认决策、外接盘环境准备与 Phase 0.5 真机实测结果）｜需求来源：飞书个人需求（Levi，2026-11-24）｜本阶段只做评估、规划与环境准备，不写产品代码

## 0. 结论速览（TL;DR）

| 问题 | 结论 |
| --- | --- |
| 能不能做？ | **能做，技术难度中等偏低**。核心是「记录 + 计算 + 展示」，没有服务端、没有算法难点 |
| 推荐技术路线 | **原生 SwiftUI + SwiftData + HealthKit，本地单机运行，无后端** |
| 多久出可用 MVP | **2–3 周**（Phase 0 3 天表格验证 + Phase 0.5 环境验证 1 天 + Phase 1 约 5–8 个工作日 + 你自己试用调优） |
| 钱 | App 本身 0 元；签名二选一：**免费 Apple ID（0 元，每 7 天重签一次）** 或 **$99/年开发者账号（1 年有效，可 TestFlight）**；无服务器费 |
| 最大风险 | **不是技术，是「每天愿意花 15 秒记一餐」**。记录摩擦决定这个 App 会不会被用下去 |
| 真机验证（2026-11-24） | ✅ 免费签名真机安装、HealthKit 读取全部通过（活动能量/静息能量/体重均可读取，数值不公开）；⚠️ Keep 数据未进「健康」，需在 Keep 打开同步（详见 §3.5） |
| 建议的第一步 | 花 30 分钟做一张表格原型，**先用 3 天**再决定投不投入开发（见 §5.1） |

> **2026-11-24 12:28 更新：5 项决策已确认**（混合自制/外卖、Keep + Apple 健康、轻减脂 + 餐费预算、本机 Mac mini + 免费签名、暂自用但保留上架可能），方案已按确认调整，详见 §7。外接盘环境已实测并搭好：`/Volumes/MealValueDev`（70GB APFS 稀疏映像，装在现有 COLORFUL 外接盘上，不动原有文件）。**现在只剩 2 个只能由你完成的动作：① 登录 Apple ID 下载 Xcode；② 用数据线连接 iPhone 做真机签名验证。**

> **2026-11-24 16:30 更新：Phase 1 MVP 首版已实现并装到真机。** 代码在 `meal-app/`（SwiftUI + SwiftData + HealthKit，四页：今日/记录/报告/我的），已跑通真机构建、安装、启动；界面截图（Before/After）见 PR。营养/性价比数值与食物库均为估算，Keep 数据链路待下次运动后复测。

> **2026-11-24 16:06 更新：Phase 0.5 已完成 ✅。** 免费签名真机安装、启动与 HealthKit 读取全部实测通过（详见 §3.5）；唯一未闭环的是 Keep 的运动数据还没出现在 Apple 健康里（需在 Keep 里打开同步，或用 MVP 的手动补录兜底）。

---

## 1. 需求拆解

原始想法可以拆成 6 个可分别落地、也分别有风险的功能点：

| # | 原始诉求 | 功能点 | 实现手段 | 风险 |
| --- | --- | --- | --- | --- |
| 1 | 每日每餐计算 | 按早/午/晚/加餐记录每一餐吃了什么、多少 | 本地食物库 + 输入份量 | 记录太麻烦会被弃用 |
| 2 | 营养数值 | 每餐与每日：能量、蛋白质、脂肪、碳水、膳食纤维、钠 | 食物库营养值 × 份量求和 | 数据精度仅 ±10–20% |
| 3 | 性价比 | 每餐花多少钱、换到多少营养，横向比较 | 自维护单价 + 指标公式 | 价格维护麻烦、指标设计不能「伪精确」 |
| 4 | 按身体数据分析需要吃多少 | 身体档案 → BMR/TDEE → 每日热量与三大营养素目标 | Mifflin-St Jeor 公式 + 体重趋势校准 | 公式误差 ±10%；需要稳定称重 |
| 5 | 绑定运动消耗 App | 读取每天活动消耗，判断「今天还能吃多少」 | **Apple 健康（HealthKit）作为数据枢纽** | 那款 App 必须把数据写进「健康」 |
| 6 | 判断该怎么摄入 | 今日剩余额度、缺口提示、性价比推荐（如「蛋白还差 30g，最划算的吃法是什么」） | 目标 − 已摄入 + 运动消耗 | 建议只能做提示，不能做医疗建议 |

一句话：**这是一个「个人营养记账 + 身体收支平衡」工具**，本质和你熟悉的记账 App 很像——只是记的是热量、营养和钱三个维度。

---

## 2. 可行性结论与关键依据

### 2.1 在自己 iPhone 上运行：可行，不需要上架 App Store

个人自用不需要 App Store 审核，走「个人侧载（sideload）」即可。两种签名方式：

| 方式 | 费用 | 有效期 | 限制 | 适合 |
| --- | --- | --- | --- | --- |
| 免费 Apple ID（Personal Team） | 0 元 | **7 天**，到期要重新编译安装 | 最多 10 个 App ID、3 台设备、每台设备最多 3 个自签 App；7 天后需重新构建安装 | 先做 MVP 试用 |
| Apple Developer Program | **$99/年**（约 ¥700/年） | 1 年 | 可用 TestFlight、可长期使用、可上架 | 确认要长期使用后 |

依据：Apple 官方会员对比页明确写「Personal Team … You can register up to 10 App IDs, which expire after 7 days … Provisioning profiles … expire 7 days from issuance. You'll need to rebuild and reinstall …」（[Apple：Compare memberships](https://developer.apple.com/support/compare-memberships/)）。

**已实测验证（2026-11-24）**：用免费 Personal Team 签名成功，App 装到一台 iPhone（iOS 27.2）并正常启动，HealthKit 读取成功（详见 §3.5）。

**前置条件（必须满足，否则后面都免谈）**：

- 一台 Mac 装最新 Xcode：**已确认用本台 Mac mini**（Apple 只允许在 Mac 上用 Xcode 构建 iOS App）；
- 你的 iPhone + 数据线（首次安装用；之后可无线调试）：**已确认**；
- 你的 Apple ID 登录 Xcode（免费即可，走 Personal Team 签名）：**已确认用免费签名**。

本机（这台 Mac mini）实测：macOS 27.0 / arm64，**只装了 Command Line Tools，没有装 Xcode**；内置盘仅剩 **11GB** 可用，Xcode + iOS SDK + 模拟器通常需要 40–60GB，内置盘放不下。已确认把 Xcode 装到外接盘：外接盘 `COLORFUL` 128GB / exFAT / 可读写 / 剩 75GB / 写入约 444MB/s，**已在其上建好并挂载 70GB APFS 稀疏映像 `/Volumes/MealValueDev`**（不格式化、不动盘上原有文件），详见 §3.4。

### 2.2 运动消耗数据：可以「绑定」，但方式是走 Apple 健康

iOS 的安全模型决定了：**任何 App 都不能直接读另一个 App 的私有数据**。可行的标准做法是：

```
Keep（或其他运动 App / Apple Watch）
        ↓ 写入
   Apple 健康（HealthKit 数据库）
        ↓ HealthKit 读取
   我们的 App（活动消耗、运动记录、体重、体脂）
```

- 我们的 App 通过 HealthKit 可读：活动能量（activeEnergyBurned）、静息能量（basalEnergyBurned）、运动记录（HKWorkout）、体重、体脂率、身高、出生日期等（[HealthKit 文档](https://developer.apple.com/documentation/healthkit)）。
- 你已确认用 **Keep 记录运动**。**实测结论（2026-11-24）**：HealthKit 读取链路已通，但 Keep 的运动记录/活动能量**目前没有出现在「健康」里**（近 30 天无训练记录；活动能量来源只有 Apple Health 设备源）。需要在 Keep 里开启与「健康」的同步（Keep「我的 → 设置 → 健康/Apple 健康 → 同步」，以现版本路径为准），详见 §3.5。
- 兜底方案：如果暂时没有手表/没有可靠数据，就用「公式估算活动系数」先跑起来，精度下降但仍可用；后期用体重趋势反推真实消耗（见 §4.3）。
- 注意：HealthKit 只能在真机上完整测试（模拟器没有真实健康数据），所以 Phase 0.5 必须做真机冒烟测试。

**免费账号能否用 HealthKit？** Apple 官方「iOS 支持能力表」把 HealthKit 标为对免费 Apple Developer 账号也开放（ADP ✓ / ADEP ✓ / Apple Developer ✓，[Apple 能力表](https://developer.apple.com/help/account/reference/supported-capabilities-ios)）。但社区历来有「HealthKit 需付费账号」的旧经验，因此建议 Phase 0.5 用 30 分钟真机验证：能读到「健康」里的活动能量即通过；不行就升级 $99 账号，不影响方案本身。

### 2.3 营养数据：这是工作量所在，但没有硬障碍

没有「中国食物营养」的官方免费 API。现实可行的组合：

| 数据来源 | 覆盖 | 成本 | 用法 |
| --- | --- | --- | --- |
| **自建常见食物库**（100–300 条：米饭、鸡胸、鸡蛋、牛奶、常见菜、常点的外卖） | 覆盖你 80% 的日常饮食 | 一次性录入 + 陆续补充 | **MVP 主力** |
| **Open Food Facts 公开 API**（条码查包装食品营养） | 中国商品覆盖有限（实测按中国区检索约 1.8k 条，[API 文档](https://openfoodfacts.github.io/openfoodfacts-server/api/)） | 免费 | 扫码记包装食品（如酸奶、零食） |
| **USDA FoodData Central API** | 通用食材英文库，数据权威 | 免费（申请 API Key，[API 指南](https://fdc.nal.usda.gov/api-guide)） | 补充通用食材营养值 |
| 拍照 OCR 识别包装「营养成分表」 | 任意包装食品 | 需开发（VisionKit 文字识别） | Phase 2/3，比条码更实用 |
| 《中国食物成分表（第 6 版）》 | 最全 | 有版权、无公开 API，不建议整库复制 | 人工参考少量数据 |

精度预期：常见食物 ±10%，外卖/混合菜 ±20–30%。**这个精度对人体收支判断足够**（体重趋势的噪声本来就大于营养估算误差）。产品上应显示「约」而不是假装精确。

### 2.4 价格与性价比：没有现成数据源，靠「自维护 + 快速录入」

- 中国没有公开的食材/外卖价格 API；美团、饿了么、薄荷健康等都不提供公开接口，抓取也违反其条款 → **不做自动抓价**。
- 可行模型（三选一或混合）：
  - **自制**：维护「食材单价表」（元/100g），每次采购后批量更新一次（约每周 5 分钟），一餐成本 = Σ 食材单价 × 用量；
  - **外卖/食堂**：一餐直接记总价（3 秒），营养按菜品估算；
  - **混合**：主食用食材价、菜品用整餐价。
- 「性价比」建议用 **2 个原始指标 + 1 个综合分**，且规则透明可解释（避免一个来源不明的「性价比分」）：
  - 能量成本：**元/100 kcal**（越低越划算）
  - 蛋白成本：**元/10 g 蛋白质**（减脂/增肌期最关键的指标）
  - 综合性价比分：营养质量分与价格分归一化后加权（公式见 §4.4）
- 特别注意：**性价比不等于「越便宜越好」**。后期可以让你自己调权重（减脂期重蛋白，控制预算期重价格）。

### 2.5 身体数据 → 该吃多少：公式可算，趋势可校准

- 基础代谢（BMR）：Mifflin-St Jeor 公式（输入性别、年龄、身高、体重）；
- 日总消耗（TDEE）两条路：
  - A. BMR × 活动系数（1.2–1.9，粗）；
  - B. **BMR + HealthKit 活动消耗 + 食物热效应（约 10%）**（更贴合实际，推荐）；
- **校准（关键）**：连续 2–4 周记录体重与摄入后，用「体重变化 × 7700 kcal / 天数」反推真实 TDEE，自动修正。这比任何公式都准，也让 App 越用越准。
- 目标（已确认「轻减脂」）：热量缺口 **−300~400 kcal/天**（约 0.3–0.5 kg/周，更稳、不易掉肌肉）；蛋白质 **1.8–2.0 g/kg** 体重；脂肪 0.8–1.0 g/kg；碳水吃余量；膳食纤维 25–30 g。
- 餐费预算（已确认）：设每日餐费预算（例如 60 元/天，可改），今日页显示「预算剩余」；预算与营养分开计算，不互相折算。
- 每天判断「该怎么摄入」＝ 目标 kcal + 运动消耗（可设置只加回 50–100%）− 已摄入，再按蛋白质缺口给建议。

### 2.6 数据隐私：全部本地，风险低

个人健康数据只存在手机本地（后续可选 iCloud 私有同步），不上传任何服务器，也不接第三方统计 SDK。如果未来上架 App Store，才需要隐私政策、HealthKit 使用说明和医疗免责声明。

---

## 3. 技术方案

### 3.1 方案对比

| 方案 | HealthKit | 开发速度 | 真机安装 | 结论 |
| --- | --- | --- | --- | --- |
| **SwiftUI（原生）** | 原生支持，最简单 | 快（个人小 App 无需跨端） | 免费账号即可侧载 | ✅ **推荐** |
| React Native / Expo | 需第三方 HealthKit 模块 + 自定义 dev build | 中（多一层工具链） | 同上，但构建链更复杂 | 适合未来要 Android 时 |
| PWA / 网页 | **不支持 HealthKit**，只能手动录 | 最快 | Safari 添加到主屏即可 | ❌ 满足不了「绑定运动消耗」 |
| 快捷指令 + 表格 | 只能导入导出，无法自动 | 极快（1 小时） | 无需安装 | 只适合做「3 天验证原型」 |

推荐：**SwiftUI + SwiftData（本地数据库，iOS 17+）+ SwiftUI Charts（图表）+ HealthKit + VisionKit（扫码/OCR）+ Vision（拍照识别，后续）**。理由：单机、无后端、无订阅、开发量与维护量最低，HealthKit 访问最直接，未来想加 Apple Watch 也顺。

### 3.2 推荐架构

```
MealValue（iOS App）
├─ Views        今日 / 记录 / 报告 / 我的
├─ Models       Food, MealEntry, BodyProfile, WeightLog, PriceBook（SwiftData）
├─ Services
│   ├─ NutritionCalculator   营养求和、目标计算（纯函数，可单测）
│   ├─ CostCalculator        成本与性价比指标（纯函数，可单测）
│   ├─ HealthKitService      读活动/静息消耗、体重，写回饮食数据
│   └─ FoodRepository        内置库、扫码、搜索
└─ Resources    foods.json（种子食物库）
```

### 3.3 本机环境实测（2026-11-24）

| 项目 | 实测结果 | 影响 |
| --- | --- | --- |
| 系统 / 芯片 | macOS 27.0，arm64（Apple M6，Mac mini） | 可装最新 Xcode |
| Xcode | **未安装**（只有 Command Line Tools） | 需 Apple ID 登录后下载 |
| 内置盘 | 228GB，仅剩 **11GB** | 放不下 Xcode，装到外接盘 |
| 外接盘 COLORFUL | 128GB exFAT，可读写，剩 **75GB**，写入约 **444MB/s**（USB） | 可承载 Xcode；exFAT 不能直接装 Xcode |
| 已建 APFS 稀疏映像 | **`/Volumes/MealValueDev`，70GB，已挂载可用**（建在 COLORFUL 上，不动原有文件；实测权限、扩展属性、符号链接正常；空映像仅占约 20–26MB，按需增长） | Xcode 与构建缓存装进这里 |
| iPhone 连接 | 需在这台 Mac mini 上用数据线连接你的 iPhone | Phase 0.5 由你插线 |
| Homebrew | 已装（`/opt/homebrew`） | 可用 `brew install xcodes` 辅助下载 Xcode |

结论：**开发、构建、模拟器都在这台 Mac mini 上完成；外接盘已备好，只剩「装 Xcode + 插 iPhone 签名」两步人工操作。**

### 3.4 环境搭建方案：Xcode 装到外接盘（已实测验证）

**为什么用 APFS 稀疏映像、不直接装在外接盘：** 外接盘是 exFAT，不支持 POSIX 权限、扩展属性（xattr）和符号链接，Xcode 直接放上去会出现签名/构建异常。在 exFAT 上建一个 APFS 稀疏映像＝一个会按需扩大的文件，里面是完整的 APFS 卷，既有正确权限，又不格式化、不动盘上原有 45GB 文件。已在本机实测通过。

**已完成：**

1. 创建并挂载 70GB 映像（命令留存备查）：
   ```bash
   hdiutil create -type SPARSEBUNDLE -fs APFS -size 70g -volname MealValueDev "/Volumes/COLORFUL/MealValueDev.sparsebundle"
   hdiutil attach "/Volumes/COLORFUL/MealValueDev.sparsebundle"
   ```
2. 验证：可写、POSIX 权限（600）、扩展属性、符号链接均正常；空映像只占约 20–26MB，用多少长多少。

**待你完成的 2 个动作：**

1. **登录 Apple ID 下载 Xcode**（免费账号即可，Apple 官方说明免费注册后可获取 Xcode 等资源）：任选一种方式——
   - 在 `developer.apple.com/download/all` 登录后下载与本机 macOS 27 匹配的最新 `Xcode.xip`（下载约 3–4GB），存到 `/Volumes/MealValueDev/Downloads/`；
   - 或命令行：`brew install xcodesorg/made/xcodes`，然后 `xcodes install --latest --directory /Volumes/MealValueDev`（会要求 Apple ID 登录与两步验证）。
   App Store 安装不支持外接盘，所以不用 App Store 方式。
2. **用数据线连接 iPhone**：插到这台 Mac mini，解锁并点「信任」。

**之后由我执行（多数不需要 sudo；涉及系统目录的少数步骤需要你在终端输一次密码）：**

```bash
cd /Volumes/MealValueDev && xip --expand Downloads/Xcode.xip    # 展开后约 15–20GB
export DEVELOPER_DIR=/Volumes/MealValueDev/Xcode.app            # 免 sudo 切换工具链
# 需要 sudo 的一次性步骤（可等你在场时执行）：
#   sudo xcode-select -s /Volumes/MealValueDev/Xcode.app
#   sudo ln -s /Volumes/MealValueDev/CoreSimulator /Library/Developer/CoreSimulator
# 构建缓存（DerivedData / iOS DeviceSupport）在 Xcode 设置里指到 /Volumes/MealValueDev/XcodeData，避免占满内置盘
```

注意：磁盘映像重启后需重新挂载（一条 `hdiutil attach`，可做成登录项）；开发时不要热插拔外接盘。

**Phase 0.5 通过标准（真机）：**

1. Xcode 里能看到你的 iPhone，免费 Personal Team 签名成功，App 能装到手机并运行；
2. 建一个带 HealthKit capability 的 SwiftUI 小工程，授权后读取「健康」里 Keep 写入的活动能量并在手机上显示；
3. 记录：免费签名有效期（7 天）、Keep 数据链路是否完整（「活动能量」或「体能训练」至少一个可用）。

若第 2 步失败（免费账号无法用 HealthKit），回退 $99/年开发者账号；若映像性能不可接受，再考虑换 APFS 分区或新 SSD。

### 3.5 Phase 0.5 真机实测结果（2026-11-24，✅ 已通过）

真机：一台 iPhone（iOS 27.2，USB 配对、开发者模式已开启；具体 UDID 与设备名不记录）。测试用最小 App：`/Volumes/MealValueDev/HealthSmoke`（SwiftUI + HealthKit 冒烟工程，非产品代码），用免费 Personal Team 签名。

| 验证项 | 结果 | 证据 |
| --- | --- | --- |
| 免费签名真机安装/启动 | ✅ 通过 | Xcode 自动生成 Apple Development 证书与 `iOS Team Provisioning Profile: com.levi.healthsmoke`；`devicectl install` + `process launch` 成功 |
| HealthKit 权限 | ✅ 通过 | 系统授权页出现并完成授权（读取活动能量/静息能量/体能训练/体重） |
| 读取当日活动能量 | ✅ 通过 | 读到当日累计活动能量（非零；具体数值不公开） |
| 读取当日静息能量 | ✅ 通过 | 读到当日静息能量（非零；具体数值不公开） |
| 读取体重 | ✅ 通过 | 读到最新体重（「健康」里已有体重记录；具体数值不公开） |
| 运动记录 | 0 条 | 近 30 天 `HKWorkout` 查询为空 |
| 数据来源 | 仅 Apple Health 设备源 | 活动能量 `HKSource` 只有 `com.apple.health…` 设备源，**没有 Keep 等第三方 App** |

**结论：**

- 「免费签名 + 真机安装 + HealthKit 读数」链路**完全打通**，技术可行性从纸面变成实测。
- **Keep 的数据目前没有进入 Apple 健康**：近 30 天没有任何训练记录，活动能量来源只有 iPhone 本身。需要在 Keep 里打开与「健康」的同步，并在下次运动后再跑一次冒烟 App 确认；若 Keep 不支持写活动能量，MVP 必须自带「手动补录运动 / 公式估算」兜底（风险表已更新）。
- 流程性发现：iPhone 的「开发者模式」开关要等首次信任开发者后才出现（属正常）；免费签名 App 首次启动需在 iPhone「设置 → 通用 → VPN 与设备管理」里信任，且 7 天后需要重签。
- 测试 App（HealthSmoke）当前还装在手机上，可保留用于下次验证 Keep 同步；它会随 7 天签名到期失效。

---

## 4. 产品设计（MVP）

### 4.1 页面与交互

四个 Tab：

```
今日：今日摄入 vs 目标（能量环 + 蛋白条）｜今日花费 vs 餐费预算｜运动消耗｜还能吃多少
      └─ 早/午/晚/加餐 四张卡片：营养合计、成本、性价比分、编辑
记录：选餐次 → 选「自制/外卖」→ 搜索「常吃/最近」或扫码 → 填份量（g / 份）→ 实时预览营养与成本 → 保存
报告：近 7/30 天：每日成本、元/100kcal、蛋白达标率、体重趋势、三餐性价比排行
我的：身体档案（性别/年龄/身高/体重/体脂）｜目标（默认轻减脂）｜餐费预算｜价格库｜HealthKit 授权
```

设计原则：**一餐 15 秒内记完**。手段：常吃一键添加、复制昨天、搜索优先最近 20 条、扫码/OCR、不强制填精确克数（用「一碗/一份」默认值）。

### 4.2 数据模型（最小集）

| 实体 | 关键字段 |
| --- | --- |
| Food | id、名称/别名、分类、每 100g 能量/蛋白/脂肪/碳水/纤维/钠、数据来源 |
| PriceBook | foodId、单价（元/100g）、更新日期、门店（可选） |
| MealEntry | 日期、餐次、条目[{foodId, 用量(g/份), 价格覆盖}]、备注 |
| BodyProfile | 性别、出生年、身高、目标体重、目标类型（减脂/增肌/维持） |
| WeightLog | 日期、体重、体脂率（可选） |
| DailyAggregate | 当日营养合计、成本、HealthKit 活动/静息消耗、剩余额度 |

### 4.3 核心算法

```
BMR(男) = 10×体重kg + 6.25×身高cm − 5×年龄 + 5
BMR(女) = 10×体重kg + 6.25×身高cm − 5×年龄 − 161

TDEE = BMR + HealthKit活动消耗 + 0.10×当日摄入            （推荐）
TDEE_校准 = 近N天平均摄入 − Δ体重kg×7700 / N天            （连续记录 2–4 周后启用，替换 BMR 估算部分）

目标摄入 = TDEE ± 目标缺口（减脂 −300~500；增肌 +200~300）
剩余可摄入 = 目标摄入 + 运动消耗×加回比例(0~100%) − 已摄入
剩余餐费预算 = 每日预算 − 当日已花
```

### 4.4 性价比指标定义（透明、可解释）

```
每餐成本 C（元）＝ 自制：Σ(食材单价 × 用量)　/　外卖：直接填整餐价（记录页一键切「自制/外卖」，对应随机切换习惯）
能量成本 = C / 能量(kcal) × 100            → 元/100kcal，越低越省
蛋白成本 = C / 蛋白质(g) × 10              → 元/10g 蛋白，越低越划算
营养质量分 Q（0–100）= 按当日推荐摄入量归一后的（蛋白 + 纤维 + 低钠 + 低饱和脂肪）加权，可随数据完整度扩展微量营养素
价格分 V（0–100）= 与同餐次近 30 天「元/100kcal」中位数比较归一
性价比分 = 0.6×Q + 0.4×V                    → 权重可在设置里调整
```

展示时**原始指标和综合分都显示**，并标注「估算」；不做「健康评分」「营养师建议」这类容易被误解为医疗结论的表述。

---

## 5. MVP 范围与迭代计划

### 5.1 Phase 0：先做 3 天验证（0 成本，强烈建议）

在写代码之前，先花 30 分钟用飞书表格/Numbers 建一张记录表，**连续记 3 天**：每餐吃了什么、大概多少钱、用手机查一下营养。然后回答 3 个问题：

1. 记录过程烦不烦？大概一餐花多久？
2. 算出来的「性价比」和「该吃多少」对你有没有实际指导？
3. 你最想要的是「记录」还是「建议」？（决定 MVP 取舍）

如果 3 天后觉得有用 → 进入 Phase 1；如果记录本身就觉得累 → 应该做的是更轻量的版本（只记成本 + 蛋白 + 体重），而不是更完整的 App。

### 5.2 Phase 0.5：环境验证（✅ 已完成，2026-11-24）

已完成并通过，详细结果见 §3.5：

- 免费 Personal Team 真机签名、安装、启动 ✅
- HealthKit 读取（当日活动能量、静息能量、体重均可读）✅
- Keep → Apple 健康 数据：**未出现**（近 30 天无训练记录，来源仅 iPhone）→ 需在 Keep 打开同步后复测。

下一阶段：Phase 1 MVP 开发，任务拆分见 §5.3（等你确认开始）。

### 5.3 Phase 1：MVP（约 5–8 个工作日）

| 模块 | 内容 |
| --- | --- |
| 身体档案 | 性别/年龄/身高/体重/目标 → BMR/TDEE/每日目标与蛋白目标 |
| 食物库 | 内置 100–150 条常见食材与外卖菜品（营养 + 参考价） |
| 记录 | 早/午/晚/加餐，搜索 + 份量 + 实时营养/成本预览，复制昨日 |
| 今日页 | 摄入 vs 目标、今日花费、HealthKit 活动消耗、剩余可吃 |
| 基础报告 | 近 7 天成本与蛋白达标率、体重录入与趋势 |
| 餐费预算 | 每日预算设置、今日剩余、超支提示（不影响营养计算） |
| 数据 | 本地存储、JSON 导出备份（防换机丢失） |

MVP 验收标准（你自己试用 1 周）：能每天记完 3 餐，记录一餐 ≤ 20 秒，能看懂「今天还能吃多少」，报告数字和你的直觉不冲突，预算与营养两个维度都能看到。

**状态（2026-11-24 16:30）**：T1–T7 首版已完成并装到真机（代码见 `meal-app/`），T8 真机验收进行中；Keep 数据链路仍待复测。MVP 支持 `-demoMode` 启动参数加载合成数据用于截图/试用，不读取真实健康数据。

**Phase 1 任务拆分（下一张实现任务单可直接引用）**

| # | 任务 | 交付物 / 验收 |
| --- | --- | --- |
| T1 | Xcode 工程骨架 + SwiftData 模型 + 纯函数计算器 + 单测 | 工程可构建、计算器单测通过 |
| T2 | 身体档案与目标计算（BMR/TDEE/蛋白质/预算） | 输入身体数据得到合理目标值 |
| T3 | 食物库 + 价格库（100–150 条种子数据，支持自制/外卖两种计价） | 能搜到常吃食物并带默认价 |
| T4 | 记录流程（餐次、份量、实时营养与成本、复制昨日） | 一餐 ≤ 20 秒记完 |
| T5 | 今日页（摄入 vs 目标、预算剩余、HealthKit 运动消耗、还能吃多少） | 手机真机可读 Keep 数据 |
| T6 | 报告（近 7 天成本、元/100kcal、蛋白达标率、体重趋势） | 图表可读、数字与手算一致 |
| T7 | JSON 导出/导入备份 + HealthKit 写回饮食数据 | 换机可恢复；健康 App 可见饮食记录 |
| T8 | 真机验收（免费签名 7 天重签）+ 问题清单 | 你试用 1 周的真实反馈 |

### 5.4 Phase 2：好用（MVP 验证后，约 1–2 周）

- 条码扫码（Open Food Facts）+ 营养成分表 OCR 录入
- 常吃/收藏/最近记录、价格库批量维护
- 周/月报告：成本趋势、性价比排行（同营养目标下最划算的吃法）
- TDEE 自适应校准（体重趋势反推）
- iCloud 私有同步（可选）

### 5.5 明确不做（防止过度设计）

账号体系、社交/分享、上架 App Store、多用户、云服务器、AI 营养师、精确到克的医学级建议、Android 版本。这些都不影响「你自己每天用」这个核心目标。

### 5.6 时间与成本估算

| 阶段 | 用时 | 成本 |
| --- | --- | --- |
| 3 天表格验证 | 30 分钟 + 3 天记录 | 0 元 |
| Phase 0.5 环境验证（含下载 Xcode） | 0.5–1 天 | 0 元（免费 Apple ID） |
| Phase 1 MVP | 5–8 个工作日（我写代码 + 你试用反馈） | 0 元（免费签名；外接盘复用现有盘） |
| Phase 2 | 1–2 周 | 同上 |
| 长期使用 | 每周 5 分钟维护价格库 | 0 元/年（免费签名 7 天重签）或 $99/年 |
| 可选：新外接 SSD | — | 约 ¥200–300（现有盘方案不可用时） |

---

## 6. 风险与对策

| 风险 | 概率 | 影响 | 对策 |
| --- | --- | --- | --- |
| 记录太麻烦 → 用几天就弃用 | 高 | 高 | 15 秒记一餐：常吃、复制昨日、扫码/OCR、默认份量；先做 3 天验证再投入 |
| 营养数据不准 | 高 | 中 | 自建常用食物库优先；显示「约」和区间；用体重趋势校准，不追求账面精确 |
| 价格维护成本高 | 高 | 中 | 每周批量更新一次；外卖直接填整餐价；价格库允许留空 |
| 运动数据缺失或不进「健康」 | 中 | 中 | 先公式估算；在 App 内提示「未读取到今日活动数据」；再换/同步运动 App |
| 免费签名 7 天到期 | 高 | 中 | MVP 阶段可接受；确认长期使用后买 $99/年 |
| 内置盘空间不足 | 高 | 中 | 已确认用本机 Mac mini + 外接盘映像；构建缓存/设备支持/模拟器运行时都要放外接盘，内置盘只剩 11GB |
| 本地数据丢失（换机/删 App） | 低 | 高 | JSON 导出备份；Phase 2 加 iCloud |
| 健康指标被当成医疗建议 | 低 | 中 | 只做「估算/提示」，加免责说明；不输出诊断结论 |
| 口味/场景差异导致性价比失真（外卖 vs 自制 vs 聚餐） | 中 | 中 | 分场景计算；聚餐用「估算一餐」而不是逐项记 |
| 外接盘是 exFAT、磁盘映像断连 | 中 | 中 | 已用 APFS 稀疏映像规避权限问题；开机重新挂载；开发时不热插拔 |
| Keep 不写活动能量/训练到「健康」（**2026-11-24 实测已出现**） | 高 | 中 | 实测近 30 天无训练记录、活动能量来源仅 iPhone；对策：在 Keep 里打开「同步到 Apple 健康」，并在下次运动后复测；MVP 内置「手动补录运动 + 公式估算」兜底，不依赖单一 App |
| 「轻减脂 + 预算」下便宜但蛋白低的餐被高估 | 中 | 低 | 报告同时给「元/100kcal」与「元/10g 蛋白」，不强行合成单一结论 |
| 以后想上架 App Store | 低 | 中 | 现在保持无私有 API、无广告 SDK、HealthKit 权限说明完整、Bundle ID 规范；上架前再补隐私政策与审核材料 |

---

## 7. 决策记录与剩余动作

### 7.1 已确认决策（Levi，2026-11-24 12:28）

| # | 原问题 | 你的确认 | 对方案的影响 |
| --- | --- | --- | --- |
| Q1 | 三餐场景 | **自制 / 外卖随机切换** | 记录页首屏放「自制（食材价）/ 外卖（整餐价）」切换；两套计价从 MVP 就要有 |
| Q2 | 运动数据 | **Keep + 健康记录** | 走 Keep → Apple 健康 → HealthKit 链路；Phase 0.5 实测 Keep 是否写活动能量 |
| Q3 | 目标 | **轻减脂 + 餐费预算** | 默认 −300~400 kcal/天、蛋白 1.8–2.0 g/kg、0.3–0.5 kg/周；今日页加预算剩余 |
| Q4 | 开发/安装条件 | **本台 Mac mini + 免费签名 + 外接盘** | Xcode 装到外接盘 APFS 映像（已建好 `/Volumes/MealValueDev`）；7 天重签可接受 |
| Q5 | 数据范围 | **目前自用，不排除以后上架** | MVP 不上架；代码保持无私有 API、无广告 SDK、HealthKit 权限说明完整，给未来上架留余地 |

### 7.2 剩余动作（Phase 0.5 之后）

1. **Keep → Apple 健康 同步**：Levi 已在 Keep 里打开同步；下次用 Keep 记录一次运动后告诉我，我复跑验证数据是否进入「健康」（目前已确认 Keep 不会回填历史运动，活动能量来源仍只有 Apple Health 设备源）。
2. **Phase 1 已开始（2026-11-24 16:20）**：MVP 首版已实现并装到真机（`meal-app/`）；后续按试用反馈迭代（食物库扩充、Keep 数据复测、预算/加回比例可配置等）。

### 7.3 可选决定（不影响开工）

- 外接盘方案：默认用已建好的 APFS 稀疏映像（不丢数据、0 成本）；若你更想要「整盘 APFS」或「新买一块 SSD」，告诉我再换。
- 7 天签名到期：先用免费签名；试用两周觉得值得长期用，再考虑 $99/年（含 TestFlight）。

**关于与员工1 的协同（你 11:55 的补充）**：可以，但协同必须有明确边界，避免两边改同一份代码。

- **数据类工作**：员工1 负责食物库 100–150 条初始数据（名称、每 100g 营养、参考单价）的整理与交叉校核，这是最耗时间、最容易并行的部分；
- **验证类工作**：员工1 独立执行测试清单（记录流程、计算边界、HealthKit 权限），用「只读复核」的方式给我反馈；
- **代码类工作**：同一时间只允许一方改同一模块；若并行开发，按页面/模块切分（例如我负责记录 + 计算，员工1 负责报告 + 设置页），通过 Git 分支合并；
- **前提**：员工1 需要能访问同一份仓库；Xcode 真机构建只在这台 Mac mini 上做，避免两边签名环境冲突。

---

## 8. 参考链接

- Apple 支持能力表（HealthKit 等能力与账号类型）：https://developer.apple.com/help/account/reference/supported-capabilities-ios
- Apple 会员对比（免费账号 7 天有效期等限制）：https://developer.apple.com/support/compare-memberships/
- HealthKit 开发文档：https://developer.apple.com/documentation/healthkit
- SwiftData 文档：https://developer.apple.com/documentation/swiftdata
- VisionKit 条码扫描（DataScannerViewController）：https://developer.apple.com/documentation/visionkit/datascannerviewcontroller
- Open Food Facts API：https://openfoodfacts.github.io/openfoodfacts-server/api/
- USDA FoodData Central API：https://fdc.nal.usda.gov/api-guide

---

## 附录 A. English summary

**Feasibility summary — Daily per-meal nutrition & value iOS app (personal use)**

- **Verdict:** feasible. A local-only SwiftUI app with SwiftData and HealthKit covers all requirements; no backend, no server cost, no App Store submission.
- **Verified on device (2026-11-24):** free Personal Team signing installed and launched a SwiftUI test app on an iPhone (iOS 27.2); HealthKit reads of today's active energy, basal energy and weight all succeeded (values not recorded here). Keep data is not yet present in Apple Health (no workouts in 30 days; activity-energy sources are Apple Health device sources only) — Keep's Apple Health sync must be enabled, and the MVP will fall back to manual workout entry.
- **Confirmed decisions (2026-11-24):** mixed home-cooked/takeout meals, Keep → Apple Health for exercise data, light fat loss with a daily meal budget, build on this Mac mini with free signing and Xcode on an external APFS disk image, personal use now with a possible App Store release later.
- **Exercise data:** read through Apple Health (HealthKit), not by connecting directly to another app; the exercise app must write its data into Apple Health.
- **Nutrition data:** no free Chinese nutrition API. Plan: a self-built library of 100–300 common foods as the primary source, Open Food Facts barcode API for packaged goods, and USDA FoodData Central as a generic reference. Accuracy about ±10–20%, which is adequate for body-balance decisions.
- **Cost/price data:** no public API; maintain a small ingredient price book (weekly, ~5 min) plus per-meal price entry for takeout.
- **Body targets:** Mifflin-St Jeor BMR + HealthKit activity energy for TDEE, calibrated weekly against weight trend.
- **Delivery:** personal sideload (free Apple ID, 7-day re-sign) or $99/year developer account; requires a Mac with Xcode and the user's iPhone for installation.
- **Timeline:** validate with a 3-day spreadsheet prototype first, then a 5–8 working-day MVP, then a 1–2 week "nice to have" phase.
- **Main risk:** logging friction, not technical difficulty. Design target: log a meal in under ~15 seconds.

## 附录 B. 分工建议（我 vs 你 vs 员工1）

| 事项 | 我（DSH 代理） | 你 | 员工1（若协同） |
| --- | --- | --- | --- |
| 工程/代码/单元测试 | ✅ 全部 | 试用反馈 | 只读复核 or 独立模块 |
| 食物库初始数据 | 定义字段、校验、导入 | 补充你常吃的东西 | ✅ 100–150 条数据整理 |
| 下载 Xcode / 连接 iPhone | 提供步骤与链接 | ✅ 登录 Apple ID 下载、插线、信任 | 无法替代 |
| Xcode 展开与工具链配置 | ✅ 在外接盘映像里完成 | 少数 sudo 步骤输一次密码 | 无法替代 |
| HealthKit 权限与 Keep 数据链路 | 建最小工程验证 | ✅ 在 Keep 里开启「同步到 Apple 健康」 | 执行测试清单 |
| 价格库维护 | 提供批量导入方式 | ✅ 每周更新 | 可协助整理 |
| 与员工1 的协作边界 | 模块划分、合并流程、验收 | ✅ 决定是否启用 | 只读复核，不改同一文件 |
| 用药/健康决策 | 不做 | ✅ 自行判断，App 不提供医疗建议 | 不做 |
