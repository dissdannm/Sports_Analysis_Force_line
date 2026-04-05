# storage/path_provider.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StoragePathProvider(ABC):
    """
    存储路径提供器抽象基类。

    设计目标：
    1. 将“数据存到哪里”从“怎么写文件”中分离出来
    2. 为不同平台、不同部署方式预留统一接口
    3. 避免把路径策略写死在 SessionManager 或 Writer 中

    当前约定：
    - get_output_root() 返回会话数据的根目录
    """

    @abstractmethod
    def get_output_root(self) -> Path:
        """
        返回当前运行环境下的输出根目录。
        """
        raise NotImplementedError