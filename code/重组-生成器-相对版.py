"""重组（相对坐标版）：所有定位都从 cx / cy / r 推出来，改头的大小不用重调。

相对化清单（原绝对值 → 现在怎么算）：
  后发底      340        → 底Y + 0.49r
  发尾中心    ±69.5      → ±0.695r
  发尾半宽    40         → 0.40r
  发尾尖      422        → 底Y + 1.31r
  垫底片顶    73         → 顶y(cx) − 0.063r
  垫底片高    74         → 0.74r
  垫底片左右  x 100~219  → cx±界（本来就是 0.6r）
  侧发矩形    x 60~100   → cx−r ~ cx−界
  描边内边    砍到 131   → 转折y + 0.284×(鼻y−转折y)
  描边外缘    砍到 126   → 转折y + 0.25×(鼻y−转折y)
  分叉线起点  272        → 鼻y + 0.63×(底Y−鼻y)

跑完和绝对坐标版对比，应当逐像素一致。
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
根 = Path(r"D:\DDSH\我的")
出 = 根 / "画板"

源码 = (根 / "贴零件1c.py").read_text(encoding="utf-8")
段 = 源码.split("# ---------- 贴零件1")[0]
广 = {}
exec(compile(段, "face", "exec"), 广)
W, H = 广["W"], 广["H"]
cx, cy, r = 广["cx"], 广["cy"], 广["r"]
半, 界 = 广["半"], 广["界"]
顶y, 底Y, 鼻y, 眉y = 广["顶y"], 广["底Y"], 广["鼻y"], 广["眉y"]
根线 = 广["根线"]
转折x, 转折y = cx - 界, 顶y(cx - 界)
发色, 发边 = (0x4a, 0x58, 0x88), (0x1e, 0x24, 0x34)

# —— 相对量（全部以 r 为单位） ——
外扩, 上移 = 0.12 * r, 0.04 * r
圆心y = cy - 上移
后发底 = round(底Y + 0.49 * r)
尾中心偏 = 0.695 * r
尾半宽 = 0.40 * r
尾尖y = round(底Y + 1.31 * r)
垫顶 = round(顶y(cx) - 0.063 * r)
垫高 = round(0.74 * r)
内边砍到 = 转折y + 0.284 * (鼻y - 转折y)
外缘砍到 = 转折y + 0.25 * (鼻y - 转折y)
分叉起 = 鼻y + 0.63 * (底Y - 鼻y)
yy, xx = np.mgrid[0:H, 0:W]


def 圆顶(x):
    d2 = (r + 外扩) ** 2 - (x - cx) ** 2
    return 1e9 if d2 <= 0 else 圆心y - math.sqrt(d2)


def 根y(x):
    点 = sorted(根线, key=lambda p: p[0])
    if x <= 点[0][0]:
        return 点[0][1]
    if x >= 点[-1][0]:
        return 点[-1][1]
    for i in range(len(点) - 1):
        x0, y0 = 点[i]
        x1, y1 = 点[i + 1]
        if x0 <= x <= x1 and x1 > x0:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 点[-1][1]


def 多边(点们):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in 点们], fill=255)
    return np.array(m) > 127


# ① 后发
后发 = np.zeros((H, W), bool)
for x in range(int(cx - (r + 外扩)), int(cx + (r + 外扩)) + 1):
    if 0 <= x < W:
        上y = max(int(圆心y - (r + 外扩)), 圆顶(x))
        if 上y <= 后发底:
            后发[int(上y):int(后发底) + 1, x] = True

for 心 in (cx - 尾中心偏, cx, cx + 尾中心偏):
    左半, 右半 = [], []
    for k in range(31):
        tt = k / 30.0
        半w = 尾半宽 * (1 - tt ** 2.2) ** 0.70 * (1 - tt) ** 0.35
        y = 后发底 + (尾尖y - 后发底) * tt
        左半.append((心 - 半w, y))
        右半.append((心 + 半w, y))
    后发 |= 多边(左半 + 右半[::-1])

# ② 头顶
圆 = (xx - cx) ** 2 + (yy - 圆心y) ** 2 <= (r + 外扩) ** 2
上 = np.zeros((H, W), bool)
for x in range(W):
    上[:, x] = yy[:, x] <= 根y(x)
头顶 = 圆 & 上

# ③ 垫底片
垫底 = np.zeros((H, W), bool)
垫底[int(垫顶):int(垫顶 + 垫高), int(cx - 界):int(cx + 界) + 1] = True

# ④ 刘海（从定稿图取掩码：那张图只有脸+刘海，脸是肤色不会混）
a = np.array(Image.open(根 / "素材" / "刘海零件" / "刘海-M字-七根-定稿.png").convert("RGB")).astype(int)
刘海 = ((abs(a[:, :, 0] - 0x4a) < 12) & (abs(a[:, :, 1] - 0x58) < 12) & (abs(a[:, :, 2] - 0x88) < 14)) | \
       ((abs(a[:, :, 0] - 0x1e) < 12) & (abs(a[:, :, 1] - 0x24) < 12) & (abs(a[:, :, 2] - 0x34) < 12))

# ⑤ 侧发
外x, 内x = cx - r, cx - 界
本体尖 = (内x + (内x - 外x) / 3.0, 底Y)
左尖 = (本体尖[0] + 0.067 * r, 本体尖[1] - 0.062 * r)
右尖 = ((2 * cx - 本体尖[0]) - 0.077 * r, 本体尖[1] - 0.086 * r)


def 侧片(a外, a内, 尖x, 尖y):
    外缘, 内缘 = [], []
    for k in range(21):
        t = k / 20
        外缘.append((a外 - 0.025 * r * math.sin(math.pi * t) + (尖x - a外) * (t ** 1.9),
                     鼻y + (尖y - 鼻y) * t))
        内缘.append((a内 + (尖x - a内) * (t ** 0.75), 鼻y + (尖y - 鼻y) * t))
    return [(a外, 鼻y)] + 外缘 + 内缘[::-1] + [(a内, 鼻y)]


def 叶片们(左=True):
    矩形点 = [(外x, 转折y), (内x, 转折y), (内x, 鼻y), (外x, 鼻y)]
    本点 = 侧片(外x, 内x, 本体尖[0], 本体尖[1])
    if 左:
        复点 = 侧片(外x + 0.08 * r, 内x - 0.08 * r, 左尖[0], 左尖[1])
    else:
        矩形点 = [(2 * cx - x, y) for (x, y) in 矩形点]
        本点 = [(2 * cx - x, y) for (x, y) in 本点]
        复点 = 侧片(2 * cx - (外x + 0.08 * r), 2 * cx - (内x - 0.08 * r), 右尖[0], 右尖[1])
    return 多边(矩形点), 多边(本点), 多边(复点)


def 侧发掩码(左=True):
    掩 = np.zeros((H, W), bool)
    for m in 叶片们(左):
        掩 |= m
    for x in range(W):
        上边y = max(转折y, 圆顶(x))
        if 上边y > 0:
            掩[:int(上边y), x] = False
    return 掩


侧左, 侧右 = 侧发掩码(True), 侧发掩码(False)
脸 = 多边(广["轮廓"])


def 清描边(边):
    边 = 边.copy()
    边[int(转折y - 2.5):int(转折y + 3.5), :] = False          # 上边横线
    for 内 in (cx - 界, cx + 界):
        边[:int(内边砍到), int(内) - 1:int(内) + 2] = False     # 内边竖线（砍上段）
    for 外 in (cx - r, cx + r):
        边[:int(外缘砍到), int(外) - 1:int(外) + 2] = False     # 外缘（砍上 1/4）
    return 边


def 交界线(左=True):
    _, 本, 复 = 叶片们(左)
    本边 = 本 ^ (np.roll(本, 1, 0) & np.roll(本, -1, 0) & np.roll(本, 1, 1) & np.roll(本, -1, 1))
    界 = 本边 & 复
    if not 界.any():
        return 界
    ys, _ = np.where(界)
    y0, y1 = ys.min(), ys.max()
    砍 = np.zeros((H, W), bool)
    砍[:int(y0 + (y1 - y0) / 3.0), :] = True
    return 界 & ~砍


# 合成
合 = 广["图"].copy()
脸arr = np.array(合).astype(int)
背景 = (脸arr.sum(axis=2) > 750) & (~脸)
for 掩, 描边 in ((后发 & 背景, True), (头顶, False), (刘海, True), (垫底, False), (侧左, True), (侧右, True)):
    层 = np.zeros((H, W, 4), np.uint8)
    层[掩] = (*发色, 255)
    if 描边:
        边 = 掩 ^ (np.roll(掩, 1, 0) & np.roll(掩, -1, 0) & np.roll(掩, 1, 1) & np.roll(掩, -1, 1))
        if 掩 is 侧左 or 掩 is 侧右:
            边 = 清描边(边)
        层[边] = (*发边, 255)
    合.paste(Image.fromarray(层, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层[:, :, 3], "L"))

for 左 in (True, False):
    界m = 交界线(左)
    层j = np.zeros((H, W, 4), np.uint8)
    层j[界m] = (*发边, 255)
    合.paste(Image.fromarray(层j, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层j[:, :, 3], "L"))

合.save(出 / "整体-相对版.png")
合.resize((W * 4, H * 4), Image.NEAREST).save(出 / "整体-相对版-放大.png")
print(f"相对量：外扩{外扩} 上移{上移} 后发底{后发底:.1f} 尾尖{尾尖y:.1f} 垫顶{垫顶:.1f}")
print("已出：整体-相对版（含 -放大）")
