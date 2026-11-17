"""重组：所有零件都直接从几何算，不再从合成图里抠颜色。

零件：
  1 后发    2 头顶    3 垫底片    4 刘海    5/6 侧发（左/右）   7 脸
图层（下→上）：后发 → 脸 → 头顶 → 刘海 → 垫底片 → 侧发
输出：拆解-编号v17.png（爆炸图，看每块单独长什么样）
      整体-定稿v17.png（叠好的成品）
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
cx, cy, r, 界 = 广["cx"], 广["cy"], 广["r"], 广["界"]
顶y, 底Y, 鼻y = 广["顶y"], 广["底Y"], 广["鼻y"]
根线 = 广["根线"]
转折x, 转折y = cx - 界, 顶y(cx - 界)
发色, 发边 = (0x4a, 0x58, 0x88), (0x1e, 0x24, 0x34)
外扩, 上移 = 12.0, 4.0
圆心y = cy - 上移
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


# 1 后发
后发 = np.zeros((H, W), bool)
for x in range(int(cx - (r + 外扩)), int(cx + (r + 外扩)) + 1):
    if 0 <= x < W:
        上y = max(int(圆心y - (r + 外扩)), 圆顶(x))
        if 上y <= 340:
            后发[int(上y):341, x] = True

# 后发发尾：底部接三个大柳叶（尖朝下）
for 心 in (cx - 69.5, cx, cx + 69.5):
    半宽 = 40.0
    尖y = 422.0
    左半, 右半 = [], []
    for k in range(31):
        tt = k / 30.0
        半 = 半宽 * (1 - tt ** 2.2) ** 0.70 * (1 - tt) ** 0.35  # 外凸 + 尾端收得更尖
        y = 340 + (尖y - 340) * tt
        左半.append((心 - 半, y))
        右半.append((心 + 半, y))
    后发 |= 多边(左半 + 右半[::-1])
# 2 头顶
圆 = (xx - cx) ** 2 + (yy - 圆心y) ** 2 <= (r + 外扩) ** 2
上 = np.zeros((H, W), bool)
for x in range(W):
    上[:, x] = yy[:, x] <= 根y(x)
头顶 = 圆 & 上

# 3 垫底片（x 100~219，y 73~146）
垫底 = np.zeros((H, W), bool)
垫底[73:147, 100:220] = True

# 4 刘海：从"刘海定稿图"里抠发色（那张图只有脸+刘海，脸是肤色，不会混）
a = np.array(Image.open(根 / "素材" / "刘海零件" / "刘海-M字-七根-定稿.png").convert("RGB")).astype(int)
刘主 = (abs(a[:, :, 0] - 0x4a) < 12) & (abs(a[:, :, 1] - 0x58) < 12) & (abs(a[:, :, 2] - 0x88) < 14)
刘边 = (abs(a[:, :, 0] - 0x1e) < 12) & (abs(a[:, :, 1] - 0x24) < 12) & (abs(a[:, :, 2] - 0x34) < 12)
刘海 = 刘主 | 刘边

# 5/6 侧发：直接算几何（矩形 + 本体叶 + 复制叶），左右各一套
本体尖 = (转折x + 40 / 3.0, 底Y)
左尖 = (本体尖[0] + 6.7, 本体尖[1] - 6.2)
右尖 = ((2 * cx - 本体尖[0]) - 7.7, 本体尖[1] - 8.6)


def 侧片(外x, 内x, 尖x, 尖y):
    外缘, 内缘 = [], []
    for k in range(21):
        t = k / 20
        外缘.append((外x - 2.5 * math.sin(math.pi * t) + (尖x - 外x) * (t ** 1.9),
                     鼻y + (尖y - 鼻y) * t))
        内缘.append((内x + (尖x - 内x) * (t ** 0.75), 鼻y + (尖y - 鼻y) * t))
    return [(外x, 鼻y)] + 外缘 + 内缘[::-1] + [(内x, 鼻y)]


def 叶片们(左=True):
    """返回 (矩形, 本体叶, 复制叶) 三个掩码。"""
    矩形点 = [(60, 转折y), (100, 转折y), (100, 鼻y), (60, 鼻y)]
    本点 = 侧片(60, 100, 本体尖[0], 本体尖[1])
    if 左:
        复点 = 侧片(68, 92, 左尖[0], 左尖[1])
    else:
        矩形点 = [(2 * cx - x, y) for (x, y) in 矩形点]
        本点 = [(2 * cx - x, y) for (x, y) in 本点]
        复点 = 侧片(2 * cx - 68, 2 * cx - 92, 右尖[0], 右尖[1])
    return 多边(矩形点), 多边(本点), 多边(复点)


def 侧发掩码(左=True):
    矩形 = [(60, 转折y), (100, 转折y), (100, 鼻y), (60, 鼻y)]
    本 = 侧片(60, 100, 本体尖[0], 本体尖[1])
    if 左:
        复 = 侧片(68, 92, 左尖[0], 左尖[1])
    else:
        矩形 = [(2 * cx - x, y) for (x, y) in 矩形]
        本 = [(2 * cx - x, y) for (x, y) in 本]
        复 = 侧片(2 * cx - 68, 2 * cx - 92, 右尖[0], 右尖[1])
    掩 = 多边(矩形) | 多边(本) | 多边(复)
    # 上边跟着头顶外轮廓走
    for x in range(W):
        上边y = max(转折y, 圆顶(x))
        if 上边y > 0:
            掩[:int(上边y), x] = False
    return 掩


侧左 = 侧发掩码(True)
侧右 = 侧发掩码(False)

# 7 脸
脸 = 多边(广["轮廓"])

块们 = [("1 后发", 后发), ("2 头顶", 头顶), ("3 垫底片", 垫底), ("4 刘海", 刘海),
        ("5 侧发-左", 侧左), ("6 侧发-右", 侧右), ("7 脸", 脸)]

# 爆炸图
格宽, 格高, 列数 = 300, 420, 4
板 = Image.new("RGB", (格宽 * 列数, 格高 * 2), (250, 250, 250))
d = ImageDraw.Draw(板)
for i, (名, 掩) in enumerate(块们):
    cxg, cyg = (i % 列数) * 格宽, (i // 列数) * 格高
    小 = Image.new("RGB", (W, H), (255, 255, 255))
    if 名.endswith("脸"):
        小.paste(广["图"], (0, 0))
    else:
        层 = np.zeros((H, W, 4), np.uint8)
        层[掩] = (*发色, 255)
        边 = 掩 ^ (np.roll(掩, 1, 0) & np.roll(掩, -1, 0) & np.roll(掩, 1, 1) & np.roll(掩, -1, 1))
        层[边] = (*发边, 255)
        小.paste(Image.fromarray(层, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层[:, :, 3], "L"))
    板.paste(小, (cxg, cyg + 24))
    d.text((cxg + 6, cyg + 6), 名, fill=(20, 20, 20))
    d.rectangle([cxg, cyg, cxg + 格宽 - 1, cyg + 格高 - 1], outline=(220, 220, 220))
    print(f"{名}: {int(掩.sum())} 像素")
板.save(出 / "拆解-编号v17.png")

# 成品：后发 → 脸 → 头顶 → 刘海 → 垫底片 → 侧发
合 = 广["图"].copy()
脸arr = np.array(合).astype(int)
背景 = (脸arr.sum(axis=2) > 750) & (~脸)
def 清描边(边):
    """去掉侧发矩形上边那条横线，并把内边竖线砍掉上半截。"""
    边 = 边.copy()
    边[86:92, :] = False                                  # 横线（矩形上边）
    for 内x in (100, 220):
        边[:131, 内x - 1:内x + 2] = False                  # 内边竖线上半截
    for 外x in (60, 260):
        边[:126, 外x - 1:外x + 2] = False                  # 外缘最上 1/4
    return 边


def 交界线(左=True):
    """P1→P2 分叉线：只画靠近发尾那半段（y>272），靠近根部不画（看着连成一片）。"""
    # v8 的做法：本体叶的边落在复制叶里面的那段，去掉上 1/3
    _, 本, 复 = 叶片们(左)
    本边 = 本 ^ (np.roll(本, 1, 0) & np.roll(本, -1, 0) & np.roll(本, 1, 1) & np.roll(本, -1, 1))
    界 = 本边 & 复
    if not 界.any():
        return 界
    ys, _ = np.where(界)
    y0, y1 = ys.min(), ys.max()
    砍到 = int(y0 + (y1 - y0) / 3.0)
    砍 = np.zeros((H, W), bool)
    砍[:砍到, :] = True
    return 界 & ~砍
    点们 = []
    for k in range(41):
        tt = k / 40.0
        if 左:
            px = 68 + (左尖[0] - 68) * (tt ** 0.75)
            py = 鼻y + (左尖[1] - 鼻y) * tt
        else:
            px = (2 * cx - 68) - ((2 * cx - 68) - 右尖[0]) * (tt ** 0.75)
            py = 鼻y + (右尖[1] - 鼻y) * tt
        if py > 272:
            点们.append((px, py))
    m = Image.new("L", (W, H), 0)
    if len(点们) >= 2:
        ImageDraw.Draw(m).line([(float(x), float(y)) for x, y in 点们], fill=255, width=1)
    return np.array(m) > 0


for 掩, 边色 in ((后发 & 背景, 发边), (头顶, None), (刘海, 发边), (垫底, None), (侧左, 发边), (侧右, 发边)):
    层 = np.zeros((H, W, 4), np.uint8)
    层[掩] = (*发色, 255)
    if 边色 is not None:
        边 = 掩 ^ (np.roll(掩, 1, 0) & np.roll(掩, -1, 0) & np.roll(掩, 1, 1) & np.roll(掩, -1, 1))
        if 掩 is 侧左 or 掩 is 侧右:
            边 = 清描边(边)
        层[边] = (*发边, 255)
    合.paste(Image.fromarray(层, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层[:, :, 3], "L"))

# 显式补上两片叶子的交界线（本体叶填充把复制叶的边盖掉了）
for 左 in (True, False):
    界 = 交界线(左)
    层j = np.zeros((H, W, 4), np.uint8)
    层j[界] = (*发边, 255)
    合.paste(Image.fromarray(层j, "RGBA").convert("RGB"), (0, 0), Image.fromarray(层j[:, :, 3], "L"))
print(f"交界线像素：左 {int(交界线(True).sum())}  右 {int(交界线(False).sum())}")

合.save(出 / "整体-定稿v17.png")
合.resize((W * 4, H * 4), Image.NEAREST).save(出 / "整体-定稿v17-放大.png")
print("已出：拆解-编号v17、整体-定稿v17（含 -放大）")
