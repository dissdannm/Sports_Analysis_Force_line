# backend/routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from analysis.alignment_analyzer import AlignmentAnalyzer
from analysis.angle_calculator import AngleCalculator
from analysis.motion_analyzer import MotionAnalyzer
from analysis.rule_engine import RuleEngine
from backend.schemas import (
    AlertResponse,
    AnalyzeFrameRequest,
    AnalyzeFrameResponse,
    HealthResponse,
    MotionDetailResponse,
    MotionListItem,
    MotionListResponse,
)
from core.motion_registry import MotionRegistry
from models.landmarks import Landmark, PoseLandmarks


router = APIRouter(prefix="/api/v1")


def get_motion_registry(request: Request) -> MotionRegistry:
    """
    从 FastAPI app.state 中获取 MotionRegistry。
    """
    motion_registry = getattr(request.app.state, "motion_registry", None)
    if motion_registry is None:
        raise RuntimeError("MotionRegistry 尚未初始化")
    return motion_registry


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    健康检查接口。
    """
    return HealthResponse(
        status="ok",
        service="sports-analysis-force-line-backend",
    )


@router.get("/motions", response_model=MotionListResponse)
def list_motions(request: Request) -> MotionListResponse:
    """
    获取当前可用动作列表。
    """
    motion_registry = get_motion_registry(request)

    items: list[MotionListItem] = []
    for motion_id in motion_registry.list_motion_ids():
        motion = motion_registry.get_motion(motion_id)
        items.append(
            MotionListItem(
                motion_id=motion.motion_id,
                motion_name=motion.motion_name,
                version=motion.version,
                description=motion.description,
            )
        )

    return MotionListResponse(items=items)


@router.get("/motions/{motion_id}", response_model=MotionDetailResponse)
def get_motion_detail(motion_id: str, request: Request) -> MotionDetailResponse:
    """
    获取单个动作的配置摘要。
    """
    motion_registry = get_motion_registry(request)

    try:
        motion = motion_registry.get_motion(motion_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"未找到动作: {motion_id}") from exc

    return MotionDetailResponse(
        motion_id=motion.motion_id,
        motion_name=motion.motion_name,
        version=motion.version,
        description=motion.description,
        landmarks_required=motion.landmarks_required,
        enabled_metrics=motion.enabled_metrics,
        tags=motion.tags,
        stable_frames=motion.timing.stable_frames,
        voice_cooldown_ms=motion.timing.voice_cooldown_ms,
        min_hold_ms=motion.timing.min_hold_ms,
    )


@router.post("/analyze/frame", response_model=AnalyzeFrameResponse)
def analyze_frame(request_body: AnalyzeFrameRequest, request: Request) -> AnalyzeFrameResponse:
    """
    单帧分析接口。

    当前版本说明：
    - 先约定前端直接传 landmarks
    - 后端直接复用平台分析能力做动作级指标与告警计算
    - 后续可再扩“上传图片 -> 后端跑 MediaPipe”的接口
    """
    motion_registry = get_motion_registry(request)

    try:
        motion_definition = motion_registry.get_motion(request_body.motion_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"未找到动作: {request_body.motion_id}",
        ) from exc

    if not request_body.landmarks:
        return AnalyzeFrameResponse(
            motion_id=request_body.motion_id,
            session_id=request_body.session_id,
            timestamp_ms=request_body.timestamp_ms,
            pose_detected=False,
            metrics={},
            alerts=[],
        )

    pose_landmarks = _convert_request_landmarks(request_body.landmarks)

    angle_calculator = AngleCalculator()
    alignment_analyzer = AlignmentAnalyzer()
    motion_analyzer = MotionAnalyzer(
        angle_calculator=angle_calculator,
        alignment_analyzer=alignment_analyzer,
    )
    rule_engine = RuleEngine()

    motion_metrics = motion_analyzer.analyze(
        pose_landmarks=pose_landmarks,
        motion_definition=motion_definition,
    )

    alerts = rule_engine.evaluate(
        motion_definition=motion_definition,
        motion_metrics=motion_metrics,
    )

    alert_items = [
        AlertResponse(
            code=alert.code,
            level=alert.level.value,
            message=alert.message,
            speak=alert.speak,
            speak_text=alert.speak_text,
            metric_id=alert.metric_id,
            motion_id=alert.motion_id,
        )
        for alert in alerts
    ]

    return AnalyzeFrameResponse(
        motion_id=request_body.motion_id,
        session_id=request_body.session_id,
        timestamp_ms=request_body.timestamp_ms,
        pose_detected=True,
        metrics=motion_metrics.selected,
        alerts=alert_items,
    )


def _convert_request_landmarks(landmarks: dict[str, object]) -> PoseLandmarks:
    """
    将请求中的 landmarks 转换为内部 PoseLandmarks。
    """
    converted = {}

    for landmark_name, landmark_input in landmarks.items():
        converted[landmark_name] = Landmark(
            x=landmark_input.x,
            y=landmark_input.y,
            z=landmark_input.z,
            visibility=landmark_input.visibility,
        )

    return PoseLandmarks(landmarks=converted)