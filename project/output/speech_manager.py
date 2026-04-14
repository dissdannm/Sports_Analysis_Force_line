# output/speech_manager.py

from __future__ import annotations

from dataclasses import dataclass

from models.alert import Alert
from models.enums import AlertLevel
from output.speech_interface import SpeechInterface


@dataclass(slots=True)
class SpeechDecision:
    """
    一次语音决策结果。

    字段说明：
    - should_speak:
        当前是否应该播报
    - text:
        若需要播报，实际播报内容
    - alert:
        若是异常播报，对应触发的原始告警对象
        若是恢复播报，则为 None
    """
    should_speak: bool
    text: str = ""
    alert: Alert | None = None


class SpeechManager:
    """
    语音播报管理器。

    当前策略：
    1. 第一次出现主告警时播报
    2. 主告警发生切换时播报新的主告警
    3. 所有告警消失时播报恢复提示
    4. 主告警持续不变时不重复播报
    """

    _ALERT_PRIORITY = {
        AlertLevel.SEVERE: 3,
        AlertLevel.MODERATE: 2,
        AlertLevel.MILD: 1,
    }

    def __init__(
        self,
        speech_engine: SpeechInterface | None = None,
        recovery_text: str = "动作已经正确，请继续保持",
    ) -> None:
        self.speech_engine = speech_engine
        self.recovery_text = recovery_text

        self._last_primary_alert_code: str | None = None
        self._last_primary_alert_level: AlertLevel | None = None

    def handle_alerts(
        self,
        alerts: list[Alert],
        timestamp_ms: int,
        cooldown_ms: int,
    ) -> SpeechDecision:
        """
        根据当前告警列表决定是否播报。

        说明：
        - 当前先不依赖 timestamp_ms / cooldown_ms
        - 保留参数只是为了兼容现有主流程
        """
        candidate_alerts = [alert for alert in alerts if alert.speak]
        current_primary_alert = self._select_highest_priority_alert(candidate_alerts)

        # 情况 1：当前没有任何告警，且上一帧有主告警 -> 播恢复
        if current_primary_alert is None:
            if self._last_primary_alert_code is not None:
                self._last_primary_alert_code = None
                self._last_primary_alert_level = None
                self._emit_speech(self.recovery_text)

                return SpeechDecision(
                    should_speak=True,
                    text=self.recovery_text,
                    alert=None,
                )

            return SpeechDecision(should_speak=False)

        # 当前主告警标识
        current_code = current_primary_alert.code
        current_level = current_primary_alert.level

        # 情况 2：第一次出现主告警 -> 播报
        if self._last_primary_alert_code is None:
            speak_text = current_primary_alert.speak_text.strip() or current_primary_alert.message.strip()
            self._last_primary_alert_code = current_code
            self._last_primary_alert_level = current_level
            self._emit_speech(speak_text)

            return SpeechDecision(
                should_speak=True,
                text=speak_text,
                alert=current_primary_alert,
            )

        # 情况 3：主告警变了（code 变了，或者等级变了）-> 播新告警
        if (
            current_code != self._last_primary_alert_code
            or current_level != self._last_primary_alert_level
        ):
            speak_text = current_primary_alert.speak_text.strip() or current_primary_alert.message.strip()
            self._last_primary_alert_code = current_code
            self._last_primary_alert_level = current_level
            self._emit_speech(speak_text)

            return SpeechDecision(
                should_speak=True,
                text=speak_text,
                alert=current_primary_alert,
            )

        # 情况 4：主告警没变 -> 不播
        return SpeechDecision(should_speak=False)

    def _select_highest_priority_alert(self, alerts: list[Alert]) -> Alert | None:
        """
        从候选告警中选出优先级最高的一条。

        优先级规则：
        1. 告警等级越高优先级越高
        2. 若等级相同，保留列表中最先出现的一条
        """
        if not alerts:
            return None

        return max(
            alerts,
            key=lambda alert: self._ALERT_PRIORITY.get(alert.level, 0),
        )

    def _emit_speech(self, text: str) -> None:
        """
        实际触发语音输出。
        """
        if self.speech_engine is not None:
            self.speech_engine.speak(text)