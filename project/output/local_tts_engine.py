# output/local_tts_engine.py

from __future__ import annotations

import threading

import pyttsx3

from output.speech_interface import SpeechInterface


class LocalTTSEngine(SpeechInterface):
    """
    本地 TTS 引擎。

    当前实现基于 pyttsx3，适用于：
    - 本地开发调试
    - Windows 电脑端测试
    - 无外网环境下的离线播报

    设计原则：
    1. 只负责“把文本播报出来”
    2. 不负责节流、优先级和重复抑制
    3. 语音调度逻辑统一由 SpeechManager 负责

    注意：
    - pyttsx3 在部分环境下是阻塞式调用
    - 为减少对主流程的影响，这里默认使用后台线程执行播报
    """

    def __init__(
        self,
        rate: int = 180,
        volume: float = 1.0,
        voice_id: str | None = None,
        use_background_thread: bool = True,
    ) -> None:
        """
        参数说明：
        - rate:
            语速，默认 180
        - volume:
            音量，范围通常为 0.0 ~ 1.0
        - voice_id:
            可选语音 ID，不传则使用系统默认语音
        - use_background_thread:
            是否使用后台线程播报，默认开启
        """
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.use_background_thread = use_background_thread

        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)

            if self.voice_id:
                self._engine.setProperty("voice", self.voice_id)
        except Exception as exc:
            raise RuntimeError(f"初始化本地 TTS 引擎失败: {exc}") from exc

        self._lock = threading.Lock()

    def speak(self, text: str) -> None:
        """
        播报指定文本。

        说明：
        - 空字符串直接忽略
        - 默认走后台线程，避免长播报阻塞主流程
        """
        normalized_text = text.strip()
        if not normalized_text:
            return

        if self.use_background_thread:
            thread = threading.Thread(
                target=self._speak_blocking,
                args=(normalized_text,),
                daemon=True,
            )
            thread.start()
        else:
            self._speak_blocking(normalized_text)

    def _speak_blocking(self, text: str) -> None:
        """
        阻塞式播报实现。

        说明：
        - pyttsx3 引擎不是天然线程安全的
        - 这里用锁保证同一时刻只有一个播报任务操作引擎
        """
        try:
            with self._lock:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as exc:
            raise RuntimeError(f"本地 TTS 播报失败: {exc}") from exc