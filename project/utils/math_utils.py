# utils/math_utils.py

from __future__ import annotations

import math
from typing import Optional, Tuple


Point2D = Tuple[float, float]
Vector2D = Tuple[float, float]


def vector_from_points(start: Point2D, end: Point2D) -> Vector2D:
    """
    根据两个二维点生成向量 start -> end。

    参数：
    - start: 起点
    - end: 终点

    返回：
    - 二维向量 (dx, dy)
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

    参数：
    - p1: 第一条边上的点
    - vertex: 顶点
    - p3: 第二条边上的点

    返回：
    - 角度值，单位为度

    说明：
    - 若任一向量长度为 0，则返回 0.0
    - 内部会自动处理浮点误差，避免 acos 域错误
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

    当 denominator 为 0 时，返回 default。
    """
    if denominator == 0:
        return default
    return numerator / denominator


def point_from_landmark_xy(landmark) -> Optional[Point2D]:
    """
    从 Landmark 对象提取二维坐标 (x, y)。

    参数：
    - landmark: 任意具有 x、y 属性的对象

    返回：
    - (x, y) 二元组
    - 若 landmark 为 None，则返回 None

    设计说明：
    - 这个函数有助于降低 analysis 层对具体数据类实现的耦合
    """
    if landmark is None:
        return None
    return landmark.x, landmark.y