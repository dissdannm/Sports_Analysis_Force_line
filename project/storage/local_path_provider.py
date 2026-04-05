# storage/local_path_provider.py

from __future__ import annotations

from pathlib import Path

from storage.path_provider import StoragePathProvider


class LocalPathProvider(StoragePathProvider):
    """
    本地桌面环境的存储路径提供器。

    默认策略：
    - 若未显式指定 base_dir，则使用用户 Documents 目录下的 SportsAnalysis
    - 若显式指定 base_dir，则优先使用传入目录

    设计说明：
    - 当前适用于 Windows 本地开发与测试
    - 后续如需支持其他平台，可新增新的 PathProvider 实现
    """

    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            self.base_dir = Path.home() / "Documents" / "SportsAnalysis"
        else:
            self.base_dir = Path(base_dir)

    def get_output_root(self) -> Path:
        """
        返回本地输出根目录，并确保目录存在。
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir