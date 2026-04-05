# analysis/noise_filter.py

from __future__ import annotations

from collections import deque
from copy import deepcopy

from models.metrics import AlignmentMetrics, AngleMetrics, MotionMetrics


class NoiseFilter:
    """
    数值滤波器（企业第一版）。

    设计定位：
    - 属于平台稳定性层
    - 负责平滑指标波动
    - 不负责业务规则判断
    - 不负责动作选择逻辑

    当前实现：
    - 使用简单移动平均
    - 对 angle_metrics.values 和 motion_metrics.selected 做逐指标平滑
    - 对 alignment_metrics 的固定字段做逐字段平滑

    设计原则：
    1. 第一版优先稳定、可解释、易维护
    2. 后续如有需要，可升级为 EMA / 中值滤波 / 卡尔曼滤波
    """

    def __init__(self, window_size: int = 5) -> None:
        """
        参数说明：
        - window_size:
            移动平均窗口大小。
            例如 5 表示最近 5 帧做平均。
        """
        if window_size <= 0:
            raise ValueError("window_size 必须大于 0")

        self.window_size = window_size

        self._angle_history: dict[str, deque[float]] = {}
        self._selected_history: dict[str, deque[float]] = {}
        self._alignment_history: dict[str, deque[float]] = {
            "trunk_tilt": deque(maxlen=window_size),
            "pelvis_tilt": deque(maxlen=window_size),
            "neck_forward_offset": deque(maxlen=window_size),
            "center_offset": deque(maxlen=window_size),
            "knee_offset_left": deque(maxlen=window_size),
            "knee_offset_right": deque(maxlen=window_size),
            "body_line_angle": deque(maxlen=window_size),
        }

    def apply(self, motion_metrics: MotionMetrics) -> MotionMetrics:
        """
        对 MotionMetrics 进行平滑处理，并返回新的结果对象。

        说明：
        - 返回的是新对象，不直接原地修改输入
        - 这样更安全，也更利于后续调试
        """
        filtered_metrics = deepcopy(motion_metrics)

        filtered_metrics.angles = self._filter_angle_metrics(filtered_metrics.angles)
        filtered_metrics.alignment = self._filter_alignment_metrics(filtered_metrics.alignment)
        filtered_metrics.selected = self._filter_selected_metrics(filtered_metrics.selected)

        return filtered_metrics

    def _filter_angle_metrics(self, angle_metrics: AngleMetrics) -> AngleMetrics:
        """
        平滑角度类指标。
        """
        filtered_values: dict[str, float] = {}

        for metric_id, value in angle_metrics.values.items():
            history = self._angle_history.setdefault(
                metric_id,
                deque(maxlen=self.window_size),
            )
            history.append(value)
            filtered_values[metric_id] = self._average(history)

        return AngleMetrics(values=filtered_values)

    def _filter_alignment_metrics(self, alignment_metrics: AlignmentMetrics) -> AlignmentMetrics:
        """
        平滑力线 / 偏移类指标。
        """
        filtered = deepcopy(alignment_metrics)

        filtered.trunk_tilt = self._append_and_average("trunk_tilt", alignment_metrics.trunk_tilt)
        filtered.pelvis_tilt = self._append_and_average("pelvis_tilt", alignment_metrics.pelvis_tilt)
        filtered.neck_forward_offset = self._append_and_average(
            "neck_forward_offset",
            alignment_metrics.neck_forward_offset,
        )
        filtered.center_offset = self._append_and_average("center_offset", alignment_metrics.center_offset)
        filtered.knee_offset_left = self._append_and_average(
            "knee_offset_left",
            alignment_metrics.knee_offset_left,
        )
        filtered.knee_offset_right = self._append_and_average(
            "knee_offset_right",
            alignment_metrics.knee_offset_right,
        )
        filtered.body_line_angle = self._append_and_average(
            "body_line_angle",
            alignment_metrics.body_line_angle,
        )

        return filtered

    def _filter_selected_metrics(self, selected_metrics: dict[str, float]) -> dict[str, float]:
        """
        平滑当前动作实际启用的指标结果。
        """
        filtered_selected: dict[str, float] = {}

        for metric_id, value in selected_metrics.items():
            history = self._selected_history.setdefault(
                metric_id,
                deque(maxlen=self.window_size),
            )
            history.append(value)
            filtered_selected[metric_id] = self._average(history)

        return filtered_selected

    def _append_and_average(self, field_name: str, value: float) -> float:
        """
        将数值加入历史窗口并计算平均值。
        """
        history = self._alignment_history[field_name]
        history.append(value)
        return self._average(history)

    @staticmethod
    def _average(values: deque[float]) -> float:
        """
        计算窗口平均值。
        """
        if not values:
            return 0.0
        return sum(values) / len(values)