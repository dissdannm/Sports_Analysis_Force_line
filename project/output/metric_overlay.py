# output/metric_overlay.py

from __future__ import annotations

import cv2

from models.alert import Alert
from models.metrics import AlignmentMetrics, AngleMetrics


class MetricOverlay:
    """
    指标文字叠加器。

    设计定位：
    - 只负责把结果画到图像上
    - 不负责分析逻辑
    - 不负责告警判定
    - 不负责语音播报
    """

    def __init__(
        self,
        font_scale: float = 0.55,
        font_thickness: int = 2,
        left_margin: int = 20,
        top_margin: int = 30,
        line_height: int = 24,
    ) -> None:
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.left_margin = left_margin
        self.top_margin = top_margin
        self.line_height = line_height

    def draw_angles(self, frame, angle_metrics: AngleMetrics):
        """
        在图像左上角绘制角度指标。
        """
        current_y = self.top_margin + 70

        angle_items = sorted(angle_metrics.values.items(), key=lambda item: item[0])

        for metric_id, value in angle_items:
            text = f"{metric_id}: {value:.2f}"
            self._draw_text(
                frame=frame,
                text=text,
                x=self.left_margin,
                y=current_y,
                color=(255, 255, 255),
            )
            current_y += self.line_height

        return frame

    def draw_alignment(self, frame, alignment_metrics: AlignmentMetrics):
        """
        在图像左侧中下区域绘制力线 / 偏移指标。
        """
        current_y = self.top_margin + 320

        alignment_lines = [
            f"trunk_tilt: {alignment_metrics.trunk_tilt:.4f}",
            f"pelvis_tilt: {alignment_metrics.pelvis_tilt:.4f}",
            f"neck_forward_offset: {alignment_metrics.neck_forward_offset:.4f}",
            f"center_offset: {alignment_metrics.center_offset:.4f}",
            f"knee_offset_left: {alignment_metrics.knee_offset_left:.4f}",
            f"knee_offset_right: {alignment_metrics.knee_offset_right:.4f}",
            f"body_line_angle: {alignment_metrics.body_line_angle:.2f}",
            f"trunk_ground_angle: {alignment_metrics.trunk_ground_angle:.2f}",
            f"neck_flexion_angle: {alignment_metrics.neck_flexion_angle:.2f}",
            f"lumbar_gap_distance: {alignment_metrics.lumbar_gap_distance:.4f}",
        ]

        for text in alignment_lines:
            self._draw_text(
                frame=frame,
                text=text,
                x=self.left_margin,
                y=current_y,
                color=(0, 255, 255),
            )
            current_y += self.line_height

        return frame

    def draw_alerts(self, frame, alerts: list[Alert]):
        """
        在图像右上角绘制当前告警列表。
        """
        if not alerts:
            return frame

        image_width = frame.shape[1]
        current_y = self.top_margin + 70

        for alert in alerts:
            text = f"[{alert.level.value}] {alert.message}"
            color = self._resolve_alert_color(alert.level.value)

            text_x = max(20, image_width - 520)
            self._draw_text(
                frame=frame,
                text=text,
                x=text_x,
                y=current_y,
                color=color,
            )
            current_y += self.line_height

        return frame

    def draw_scores(self, frame, motion_id: str, selected_metrics: dict[str, float]):
        """
        在画面左上角绘制动作评分与等级。
        """
        score = None
        label = None

        if motion_id == "sit_up":
            score = selected_metrics.get("quality_score")
            label = "Quality Score"
        elif motion_id == "bridge":
            score = selected_metrics.get("ahp_quality_score")
            label = "AHP Score"

        if score is None:
            return frame

        if score >= 90:
            grade = "Excellent"
            score_color = (0, 255, 0)
        elif score >= 75:
            grade = "Good"
            score_color = (0, 255, 255)
        elif score >= 60:
            grade = "Fair"
            score_color = (0, 165, 255)
        else:
            grade = "Poor"
            score_color = (0, 0, 255)

        self._draw_text(
            frame=frame,
            text=f"{label}: {score:.2f}",
            x=self.left_margin,
            y=self.top_margin,
            color=score_color,
        )
        self._draw_text(
            frame=frame,
            text=f"Level: {grade}",
            x=self.left_margin,
            y=self.top_margin + self.line_height,
            color=score_color,
        )

        return frame

    def _draw_text(
        self,
        frame,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        cv2.putText(
            frame,
            text,
            (x, y),
            self.font,
            self.font_scale,
            color,
            self.font_thickness,
            cv2.LINE_AA,
        )

    @staticmethod
    def _resolve_alert_color(level: str) -> tuple[int, int, int]:
        if level == "severe":
            return (0, 0, 255)
        if level == "moderate":
            return (0, 165, 255)
        if level == "mild":
            return (0, 255, 255)
        return (255, 255, 255)