# backend/schemas.py

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    健康检查响应。
    """
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")


class MotionListItem(BaseModel):
    """
    动作列表中的单个动作摘要。
    """
    motion_id: str = Field(..., description="动作唯一 ID")
    motion_name: str = Field(..., description="动作名称")
    version: str = Field(..., description="动作配置版本")
    description: str = Field(..., description="动作描述")


class MotionListResponse(BaseModel):
    """
    动作列表响应。
    """
    items: list[MotionListItem] = Field(default_factory=list)


class MotionDetailResponse(BaseModel):
    """
    单个动作详情响应。
    """
    motion_id: str = Field(..., description="动作唯一 ID")
    motion_name: str = Field(..., description="动作名称")
    version: str = Field(..., description="动作配置版本")
    description: str = Field(..., description="动作描述")
    landmarks_required: list[str] = Field(default_factory=list, description="所需关键点")
    enabled_metrics: list[str] = Field(default_factory=list, description="启用指标")
    tags: list[str] = Field(default_factory=list, description="动作标签")
    stable_frames: int = Field(..., description="稳定帧数")
    voice_cooldown_ms: int = Field(..., description="语音冷却时间（毫秒）")
    min_hold_ms: int = Field(..., description="最小保持时间（毫秒）")


class LandmarkInput(BaseModel):
    """
    单个关键点输入模型。

    说明：
    - 当前后端分析接口先约定前端传 landmarks
    - 这样先把分析契约稳定下来
    - 后续如果要支持前端传图片，再单独扩图片上传接口
    """
    x: float = Field(..., description="关键点 x 坐标")
    y: float = Field(..., description="关键点 y 坐标")
    z: float = Field(0.0, description="关键点 z 坐标")
    visibility: float = Field(0.0, description="关键点可见性")


class AnalyzeFrameRequest(BaseModel):
    """
    单帧分析请求。

    字段说明：
    - motion_id:
        当前动作 ID，由前端按钮点击或业务逻辑决定
    - session_id:
        前端侧会话 ID，可选
    - timestamp_ms:
        当前帧毫秒时间戳
    - landmarks:
        关键点字典，key 为 landmark 名称
    """
    motion_id: str = Field(..., description="动作唯一 ID")
    session_id: str | None = Field(default=None, description="前端会话 ID")
    timestamp_ms: int = Field(..., description="当前帧时间戳（毫秒）")
    landmarks: dict[str, LandmarkInput] = Field(default_factory=dict, description="关键点数据")


class AlertResponse(BaseModel):
    """
    告警响应模型。
    """
    code: str = Field(..., description="告警编码")
    level: str = Field(..., description="告警等级")
    message: str = Field(..., description="告警显示文本")
    speak: bool = Field(..., description="是否建议播报")
    speak_text: str = Field(..., description="建议播报文本")
    metric_id: str = Field(..., description="关联指标 ID")
    motion_id: str = Field(..., description="关联动作 ID")


class AnalyzeFrameResponse(BaseModel):
    """
    单帧分析响应。

    字段说明：
    - pose_detected:
        当前请求是否视为检测到有效关键点
    - metrics:
        当前动作启用指标的结果
    - alerts:
        当前动作触发的告警列表
    """
    motion_id: str = Field(..., description="动作唯一 ID")
    session_id: str | None = Field(default=None, description="前端会话 ID")
    timestamp_ms: int = Field(..., description="当前帧时间戳（毫秒）")
    pose_detected: bool = Field(..., description="是否检测到有效姿态")
    metrics: dict[str, float] = Field(default_factory=dict, description="动作启用指标结果")
    alerts: list[AlertResponse] = Field(default_factory=list, description="告警列表")