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

    当前支持三类输出：
    1. 角度指标
    2. 力线 / 偏移指标
    3. 告警列表
    """

    def __init__(
        self,
        font_scale: float = 0.55,
        font_thickness: int = 2,
        left_margin: int = 20,
        top_margin: int = 30,
        line_height: int = 24,
    ) -> None:
        """
        参数说明：
        - font_scale:
            字体大小
        - font_thickness:
            字体粗细
        - left_margin:
            左侧边距
        - top_margin:
            顶部起始位置
        - line_height:
            每行文字之间的间距
        """
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
        current_y = self.top_margin

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
        在图像左侧中上区域绘制力线 / 偏移指标。
        """
        current_y = self.top_margin + 260

        alignment_lines = [
            f"trunk_tilt: {alignment_metrics.trunk_tilt:.4f}",
            f"pelvis_tilt: {alignment_metrics.pelvis_tilt:.4f}",
            f"neck_forward_offset: {alignment_metrics.neck_forward_offset:.4f}",
            f"center_offset: {alignment_metrics.center_offset:.4f}",
            f"knee_offset_left: {alignment_metrics.knee_offset_left:.4f}",
            f"knee_offset_right: {alignment_metrics.knee_offset_right:.4f}",
            f"body_line_angle: {alignment_metrics.body_line_angle:.2f}",
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

        设计说明：
        - 严重级别不同，颜色不同
        - 第一版直接显示 message，保持简单和稳定
        """
        if not alerts:
            return frame

        image_width = frame.shape[1]
        current_y = self.top_margin

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

    def _draw_text(
        self,
        frame,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        """
        绘制单行文字。
        """
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
        """
        根据告警等级返回显示颜色（BGR）。
        """
        if level == "severe":
            return (0, 0, 255)
        if level == "moderate":
            return (0, 165, 255)
        if level == "mild":
            return (0, 255, 255)
        return (255, 255, 255)