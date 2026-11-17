"""零件-1 按原始尺寸贴在发际线中间 + 带上五官（不放大，因为这只是其中一片）。"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")

W, H = 320, 440
cx, cy, r = 160, 150, 100
半 = r / math.sqrt(2)
方左, 方右 = cx - 半, cx + 半
方上, 方底 = cy - 半, cy + 半
小 = 半
底Y = 方底 + 小
鼓 = (r - 半) * 0.5
界 = r * 0.6
rf = 6.0
R大 = r * 2.0
眉y = cy + 半 / 2

肤, 线 = "#f9e9dd", "#3a3f4a"
发 = (0x5a, 0x6b, 0xa8)
睫, 虹上, 虹下, 瞳, 白 = (0x3a, 0x42, 0x50), (0x46, 0x54, 0x6a), (0xa8, 0xc8, 0xe8), (0x22, 0x30, 0x4a), (255, 255, 255)
眉色, 嘴色 = (0x8a, 0x5a, 0x4a), (0xc0, 0x60, 0x70)

图 = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(图)


def 二次(p0, p1, p2, n=10):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])
            for t in (k / n for k in range(n + 1))]


def 竖弦外弧(P, Q, s, 外=-1, n=30):
    L = abs(Q[1] - P[1])
    R = (L * L / 4 + s * s) / (2 * s)
    mx, my = (P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2
    ox = mx - 外 * (R - s)
    oy = my
    aP = math.atan2(P[1] - oy, P[0] - ox)
    aQ = math.atan2(Q[1] - oy, Q[0] - ox)
    aM = math.atan2(my - oy, mx - ox)

    def 归(a):
        return a % (2 * math.pi)

    aP, aQ, aM = 归(aP), 归(aQ), 归(aM)
    跨 = (aQ - aP) % (2 * math.pi)
    if (aM - aP) % (2 * math.pi) > 跨:
        跨 -= 2 * math.pi
    return [(ox + R * math.cos(aP + 跨 * k / n), oy + R * math.sin(aP + 跨 * k / n))
            for k in range(n + 1)]


上弧 = [(cx + r * math.cos(math.radians(k)), cy + r * math.sin(math.radians(k)))
        for k in range(-135, -44, 3)][::-1]
左弧 = 竖弦外弧((方左, 方上), (方左, 方底), 鼓)
dx, dy = 左弧[-1][0] - 左弧[-4][0], 左弧[-1][1] - 左弧[-4][1]
Lt = math.hypot(dx, dy) or 1
d1 = (dx / Lt, dy / Lt)
切点 = (左弧[-1][0] + d1[0] * 小 / 3, 左弧[-1][1] + d1[1] * 小 / 3)
左 = 左弧 + 二次(切点, (切点[0] + d1[0] * 小 * 0.4, 切点[1] + d1[1] * 小 * 0.4), (cx, 底Y), 12)
右 = [(2 * cx - x, y) for (x, y) in 左[::-1]]
轮廓 = 左 + 右 + 上弧

# 脸 + 发根线
d.polygon(轮廓, fill=肤, outline=线)
cy大 = 方上 + R大


def 顶y(x):
    return cy大 - math.sqrt(max(0.0, R大 * R大 - (x - cx) ** 2))


顶弧 = [(x, 顶y(x)) for x in [(cx - 界) + (2 * 界) * k / 40 for k in range(41)]]
左角 = [(cx - 界 - rf + rf * math.cos(math.radians(90 * k / 6)),
         cy - rf + rf * math.sin(math.radians(90 * k / 6))) for k in range(7)]
右角 = [(2 * cx - x, y) for (x, y) in 左角]
根线 = [(cx - (半 + 鼓), cy + 7)] + 左角[::-1] + [(cx - 界, 顶弧[0][1])] + 顶弧 + \
       [(cx + 界, 顶弧[-1][1])] + 右角 + [(cx + (半 + 鼓), cy + 7)]
d.line(根线, fill=(184, 190, 202), width=1)

# 五官
带上 = 眉y
带下 = 方底
脸宽 = 2 * (半 + 鼓)
眼宽 = 脸宽 * 0.24
眼距 = 脸宽 * 0.16
眼高 = min((带下 - 带上) * 0.85, 眼宽 * 0.78)
眼中心y = 带上 + (带下 - 带上) * 0.5
嘴y = 方底 + 小 / 2
鼻y = 方底 + 小 / 4


def 眼(眼心x, 外符号):
    rx, ry = 眼宽 / 2, 眼高 / 2
    d.ellipse([眼心x - rx, 眼中心y - ry, 眼心x + rx, 眼中心y + ry], fill=白)
    # 虹膜：正圆（半径 = 0.72 × 眼高一半），上半深、下半浅
    虹r = ry * 1.0
    虹心y = 眼中心y + ry * 0.10
    框 = [眼心x - 虹r, 虹心y - 虹r, 眼心x + 虹r, 虹心y + 虹r]
    # 虹膜内部：上深下浅，分界是一条向下凹的弧（不是直线）
    yy, xx = np.mgrid[0:H, 0:W]
    # 用 PIL 光栅化圆（跟眼白同一套取整，否则会偏 1 像素）
    圆图 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(圆图).ellipse(框, fill=255)
    圆内 = np.array(圆图) > 127
    dx_ = (xx - 眼心x) / max(1e-6, 虹r)
    边 = 虹心y - 0.25 * 虹r * (1 - np.clip(dx_ ** 2, 0, 1))   # 中间高、两边低
    上掩 = 圆内 & (yy <= 边)
    下掩 = 圆内 & ~上掩
    for 掩, 色 in ((上掩, 虹上), (下掩, 虹下)):
        层 = Image.new("RGB", (W, H), 色)
        蒙 = Image.fromarray((掩 * 255).astype(np.uint8), "L")
        图.paste(层, (0, 0), 蒙)
    d.ellipse([眼心x - 5, 虹心y - 5, 眼心x + 5, 虹心y + 5], fill=瞳)   # 瞳孔严格对齐虹膜圆心
    d.ellipse([眼心x - 11, 眼中心y - 7, 眼心x - 5, 眼中心y - 3], fill=白)
    # 瞳孔正下方的小反光：与瞳孔外切、超出虹膜的部分裁掉、比虹膜下半更浅
    # 半径 = (瞳孔下缘到虹膜下缘的距离) / 2 → 这个圆正好填满那段空隙，且与瞳孔外切
    # 虹r=15, 瞳孔半径=5 → 间距 10 → 半径 5
    反光r = 虹r - 5   # 半径 = 瞳孔下缘到虹膜下缘的距离（=10），超出虹膜的部分裁掉
    反光心y = 虹心y + 5 + 反光r
    反光图 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(反光图).ellipse([眼心x - 反光r, 反光心y - 反光r,
                                    眼心x + 反光r, 反光心y + 反光r], fill=255)
    反光掩 = (np.array(反光图) > 127) & 圆内
    图.paste(Image.new("RGB", (W, H), (0xc8, 0xe2, 0xf4)), (0, 0),
             Image.fromarray((反光掩 * 255).astype(np.uint8), "L"))
    for k in range(15):
        t = k / 14
        a = math.radians(180 + 180 * t)
        px = 眼心x + rx * math.cos(a)
        py = 眼中心y + ry * math.sin(a)
        if 外符号 < 0:
            px = 2 * 眼心x - px
        d.ellipse([px - 1.4 - math.sin(math.pi * t), py - 1.4 - math.sin(math.pi * t),
                   px + 1.4 + math.sin(math.pi * t), py + 1.4 + math.sin(math.pi * t)], fill=睫)


眼(cx - (眼距 / 2 + 眼宽 / 2), -1)
眼(cx + (眼距 / 2 + 眼宽 / 2), +1)
for 侧 in (-1, 1):
    眉心x = cx + 侧 * (眼距 / 2 + 眼宽 / 2)
    d.line([(眉心x - 眼宽 * 0.45, 带上 - 2), (眉心x, 带上 - 6), (眉心x + 眼宽 * 0.45, 带上 - 2)],
           fill=眉色, width=2)
d.point((cx, 鼻y), fill=(0xd9, 0xa0, 0x8c))
d.line([(cx - 9, 嘴y), (cx, 嘴y + 2), (cx + 9, 嘴y)], fill=嘴色, width=2)

# ---------- 贴零件1（原始尺寸，不放大）----------
件0 = Image.open(r"D:\DDSH\我的\素材\刘海零件\零件1-轮廓.png").convert("RGB")
arr = np.array(件0)
非白 = (arr.sum(axis=2) < 720).astype(np.uint8) * 255
ys, xs = np.where(非白 > 0)
件左, 件上 = int(xs.min()), int(ys.min())
件宽, 件高 = int(xs.max() - 件左 + 1), int(ys.max() - 件上 + 1)
件 = 件0.crop((件左, 件上, 件左 + 件宽, 件上 + 件高))
件掩 = Image.fromarray((np.array(件).sum(axis=2) < 720).astype(np.uint8) * 255, "L")
贴x = int(round(cx - 件宽 / 2))
贴y = int(round(顶弧[20][1] - 8))
图.paste(件, (贴x, 贴y), 件掩)
d.line(list(轮廓) + [轮廓[0]], fill=线, width=1)

图.save(Path(r"D:\DDSH\我的\画板\贴零件1-原尺寸五官.png"))
图.resize((W * 4, H * 4), Image.NEAREST).save(
    Path(r"D:\DDSH\我的\画板\贴零件1-原尺寸五官-放大.png"))
print(f"零件原始尺寸 {件宽}×{件高}，贴到 ({贴x},{贴y})；根线顶 y≈{顶弧[20][1]:.0f}")
