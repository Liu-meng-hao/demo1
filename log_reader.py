import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class LogReader:
    """
    日志文件读取器，负责读取指定目录下的日志文件，实现文件遍历与内容加载。
    """

    SUPPORTED_EXTENSION = ".log"

    def __init__(self, raw_logs_path: str = "./logs/raw/"):
        """
        初始化日志读取器。

        Args:
            raw_logs_path: 原始日志文件目录路径（相对路径）
        """
        self.raw_logs_path = raw_logs_path
        self._log_files: List[str] = []
        self._loaded_contents: Dict[str, List[str]] = {}

    def discover_files(self) -> List[str]:
        """
        发现并返回指定目录下所有符合格式的日志文件路径列表。
        仅识别 .log 后缀的文本日志文件。

        Returns:
            日志文件路径列表（相对路径）
        """
        self._log_files = []

        if not os.path.exists(self.raw_logs_path):
            return self._log_files

        for entry in os.listdir(self.raw_logs_path):
            entry_path = os.path.join(self.raw_logs_path, entry)

            if os.path.isfile(entry_path) and entry.endswith(self.SUPPORTED_EXTENSION):
                self._log_files.append(entry_path)

        self._log_files.sort()
        return self._log_files

    def read_file(self, file_path: str) -> List[str]:
        """
        读取单个日志文件的内容。

        Args:
            file_path: 日志文件路径

        Returns:
            文件内容行列表

        Raises:
            FileNotFoundError: 文件不存在
            IOError: 文件读取错误
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"日志文件不存在: {file_path}")

        lines = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            for line in file:
                lines.append(line.rstrip("\n\r"))

        return lines

    def read_all_files(self) -> Dict[str, List[str]]:
        """
        读取所有发现的日志文件内容。

        Returns:
            字典，键为文件路径，值为文件内容行列表
        """
        if not self._log_files:
            self.discover_files()

        self._loaded_contents = {}

        for file_path in self._log_files:
            try:
                content = self.read_file(file_path)
                self._loaded_contents[file_path] = content
            except (FileNotFoundError, IOError) as e:
                self._loaded_contents[file_path] = []

        return self._loaded_contents

    def get_file_info(self, file_path: str) -> Dict[str, any]:
        """
        获取日志文件的元信息。

        Args:
            file_path: 日志文件路径

        Returns:
            文件信息字典，包含文件名、大小、行数等
        """
        if not os.path.exists(file_path):
            return {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "exists": False,
                "size_bytes": 0,
                "line_count": 0
            }

        stat = os.stat(file_path)
        lines = self.read_file(file_path)

        return {
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "exists": True,
            "size_bytes": stat.st_size,
            "line_count": len(lines)
        }

    def get_all_files_info(self) -> List[Dict[str, any]]:
        """
        获取所有日志文件的元信息列表。

        Returns:
            文件信息字典列表
        """
        if not self._log_files:
            self.discover_files()

        info_list = []
        for file_path in self._log_files:
            info_list.append(self.get_file_info(file_path))

        return info_list

    def get_total_stats(self) -> Dict[str, int]:
        """
        获取所有日志文件的总体统计信息。

        Returns:
            统计信息字典
        """
        if not self._loaded_contents:
            self.read_all_files()

        total_files = len(self._loaded_contents)
        total_lines = sum(len(lines) for lines in self._loaded_contents.values())
        total_size = sum(
            os.path.getsize(fp) if os.path.exists(fp) else 0
            for fp in self._loaded_contents.keys()
        )

        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_size_bytes": total_size
        }

    @property
    def log_files(self) -> List[str]:
        """
        获取已发现的日志文件路径列表。

        Returns:
            日志文件路径列表
        """
        if not self._log_files:
            self.discover_files()
        return self._log_files

    @property
    def loaded_contents(self) -> Dict[str, List[str]]:
        """
        获取已加载的文件内容字典。

        Returns:
            文件内容字典
        """
        if not self._loaded_contents:
            self.read_all_files()
        return self._loaded_contents
