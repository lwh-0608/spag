# -*- coding: utf-8 -*-
"""Deliverable platform formats and their safe areas.

Every format has:
  canvas   — the exact pixel size of the exported PNG (the size we upload).
  safe     — the rectangle that must stay visible on the smallest / most
             cropped platform view. All *critical* content (logo, headline,
             essential meta) must sit inside it. Decorative marks may bleed.
  blocked  — rectangles covered by platform UI (avatar / page logo), so no
             critical content may sit there even if the safe rect would allow.
  sources  — where the size / safe area is documented (checked 2026-11).

The five formats were chosen because they are the banner slots on the four
platforms named in the brief (LinkedIn) plus the other mainstream English-
language social platforms a CSCV buyer checks: X, Facebook and YouTube.
"""

PLATFORMS = {
    "linkedin-personal": {
        "name_cn": "领英 · 个人主页背景",
        "name_en": "LinkedIn · personal profile background",
        "slug": "linkedin-personal",
        "canvas": (1584, 396),
        "safe": (24, 24, 1536, 348),           # x, y, w, h (hard crop floor)
        "blocked": [(40, 324, 152, 72)],       # profile photo overlaps bottom-left
        "critical": True,
        "platform": "LinkedIn",
        "sources": [
            "https://sproutsocial.com/insights/social-media-image-sizes-guide/",
            "https://buffer.com/resources/social-media-image-sizes/",
        ],
        "notes_cn": "个人头像覆盖左下角；右侧与顶部保留 32px 以上留白。",
        "notes_en": "Profile photo overlaps the bottom-left; keep 32px+ clear at top and right.",
    },
    "linkedin-company": {
        "name_cn": "领英 · 公司主页封面",
        "name_en": "LinkedIn · company page cover",
        "slug": "linkedin-company",
        "canvas": (1512, 256),
        "safe": (24, 24, 1464, 208),
        "blocked": [(30, 206, 120, 50)],      # page logo overlaps the bottom-left edge
        "critical": True,
        "platform": "LinkedIn",
        "sources": [
            "https://www.linkedin.com/help/linkedin/answer/a563309",
            "https://sproutsocial.com/insights/social-media-image-sizes-guide/",
        ],
        "notes_cn": "官方建议 1512×256；重要内容居中，避免贴边（尤其右下角）。",
        "notes_en": "Official recommended 1512×256; keep key content centred and away from edges.",
    },
    "x-header": {
        "name_cn": "X（Twitter）· 页头横幅",
        "name_en": "X (Twitter) · header banner",
        "slug": "x-header",
        "canvas": (1500, 500),
        "safe": (24, 40, 1452, 420),
        "blocked": [(0, 360, 220, 140)],      # profile photo overlaps bottom-left
        "critical": True,
        "platform": "X (Twitter)",
        "sources": [
            "https://snappa.com/blog/twitter-header-size/",
        ],
        "notes_cn": "1500×500；头像覆盖左下角，顶/底可能轻微裁切。",
        "notes_en": "1500×500; profile photo covers the bottom-left, slight top/bottom crop.",
    },
    "facebook-cover": {
        "name_cn": "Facebook · 主页封面",
        "name_en": "Facebook · page cover",
        "slug": "facebook-cover",
        "canvas": (820, 360),
        "safe": (90, 24, 640, 312),
        "blocked": [(0, 270, 100, 90)],       # profile photo overlaps bottom-left
        "critical": True,
        "platform": "Facebook",
        "sources": [
            "https://snappa.com/blog/facebook-cover-photo-size/",
            "https://socialbee.com/blog/facebook-cover-photo-size/",
        ],
        "notes_cn": "桌面显示 820×312、手机 640×360；设计 820×360，关键内容放进中央 640×312。",
        "notes_en": "Displays 820×312 on desktop and 640×360 on mobile; design at 820×360 with the central 640×312 safe.",
    },
    "youtube-channel": {
        "name_cn": "YouTube · 频道封面",
        "name_en": "YouTube · channel art",
        "slug": "youtube-channel",
        "canvas": (2560, 1440),
        "safe": (507, 508, 1546, 423),         # standard safe area on all devices
        "blocked": [(0, 0, 0, 0)],
        "critical": True,
        "platform": "YouTube",
        "sources": [
            "https://snappa.com/blog/youtube-channel-art-size/",
        ],
        "notes_cn": "2560×1440；所有设备可见安全区 1546×423，置于画面正中。",
        "notes_en": "2560×1440; the 1546×423 safe area is centred and visible on all devices.",
    },
}

ORDER = [
    "linkedin-personal",
    "linkedin-company",
    "x-header",
    "facebook-cover",
    "youtube-channel",
]
