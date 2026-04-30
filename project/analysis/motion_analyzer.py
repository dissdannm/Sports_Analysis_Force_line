from __future__ import annotations

from analysis.alignment_analyzer import AlignmentAnalyzer
from analysis.angle_calculator import AngleCalculator
from analysis.temporal_analyzer import TemporalAnalyzer
from models.metrics import MotionMetrics
from models.motion_definition import MotionDefinition


class MotionAnalyzer:
    def __init__(
        self,
        angle_calculator: AngleCalculator,
        alignment_analyzer: AlignmentAnalyzer,
        temporal_analyzer: TemporalAnalyzer,
    ) -> None:
        self.angle_calculator = angle_calculator
        self.alignment_analyzer = alignment_analyzer
        self.temporal_analyzer = temporal_analyzer

    def analyze(
        self,
        pose_landmarks,
        motion_definition: MotionDefinition,
        timestamp_ms: int,
    ) -> MotionMetrics:
        angle_metrics = self.angle_calculator.calculate_all(pose_landmarks)
        alignment_metrics = self.alignment_analyzer.calculate_all(pose_landmarks)

        base_metric_values = self._merge_metric_values(
            angle_values=angle_metrics.values,
            alignment_values={
                "trunk_tilt": alignment_metrics.trunk_tilt,
                "pelvis_tilt": alignment_metrics.pelvis_tilt,
                "neck_forward_offset": alignment_metrics.neck_forward_offset,
                "center_offset": alignment_metrics.center_offset,
                "knee_offset_left": alignment_metrics.knee_offset_left,
                "knee_offset_right": alignment_metrics.knee_offset_right,
                "body_line_angle": alignment_metrics.body_line_angle,
                "trunk_ground_angle": alignment_metrics.trunk_ground_angle,
                "neck_flexion_angle": alignment_metrics.neck_flexion_angle,
                "lumbar_gap_distance": alignment_metrics.lumbar_gap_distance,
            },
        )

        temporal_metrics = self.temporal_analyzer.calculate(
            motion_definition=motion_definition,
            base_metrics=base_metric_values,
            timestamp_ms=timestamp_ms,
        )

        all_metric_values = dict(base_metric_values)
        all_metric_values.update(temporal_metrics.values)

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
        merged = {}
        merged.update(angle_values)
        merged.update(alignment_values)
        return merged

    @staticmethod
    def _select_enabled_metrics(
        all_metric_values: dict[str, float],
        enabled_metrics: list[str],
    ) -> dict[str, float]:
        selected = {}

        for metric_id in enabled_metrics:
            if metric_id in all_metric_values:
                selected[metric_id] = all_metric_values[metric_id]

        return selected