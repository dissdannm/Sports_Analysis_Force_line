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

    当前企业第一版策略：
    1. 正常 -> 异常：播报一次异常提示
    2. 异常持续：不重复播报
    3. 异常 -> 正常：播报一次恢复提示
    4. 正常持续：不重复播报

    设计说明：
    - 这更符合真实运动场景
    - 用户不需要频繁看手机
    - 语音只在关键状态变化时提醒
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
        """
        参数说明：
        - speech_engine:
            具体语音实现，可为 None
        - recovery_text:
            恢复正常时的统一提示语
        """
        self.speech_engine = speech_engine
        self.recovery_text = recovery_text

        self._had_active_alert_last_frame = False

    def handle_alerts(
        self,
        alerts: list[Alert],
        timestamp_ms: int,
        cooldown_ms: int,
    ) -> SpeechDecision:
        """
        根据当前告警列表决定是否播报。

        说明：
        - 当前版本不依赖 timestamp_ms 和 cooldown_ms 做重复抑制，
          因为我们已经改为“只在状态切换时播报”
        - 保留这两个参数是为了兼容现有主流程接口
        """
        candidate_alerts = [alert for alert in alerts if alert.speak]
        has_active_alert = len(candidate_alerts) > 0

        # 情况 1：正常 -> 异常，播报一次异常
        if has_active_alert and not self._had_active_alert_last_frame:
            best_alert = self._select_highest_priority_alert(candidate_alerts)
            if best_alert is None:
                return SpeechDecision(should_speak=False)

            speak_text = best_alert.speak_text.strip() or best_alert.message.strip()
            if not speak_text:
                return SpeechDecision(should_speak=False)

            self._had_active_alert_last_frame = True
            self._emit_speech(speak_text)

            return SpeechDecision(
                should_speak=True,
                text=speak_text,
                alert=best_alert,
            )

        # 情况 2：异常 -> 正常，播报一次恢复
        if not has_active_alert and self._had_active_alert_last_frame:
            self._had_active_alert_last_frame = False
            self._emit_speech(self.recovery_text)

            return SpeechDecision(
                should_speak=True,
                text=self.recovery_text,
                alert=None,
            )

        # 情况 3：异常持续 或 正常持续，不播
        self._had_active_alert_last_frame = has_active_alert
        return SpeechDecision(should_speak=False)

    def _select_highest_priority_alert(self, alerts: list[Alert]) -> Alert | None:
        """
        从候选告警中选出优先级最高的一条。
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