# acquisition/local_camera_source.py

from __future__ import annotations

from typing import Any, Tuple

import cv2

from acquisition.frame_source import FrameSource


class LocalCameraSource(FrameSource):
    """
    本地摄像头输入源。

    适用场景：
    - Windows / macOS / Linux 本地开发调试
    - 电脑内置摄像头
    - USB 外接摄像头

    设计原则：
    1. 只负责打开、读取、关闭摄像头
    2. 不承担任何分析逻辑
    3. 不假设上层业务用途，只提供统一帧读取能力
    """

    def __init__(
        self,
        camera_index: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """
        参数说明：
        - camera_index:
            摄像头编号，通常 0 表示默认摄像头
        - width:
            可选图像宽度设置
        - height:
            可选图像高度设置
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """
        打开本地摄像头。
        """
        self._capture = cv2.VideoCapture(self.camera_index)

        if not self._capture.isOpened():
            raise RuntimeError(f"无法打开本地摄像头，camera_index={self.camera_index}")

        if self.width is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)

        if self.height is not None:
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> Tuple[bool, Any]:
        """
        读取单帧图像。

        返回：
        - success: 是否读取成功
        - frame: OpenCV BGR 图像；失败时通常为 None
        """
        if self._capture is None:
            raise RuntimeError("摄像头尚未打开，请先调用 open()")

        success, frame = self._capture.read()
        return success, frame

    def close(self) -> None:
        """
        关闭摄像头并释放资源。
        """
        if self._capture is not None:
            self._capture.release()
            self._capture = None