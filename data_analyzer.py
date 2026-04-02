import re
import os
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter


class DataAnalyzer:
    """
    数据分析器，负责关键词统计、异常日志筛选、数据计算。
    """

    def __init__(
        self,
        keywords: Optional[List[str]] = None,
        anomaly_markers: Optional[Dict[str, List[str]]] = None,
        keywords_file: Optional[str] = None
    ):
        """
        初始化数据分析器。

        Args:
            keywords: 关键词列表
            anomaly_markers: 异常标识配置
            keywords_file: 关键词基准文件路径
        """
        self.keywords = set()
        if keywords:
            self.keywords.update(k.lower() for k in keywords)

        if keywords_file and os.path.exists(keywords_file):
            self._load_keywords_from_file(keywords_file)

        self.anomaly_markers = anomaly_markers or {
            "error_levels": ["ERROR", "FATAL", "CRITICAL"],
            "warning_levels": ["WARN", "WARNING"],
            "anomaly_keywords": [
                "exception", "failed", "failure", "error",
                "timeout", "refused", "denied", "unavailable"
            ]
        }

        self._keyword_stats: Dict[str, int] = {}
        self._anomaly_logs: List[Dict[str, Any]] = []
        self._error_logs: List[Dict[str, Any]] = []
        self._warning_logs: List[Dict[str, Any]] = []

    def _load_keywords_from_file(self, file_path: str):
        """
        从文件加载关键词（只读）。

        Args:
            file_path: 关键词文件路径
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.keywords.add(line.lower())
        except (IOError, OSError):
            pass

    def analyze(self, lines: List[str], source_file: str = "") -> Dict[str, Any]:
        """
        分析日志数据。

        Args:
            lines: 清洗后的日志行列表
            source_file: 来源文件路径

        Returns:
            分析结果字典
        """
        self._reset_stats()

        self._analyze_keywords(lines)
        self._identify_anomalies(lines, source_file)

        return {
            "keyword_stats": self._keyword_stats.copy(),
            "anomaly_count": len(self._anomaly_logs),
            "error_count": len(self._error_logs),
            "warning_count": len(self._warning_logs),
            "total_lines": len(lines)
        }

    def _analyze_keywords(self, lines: List[str]):
        """
        统计关键词出现频次。

        Args:
            lines: 日志行列表
        """
        keyword_counts = Counter()

        for line in lines:
            line_lower = line.lower()
            for keyword in self.keywords:
                count = len(re.findall(r"\b" + re.escape(keyword) + r"\b", line_lower))
                if count > 0:
                    keyword_counts[keyword] += count

        self._keyword_stats = dict(keyword_counts)

    def _identify_anomalies(self, lines: List[str], source_file: str = ""):
        """
        识别异常日志。

        Args:
            lines: 日志行列表
            source_file: 来源文件路径
        """
        error_levels = set(lvl.upper() for lvl in self.anomaly_markers.get("error_levels", []))
        warning_levels = set(lvl.upper() for lvl in self.anomaly_markers.get("warning_levels", []))
        anomaly_keywords = set(kw.lower() for kw in self.anomaly_markers.get("anomaly_keywords", []))

        for line_num, line in enumerate(lines, 1):
            is_anomaly = False
            anomaly_type = None
            log_level = self._extract_log_level(line)

            if log_level in error_levels:
                is_anomaly = True
                anomaly_type = "ERROR"
            elif log_level in warning_levels:
                is_anomaly = True
                anomaly_type = "WARNING"
            else:
                line_lower = line.lower()
                for keyword in anomaly_keywords:
                    if keyword in line_lower:
                        is_anomaly = True
                        anomaly_type = "ANOMALY"
                        break

            if is_anomaly:
                anomaly_entry = {
                    "line_number": line_num,
                    "content": line,
                    "source_file": source_file,
                    "anomaly_type": anomaly_type,
                    "log_level": log_level
                }
                self._anomaly_logs.append(anomaly_entry)

                if anomaly_type == "ERROR":
                    self._error_logs.append(anomaly_entry)
                elif anomaly_type == "WARNING":
                    self._warning_logs.append(anomaly_entry)

    def _extract_log_level(self, line: str) -> Optional[str]:
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
        self._keyword_stats = {}
        self._anomaly_logs = []
        self._error_logs = []
        self._warning_logs = []

    def get_keyword_stats(self) -> Dict[str, int]:
        """
        获取关键词统计结果。

        Returns:
            关键词统计字典
        """
        return self._keyword_stats.copy()

    def get_sorted_keywords(self, reverse: bool = True) -> List[Tuple[str, int]]:
        """
        获取按频次排序的关键词列表。

        Args:
            reverse: 是否降序排列

        Returns:
            (关键词, 频次) 元组列表
        """
        return sorted(self._keyword_stats.items(), key=lambda x: x[1], reverse=reverse)

    def get_anomaly_logs(self) -> List[Dict[str, Any]]:
        """
        获取所有异常日志。

        Returns:
            异常日志列表
        """
        return self._anomaly_logs.copy()

    def get_error_logs(self) -> List[Dict[str, Any]]:
        """
        获取错误级别日志。

        Returns:
            错误日志列表
        """
        return self._error_logs.copy()

    def get_warning_logs(self) -> List[Dict[str, Any]]:
        """
        获取警告级别日志。

        Returns:
            警告日志列表
        """
        return self._warning_logs.copy()

    def get_top_keywords(self, n: int = 10) -> List[Tuple[str, int]]:
        """
        获取出现频次最高的N个关键词。

        Args:
            n: 返回数量

        Returns:
            (关键词, 频次) 元组列表
        """
        sorted_keywords = self.get_sorted_keywords(reverse=True)
        return sorted_keywords[:n]

    def analyze_multiple_files(self, file_contents: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        分析多个文件的内容。

        Args:
            file_contents: 文件内容字典，键为文件路径，值为行列表

        Returns:
            汇总分析结果
        """
        all_lines = []
        file_stats = {}

        for file_path, lines in file_contents.items():
            file_result = self.analyze(lines, file_path)
            file_stats[file_path] = file_result
            all_lines.extend(lines)

        overall_result = self.analyze(all_lines, "ALL_FILES")

        return {
            "overall": overall_result,
            "by_file": file_stats,
            "total_files": len(file_contents),
            "total_lines": len(all_lines)
        }

    def get_anomaly_summary(self) -> Dict[str, Any]:
        """
        获取异常日志汇总信息。

        Returns:
            异常汇总字典
        """
        error_types = Counter()
        for log in self._anomaly_logs:
            error_types[log["anomaly_type"]] += 1

        files_with_anomalies = set()
        for log in self._anomaly_logs:
            if log["source_file"]:
                files_with_anomalies.add(log["source_file"])

        return {
            "total_anomalies": len(self._anomaly_logs),
            "error_count": len(self._error_logs),
            "warning_count": len(self._warning_logs),
            "anomaly_type_distribution": dict(error_types),
            "files_affected": len(files_with_anomalies),
            "affected_file_list": list(files_with_anomalies)
        }
