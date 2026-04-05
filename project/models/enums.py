# models/enums.py

from __future__ import annotations

from enum import Enum


class AlertLevel(str, Enum):
    """
    告警等级枚举。

    设计说明：
    - 继承 str 和 Enum，便于直接序列化到 JSON
    - 后续后端接口、语音模块、前端展示都统一使用这组值
    """
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class InputSourceType(str, Enum):
    """
    输入源类型枚举。

    当前先定义企业第一版会用到的几类输入源。
    """
    LOCAL_CAMERA = "local_camera"
    VIDEO_FILE = "video_file"
    API_FRAME = "api_frame"


class MotionMetricType(str, Enum):
    """
    动作指标类型枚举。

    当前版本先保留企业第一版最常用的几种。
    """
    ANGLE = "angle"
    OFFSET = "offset"
    DISTANCE = "distance"
    RATIO = "ratio"


class RuntimeMode(str, Enum):
    """
    运行模式枚举。

    说明：
    - LOCAL_DEBUG：本地调试模式，后端可直接操作本地摄像头
    - SERVICE：服务模式，前端负责采集，后端负责分析
    """
    LOCAL_DEBUG = "local_debug"
    SERVICE = "service"