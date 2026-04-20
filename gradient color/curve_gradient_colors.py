"""
中心线渐变颜色生成（抠自 render_gaussian_matlab_overlay.py）
================================================================
本文件把"为中心线上每个点按弧长比例赋予渐变颜色"的逻辑单独抽出来，
供其它 code agent 参考/移植。仅依赖 numpy。

上游调用点（原始代码在 render_gaussian_circles3_synthetic_volume_paper.py:846）：
    curve_colors = build_curve_colors(len(render_curve_points))

语义：给定中心线上的 N 个采样点，按它们在序列中的归一化位置
(index / (N - 1)) ∈ [0, 1] 在 CURVE_GRADIENT_STOPS 里做分段线性插值，
返回 N 个 (r, g, b) ∈ [0, 1] 三元组，与点一一对应。

下游（可选）使用方式：
    for layer in build_curve_render_layers(curve_colors, point_size):
        # 每个 layer 含 colors / point_size / opacity，
        # 原始代码把它们丢给 pyvista.add_points 分两层渲染（glow + core）
        ...
"""

from __future__ import annotations

import numpy as np


# ----------------------------------------------------------------------
# 1. 渐变色端点定义
# ----------------------------------------------------------------------
# 每个元素是 (ratio, (r, g, b))，ratio ∈ [0, 1]，颜色通道也在 [0, 1]。
# 默认使用两端点：起点偏青蓝 (33,248,255)，终点偏橙红 (255,108,0)。
# 如果要多段渐变，按 ratio 升序继续加 tuple 即可，_sample_curve_gradient
# 会自动做逐段线性插值。
CURVE_GRADIENT_STOPS = (
    (0.0, (33.0 / 255.0, 248.0 / 255.0, 1.0)),
    (1.0, (1.0, 108.0 / 255.0, 0.0)),
)

# 备用色标（与上面结构一致，只换颜色，作为第二组渐变方案供对比）：
# 起点深紫 (103, 0, 167)，终点亮黄 (253, 231, 37) —— 类 "plasma" 冷暖对比。
CURVE_GRADIENT_STOPS_ALT = (
    (0.0, (103.0 / 255.0, 0.0 / 255.0, 167.0 / 255.0)),
    (1.0, (253.0 / 255.0, 231.0 / 255.0, 37.0 / 255.0)),
)


# ----------------------------------------------------------------------
# 2. 渲染分层用到的常量（仅在使用 build_curve_render_layers 时需要）
# ----------------------------------------------------------------------
# 两层渲染（外发光 glow + 核心 core）各自的：
#   - *_WHITE_BLEND   : 把原色朝白色混合的比例（0 不变，1 纯白）
#   - *_POINT_SIZE_SCALE : 相对输入 point_size 的缩放倍率
#   - *_OPACITY       : 该层整体透明度
CURVE_GLOW_WHITE_BLEND = 0.18
CURVE_CORE_WHITE_BLEND = 0.32
CURVE_GLOW_POINT_SIZE_SCALE = 1.9
CURVE_CORE_POINT_SIZE_SCALE = 1.15
CURVE_GLOW_OPACITY = 0.35
CURVE_CORE_OPACITY = 0.98


# ----------------------------------------------------------------------
# 3. 通道级 / RGB 级 线性插值工具
# ----------------------------------------------------------------------
def _interpolate_channel(start, end, ratio):
    """单通道线性插值：start + (end - start) * ratio。"""
    return start + (end - start) * ratio


def _interpolate_rgb(start, end, ratio):
    """对 RGB 三通道分别做线性插值，返回 (r, g, b) 三元组。"""
    return tuple(_interpolate_channel(start[index], end[index], ratio) for index in range(3))


# ----------------------------------------------------------------------
# 4. 按 ratio 采样渐变色
# ----------------------------------------------------------------------
def _sample_curve_gradient(ratio, stops=None):
    """
    给定归一化位置 ratio ∈ [0, 1]，返回渐变带上对应的 (r, g, b) 颜色。

    参数：
      stops: 可选，格式同 CURVE_GRADIENT_STOPS 的 tuple；默认使用模块级
             CURVE_GRADIENT_STOPS。传入 CURVE_GRADIENT_STOPS_ALT 即可切换第二套色。

    逻辑：
      - ratio 小于等于第一个 stop 的 ratio：返回第一个 stop 的颜色（端点夹紧）。
      - 落在某段 [left_ratio, right_ratio] 内：按 (ratio - left) / (right - left)
        做线性插值。
      - 超过最后一个 stop：返回最后一个 stop 的颜色。
    """
    if stops is None:
        stops = CURVE_GRADIENT_STOPS
    if ratio <= stops[0][0]:
        return stops[0][1]
    for index in range(1, len(stops)):
        left_ratio, left_color = stops[index - 1]
        right_ratio, right_color = stops[index]
        if ratio <= right_ratio:
            local_ratio = (ratio - left_ratio) / (right_ratio - left_ratio)
            return _interpolate_rgb(left_color, right_color, local_ratio)
    return stops[-1][1]


# ----------------------------------------------------------------------
# 5. 主函数：给中心线上每个点生成颜色
# ----------------------------------------------------------------------
def build_curve_colors(count, stops=None):
    """
    输入：
      count —— 中心线上的点数 N。
      stops —— 可选色标，默认 CURVE_GRADIENT_STOPS；传 CURVE_GRADIENT_STOPS_ALT
               可生成第二套渐变。
    输出：长度为 N 的 list，每个元素是 (r, g, b) ∈ [0, 1] 三元组，
          第 i 个点的颜色 = _sample_curve_gradient(i / (N - 1), stops)。

    边界情况：
      - count <= 0：返回空 list。
      - count == 1：返回起点颜色（无法定义 ratio）。

    注意：这里只按"索引序号"做均匀渐变，没有按几何弧长做加权。
    如果中心线采样点密度不均、希望按真实弧长着色，调用前先做等弧长重采样，
    或者把 ratio 改成 (累积弧长 / 总弧长)。
    """
    if stops is None:
        stops = CURVE_GRADIENT_STOPS
    if count <= 0:
        return []
    if count == 1:
        return [stops[0][1]]

    colors = []
    for index in range(count):
        ratio = index / (count - 1)
        colors.append(_sample_curve_gradient(ratio, stops))
    return colors


# ======================================================================
# 以下部分是"下游消费代码"——把上面每点颜色喂给实际渲染 pipeline 时
# 用来做 glow/core 双层叠加的辅助函数。和"给每个点赋颜色"不是一回事，
# 一并抄过来让参考方能看懂上下游衔接；如果只需要颜色数组可以忽略。
# ======================================================================


def _blend_curve_colors_toward_white(curve_colors, ratio):
    """
    将颜色数组整体朝白色混合：out = color * (1 - ratio) + ratio。
    ratio=0 原色不变，ratio=1 纯白。用于让 glow 层比 core 层更淡。
    返回 np.ndarray(shape=(N, 3))，范围夹紧到 [0, 1]。
    """
    colors = np.asarray(curve_colors, dtype=float)
    return np.clip(colors * (1.0 - ratio) + ratio, 0.0, 1.0)


def build_curve_render_layers(curve_colors, point_size):
    """
    把单套 per-point 颜色扩展成两层渲染属性，供 pyvista.add_points 之类 API 使用：
      - 第 0 层 glow：点更大、更透明、更偏白 —— 制造外发光。
      - 第 1 层 core：点稍大、几乎不透明、偏白少 —— 保证核心可辨。

    返回 tuple(dict, dict)，每个 dict 包含：
        colors     : np.ndarray(N, 3)，取值 [0, 1]
        point_size : float
        opacity    : float

    原始 pipeline 的典型消费 (见 render_gaussian_matlab_overlay_volume_paper.py)：
        for layer in build_curve_render_layers(curve_colors, point_size):
            poly.point_data["rgb"] = np.round(layer["colors"] * 255.0).astype(np.uint8)
            plotter.add_points(
                poly,
                scalars="rgb", rgb=True,
                point_size=layer["point_size"],
                render_points_as_spheres=True,
                opacity=layer["opacity"],
                lighting=False,
            )
    """
    point_size = float(point_size)
    return (
        {
            "colors": _blend_curve_colors_toward_white(curve_colors, CURVE_GLOW_WHITE_BLEND),
            "point_size": point_size * CURVE_GLOW_POINT_SIZE_SCALE,
            "opacity": CURVE_GLOW_OPACITY,
        },
        {
            "colors": _blend_curve_colors_toward_white(curve_colors, CURVE_CORE_WHITE_BLEND),
            "point_size": point_size * CURVE_CORE_POINT_SIZE_SCALE,
            "opacity": CURVE_CORE_OPACITY,
        },
    )


# ----------------------------------------------------------------------
# 6. 可视化：把一组 per-point 颜色画成一条 2D 合成中心线 PNG
# ----------------------------------------------------------------------
def render_curve_png(colors, output_path, title=None, width=1200, height=360, dpi=150):
    """
    用 matplotlib 画一条合成的 2D 中心线（正弦波形），按 colors 里每个点的
    (r, g, b) 逐段上色并保存 PNG。仅用于直观检查色标效果，不涉及真实几何。

    输入：
      colors      : 长度 N 的 (r, g, b) 序列，取值 [0, 1]。
      output_path : 输出 PNG 路径。
      title       : 可选标题。
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    colors_array = np.asarray(colors, dtype=float)
    count = len(colors_array)
    if count < 2:
        raise ValueError("render_curve_png requires at least 2 colored points")

    # 合成一条正弦中心线，纯视觉展示；替换成真实中心线坐标也能直接用。
    x = np.linspace(0.0, 1.0, count)
    y = 0.35 * np.sin(2.0 * np.pi * x * 1.25)

    points = np.stack([x, y], axis=1).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    # 每段颜色取相邻两点颜色的平均，避免视觉跳变。
    segment_colors = 0.5 * (colors_array[:-1] + colors_array[1:])

    figure, axis = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    line_collection = LineCollection(segments, colors=segment_colors, linewidths=6.0)
    axis.add_collection(line_collection)
    axis.scatter(x, y, c=colors_array, s=18, zorder=3, edgecolors="none")

    axis.set_xlim(-0.02, 1.02)
    axis.set_ylim(-0.6, 0.6)
    axis.set_aspect("auto")
    axis.set_xticks([])
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)
    if title:
        axis.set_title(title)

    figure.tight_layout()
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(figure)


if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).resolve().parent
    point_count = 256

    default_colors = build_curve_colors(point_count, stops=CURVE_GRADIENT_STOPS)
    alt_colors = build_curve_colors(point_count, stops=CURVE_GRADIENT_STOPS_ALT)

    default_png = output_dir / "curve_gradient_default.png"
    alt_png = output_dir / "curve_gradient_alt.png"

    render_curve_png(default_colors, default_png, title="CURVE_GRADIENT_STOPS (cyan -> orange)")
    render_curve_png(alt_colors, alt_png, title="CURVE_GRADIENT_STOPS_ALT (purple -> yellow)")
