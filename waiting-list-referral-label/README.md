# 等候名单协议：底部登记栏 JFC UUID → JFC 推荐代码（JFC Referral Code）

工单：`uuid-referral-label-b09ad30a6f92`
来源请求（Feishu，2026-11-26 12:19，Levi）：
> 底部的JFC UUID应该改为JFC 推荐代码(JFC Referral Code)

请求消息前 47 秒，Levi 在同一线程上传了 `JFC SME Waiting List 创始合伙人预留与等候名单协议（中英对照）v5.pdf`
（与 `JFC_文档重排版/out/` 内 v5 文件 MD5 相同：`a698ad5770d5892feeb2705b0d3c54c0`）。

## 1. 目标与解读

同一份《JFC 创始合伙人上线前预留与等候名单协议（中英对照）》第 4 页最底部是"内部登记"填写栏。
其英文全称可写作 "JFC Handling Employee UUID"（v5），用户把它称作 "底部的 JFC UUID"。
本次要求把该栏名称改为 **「JFC 推荐代码 / JFC Referral Code」**。

版本沿革（见 `source/02_waiting_list.py` 文件头注释）：

| 版本 | 日期 | 底部登记栏 |
|---|---|---|
| v5 | 2026-11-18 | 表格：`内部登记 / Internal Registration` + `填写内容 36 位字符` + `JFC 经办员工 UUID / JFC Handling Employee UUID`（**请求附件所用版本**） |
| v6 | 2026-11-19 | 改为模版矢量横线填写栏 `JFC 参考编码 / JFC Reference Code`；取消 UUID 专属的"36 位字符"规格与经办员工指向 |
| **v7** | **2026-11-26（本次）** | **`JFC 推荐代码 / JFC Referral Code`**；填写区形制、留白与 v6 完全相同 |

本次改动以仓库当前主文件（v6）为基线，只把底部填写栏名称由 `JFC 参考编码` 改为请求指定的
`JFC 推荐代码（JFC Referral Code）`；不恢复 v6 已取消的 UUID / 36 位字符规格（属上一版已定的版式结论，
非本次请求范围）。

## 2. 代码改动

只动一个内容模块：`~/Desktop/待办事件/JFC_文档重排版/contents/02_waiting_list.py`（渲染器 / 模版零改动）。

- 文件头版本注释新增 v7 说明；
- `EXTRA_ALLOWED`：`JFC 参考编码 Reference Code` → `JFC 推荐代码 Referral Code`
  （反自造闸门要求"源件没有、产出新增"的词必须在内容层显式声明）；
- `CONTENT` 末尾填写栏：`{"t": "sig", "cn": "JFC 参考编码", "en": "JFC Reference Code", "gap": 11.0}`
  → `{"t": "sig", "cn": "JFC 推荐代码", "en": "JFC Referral Code", "gap": 11.0}`。

逐行差异见 `source/02_waiting_list.py.diff`。

## 3. 产物

- `out/JFC SME Waiting List 创始合伙人预留与等候名单协议（中英对照）v7.pdf`
  —— 4 页 A4，交付件；SHA-256 见 `verify/hashes_and_pdfinfo.txt`。
- `out/baseline/` —— 对照基线：v5（请求附件）、v6（改动前仓库主文件产物）。
- 同内容也构建到仓库默认产物位置 `JFC_文档重排版/out/JFC Waiting List Contract 中文 v1.pdf`
  （`verify_reflow.py` 的校验路径；与 v7 逐字节相同）。

## 4. 校验（实际运行）

框架 Python 3.13：`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`

| 检查 | 结果 | 日志 |
|---|---|---|
| `jfc_reflow.py contents/02_waiting_list.py` 构建 | ✓ 4 页，331 287 B | `verify/build.log` |
| `verify_reflow.py contents/02_waiting_list.py` 七项交付闸门 | **PASS**（字体 / 几何 / 内容守恒 1247 token / 反自造 / 双语成对 / 版心越界 / 版面几何全部通过） | `verify/verify_reflow.log` |
| `pytest test_jfc_text.py -q` 文本规约冒烟 | **13 passed** | `verify/test_jfc_text.log` |
| `jfc_reflow.py ... --check` 内容模型 | ✓ 29 块、中英成对、封面权益卡 3 项成对 | `verify/test_jfc_text.log` |
| 页面像素对照（150 dpi） | v6→v7 仅第 4 页底部标签区（164,1460–299,1511）不同；第 1–3 页逐像素相同 | `verify/page_render_diff.txt` |
| 文本对照 | v6→v7 仅底部两行标签文字变化；正文/页脚零变化 | `verify/text_diff.txt` |
| 基线一致性 | v5 附件 MD5 = 仓库 `out/` v5 | `verify/hashes_and_pdfinfo.txt` |

## 5. 视觉证据（Before / After）

全部为同一页面（第 4 页）、同一渲染参数（150 dpi，1241×1754 px/页）、同一边界裁剪：

- `evidence/before_after_bottom_compare.png` —— v5（请求附件，`JFC ... UUID`）/
  v6（改动前仓库产物，`JFC 参考编码`）/ v7（改后，`JFC 推荐代码`）三版底栏并排。
- `evidence/before_after_page4_compare.png` —— v6 整页 vs v7 整页。
- `evidence/before_v5_after_v7_page4.png` —— 请求附件 v5 整页 vs v7 整页。
- `evidence/after_v7_all_pages.png` —— v7 全 4 页缩览，证明页数/其余页面不变。
- 单张裁剪：`before_v5_bottom.png`、`before_v6_bottom.png`、`after_v7_bottom.png`。

## 6. 交付与限制

- 交付件已发回原 Feishu 线程（PDF 附件）。
- 版式无新增元素；长标签（`JFC Referral Code` 比旧英文更短）无溢出，页数保持 4 页。
- 本次未改动 v5/v6 历史快照，也未改动渲染器。
