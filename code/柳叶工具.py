"""柳叶生成器：给两个端点 + 弯度 + 最大宽度 + 最宽位置，出一片柳叶。

用法（命令行）：
  python 柳叶工具.py 演示
  python 柳叶工具.py 出一片 名称 x1 y1 x2 y2 弯度 最宽 最宽位置 [画布W 画布H]

可被别的脚本 import：
  from 柳叶工具 import 柳叶掩码
  形 = 柳叶掩码(W, H, A, B, 弯度, 最宽, 最宽位置)

参数含义：
  A, B        两个端点（浮点像素坐标）
  弯度        0 = 直的；正 = 往左法线方向鼓；负 = 往右（数值是控制点偏移的像素）
  最宽        叶身最宽处宽度（像素）
  最宽位置    0~1，最宽处在整条长度的哪个位置（0.5 = 正中间）
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
出 = Path(r"D:\DDSH\我的\画板")


def _贝塞尔(P0, P1, P2, n=400):
    ts = np.linspace(0, 1, n)
    x = (1 - ts) ** 2 * P0[0] + 2 * (1 - ts) * ts * P1[0] + ts ** 2 * P2[0]
    y = (1 - ts) ** 2 * P0[1] + 2 * (1 - ts) * ts * P1[1] + ts ** 2 * P2[1]
    return x, y


def 柳叶掩码(W, H, A, B, 弯度=0.0, 最宽=14.0, 最宽位置=0.45, 端正=1.4):
    """返回 bool 掩码。"""
    ax, ay = float(A[0]), float(A[1])
    bx, by = float(B[0]), float(B[1])
    dx, dy = bx - ax, by - ay
    L = max(1e-6, (dx * dx + dy * dy) ** 0.5)
    # 法线
    nx, ny = -dy / L, dx / L
    # 控制点：中点 + 法线方向偏移（弯度）
    cx = (ax + bx) / 2 + nx * 弯度
    cy = (ay + by) / 2 + ny * 弯度

    xs, ys = _贝塞尔((ax, ay), (cx, cy), (bx, by), 500)

    # 宽度剖面：在 t=最宽位置 处达到最宽，两端收到 0
    n = len(xs)
    t = np.linspace(0, 1, n)
    k = 最宽位置
    段1 = np.clip(t / max(1e-6, k), 0.0, 1.0)
    段2 = np.clip((t - k) / max(1e-6, 1 - k), 0.0, 1.0)
    prof = np.where(t <= k,
                    np.sin(段1 * np.pi / 2) ** 端正,
                    np.cos(段2 * np.pi / 2) ** 端正)
    半 = prof * (最宽 / 2.0)

    左缘, 右缘 = [], []
    for i in range(n):
        if i == 0:
            tanx, tany = xs[1] - xs[0], ys[1] - ys[0]
        elif i == n - 1:
            tanx, tany = xs[-1] - xs[-2], ys[-1] - ys[-2]
        else:
            tanx, tany = xs[i + 1] - xs[i - 1], ys[i + 1] - ys[i - 1]
        m = max(1e-9, (tanx * tanx + tany * tany) ** 0.5)
        ux, uy = -tany / m, tanx / m
        左缘.append((xs[i] + ux * 半[i], ys[i] + uy * 半[i]))
        右缘.append((xs[i] - ux * 半[i], ys[i] - uy * 半[i]))

    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in 左缘 + 右缘[::-1]], fill=255)
    return np.array(m) > 127


def 画一片(形, 名称="柳叶", 色=(60, 64, 84), 边色=(30, 32, 44)):
    H, W = 形.shape
    色阵 = np.zeros((H, W, 4), np.uint8)
    色阵[形] = (*色, 255)
    边 = 形 ^ (np.roll(形, 1, 0) & np.roll(形, -1, 0) & np.roll(形, 1, 1) & np.roll(形, -1, 1))
    色阵[边] = (*边色, 255)
    return Image.fromarray(色阵, "RGBA")


def 演示():
    组 = [
        # 名称,        A,          B,          弯,  宽, 位置
        ("直的短叶", (20, 20), (20, 90), 0, 14, 0.45),
        ("直的胖叶", (70, 20), (70, 90), 0, 24, 0.45),
        ("左弯小叶", (120, 20), (120, 90), 14, 14, 0.45),
        ("左弯大叶", (170, 20), (180, 92), 22, 22, 0.40),
        ("右弯小叶", (230, 20), (230, 90), -14, 14, 0.45),
        ("上胖下尖", (280, 20), (280, 90), 0, 20, 0.30),
        ("上尖下胖", (330, 20), (330, 90), 0, 20, 0.70),
        ("斜着扫出", (380, 90), (330, 20), 16, 18, 0.45),
    ]
    W, H = 440, 120
    板 = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(板)
    for 名, A, B, 弯, 宽, 位 in 组:
        形 = 柳叶掩码(W, H, A, B, 弯, 宽, 位)
        板.alpha_composite(画一片(形))
        d.text((A[0] - 18, 100), 名, fill=(40, 40, 40))
    板.resize((W * 4, H * 4), Image.NEAREST).save(出 / "柳叶-演示-放大.png")
    板.save(出 / "柳叶-演示.png")
    print("已出：柳叶-演示 / 柳叶-演示-放大")


if __name__ == "__main__":
    参 = sys.argv[1:]
    if not 参 or 参[0] == "演示":
        演示()
    elif 参[0] == "出一片":
        名 = 参[1]
        x1, y1, x2, y2 = map(float, 参[2:6])
        弯, 宽, 位 = map(float, 参[6:9])
        W = int(参[9]) if len(参) > 9 else 240
        H = int(参[10]) if len(参) > 10 else 240
        形 = 柳叶掩码(W, H, (x1, y1), (x2, y2), 弯, 宽, 位)
        图 = 画一片(形)
        图.save(出 / f"{名}.png")
        图.resize((W * 8, H * 8), Image.NEAREST).save(出 / f"{名}-放大.png")
        ys, xs = np.where(形)
        print(f"{名}: 宽 {xs.max()-xs.min()+1} 高 {ys.max()-ys.min()+1} x {xs.min()}~{xs.max()} y {ys.min()}~{ys.max()}")
    else:
        print(__doc__)
