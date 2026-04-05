# perception/pose_estimator.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from models.landmarks import PoseLandmarks


class PoseEstimator(ABC):
    """
    姿态识别器抽象基类。

    设计目标：
    1. 统一不同姿态识别模型的调用方式
    2. 让上层 pipeline 不依赖具体实现
    3. 为未来替换 MediaPipe 或加入其他识别器预留接口

    当前统一约定：
    - 输入：frame + timestamp_ms
    - 输出：PoseLandmarks 或 None
    """

    @abstractmethod
    def process(self, frame, timestamp_ms: int) -> Optional[PoseLandmarks]:
        """
        处理单帧图像并输出人体关键点。

        参数：
        - frame:
            输入图像，通常为 OpenCV BGR 帧
        - timestamp_ms:
            当前帧的毫秒时间戳

        返回：
        - PoseLandmarks:
            检测到人体时返回关键点集合
        - None:
            未检测到人体时返回 None
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        释放识别器资源。
        """
        raise NotImplementedError