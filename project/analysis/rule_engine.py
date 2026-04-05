# analysis/rule_engine.py

from __future__ import annotations

from models.alert import Alert
from models.enums import AlertLevel
from models.metrics import MotionMetrics
from models.motion_definition import MotionDefinition, RangeRule, SeverityThreshold


class RuleEngine:
    """
    动作规则引擎。

    设计定位：
    - 负责把动作级指标结果转换成统一告警
    - 只读取动作配置，不负责计算指标
    - 不负责语音播报，只负责输出 speak / speak_text 建议

    规则来源：
    - motion_definition.metric_rules
    - motion_definition.voice_prompts

    企业第一版设计原则：
    1. 优先简单、稳定、可解释
    2. 不做复杂推理，不引入隐式魔法
    3. 让业务同学能清楚知道 json 是如何生效的
    """

    def evaluate(
        self,
        motion_definition: MotionDefinition,
        motion_metrics: MotionMetrics,
    ) -> list[Alert]:
        """
        根据动作配置和当前指标结果生成告警列表。
        """
        alerts: list[Alert] = []

        for metric_id in motion_definition.enabled_metrics:
            if metric_id not in motion_metrics.selected:
                continue

            metric_value = motion_metrics.selected[metric_id]
            metric_rule = motion_definition.metric_rules.get(metric_id)
            voice_prompt_rule = motion_definition.voice_prompts.get(metric_id)

            if metric_rule is None or voice_prompt_rule is None:
                # 理论上 motion_registry 已经做过校验，
                # 这里仍保留防御式处理，增强稳定性
                continue

            if self._is_in_range(metric_value, metric_rule.normal_range):
                continue

            alert_level = self._resolve_alert_level(metric_value, metric_rule.severity_rules)
            if alert_level is None:
                # 不在 normal_range，但又未落入任何等级阈值时，
                # 当前版本不强行输出告警，避免误判
                continue

            message = self._resolve_message(metric_id, alert_level, voice_prompt_rule)
            speak_text = message

            alerts.append(
                Alert(
                    code=metric_id,
                    level=alert_level,
                    message=message,
                    speak=True,
                    speak_text=speak_text,
                    metric_id=metric_id,
                    motion_id=motion_definition.motion_id,
                )
            )

        return alerts

    def _resolve_alert_level(
        self,
        value: float,
        severity_rule,
    ) -> AlertLevel | None:
        """
        根据阈值规则判断告警等级。

        判断顺序：
        - severe
        - moderate
        - mild

        这样做的原因是：
        同一个数值如果错误地落入多个区间，优先采用更严重的等级。
        """
        if severity_rule.severe and self._is_in_threshold(value, severity_rule.severe):
            return AlertLevel.SEVERE

        if severity_rule.moderate and self._is_in_threshold(value, severity_rule.moderate):
            return AlertLevel.MODERATE

        if severity_rule.mild and self._is_in_threshold(value, severity_rule.mild):
            return AlertLevel.MILD

        return None

    @staticmethod
    def _is_in_range(value: float, rule: RangeRule) -> bool:
        """
        判断数值是否落在 normal_range 内。
        """
        if rule.min_value is not None and value < rule.min_value:
            return False

        if rule.max_value is not None and value > rule.max_value:
            return False

        return True

    @staticmethod
    def _is_in_threshold(value: float, threshold: SeverityThreshold) -> bool:
        """
        判断数值是否落在某个告警等级区间内。
        """
        if threshold.min_value is not None and value < threshold.min_value:
            return False

        if threshold.max_value is not None and value > threshold.max_value:
            return False

        return True

    @staticmethod
    def _resolve_message(metric_id: str, alert_level: AlertLevel, voice_prompt_rule) -> str:
        """
        根据 metric_id 和告警等级生成提示文本。

        说明：
        - 优先使用 motion json 中配置的语音提示文本
        - 若缺失，则回退到通用默认文案
        """
        if alert_level == AlertLevel.SEVERE and voice_prompt_rule.severe:
            return voice_prompt_rule.severe

        if alert_level == AlertLevel.MODERATE and voice_prompt_rule.moderate:
            return voice_prompt_rule.moderate

        if alert_level == AlertLevel.MILD and voice_prompt_rule.mild:
            return voice_prompt_rule.mild

        return f"{metric_id} 检测到异常，请调整动作"