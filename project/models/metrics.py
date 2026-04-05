# models/metrics.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(slots=True)
class AngleMetrics:
    """
    角度类指标结果。

    设计说明：
    - 用字典保存，便于扩展
    - key 为 metric_id，例如 left_knee / right_elbow
    - value 为角度数值，单位通常为度
    """
    values: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class AlignmentMetrics:
    """
    力线 / 对齐类指标结果。

    设计说明：
    - 当前保留平台第一版常用固定字段
    - 这些字段对应 alignment_analyzer.py 中的基础可计算能力
    """
    trunk_tilt: float = 0.0
    pelvis_tilt: float = 0.0
    neck_forward_offset: float = 0.0
    center_offset: float = 0.0
    knee_offset_left: float = 0.0
    knee_offset_right: float = 0.0
    body_line_angle: float = 0.0


@dataclass(slots=True)
class MotionMetrics:
    """
    动作级指标总结果。

    字段说明：
    - angles:
        通用角度指标结果
    - alignment:
        通用力线 / 偏移指标结果
    - selected:
        当前动作真正启用并输出的指标结果
    - extras:
        预留扩展字段，便于后续加入 gait、阶段识别等结果
    """
    angles: AngleMetrics = field(default_factory=AngleMetrics)
    alignment: AlignmentMetrics = field(default_factory=AlignmentMetrics)
    selected: Dict[str, float] = field(default_factory=dict)
    extras: Dict[str, float] = field(default_factory=dict)