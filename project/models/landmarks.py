# models/landmarks.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class Landmark:
    """
    单个关键点。

    字段说明：
    - x, y:
        二维归一化坐标，通常范围在 0~1
    - z:
        深度坐标。当前主线仍是 2D 分析，但保留该字段，
        以便未来扩展 3D 增强模块
    - visibility:
        关键点可见性或置信参考值，不同识别器可能含义略有差异
    """
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.0


@dataclass(slots=True)
class PoseLandmarks:
    """
    一整组人体关键点。

    设计说明：
    - 使用字典按名称存储关键点
    - 上层业务按关键点名直接取值，不直接依赖第三方库对象
    - 未检测到的点允许缺失，以便分析层做鲁棒处理
    """
    landmarks: Dict[str, Landmark] = field(default_factory=dict)

    def get(self, name: str) -> Optional[Landmark]:
        """
        根据关键点名称获取 Landmark。

        不存在时返回 None。
        """
        return self.landmarks.get(name)

    def has(self, name: str) -> bool:
        """
        判断是否包含某个关键点。
        """
        return name in self.landmarks

    def has_all(self, names: list[str]) -> bool:
        """
        判断是否同时包含一组关键点。
        """
        return all(name in self.landmarks for name in names)