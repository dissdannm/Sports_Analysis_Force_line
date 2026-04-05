# analysis/motion_analyzer.py

from __future__ import annotations

from analysis.alignment_analyzer import AlignmentAnalyzer
from analysis.angle_calculator import AngleCalculator
from models.metrics import MotionMetrics
from models.motion_definition import MotionDefinition


class MotionAnalyzer:
    """
    动作级分析器。

    设计定位：
    - 这是平台能力层和动作规则层之间的桥梁
    - 它会先计算平台当前支持的全部基础指标
    - 再根据 MotionDefinition 选择当前动作真正启用的指标
    - 它不负责阈值比较，不负责告警，不负责语音

    维护思想：
    - 平台“能算什么”由基础分析器维护
    - 动作“用什么”由 motion json 配置决定
    """

    def __init__(
        self,
        angle_calculator: AngleCalculator,
        alignment_analyzer: AlignmentAnalyzer,
    ) -> None:
        self.angle_calculator = angle_calculator
        self.alignment_analyzer = alignment_analyzer

    def analyze(self, pose_landmarks, motion_definition: MotionDefinition) -> MotionMetrics:
        """
        根据动作定义分析当前姿态，输出动作级指标结果。
        """
        angle_metrics = self.angle_calculator.calculate_all(pose_landmarks)
        alignment_metrics = self.alignment_analyzer.calculate_all(pose_landmarks)

        all_metric_values = self._merge_metric_values(
            angle_values=angle_metrics.values,
            alignment_values={
                "trunk_tilt": alignment_metrics.trunk_tilt,
                "pelvis_tilt": alignment_metrics.pelvis_tilt,
                "neck_forward_offset": alignment_metrics.neck_forward_offset,
                "center_offset": alignment_metrics.center_offset,
                "knee_offset_left": alignment_metrics.knee_offset_left,
                "knee_offset_right": alignment_metrics.knee_offset_right,
                "body_line_angle": alignment_metrics.body_line_angle,
            },
        )

        selected_values = self._select_enabled_metrics(
            all_metric_values=all_metric_values,
            enabled_metrics=motion_definition.enabled_metrics,
        )

        return MotionMetrics(
            angles=angle_metrics,
            alignment=alignment_metrics,
            selected=selected_values,
        )

    @staticmethod
    def _merge_metric_values(
        angle_values: dict[str, float],
        alignment_values: dict[str, float],
    ) -> dict[str, float]:
        """
        合并平台全部可计算指标，形成统一 metric_id -> value 字典。
        """
        merged = {}
        merged.update(angle_values)
        merged.update(alignment_values)
        return merged

    @staticmethod
    def _select_enabled_metrics(
        all_metric_values: dict[str, float],
        enabled_metrics: list[str],
    ) -> dict[str, float]:
        """
        根据动作配置筛选当前动作真正启用的指标。

        说明：
        - 只返回 motion_definition.enabled_metrics 中指定的指标
        - 若某个指标当前帧未能算出，则跳过，不抛异常
        - 这样可以提高系统在关键点缺失场景下的鲁棒性
        """
        selected = {}

        for metric_id in enabled_metrics:
            if metric_id in all_metric_values:
                selected[metric_id] = all_metric_values[metric_id]

        return selected