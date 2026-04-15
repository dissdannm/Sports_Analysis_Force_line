# models/enums.py

from __future__ import annotations

from enum import Enum


class RuntimeMode(str, Enum):
    """
    运行模式枚举。
    """
    LOCAL_DEBUG = "local_debug"
    SERVICE = "service"


class AlertLevel(str, Enum):
    """
    告警等级枚举。
    """
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class MotionMetricType(str, Enum):
    """
    动作指标类型枚举。

    说明：
    - ANGLE:
        角度类指标
    - OFFSET:
        偏移 / 力线类指标
    - TEMPORAL:
        时序类指标，例如计次、阶段、周期时长、角速度
    """
    ANGLE = "angle"
    OFFSET = "offset"
    TEMPORAL = "temporal"