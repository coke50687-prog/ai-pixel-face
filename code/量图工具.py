"""量图：把一张图变成"数字报告 + 带坐标系和标注的图"。

用法：
    python 量图.py 量 <图片> [网格步长] [--色 #rrggbb] [--色 #rrggbb] [--容差 24]
    python 量图.py 比 <图A> <图B> [--阈值 12]

    「量」不给 --色 时自动找主色（粗）；给了 --色 就只量这几个颜色（准）
    「比」输出两图差异像素数与分布，用来验证"改一个参数有没有生效"

例：
    python 量图.py 量 参考.png 100 --色 #d896a9 --色 #5c4545
    python 量图.py 比 old.png new.png
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")


def 读(路径):
    im = Image.open(路径).convert("RGB")
    return im, np.array(im).astype(int)


def 十六进制(s):
    s = s.strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def 颜色掩码(a, rgb, 容差=24):
    return ((np.abs(a[:, :, 0] - rgb[0]) < 容差) &
            (np.abs(a[:, :, 1] - rgb[1]) < 容差) &
            (np.abs(a[:, :, 2] - rgb[2]) < 容差))


def 主色(a, 占比阈值=0.004, 合并距离=26):
    q = (a // 24 * 24).astype(int)
    平 = q.reshape(-1, 3)
    键 = 平[:, 0] * 65536 + 平[:, 1] * 256 + 平[:, 2]
    唯一, 计数 = np.unique(键, return_counts=True)
    中心们 = []
    for i in np.argsort(-计数):
        k = int(唯一[i])
        c = np.array([k // 65536, (k // 256) % 256, k % 256])
        n = int(计数[i])
        if n / len(键) < 占比阈值:
            continue
        for j, (c0, n0) in enumerate(中心们):
            if np.abs(c - c0).sum() < 合并距离 * 3:
                中心们[j] = ((c0 * n0 + c * n) / (n0 + n), n0 + n)
                break
        else:
            中心们.append((c.astype(float), n))
    结果 = []
    for c, n in 中心们:
        rgb = tuple(int(v) for v in c)
        结果.append((rgb, n / len(键), 颜色掩码(a, rgb, 20)))
    结果.sort(key=lambda x: -x[1])
    return 结果


def 最大块(掩, 降=4):
    """降采样后连通块，返回最大块的 bbox（原图坐标）。精度 ±降。"""
    H, W = 掩.shape
    h, w = max(1, H // 降), max(1, W // 降)
    小 = np.zeros((h, w), np.uint8)
    for j in range(h):
        for i in range(w):
            小[j, i] = 1 if 掩[j * 降:(j + 1) * 降, i * 降:(i + 1) * 降].mean() > 0.5 else 0
    看 = np.zeros((h, w), bool)
    最好 = (0, None)
    for j0 in range(h):
        for i0 in range(w):
            if 小[j0, i0] and not 看[j0, i0]:
                栈 = [(j0, i0)]
                看[j0, i0] = True
                点 = []
                while 栈:
                    y, x = 栈.pop()
                    点.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and 小[ny, nx] and not 看[ny, nx]:
                            看[ny, nx] = True
                            栈.append((ny, nx))
                if len(点) > 最好[0]:
                    ys = [p[0] for p in 点]
                    xs = [p[1] for p in 点]
                    最好 = (len(点), (min(xs) * 降, max(xs) * 降 + 降 - 1,
                                     min(ys) * 降, max(ys) * 降 + 降 - 1))
    if 最好[1] is None:
        return None
    x0, x1, y0, y1 = 最好[1]
    return {"块": 最好[0], "降": 降, "bbox": (x0, x1, y0, y1),
            "占比": 最好[0] * 降 * 降 / (H * W)}


def 量(路径, 网格=100, 指定色=None, 容差=24):
    路径 = Path(路径)
    im, a = 读(路径)
    H, W = a.shape[:2]
    报告 = [f"图：{路径.name}   尺寸 {W}×{H}", ""]

    if 指定色:
        清单 = [(c, 颜色掩码(a, c, 容差)) for c in 指定色]
        报告.append("== 指定颜色 ==")
    else:
        清单 = []
        报告.append("== 自动主色（粗）==")
        for rgb, 比, 掩 in 主色(a)[:10]:
            清单.append((rgb, 掩))
            报告.append(f"  #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  {比*100:5.1f}%")

    报告.append("")
    报告.append("== 位置 ==")
    画 = im.copy()
    d = ImageDraw.Draw(画)
    色环 = [(220, 40, 40), (30, 90, 220), (20, 150, 80), (230, 130, 20), (150, 40, 200),
            (200, 40, 140), (30, 160, 160), (140, 120, 20), (90, 90, 90), (230, 90, 60)]
    for idx, (rgb, 掩) in enumerate(清单[:10]):
        n = int(掩.sum())
        if n < 200:
            continue
        ys, xs = np.where(掩)
        报告.append(f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}: {n} px（{n/(W*H)*100:.1f}%）")
        报告.append(f"      整体 bbox x {xs.min()}~{xs.max()} y {ys.min()}~{ys.max()}"
                    f"（宽 {xs.max()-xs.min()+1} 高 {ys.max()-ys.min()+1}） 质心 ({xs.mean():.0f},{ys.mean():.0f})")
        块 = 最大块(掩)
        if 块:
            报告.append(f"      最大块 bbox x {块['bbox'][0]}~{块['bbox'][1]} "
                        f"y {块['bbox'][2]}~{块['bbox'][3]}（精度 ±{块['降']}px）")
        抽样 = [xs.min() + int((xs.max() - xs.min()) * t) for t in (0.25, 0.5, 0.75)]
        段 = []
        for x in 抽样:
            列 = np.where(掩[:, x])[0]
            if len(列):
                段.append(f"x={x}: y {列.min()}~{列.max()}")
        报告.append("      逐列：" + ("；".join(段) if 段 else "无"))
        c = 色环[idx % len(色环)]
        d.rectangle([xs.min(), ys.min(), xs.max(), ys.max()], outline=c, width=2)
        d.text((xs.min() + 3, max(0, ys.min() - 14)),
               f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}", fill=c)

    for x in range(0, W, 网格):
        d.line([(x, 0), (x, H)], fill=(0, 170, 240), width=1)
        d.text((x + 2, 3), str(x), fill=(0, 110, 190))
    for y in range(0, H, 网格):
        d.line([(0, y), (W, y)], fill=(0, 170, 240), width=1)
        d.text((3, y + 2), str(y), fill=(0, 110, 190))

    图出 = 路径.with_name(路径.stem + "-量图.png")
    文出 = 路径.with_name(路径.stem + "-量图.txt")
    画.save(图出)
    文出.write_text("\n".join(报告), encoding="utf-8")
    print("\n".join(报告))
    print(f"\n已出：{图出.name} / {文出.name}")


def 比(甲, 乙, 阈值=12):
    _, a = 读(甲)
    _, b = 读(乙)
    if a.shape != b.shape:
        print(f"尺寸不同：{a.shape[:2]} vs {b.shape[:2]}，无法逐像素比")
        return
    d = np.abs(a - b).sum(axis=2) > 阈值
    H, W = a.shape[:2]
    print(f"差异像素：{int(d.sum())} / {H*W}（{d.sum()/(H*W)*100:.2f}%）")
    if d.sum():
        ys, xs = np.where(d)
        print(f"范围 x {xs.min()}~{xs.max()}  y {ys.min()}~{ys.max()}")
        行 = {}
        for y in ys:
            行[int(y)] = 行.get(int(y), 0) + 1
        最多 = sorted(行.items(), key=lambda kv: -kv[1])[:5]
        print("差异最多的行：" + "，".join(f"y={y}({n})" for y, n in 最多))
        print("判断：" + ("改描边级别的量" if d.sum() < 2000 else "改形状级别的量"))


if __name__ == "__main__":
    参 = sys.argv[1:]
    if not 参:
        print(__doc__)
        sys.exit(0)
    模式 = 参[0]
    if 模式 == "量":
        if len(参) < 2:
            print("用法：量 <图片> [网格] [--色 #rrggbb]")
            sys.exit(1)
        路径 = 参[1]
        网格, 容差, 色们 = 100, 24, []
        i = 2
        while i < len(参):
            if 参[i] == "--色":
                色们.append(十六进制(参[i + 1]))
                i += 2
            elif 参[i] == "--容差":
                容差 = int(参[i + 1])
                i += 2
            else:
                网格 = int(参[i])
                i += 1
        量(路径, 网格, 色们 or None, 容差)
    elif 模式 == "比":
        if len(参) < 3:
            print("用法：比 <图A> <图B> [阈值]")
            sys.exit(1)
        阈值 = int(参[3]) if len(参) > 3 else 12
        比(参[1], 参[2], 阈值)
    else:
        print(__doc__)
