# 每餐值（MealValue）— iOS MVP

每日每餐的营养、花费与性价比记录 App。SwiftUI + SwiftData + Charts + HealthKit，本地单机运行，无后端。

## 功能（MVP）

- **今日**：能量环（摄入 vs 目标）、蛋白质/脂肪/碳水进度、今日花费 vs 餐费预算、健康 App 运动消耗、四餐卡片与性价比分
- **记录**：按餐次列出当日记录，可编辑/删除
- **记录一餐**：自制（食材价）/ 外卖（整餐价）双计价，食物搜索、份量调整、实时营养与性价比预览
- **报告**：近 7 天花费柱状图、蛋白达标率、体重趋势
- **我的**：身体数据（性别/年龄/身高/体重/目标）、目标（轻减脂/维持/增肌）、每日餐费预算、HealthKit 连接、JSON 导出分享

## 计算口径

- BMR：Mifflin-St Jeor；TDEE = BMR + 健康 App 活动消耗 + 10% 食物热效应
- 目标：轻减脂 −350 kcal/天；蛋白质 1.8 g/kg（维持 1.6、增肌 2.0）；脂肪 0.9 g/kg；碳水吃余量
- 性价比：营养质量分（每 100 kcal 的蛋白/纤维密度、钠扣分）+ 价格分（元/100 kcal 与参考价 6 元/100 kcal 比较），6:4 加权

## 构建

```bash
# 1. 生成 Xcode 工程（修改/新增 Swift 文件后重新执行）
python3 tools/gen_project.py

# 2. 真机构建（免费 Personal Team，需在工程里配置自己的 DEVELOPMENT_TEAM）
xcodebuild -project MealValue.xcodeproj -scheme MealValue -configuration Debug \
  -destination 'generic/platform=iOS' -derivedDataPath /tmp/mv-dd -allowProvisioningUpdates build

# 3. 安装到已连接的 iPhone
xcrun devicectl device install app --device <UDID> /tmp/mv-dd/Build/Products/Debug-iphoneos/MealValue.app
```

## 演示数据

无真实数据时可加启动参数 `-demoMode 1`，使用合成身体数据/三餐/体重记录（用于截图与试用，不读取真实健康数据）。

## 说明

- 营养与性价比数值均为估算，不构成医疗或营养建议。
- 内置食物库（50 条）为常见食材/菜品参考值，后续可扩充或接入 Open Food Facts 条码。
