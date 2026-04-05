# core/motion_registry.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from models.enums import MotionMetricType
from models.motion_definition import (
    MetricCatalogItem,
    MetricRuleConfig,
    MotionDefinition,
    RangeRule,
    SeverityRule,
    SeverityThreshold,
    TimingConfig,
    VoicePromptRule,
)


class MotionRegistry:
    """
    动作配置注册表。

    设计目标：
    1. 加载平台级基础指标总表（metric_catalog.json）
    2. 加载具体动作配置（motions/*.json）
    3. 校验动作配置是否合法
    4. 为上层提供稳定的动作检索能力

    维护边界：
    - 程序员维护 metric_catalog.json：定义平台“能算什么”
    - 业务同学维护 motions/*.json：定义动作“启用什么、阈值多少、怎么提示”
    """

    def __init__(self, motions_dir: str | Path) -> None:
        self.motions_dir = Path(motions_dir)
        self.metric_catalog: Dict[str, MetricCatalogItem] = {}
        self.motions: Dict[str, MotionDefinition] = {}

    def load_all(self) -> None:
        """
        加载平台指标总表和全部动作配置。
        """
        if not self.motions_dir.exists():
            raise FileNotFoundError(f"motions 目录不存在: {self.motions_dir}")

        self.metric_catalog = self._load_metric_catalog()
        self.motions = self._load_motion_files()

    def get_motion(self, motion_id: str) -> MotionDefinition:
        """
        根据 motion_id 获取动作定义。
        """
        if motion_id not in self.motions:
            raise KeyError(f"未找到动作配置: {motion_id}")
        return self.motions[motion_id]

    def list_motion_ids(self) -> List[str]:
        """
        返回全部已注册动作 ID。
        """
        return sorted(self.motions.keys())

    def get_metric_catalog_item(self, metric_id: str) -> MetricCatalogItem:
        """
        根据 metric_id 获取平台级指标定义。
        """
        if metric_id not in self.metric_catalog:
            raise KeyError(f"未找到平台指标定义: {metric_id}")
        return self.metric_catalog[metric_id]

    def _load_metric_catalog(self) -> Dict[str, MetricCatalogItem]:
        """
        加载平台级基础指标总表。
        """
        catalog_path = self.motions_dir / "metric_catalog.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"未找到平台指标总表文件: {catalog_path}")

        with open(catalog_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        metrics_raw = raw_data.get("metrics", [])
        if not isinstance(metrics_raw, list):
            raise ValueError("metric_catalog.json 中的 metrics 必须是数组")

        catalog: Dict[str, MetricCatalogItem] = {}

        for item_raw in metrics_raw:
            metric_item = self._parse_metric_catalog_item(item_raw)

            if metric_item.metric_id in catalog:
                raise ValueError(f"平台指标总表中存在重复 metric_id: {metric_item.metric_id}")

            catalog[metric_item.metric_id] = metric_item

        return catalog

    def _load_motion_files(self) -> Dict[str, MotionDefinition]:
        """
        加载 motions 目录下全部动作配置文件。
        """
        motions: Dict[str, MotionDefinition] = {}

        for json_path in sorted(self.motions_dir.glob("*.json")):
            if json_path.name == "metric_catalog.json":
                continue

            motion = self._load_single_motion_file(json_path)

            if motion.motion_id in motions:
                raise ValueError(f"存在重复 motion_id: {motion.motion_id}")

            motions[motion.motion_id] = motion

        if not motions:
            raise ValueError("motions 目录中未找到任何动作配置文件")

        return motions

    def _load_single_motion_file(self, json_path: Path) -> MotionDefinition:
        """
        加载并解析单个动作配置文件。
        """
        with open(json_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        motion = self._parse_motion_definition(raw_data)
        self._validate_motion_definition(motion)

        return motion

    def _parse_metric_catalog_item(self, raw: dict) -> MetricCatalogItem:
        """
        解析平台级指标定义。
        """
        metric_type = MotionMetricType(raw["metric_type"])

        return MetricCatalogItem(
            metric_id=raw["metric_id"],
            display_name=raw.get("display_name", raw["metric_id"]),
            metric_type=metric_type,
            owner=raw["owner"],
            points=raw.get("points", []),
            description=raw.get("description", ""),
            recommended_motions=raw.get("recommended_motions", []),
            sign_convention=raw.get("sign_convention", ""),
        )

    def _parse_motion_definition(self, raw: dict) -> MotionDefinition:
        """
        解析单个动作配置。
        """
        metric_rules_raw = raw.get("metric_rules", {})
        voice_prompts_raw = raw.get("voice_prompts", {})
        timing_raw = raw.get("timing", {})

        metric_rules: Dict[str, MetricRuleConfig] = {}
        for metric_id, rule_raw in metric_rules_raw.items():
            metric_rules[metric_id] = MetricRuleConfig(
                normal_range=self._parse_range_rule(rule_raw.get("normal_range")),
                severity_rules=self._parse_severity_rule(rule_raw.get("severity_rules", {})),
            )

        voice_prompts: Dict[str, VoicePromptRule] = {}
        for metric_id, voice_raw in voice_prompts_raw.items():
            voice_prompts[metric_id] = VoicePromptRule(
                mild=voice_raw.get("mild"),
                moderate=voice_raw.get("moderate"),
                severe=voice_raw.get("severe"),
            )

        timing = TimingConfig(
            stable_frames=timing_raw.get("stable_frames", 1),
            voice_cooldown_ms=timing_raw.get("voice_cooldown_ms", 2000),
            min_hold_ms=timing_raw.get("min_hold_ms", 0),
        )

        return MotionDefinition(
            motion_id=raw["motion_id"],
            motion_name=raw["motion_name"],
            version=raw.get("version", "1.0.0"),
            description=raw.get("description", ""),
            landmarks_required=raw.get("landmarks_required", []),
            enabled_metrics=raw.get("enabled_metrics", []),
            metric_rules=metric_rules,
            voice_prompts=voice_prompts,
            timing=timing,
            tags=raw.get("tags", []),
            extras=raw.get("extras", {}),
        )

    def _validate_motion_definition(self, motion: MotionDefinition) -> None:
        """
        校验动作配置是否合法。
        """
        if not motion.enabled_metrics:
            raise ValueError(f"动作 {motion.motion_id} 未配置 enabled_metrics")

        for metric_id in motion.enabled_metrics:
            if metric_id not in self.metric_catalog:
                raise ValueError(
                    f"动作 {motion.motion_id} 启用了平台不存在的指标: {metric_id}"
                )

        for metric_id in motion.metric_rules.keys():
            if metric_id not in motion.enabled_metrics:
                raise ValueError(
                    f"动作 {motion.motion_id} 的 metric_rules 中包含未启用指标: {metric_id}"
                )

        for metric_id in motion.voice_prompts.keys():
            if metric_id not in motion.enabled_metrics:
                raise ValueError(
                    f"动作 {motion.motion_id} 的 voice_prompts 中包含未启用指标: {metric_id}"
                )

        for metric_id in motion.enabled_metrics:
            if metric_id not in motion.metric_rules:
                raise ValueError(
                    f"动作 {motion.motion_id} 的启用指标缺少规则配置: {metric_id}"
                )

            if metric_id not in motion.voice_prompts:
                raise ValueError(
                    f"动作 {motion.motion_id} 的启用指标缺少语音提示配置: {metric_id}"
                )

    @staticmethod
    def _parse_range_rule(raw: dict | None) -> RangeRule:
        """
        解析 normal_range 配置。
        """
        if raw is None:
            return RangeRule()

        return RangeRule(
            min_value=raw.get("min"),
            max_value=raw.get("max"),
        )

    @staticmethod
    def _parse_severity_rule(raw: dict) -> SeverityRule:
        """
        解析 severity_rules 配置。
        """
        return SeverityRule(
            mild=MotionRegistry._parse_severity_threshold(raw.get("mild")),
            moderate=MotionRegistry._parse_severity_threshold(raw.get("moderate")),
            severe=MotionRegistry._parse_severity_threshold(raw.get("severe")),
        )

    @staticmethod
    def _parse_severity_threshold(raw: list | None) -> SeverityThreshold | None:
        """
        解析单个等级阈值，格式要求为 [min, max]。
        """
        if raw is None:
            return None

        if not isinstance(raw, list) or len(raw) != 2:
            raise ValueError(f"非法 severity threshold 配置: {raw}")

        return SeverityThreshold(
            min_value=raw[0],
            max_value=raw[1],
        )