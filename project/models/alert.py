# models/alert.py

from __future__ import annotations

from dataclasses import dataclass

from models.enums import AlertLevel


@dataclass(slots=True)
class Alert:
    """
    统一告警对象。

    字段说明：
    - code:
        告警编码，程序内部唯一标识，例如 "neck_forward_offset"
    - level:
        告警等级，统一使用 AlertLevel
    - message:
        用于界面显示或日志记录的文本
    - speak:
        是否建议触发语音提示
    - speak_text:
        真正用于语音播报的文本，可与 message 不完全相同
    - metric_id:
        该告警关联的指标 ID
    - motion_id:
        该告警关联的动作 ID
    """

    code: str
    level: AlertLevel
    message: str
    speak: bool = False
    speak_text: str = ""
    metric_id: str = ""
    motion_id: str = ""