# acquisition/frame_source.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Tuple


class FrameSource(ABC):
    """
    视频帧输入源抽象基类。

    设计目标：
    1. 统一不同类型的视频输入源
    2. 让上层 pipeline 不关心帧来自哪里
    3. 为本地摄像头、视频文件、前端上传帧等场景预留统一入口

    统一约定：
    - open()：打开输入源
    - read()：读取单帧，返回 (success, frame)
    - close()：关闭输入源并释放资源
    """

    @abstractmethod
    def open(self) -> None:
        """
        打开输入源。
        """
        raise NotImplementedError

    @abstractmethod
    def read(self) -> Tuple[bool, Any]:
        """
        读取一帧数据。

        返回：
        - success: 是否读取成功
        - frame: 读取到的帧对象；失败时通常为 None
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        关闭输入源并释放相关资源。
        """
        raise NotImplementedError