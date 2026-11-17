"""中分发型的重画（第一稿）。

结构（从 参考中分.jpg 量出来）：
  中线发缝在 cx，两片"帘"从中缝往左右下方扫，额头露出来
  两侧长发垂到肩下（比刘海长很多）
  配饰：左侧蓝宝石发夹、右上方金色饰、左侧白色羽毛
脸/五官沿用上一套（幼态参数）。
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
出 = Path(r"D:\DDSH\我的\画板")


def 色(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


W, H = 360, 460
r = 92
cx, cy = W // 2, 190

半 = r / math.sqrt(2) * 1.08
鼓 = (r - 半 / 1.08) * 0.62
小 = 半 * 0.52
方上, 方底 = cy - 半, cy + 半
底Y = 方底 + 小
眉y = cy + 半 / 2
鼻y = 方底 + 小 / 4
嘴y = 方底 + 小 / 2
脸宽 = 2 * (半 + 鼓)
脸边 = 半 + 鼓
发际y = cy - r * 0.62

肤, 线 = 色(0xf8f2ee), 色(0x685050)
发, 发暗, 发边 = 色(0xf2c6d6), 色(0xe0a8c0), 色(0xa87a88)   # 这张图的粉更浅
蓝 = 色(0x9ab0d8)
白 = (255, 255, 255)
虹, 虹下, 瞳 = 色(0x8a6a9a), 色(0xb89cc8), 色(0x5a4266)
腮 = 色(0xf3bcc4)

图 = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(图)
yy, xx = np.mgrid[0:H, 0:W]


def 多边(点们, 填=None, 边=None, 宽=2):
    d.polygon([(float(a), float(b)) for a, b in 点们], fill=填, outline=边)
    if 边:
        d.line([(float(a), float(b)) for a, b in 点们] + [(float(点们[0][0]), float(点们[0][1]))],
               fill=边, width=宽)


def 竖弦外弧(P, Q, s, 外=-1, n=30):
    L = abs(Q[1] - P[1])
    R = (L * L / 4 + s * s) / (2 * s)
    mx, my = (P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2
    ox = mx - 外 * (R - s)
    aP = math.atan2(P[1] - my, P[0] - ox)
    aQ = math.atan2(Q[1] - my, Q[0] - ox)

    def 归(a):
        return a % (2 * math.pi)

    aP, aQ = 归(aP), 归(aQ)
    跨 = (aQ - aP) % (2 * math.pi)
    if 跨 > math.pi:
        跨 -= 2 * math.pi
    return [(ox + R * math.cos(aP + 跨 * k / n), my + R * math.sin(aP + 跨 * k / n))
            for k in range(n + 1)]


def 二次(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])
            for t in (k / n for k in range(n + 1))]


def 柳叶掩码(A, B, C1, C2, 宽, 位=0.42, 端正=0.85, n=200):
    pts = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        pts.append((u**3 * A[0] + 3 * u * u * t * C1[0] + 3 * u * t * t * C2[0] + t**3 * B[0],
                    u**3 * A[1] + 3 * u * u * t * C1[1] + 3 * u * t * t * C2[1] + t**3 * B[1]))
    左s, 右s = [], []
    for i, (x, y) in enumerate(pts):
        t = i / n
        if i == 0:
            tx, ty = pts[1][0] - x, pts[1][1] - y
        elif i == n:
            tx, ty = x - pts[-2][0], y - pts[-2][1]
        else:
            tx, ty = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        m = max(1e-9, math.hypot(tx, ty))
        ux, uy = -ty / m, tx / m
        v = (math.sin((t / 位) * math.pi / 2) if t <= 位
             else math.cos(((t - 位) / (1 - 位)) * math.pi / 2)) ** 端正
        hw = 宽 * v / 2
        左s.append((x + ux * hw, y + uy * hw))
        右s.append((x - ux * hw, y - uy * hw))
    m2 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m2).polygon([(float(a), float(b)) for a, b in 左s + 右s[::-1]], fill=255)
    return np.array(m2) > 127


def 描边掩(掩):
    return 掩 ^ (np.roll(掩, 1, 0) & np.roll(掩, -1, 0) & np.roll(掩, 1, 1) & np.roll(掩, -1, 1))


def 落色(掩, 色值, 描=True, 边色=None, 宽=2):
    层 = np.zeros((H, W, 4), np.uint8)
    层[掩] = (*色值, 255)
    if 描:
        e = 描边掩(掩)
        层[e] = (*(边色 or 发边), 255)
    图.paste(Image.fromarray(层, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层[:, :, 3], "L"))


# ---------- ① 后发（中分也要有一大团在背后） ----------
# 后发最宽 = 头顶最宽（头顶圆半径 1.10r → 最宽处就是 cx ± 1.10r）
_顶宽 = 1.10 * r
后发点 = [(cx - _顶宽, cy + r * 2.15), (cx - _顶宽, cy + r * 0.2), (cx - r * 0.92, cy - r * 1.08),
          (cx, cy - r * 1.14), (cx + r * 0.92, cy - r * 1.08), (cx + _顶宽, cy + r * 0.2),
          (cx + _顶宽, cy + r * 2.15), (cx + r * 0.55, cy + r * 2.33),
          (cx, cy + r * 2.41), (cx - r * 0.55, cy + r * 2.33)]
m = Image.new("L", (W, H), 0)
ImageDraw.Draw(m).polygon([(float(a), float(b)) for a, b in 后发点], fill=255)
后发掩 = np.array(m) > 127
# 两个上角超出头顶圆 → 逐列按头顶圆的边界切掉
_顶r, _顶心y = r * 1.10, cy - r * 0.06
for x in range(W):
    d2 = _顶r ** 2 - (x - cx) ** 2
    if d2 <= 0:
        continue
    顶界 = _顶心y - math.sqrt(d2)
    后发掩[:int(顶界), x] = False
落色(后发掩, 发暗, 描=True)

# ---------- ② 脸 ----------
上弧 = [(cx + r * math.cos(math.radians(k)), cy + r * math.sin(math.radians(k)))
        for k in range(-140, -39, 3)][::-1]
方左 = cx - 半
左弧 = 竖弦外弧((方左, 方上), (方左, 方底), 鼓)
dx, dy = 左弧[-1][0] - 左弧[-4][0], 左弧[-1][1] - 左弧[-4][1]
Lt = math.hypot(dx, dy) or 1
u = (dx / Lt, dy / Lt)
切 = (左弧[-1][0] + u[0] * 小 / 3, 左弧[-1][1] + u[1] * 小 / 3)
左 = 左弧 + 二次(切, (切[0] + u[0] * 小 * 0.4, 切[1] + u[1] * 小 * 0.4), (cx, 底Y), 12)
右 = [(2 * cx - x, y) for (x, y) in 左[::-1]]
轮廓 = 左 + 右 + 上弧
多边(轮廓, 填=肤, 边=线, 宽=2)

# ---------- ③ 五官 ----------
眼宽 = 脸宽 * 0.26
眼距 = 脸宽 * 0.20
眼高 = 眼宽 * 0.52          # 这张图眼睛更细长
眼中心y = 眉y + (方底 - 眉y) * 0.50


def 眼(眼心x):
    rx, ry = 眼宽 / 2, 眼高 / 2
    d.ellipse([眼心x - rx, 眼中心y - ry, 眼心x + rx, 眼中心y + ry], fill=色(0xfaf6f4))
    虹r = ry * 0.95
    虹心y = 眼中心y + ry * 0.06
    框 = [眼心x - 虹r, 虹心y - 虹r, 眼心x + 虹r, 虹心y + 虹r]
    圆图 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(圆图).ellipse(框, fill=255)
    圆内 = np.array(圆图) > 127
    dxn = (xx - 眼心x) / max(1e-6, 虹r)
    边 = 虹心y - 0.22 * 虹r * (1 - np.clip(dxn ** 2, 0, 1))
    for 掩, 色值 in ((圆内 & (yy <= 边), 虹), (圆内 & (yy > 边), 虹下)):
        图.paste(Image.new("RGB", (W, H), 色值), (0, 0),
                Image.fromarray((掩 * 255).astype(np.uint8), "L"))
    d.ellipse([眼心x - 4, 虹心y - 4, 眼心x + 4, 虹心y + 4], fill=瞳)
    d.ellipse([眼心x - 8, 眼中心y - 5, 眼心x - 3, 眼中心y - 1], fill=白)
    反r = 虹r - 4
    反光 = ((xx - 眼心x) ** 2 + (yy - (虹心y + 4 + 反r)) ** 2 <= 反r ** 2) & 圆内
    图.paste(Image.new("RGB", (W, H), 色(0xd8c8e4)), (0, 0),
            Image.fromarray((反光 * 255).astype(np.uint8), "L"))
    d.line([(眼心x - rx, 眼中心y - ry * 0.1), (眼心x + rx * 0.15, 眼中心y - ry * 1.0),
            (眼心x + rx, 眼中心y - ry * 0.2)], fill=线, width=3)


眼(cx - (眼距 / 2 + 眼宽 / 2))
眼(cx + (眼距 / 2 + 眼宽 / 2))

for 侧 in (-1, 1):
    mx = cx + 侧 * (眼距 / 2 + 眼宽 / 2)
    d.line([(mx - 眼宽 * 0.42, 眉y + 2), (mx, 眉y - 2), (mx + 眼宽 * 0.42, 眉y + 2)],
           fill=色(0xc09a9a), width=2)
    bx = cx + 侧 * (眼距 / 2 + 眼宽 * 0.58)
    d.ellipse([bx - 14, 眼中心y + 22, bx + 14, 眼中心y + 38], fill=腮)

d.ellipse([cx - 4, 嘴y - 2, cx + 4, 嘴y + 3], fill=色(0xc07a84))

# ---------- ④ 中分：头顶 + 左右两片帘 ----------
头顶r = r * 1.10
头顶心y = cy - r * 0.06
头顶掩 = ((xx - cx) ** 2 + (yy - 头顶心y) ** 2 <= 头顶r ** 2) & (yy <= 发际y + 2)

帘们 = []
for 侧 in (-1, 1):
    # 内层帘：靠中缝、短
    A = (cx + 侧 * r * 0.04, 发际y + r * 0.02)
    B = (cx + 侧 * r * 0.42, cy + r * 0.52)
    L = math.hypot(B[0] - A[0], B[1] - A[1])
    C1 = (A[0] + 侧 * L * 0.22, A[1] + L * 0.30)
    C2 = (B[0] - 侧 * L * 0.10, B[1] - L * 0.28)
    帘们.append((柳叶掩码(A, B, C1, C2, r * 0.30, 0.45, 0.9), 1))
    # 外层帘：靠外、长，扫到脸颊外侧
    A2 = (cx + 侧 * r * 0.10, 发际y - r * 0.04)
    B2 = (cx + 侧 * r * 0.72, cy + r * 0.78)
    L2 = math.hypot(B2[0] - A2[0], B2[1] - A2[1])
    C1b = (A2[0] + 侧 * L2 * 0.26, A2[1] + L2 * 0.28)
    C2b = (B2[0] - 侧 * L2 * 0.12, B2[1] - L2 * 0.26)
    帘们.append((柳叶掩码(A2, B2, C1b, C2b, r * 0.34, 0.45, 0.9), 2))

前发 = 头顶掩.copy()
for 掩, _ in 帘们:
    前发 |= 掩

# 垫底片：
#   宽度 = 一直到【侧发的竖直中线】为止（不漏两侧的缝）
#   底边 = 逐列贴着帘的下缘；没有帘的列就沿用最近一列的底（不塌下去）
帘合 = np.zeros((H, W), bool)
for 掩, _ in 帘们:
    帘合 |= 掩

垫底左 = cx - 脸边          # 侧发的竖直中线（侧发就是沿这条线竖直落下的）
垫底右 = cx + 脸边
垫底顶Y = int(cy - r * 0.95)

底表 = np.full(W, np.nan)
for x in range(W):
    列 = np.where(帘合[:, x])[0]
    if len(列):
        底表[x] = 列.max()
有效 = ~np.isnan(底表)
if 有效.any():
    底表 = np.interp(np.arange(W), np.where(有效)[0], 底表[有效])   # 空缺列用邻近列补

垫底掩 = np.zeros((H, W), bool)
for x in range(int(垫底左), int(垫底右) + 1):
    if not (0 <= x < W):
        continue
    底 = int(底表[x]) if not np.isnan(底表[x]) else int(发际y + r * 0.10)
    底 = max(底, 垫底顶Y + 1)
    垫底掩[垫底顶Y:底 + 1, x] = True
垫底掩 &= ((xx - cx) ** 2 + (yy - 头顶心y) ** 2 <= 头顶r ** 2)
落色(垫底掩, 发, 描=False)
print(f"垫底片：{int(垫底掩.sum())} px，x {垫底左:.0f}~{垫底右:.0f}（到侧发中线），顶 y={垫底顶Y}")

落色(前发, 发, 描=True, 边色=发边)
print(f"中分前发：{int(前发.sum())} px（头顶 + 4 片帘）")

# 中缝：一条细线，从发际线往上一小段
d.line([(cx, 发际y + 2), (cx, 发际y - r * 0.42)], fill=发边, width=2)

# ---------- ⑤ 两侧长发（垂到肩下） ----------
for 侧 in (-1, 1):
    ax = cx + 侧 * 脸边
    A = (ax - 侧 * r * 0.05, 发际y - r * 0.04)
    B = (ax + 侧 * r * 0.10, cy + r * 1.95)
    L = B[1] - A[1]
    掩 = 柳叶掩码(A, B, (A[0] + 侧 * r * 0.04, A[1] + L * 0.25),
                 (B[0], B[1] - L * 0.18), r * 0.40, 0.45, 0.85)
    落色(掩, 发, 描=True, 边色=发边)

# ---------- ⑥ 配饰 ----------
# 左侧蓝宝石发夹
gx, gy = cx - r * 0.78, cy - r * 0.62
d.rectangle([gx - 12, gy - 16, gx + 12, gy + 16], fill=色(0x4a4a58), outline=线)
多边([(gx, gy - 12), (gx + 8, gy), (gx, gy + 12), (gx - 8, gy)], 填=色(0x6c9ad8), 边=线)
# 右上方金色饰
hx, hy = cx + r * 0.86, cy - r * 0.78
d.line([(hx - 16, hy + 10), (hx - 4, hy - 12), (hx + 8, hy + 6), (hx + 18, hy - 10)],
       fill=色(0xd8b070), width=4)
# 左侧白羽毛
for k in range(3):
    fa = (cx - r * 0.74 + k * 6, cy - r * 0.30)
    fb = (cx - r * 0.92 + k * 4, cy + r * 0.12)
    d.line([fa, fb], fill=色(0xe8eef8), width=6)

# ---- 层检查：每层都必须在 ----
应有 = {"后发": True, "头顶": bool(头顶掩.any()), "垫底片": bool(垫底掩.any()),
        "帘": len(帘们) == 4, "侧发": True, "脸": True, "五官": True}
缺 = [k for k, v in 应有.items() if not v]
print("层检查：" + ("全部齐" if not 缺 else "缺 " + "、".join(缺)))

图.save(出 / "参考中分-第一稿.png")
图.resize((W * 3, H * 3), Image.NEAREST).save(出 / "参考中分-第一稿-放大.png")
print("已出：参考中分-第一稿（含 -放大）")
