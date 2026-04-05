# core/pipeline.py

from __future__ import annotations

from dataclasses import dataclass

from analysis.motion_analyzer import MotionAnalyzer
from analysis.noise_filter import NoiseFilter
from analysis.rule_engine import RuleEngine
from core.motion_registry import MotionRegistry
from models.alert import Alert
from models.metrics import MotionMetrics
from output.metric_overlay import MetricOverlay
from output.skeleton_drawer import SkeletonDrawer
from output.speech_manager import SpeechDecision, SpeechManager
from perception.pose_estimator import PoseEstimator


@dataclass(slots=True)
class PipelineResult:
    """
    单帧处理结果。

    字段说明：
    - frame:
        处理后用于显示的图像
    - motion_metrics:
        当前动作的指标结果；未检测到人体时可为 None
    - alerts:
        当前动作的告警列表
    - speech_decision:
        当前帧的语音决策结果
    - pose_detected:
        当前帧是否检测到人体
    """
    frame: object
    motion_metrics: MotionMetrics | None
    alerts: list[Alert]
    speech_decision: SpeechDecision
    pose_detected: bool


class Pipeline:
    """
    单帧分析流水线。

    设计定位：
    - 串联输入帧到最终结果的处理流程
    - 不负责打开摄像头
    - 不负责窗口生命周期管理
    - 不负责应用启动逻辑

    设计原则：
    1. 主流程清晰
    2. 模块边界明确
    3. 只依赖已经存在的核心组件
    """

    def __init__(
        self,
        pose_estimator: PoseEstimator,
        motion_registry: MotionRegistry,
        motion_analyzer: MotionAnalyzer,
        noise_filter: NoiseFilter,
        rule_engine: RuleEngine,
        speech_manager: SpeechManager,
        skeleton_drawer: SkeletonDrawer,
        metric_overlay: MetricOverlay,
        motion_id: str,
        show_skeleton: bool = True,
        show_angles: bool = True,
        show_alignment: bool = True,
        show_alerts: bool = True,
    ) -> None:
        self.pose_estimator = pose_estimator
        self.motion_registry = motion_registry
        self.motion_analyzer = motion_analyzer
        self.noise_filter = noise_filter
        self.rule_engine = rule_engine
        self.speech_manager = speech_manager
        self.skeleton_drawer = skeleton_drawer
        self.metric_overlay = metric_overlay

        self.motion_id = motion_id
        self.motion_definition = self.motion_registry.get_motion(motion_id)

        self.show_skeleton = show_skeleton
        self.show_angles = show_angles
        self.show_alignment = show_alignment
        self.show_alerts = show_alerts

    def process_frame(self, frame, timestamp_ms: int) -> PipelineResult:
        """
        处理单帧图像，并返回结构化结果。
        """
        pose_landmarks = self.pose_estimator.process(frame, timestamp_ms)

        if pose_landmarks is None:
            return PipelineResult(
                frame=frame,
                motion_metrics=None,
                alerts=[],
                speech_decision=SpeechDecision(should_speak=False),
                pose_detected=False,
            )

        motion_metrics = self.motion_analyzer.analyze(
            pose_landmarks=pose_landmarks,
            motion_definition=self.motion_definition,
        )

        filtered_metrics = self.noise_filter.apply(motion_metrics)

        alerts = self.rule_engine.evaluate(
            motion_definition=self.motion_definition,
            motion_metrics=filtered_metrics,
        )

        speech_decision = self.speech_manager.handle_alerts(
            alerts=alerts,
            timestamp_ms=timestamp_ms,
            cooldown_ms=self.motion_definition.timing.voice_cooldown_ms,
        )

        output_frame = frame.copy()

        if self.show_skeleton:
            output_frame = self.skeleton_drawer.draw(output_frame, pose_landmarks)

        if self.show_angles:
            output_frame = self.metric_overlay.draw_angles(output_frame, filtered_metrics.angles)

        if self.show_alignment:
            output_frame = self.metric_overlay.draw_alignment(output_frame, filtered_metrics.alignment)

        if self.show_alerts:
            output_frame = self.metric_overlay.draw_alerts(output_frame, alerts)

        return PipelineResult(
            frame=output_frame,
            motion_metrics=filtered_metrics,
            alerts=alerts,
            speech_decision=speech_decision,
            pose_detected=True,
        )