# utils/math_utils.py

from __future__ import annotations

import math
from typing import Optional, Tuple


Point2D = Tuple[float, float]
Vector2D = Tuple[float, float]


def vector_from_points(start: Point2D, end: Point2D) -> Vector2D:
    """
    根据两个二维点生成向量 start -> end。
    """
    return end[0] - start[0], end[1] - start[1]


def vector_length(vector: Vector2D) -> float:
    """
    计算二维向量长度。
    """
    return math.sqrt(vector[0] ** 2 + vector[1] ** 2)


def dot_product(v1: Vector2D, v2: Vector2D) -> float:
    """
    计算两个二维向量的点积。
    """
    return v1[0] * v2[0] + v1[1] * v2[1]


def calculate_angle(p1: Point2D, vertex: Point2D, p3: Point2D) -> float:
    """
    计算三点形成的夹角，顶点为 vertex。
    """
    vector_1 = vector_from_points(vertex, p1)
    vector_2 = vector_from_points(vertex, p3)

    length_1 = vector_length(vector_1)
    length_2 = vector_length(vector_2)

    if length_1 == 0 or length_2 == 0:
        return 0.0

    cosine_value = dot_product(vector_1, vector_2) / (length_1 * length_2)
    cosine_value = max(-1.0, min(1.0, cosine_value))

    angle_radians = math.acos(cosine_value)
    return math.degrees(angle_radians)


def midpoint(point_1: Point2D, point_2: Point2D) -> Point2D:
    """
    计算两个点的中点。
    """
    return (point_1[0] + point_2[0]) / 2.0, (point_1[1] + point_2[1]) / 2.0


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法。
    """
    if denominator == 0:
        return default
    return numerator / denominator


def point_from_landmark_xy(landmark) -> Optional[Point2D]:
    """
    从 Landmark 对象提取二维坐标 (x, y)。
    """
    if landmark is None:
        return None
    return landmark.x, landmark.y


def angle_with_horizontal(
    point_start: tuple[float, float],
    point_end: tuple[float, float],
) -> float:
    """
    计算线段相对水平线的夹角，返回 0 ~ 180 度。
    """
    dx = point_end[0] - point_start[0]
    dy = point_end[1] - point_start[1]

    angle_rad = math.atan2(abs(dy), abs(dx))
    return math.degrees(angle_rad)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    将数值限制在指定区间内。
    """
    return max(min_value, min(value, max_value))


def line_midpoint_vertical_gap(
    point_a: Point2D,
    point_b: Point2D,
    reference_point: Point2D,
) -> float:
    """
    计算线段中点相对参考点的垂直差，用于近似腰部离地风险。
    """
    mid_y = (point_a[1] + point_b[1]) / 2.0
    return abs(mid_y - reference_point[1])