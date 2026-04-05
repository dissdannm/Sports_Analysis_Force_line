# output/speech_interface.py

from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechInterface(ABC):
    """
    语音输出接口抽象基类。

    设计目标：
    1. 统一不同语音实现的调用方式
    2. 让上层业务逻辑不依赖具体 TTS 库
    3. 为本地播报、前端播报、远程播报等模式预留扩展空间

    当前统一约定：
    - speak(text): 播报一段文本
    """

    @abstractmethod
    def speak(self, text: str) -> None:
        """
        播报指定文本。

        参数：
        - text:
            需要输出的语音文本
        """
        raise NotImplementedError