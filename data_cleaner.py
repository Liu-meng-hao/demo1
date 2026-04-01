import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any


class DataCleaner:
    """
    数据清洗器，负责日志数据清洗、格式校验、无效数据过滤。
    """

    def __init__(
        self,
        timestamp_formats: Optional[List[str]] = None,
        output_timestamp_format: str = "%Y-%m-%d %H:%M:%S",
        log_line_pattern: str = "",
        cleaning_rules: Optional[Dict[str, Any]] = None
    ):
        """
        初始化数据清洗器。

        Args:
            timestamp_formats: 支持的时间戳格式列表
            output_timestamp_format: 统一输出的时间戳格式
            log_line_pattern: 日志行正则匹配模式
            cleaning_rules: 清洗规则配置
        """
        self.timestamp_formats = timestamp_formats or [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S"
        ]
        self.output_timestamp_format = output_timestamp_format
        self.log_line_pattern = log_line_pattern
        self.cleaning_rules = cleaning_rules or {
            "remove_empty_lines": True,
            "trim_whitespace": True,
            "remove_duplicates": False,
            "min_line_length": 10,
            "normalize_timestamp": True
        }

        self._compiled_pattern = None
        if self.log_line_pattern:
            try:
                self._compiled_pattern = re.compile(self.log_line_pattern, re.IGNORECASE)
            except re.error:
                self._compiled_pattern = None

        self._stats = {
            "total_lines": 0,
            "removed_empty": 0,
            "removed_invalid": 0,
            "removed_short": 0,
            "removed_duplicates": 0,
            "normalized_timestamp": 0,
            "kept_lines": 0
        }

    def clean(self, lines: List[str]) -> List[str]:
        """
        清洗日志数据。

        Args:
            lines: 原始日志行列表

        Returns:
            清洗后的日志行列表
        """
        self._reset_stats()
        self._stats["total_lines"] = len(lines)

        cleaned = lines

        if self.cleaning_rules.get("remove_empty_lines", True):
            cleaned = self._remove_empty_lines(cleaned)

        if self.cleaning_rules.get("trim_whitespace", True):
            cleaned = self._trim_whitespace(cleaned)

        if self.cleaning_rules.get("min_line_length", 10) > 0:
            cleaned = self._filter_by_length(cleaned)

        if self._compiled_pattern:
            cleaned = self._filter_by_pattern(cleaned)

        if self.cleaning_rules.get("normalize_timestamp", True):
            cleaned = self._normalize_timestamps(cleaned)

        if self.cleaning_rules.get("remove_duplicates", False):
            cleaned = self._remove_duplicates(cleaned)

        self._stats["kept_lines"] = len(cleaned)
        return cleaned

    def _remove_empty_lines(self, lines: List[str]) -> List[str]:
        """
        去除空行。

        Args:
            lines: 日志行列表

        Returns:
            去除空行后的列表
        """
        result = []
        for line in lines:
            if line.strip():
                result.append(line)
            else:
                self._stats["removed_empty"] += 1
        return result

    def _trim_whitespace(self, lines: List[str]) -> List[str]:
        """
        去除每行首尾空白字符。

        Args:
            lines: 日志行列表

        Returns:
            处理后的列表
        """
        return [line.strip() for line in lines]

    def _filter_by_length(self, lines: List[str]) -> List[str]:
        """
        按最小长度过滤行。

        Args:
            lines: 日志行列表

        Returns:
            过滤后的列表
        """
        min_length = self.cleaning_rules.get("min_line_length", 10)
        result = []
        for line in lines:
            if len(line) >= min_length:
                result.append(line)
            else:
                self._stats["removed_short"] += 1
        return result

    def _filter_by_pattern(self, lines: List[str]) -> List[str]:
        """
        按正则模式过滤无效格式日志。

        Args:
            lines: 日志行列表

        Returns:
            过滤后的列表
        """
        if not self._compiled_pattern:
            return lines

        result = []
        for line in lines:
            if self._compiled_pattern.match(line):
                result.append(line)
            else:
                self._stats["removed_invalid"] += 1
        return result

    def _normalize_timestamps(self, lines: List[str]) -> List[str]:
        """
        统一时间戳格式。

        Args:
            lines: 日志行列表

        Returns:
            处理后的列表
        """
        result = []
        for line in lines:
            normalized_line = self._try_normalize_timestamp(line)
            if normalized_line != line:
                self._stats["normalized_timestamp"] += 1
            result.append(normalized_line)
        return result

    def _try_normalize_timestamp(self, line: str) -> str:
        """
        尝试将行中的时间戳统一格式。

        Args:
            line: 日志行

        Returns:
            处理后的日志行
        """
        timestamp_pattern = r"(\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2})"
        match = re.search(timestamp_pattern, line)

        if not match:
            return line

        timestamp_str = match.group(1)
        parsed_dt = self._parse_timestamp(timestamp_str)

        if parsed_dt:
            normalized = parsed_dt.strftime(self.output_timestamp_format)
            return line[:match.start()] + normalized + line[match.end():]

        return line

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        尝试用多种格式解析时间戳。

        Args:
            timestamp_str: 时间戳字符串

        Returns:
            datetime对象或None
        """
        for fmt in self.timestamp_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        return None

    def _remove_duplicates(self, lines: List[str]) -> List[str]:
        """
        去除重复行。

        Args:
            lines: 日志行列表

        Returns:
            去重后的列表
        """
        seen = set()
        result = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                result.append(line)
            else:
                self._stats["removed_duplicates"] += 1
        return result

    def validate_format(self, line: str) -> bool:
        """
        验证单行日志格式是否有效。

        Args:
            line: 日志行

        Returns:
            是否有效
        """
        if not line or len(line.strip()) < self.cleaning_rules.get("min_line_length", 10):
            return False

        if self._compiled_pattern:
            return bool(self._compiled_pattern.match(line))

        return True

    def extract_timestamp(self, line: str) -> Optional[str]:
        """
        从日志行中提取时间戳。

        Args:
            line: 日志行

        Returns:
            时间戳字符串或None
        """
        timestamp_pattern = r"(\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2})"
        match = re.search(timestamp_pattern, line)

        if match:
            return match.group(1)
        return None

    def extract_log_level(self, line: str) -> Optional[str]:
        """
        从日志行中提取日志级别。

        Args:
            line: 日志行

        Returns:
            日志级别字符串或None
        """
        level_pattern = r"\b(ERROR|WARN|WARNING|INFO|DEBUG|TRACE|FATAL|CRITICAL)\b"
        match = re.search(level_pattern, line, re.IGNORECASE)

        if match:
            return match.group(1).upper()
        return None

    def _reset_stats(self):
        """
        重置统计信息。
        """
        self._stats = {
            "total_lines": 0,
            "removed_empty": 0,
            "removed_invalid": 0,
            "removed_short": 0,
            "removed_duplicates": 0,
            "normalized_timestamp": 0,
            "kept_lines": 0
        }

    def get_stats(self) -> Dict[str, int]:
        """
        获取清洗统计信息。

        Returns:
            统计信息字典
        """
        return self._stats.copy()

    def clean_multiple_files(self, file_contents: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        清洗多个文件的内容。

        Args:
            file_contents: 文件内容字典，键为文件路径，值为行列表

        Returns:
            清洗后的文件内容字典
        """
        cleaned_contents = {}
        for file_path, lines in file_contents.items():
            cleaned_contents[file_path] = self.clean(lines)
        return cleaned_contents
