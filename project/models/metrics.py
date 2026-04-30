# models/metrics.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AngleMetrics:
    """
    角度类指标集合。
    """
    values: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class AlignmentMetrics:
    """
    力线 / 偏移类指标集合。
    """
    trunk_tilt: float = 0.0
    pelvis_tilt: float = 0.0
    neck_forward_offset: float = 0.0
    center_offset: float = 0.0
    knee_offset_left: float = 0.0
    knee_offset_right: float = 0.0
    body_line_angle: float = 0.0
    trunk_ground_angle: float = 0.0
    neck_flexion_angle: float = 0.0
    lumbar_gap_distance: float = 0.0


@dataclass(slots=True)
class MotionMetrics:
    """
    动作级指标结果。
    """
    angles: AngleMetrics
    alignment: AlignmentMetrics
    selected: dict[str, float] = field(default_factory=dict)