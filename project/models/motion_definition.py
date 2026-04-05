# models/motion_definition.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from models.enums import MotionMetricType


@dataclass(slots=True)
class RangeRule:
    """
    数值范围规则。

    字段说明：
    - min_value:
        最小允许值；为 None 时表示不限制下界
    - max_value:
        最大允许值；为 None 时表示不限制上界

    使用场景：
    - normal_range
    - 其他需要表达区间的规则
    """
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass(slots=True)
class SeverityThreshold:
    """
    告警分级阈值区间。

    说明：
    - 用于描述 mild / moderate / severe 的判定区间
    - 这里只保存数据，不做比较逻辑
    - 真正比较逻辑由 rule_engine.py 负责
    """
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass(slots=True)
class SeverityRule:
    """
    单个指标的告警分级规则。
    """
    mild: Optional[SeverityThreshold] = None
    moderate: Optional[SeverityThreshold] = None
    severe: Optional[SeverityThreshold] = None


@dataclass(slots=True)
class VoicePromptRule:
    """
    单个指标的语音提示规则。

    说明：
    - 不同等级可以配置不同提示语
    - 未配置时允许为 None
    """
    mild: Optional[str] = None
    moderate: Optional[str] = None
    severe: Optional[str] = None


@dataclass(slots=True)
class MetricCatalogItem:
    """
    平台级基础指标定义。

    这个结构对应 motions/metric_catalog.json 中的单条指标记录。
    它描述的是“平台能算什么”，而不是“某个动作要怎么用这个指标”。

    字段说明：
    - metric_id:
        指标唯一 ID
    - display_name:
        指标显示名称
    - metric_type:
        指标类型，例如 angle / offset
    - owner:
        负责计算该指标的模块名，例如 angle_calculator / alignment_analyzer
    - points:
        该指标依赖的关键点名称列表
    - description:
        指标含义说明
    - recommended_motions:
        推荐使用该指标的动作列表
    - sign_convention:
        指标正负号 / 数值方向说明
    """
    metric_id: str
    display_name: str
    metric_type: MotionMetricType
    owner: str
    points: List[str] = field(default_factory=list)
    description: str = ""
    recommended_motions: List[str] = field(default_factory=list)
    sign_convention: str = ""


@dataclass(slots=True)
class MetricRuleConfig:
    """
    动作中某个启用指标的规则配置。

    这个结构描述的是：
    某个动作里，这个指标的正常范围和严重程度划分如何定义。
    """
    normal_range: RangeRule = field(default_factory=RangeRule)
    severity_rules: SeverityRule = field(default_factory=SeverityRule)


@dataclass(slots=True)
class TimingConfig:
    """
    动作时序配置。

    字段说明：
    - stable_frames:
        连续多少帧满足条件后才判定规则成立，用于防抖
    - voice_cooldown_ms:
        同一类语音提示的冷却时间
    - min_hold_ms:
        某些静态动作最少保持多久才开始分析
    """
    stable_frames: int = 1
    voice_cooldown_ms: int = 2000
    min_hold_ms: int = 0


@dataclass(slots=True)
class MotionDefinition:
    """
    单个动作配置定义。

    这个结构对应 motions/*.json 中的一个动作配置文件。

    设计思想：
    - 平台层先固定“支持哪些指标”
    - 动作层只选择启用哪些指标，并配置规则与提示语

    字段说明：
    - motion_id:
        动作唯一 ID，例如 push_up
    - motion_name:
        动作显示名称，例如 俯卧撑
    - version:
        配置版本号
    - description:
        动作说明
    - landmarks_required:
        该动作分析依赖的关键点
    - enabled_metrics:
        该动作启用的平台指标 ID 列表
    - metric_rules:
        各启用指标的阈值与分级规则
    - voice_prompts:
        各启用指标的语音提示规则
    - timing:
        时序与防抖配置
    - tags:
        动作标签
    - extras:
        预留扩展字段
    """
    motion_id: str
    motion_name: str
    version: str
    description: str

    landmarks_required: List[str] = field(default_factory=list)
    enabled_metrics: List[str] = field(default_factory=list)
    metric_rules: Dict[str, MetricRuleConfig] = field(default_factory=dict)
    voice_prompts: Dict[str, VoicePromptRule] = field(default_factory=dict)
    timing: TimingConfig = field(default_factory=TimingConfig)
    tags: List[str] = field(default_factory=list)
    extras: Dict[str, object] = field(default_factory=dict)