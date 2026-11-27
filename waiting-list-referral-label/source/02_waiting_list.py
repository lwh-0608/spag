# -*- coding: utf-8 -*-
"""JFC 创始合伙人上线前预留与等候名单 · Founding Partner Pre-Launch Reservation & Waiting List

源：根目录 EN v1 与 中文 v1 两份 PDF——同一份协议的两个语言版本，逐段严格对应。
本份把两版合并为一份双语件（避免同一合同出现两份内容重复的成品），
中文取自中文版、英文取自 EN 版，均未改写；仅按「中字英译」重排。

v5（2026-11-18）：签署页末尾加「JFC 经办员工 UUID」内部登记栏，用于把每份
签回的等候名单归属到具体员工、做绩效追踪。属版式新增，已在 EXTRA_ALLOWED 声明。
为挤进第 4 页，签署栏行距由 16/15/20/14 收到 14/13/20/10，页数不变（4 页）。

v6（2026-11-19）：底部登记栏由「JFC 经办员工 UUID」改为「JFC 参考编码」填写栏
——编码只标识文件归属，不再指向经办员工；UUID 的「36 位字符」规格随之取消，
填写区改走模版矢量横线（sig），与上方签署栏同一形制。

v7（2026-11-26）：底部填写栏名称由「JFC 参考编码」统一为「JFC 推荐代码
（JFC Referral Code）」（owner 飞书 2026-11-26 口径）。仅改名称；填写区形制、
留白与 v6 相同，页数不变（4 页）。
"""
TITLE_CN = "JFC 创始合伙人上线前预留与等候名单"
TITLE_EN = "Founding Partner Pre-Launch Reservation & Waiting List"

OUT_NAME = "JFC 创始合伙人预留与等候名单协议（中英对照）.pdf"

SRC_PDF = [
    "/Users/a1-6/Desktop/待办事件/JFC Waiting List Contract 中文 v1.pdf",
    "/Users/a1-6/Desktop/待办事件/JFC Waiting List Contract EN v1.pdf",
]

# 两版都是原件：中英两侧都严格核对，不允许任何一侧自造。
BILINGUAL_SOURCE = "both"

COVER_INFO = [
    ("文件 File", "预留与等候名单协议 Reservation & Waiting List Agreement"),
    ("客户 Client", "[中小企业公司名称] [SME Company Name]"),
    ("服务提供商 Provider", "广州玄墨商业咨询有限公司 / JAZZFRONT Consulting"),
    ("日期 Date", "[插入日期] [Insert Date]"),
]

COVER_NOTICE = [
    ("创始合伙人计划", 11, None, True),
    ("Founding Partner Program", 9, "GRAY", False),
    ("签署本文件不产生任何付款义务 · Signing creates no payment obligation", 8.5, "GRAY", False),
]

# 首页权益卡：在封面「一眼看到」的创始合伙人权益。
# 文案是条款 3 的摘要标签；条款 3 的完整条文在正文中原样保留，一字未改。
# 「前六个月 20% 折扣」不上首页（业务要求：折扣政策不在封面展示）；
# 条款 3 第一条仍原样承诺该折扣，是否同步调整属合同实质变更，另行处理。
COVER_BENEFITS = [
    ("免费试运行与咨询（价值 1,500 元）",
     "Free Trial Run and Consultation (Valued at 1,500 RMB)"),
    ("优先入驻",
     "Priority Onboarding"),
    ("预估总促销价值（3,300 至 23,100 元）",
     "Estimated Total Promotional Value (3,300 to 23,100 RMB)"),
]

EXTRA_ALLOWED = ("文件 File 客户 Client 服务提供商 Provider 预留与等候名单协议 "
                 "Reservation Waiting List Agreement 创始合伙人计划 Founding Partner "
                 "Program 签署本文件不产生任何付款义务 Signing creates no payment obligation 签署 Signatures "
                 "创始合伙人专属权益 Founding Partner Benefits Run "
                 # v6：底部改「JFC 参考编码」填写栏（源件无此栏，属版式新增）
                 # v7：名称统一为「JFC 推荐代码」；填写区形制不变
                 "JFC 推荐代码 Referral Code")

CONTENT = [
    {"t": "p",
     "cn": "本文件作为正式的预留与等候名单协议，由以下双方共同签订：",
     "en": "This document serves as a formal reservation and waiting list agreement entered "
           "into by and between:"},
    {"t": "p", "cn": "客户：[中小企业公司名称]（以下简称“客户”）",
     "en": "Client: [SME Company Name] (hereinafter \"Client\")"},
    {"t": "p",
     "cn": "服务提供商：广州玄墨商业咨询有限公司 / JAZZFRONT Consulting"
           "（统一社会信用代码：91440115MAKKFBK005）（以下简称“JFC”）",
     "en": "Service Provider: Guangzhou Xuanmo Commercial Consulting Co., Ltd. / JAZZFRONT "
           "Consulting (Unified Social Credit Code: 91440115MAKKFBK005) (hereinafter \"JFC\")"},

    {"t": "h2", "cn": "1. 创始合伙人预留", "en": "1. Founding Partner Reservation"},
    {"t": "p",
     "cn": "客户对 JFC 基于订阅的 B2TS（Business-to-Task，任务制商业服务）咨询服务表达了浓厚兴趣，"
           "并希望加入 JFC 创始合伙人等候名单。客户认可 JFC 在提供完整的商业交付成果"
           "（如市场调研、销售支持材料和运营手册）方面的独特价值，且无需派遣人员。"
           "通过签署本文件，客户将锁定 JFC 正式上线后的优先合作权及创始合伙人专属福利。",
     "en": "The Client expresses strong interest in JFC's subscription-based B2TS "
           "(Business-to-Task) consulting services and wishes to join the JFC Founding Partner "
           "Waiting List. The Client recognizes JFC's unique value in providing completed business "
           "deliverables—such as market research, sales enablement materials, and operational "
           "playbooks—without the need for personnel dispatch. By signing this document, the "
           "Client secures priority access and Founding Partner benefits for when JFC officially "
           "opens."},

    {"t": "h2", "cn": "2. 零风险与无财务义务", "en": "2. Zero-Risk and No Financial Obligation"},
    {"t": "p",
     "cn": "客户承担零财务风险。签署本等候名单文件绝对不需要支付任何定金，不构成任何即时财务承诺，"
           "也不构成具有法律约束力的采购协议。客户没有任何义务在未来购买服务。"
           "如果 JFC 未能启动，本文件将自动失效，双方均不承担任何后续义务。",
     "en": "The Client bears zero financial risk. Signing this waiting list document requires "
           "absolutely no down payment, no immediate financial commitment, and does not constitute "
           "a legally binding purchase agreement. The Client is under no obligation to purchase "
           "services in the future. If JFC fails to launch, this document simply expires, and "
           "neither party has any further obligation."},

    {"t": "h2", "cn": "3. JFC 对创始合伙人的承诺", "en": "3. JFC Commitments to Founding Partners"},
    {"t": "p", "cn": "JFC 全面运营后，JFC 向客户保证以下事项：",
     "en": "Upon JFC becoming fully operational, JFC guarantees the following to the Client:"},
    {"t": "item", "num": "•",
     "cn": "前六个月内享受标准 B2TS 订阅费率 20% 的折扣。",
     "en": "A 20% discount on standard B2TS subscription rates for the first six months."},
    {"t": "item", "num": "•",
     "cn": "正式上线时提供一次免费的初始咨询及试运行交付成果（价值约 1,500 元人民币）。",
     "en": "A free initial consultation and trial deliverable upon official launch (valued at "
           "approximately 1,500 RMB)."},
    {"t": "item", "num": "•",
     "cn": "优先入驻及专属账户设置。",
     "en": "Priority onboarding and dedicated account setup."},
    {"t": "item", "num": "•",
     "cn": "预估总促销价值：3,300 元至 23,100 元人民币，具体取决于所选的订阅套餐档次。",
     "en": "Estimated total promotional value: 3,300 RMB to 23,100 RMB, depending on the "
           "selected subscription tier."},

    {"t": "h2", "cn": "4. 启动失效日期", "en": "4. Launch Expiration Date"},
    {"t": "p",
     "cn": "本文件在 JFC 正式公开上线后 30 天内保持有效。如果 JFC 未能在"
           "[插入月份/年份，例如：2027 年第一季度]之前上线，本文件将自动失效，双方均不承担任何义务。",
     "en": "This document remains valid for 30 days following JFC's official public launch. If "
           "JFC does not launch within [Insert Month/Year, e.g., Q1 2027], this document shall "
           "automatically expire with no obligations to either party."},

    {"t": "h2", "cn": "5. 转为付费服务", "en": "5. Conversion to Paid Service"},
    {"t": "p",
     "cn": "本文件不触发任何采购行为。实际的服务购买仅在 JFC 正式上线后发生。届时，JFC 将通知客户。"
           "客户将有 14 天的时间审阅并签署正式的 B2TS 服务协议，以激活其创始合伙人折扣并开始服务。"
           "如果客户选择在此 14 天窗口期内不签署正式协议，他们仅丧失其在等候名单上的名额，"
           "且无需承担任何违约金。",
     "en": "This document does not trigger a purchase. The actual purchase of services will occur "
           "only after JFC's official launch. At that time, JFC will notify the Client. The Client "
           "will then have 14 days to review and sign a formal B2TS Service Agreement to activate "
           "their Founding Partner discount and begin services. If the Client chooses not to sign "
           "the formal agreement within this 14-day window, they simply forfeit their spot on the "
           "waiting list with no penalties."},

    {"t": "h2", "cn": "6. 本地运营、适用法律与保密",
     "en": "6. Local Operations, Governing Law, and Confidentiality"},
    {"t": "p",
     "cn": "JFC 在广州（南沙区）设有本地运营团队，以确保无缝沟通与合规。"
           "本文件受中华人民共和国法律管辖。任何争议应提交广州市有管辖权的人民法院解决。"
           "双方同意对本预留的条款保密。",
     "en": "JFC maintains a local operations team in Guangzhou (Nansha District) to ensure "
           "seamless communication and compliance. This document shall be governed by the laws of "
           "the People's Republic of China. Any disputes shall be submitted to the competent court "
           "in Guangzhou. Both parties agree to keep the terms of this reservation confidential."},

    {"t": "h1", "cn": "签署", "en": "Signatures", "pb": True},
    {"t": "sig", "cn": "客户代表", "en": "Client Representative", "gap": 14.0},
    {"t": "sig", "cn": "客户职务", "en": "Client Title", "gap": 13.0},
    {"t": "sig", "cn": "客户公司盖章（必须）", "en": "Client Company Seal (Mandatory)", "gap": 20.0},
    {"t": "sig", "cn": "日期", "en": "Date", "gap": 10.0},

    {"t": "blank", "sa": 4.0},
    {"t": "p", "cn": "JFC 代表：Jonathan Paets，首席执行官",
     "en": "JFC Representative: Jonathan Paets, CEO"},
    {"t": "sig", "cn": "JFC 公司盖章（必须）", "en": "JFC Company Seal (Mandatory)", "gap": 20.0},
    {"t": "sig", "cn": "日期", "en": "Date", "gap": 10.0},

    # v6：底部填写栏由「JFC 经办员工 UUID」改为「JFC 参考编码」。
    # 编码只标识文件归属，不再指向具体经办员工；「36 位字符」是 UUID 的专属
    # 规格，随之取消。填写区改走模版矢量线（sig：中上英下 + 全宽横线），
    # 与上方签署栏同一形制；整块比原表格矮约 4mm，4 页压得下。
    # v7：名称统一为「JFC 推荐代码（JFC Referral Code）」，形制/留白不变。
    {"t": "sig", "cn": "JFC 推荐代码", "en": "JFC Referral Code", "gap": 11.0},
]
