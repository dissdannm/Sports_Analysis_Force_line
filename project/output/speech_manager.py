# output/speech_manager.py

from __future__ import annotations

from dataclasses import dataclass, field

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
        触发播报的原始告警对象
    """
    should_speak: bool
    text: str = ""
    alert: Alert | None = None


@dataclass(slots=True)
class _SpeechState:
    """
    内部语音状态记录。

    字段说明：
    - last_spoken_timestamp_ms:
        最近一次播报该告警的时间
    - last_spoken_text:
        最近一次播报的文本
    """
    last_spoken_timestamp_ms: int = -1
    last_spoken_text: str = ""


class SpeechManager:
    """
    语音播报管理器。

    设计定位：
    - 负责决定“是否播报、播报哪条、何时播报”
    - 不负责具体 TTS 实现
    - 不负责分析和规则判断

    当前企业第一版策略：
    1. 只对 speak=True 的告警考虑播报
    2. 多条告警同时出现时，优先级为：
       severe > moderate > mild
    3. 同一 metric_id 的播报受冷却时间限制
    4. 同样文本在冷却时间内不重复播报
    """

    _ALERT_PRIORITY = {
        AlertLevel.SEVERE: 3,
        AlertLevel.MODERATE: 2,
        AlertLevel.MILD: 1,
    }

    def __init__(self, speech_engine: SpeechInterface | None = None) -> None:
        """
        参数说明：
        - speech_engine:
            具体语音实现。
            可以为 None，此时 SpeechManager 只做决策，不实际播报。
            这对服务端模式很有用，因为服务端可能只返回 speak_text 给前端。
        """
        self.speech_engine = speech_engine
        self._speech_state_by_code: dict[str, _SpeechState] = {}

    def handle_alerts(
        self,
        alerts: list[Alert],
        timestamp_ms: int,
        cooldown_ms: int,
    ) -> SpeechDecision:
        """
        根据当前告警列表决定是否播报，并在可播报时触发语音输出。

        参数：
        - alerts:
            当前帧的告警列表
        - timestamp_ms:
            当前时间戳，单位毫秒
        - cooldown_ms:
            播报冷却时间，通常来自 motion_definition.timing.voice_cooldown_ms

        返回：
        - SpeechDecision:
            当前是否播报，以及播报的文本和对应告警
        """
        candidate_alerts = [alert for alert in alerts if alert.speak]

        if not candidate_alerts:
            return SpeechDecision(should_speak=False)

        best_alert = self._select_highest_priority_alert(candidate_alerts)
        if best_alert is None:
            return SpeechDecision(should_speak=False)

        if not self._can_speak(best_alert, timestamp_ms, cooldown_ms):
            return SpeechDecision(should_speak=False)

        speak_text = best_alert.speak_text.strip() or best_alert.message.strip()
        if not speak_text:
            return SpeechDecision(should_speak=False)

        self._record_speech(best_alert, speak_text, timestamp_ms)

        #print(f"[SpeechManager] should speak: {speak_text}")

        if self.speech_engine is not None:
            self.speech_engine.speak(speak_text)

        return SpeechDecision(
            should_speak=True,
            text=speak_text,
            alert=best_alert,
        )

    def _select_highest_priority_alert(self, alerts: list[Alert]) -> Alert | None:
        """
        从候选告警中选出优先级最高的一条。

        当前规则：
        1. 告警等级越高，优先级越高
        2. 若等级相同，保留列表中最先出现的一条
        """
        if not alerts:
            return None

        return max(
            alerts,
            key=lambda alert: self._ALERT_PRIORITY.get(alert.level, 0),
        )

    def _can_speak(self, alert: Alert, timestamp_ms: int, cooldown_ms: int) -> bool:
        """
        判断当前告警是否允许播报。

        当前规则：
        - 同一 code 在冷却时间内不重复播报
        - 相同文本在冷却时间内不重复播报
        """
        state = self._speech_state_by_code.get(alert.code)
        if state is None:
            return True

        elapsed_ms = timestamp_ms - state.last_spoken_timestamp_ms
        if elapsed_ms < cooldown_ms:
            current_text = alert.speak_text.strip() or alert.message.strip()
            if current_text == state.last_spoken_text:
                return False
            return False

        return True

    def _record_speech(self, alert: Alert, text: str, timestamp_ms: int) -> None:
        """
        记录一次播报状态。
        """
        self._speech_state_by_code[alert.code] = _SpeechState(
            last_spoken_timestamp_ms=timestamp_ms,
            last_spoken_text=text,
        )