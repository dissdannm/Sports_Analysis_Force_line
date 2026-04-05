# storage/json_writer.py

from __future__ import annotations

import json
from pathlib import Path


class JSONWriter:
    """
    JSON 文件写入器。

    设计定位：
    - 负责将结构化摘要数据写入 JSON
    - 常用于一次会话结束后的 summary 输出
    - 不承担业务统计逻辑，只做落盘
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    def write(self, data: dict) -> None:
        """
        写入 JSON 文件。
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, mode="w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)