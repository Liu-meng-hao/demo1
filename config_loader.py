import yaml
import os
from typing import Dict, Any, List, Optional


class ConfigLoader:
    """
    配置文件加载器，负责加载并解析 config.yaml 配置文件。
    """

    DEFAULT_CONFIG_PATH = "./config.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器。

        Args:
            config_path: 配置文件路径，默认为 ./config.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件。

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML 解析错误
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}"
            )

        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config = yaml.safe_load(file) or {}

        self._loaded = True
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持点号分隔的嵌套键。

        Args:
            key: 配置键，如 "paths.raw_logs"
            default: 默认值

        Returns:
            配置值或默认值
        """
        if not self._loaded:
            self.load()

        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_paths(self) -> Dict[str, str]:
        """
        获取路径配置。

        Returns:
            路径配置字典
        """
        default_paths = {
            "raw_logs": "./logs/raw/",
            "cleaned_logs": "./logs/cleaned/",
            "reports": "./reports/"
        }

        paths = self.get("paths", {})
        return {
            "raw_logs": paths.get("raw_logs", default_paths["raw_logs"]),
            "cleaned_logs": paths.get("cleaned_logs", default_paths["cleaned_logs"]),
            "reports": paths.get("reports", default_paths["reports"])
        }

    def get_timestamp_formats(self) -> List[str]:
        """
        获取支持的时间戳格式列表。

        Returns:
            时间戳格式列表
        """
        log_format = self.get("log_format", {})
        return log_format.get("timestamp_formats", [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S"
        ])

    def get_output_timestamp_format(self) -> str:
        """
        获取统一输出的时间戳格式。

        Returns:
            时间戳格式字符串
        """
        log_format = self.get("log_format", {})
        return log_format.get("output_timestamp_format", "%Y-%m-%d %H:%M:%S")

    def get_log_line_pattern(self) -> str:
        """
        获取日志行正则匹配模式。

        Returns:
            正则表达式字符串
        """
        log_format = self.get("log_format", {})
        return log_format.get("log_line_pattern", "")

    def get_keywords_config(self) -> Dict[str, Any]:
        """
        获取关键词统计配置。

        Returns:
            关键词配置字典
        """
        return self.get("keywords", {
            "load_from_file": True,
            "keywords_file": "./keywords.txt",
            "custom_keywords": []
        })

    def get_anomaly_markers(self) -> Dict[str, List[str]]:
        """
        获取异常标识配置。

        Returns:
            异常标识配置字典
        """
        default_markers = {
            "error_levels": ["ERROR", "FATAL", "CRITICAL"],
            "warning_levels": ["WARN", "WARNING"],
            "anomaly_keywords": [
                "exception", "failed", "failure", "error",
                "timeout", "refused", "denied", "unavailable"
            ]
        }

        markers = self.get("anomaly_markers", {})
        return {
            "error_levels": markers.get("error_levels", default_markers["error_levels"]),
            "warning_levels": markers.get("warning_levels", default_markers["warning_levels"]),
            "anomaly_keywords": markers.get("anomaly_keywords", default_markers["anomaly_keywords"])
        }

    def get_cleaning_rules(self) -> Dict[str, Any]:
        """
        获取清洗规则配置。

        Returns:
            清洗规则配置字典
        """
        default_rules = {
            "remove_empty_lines": True,
            "trim_whitespace": True,
            "remove_duplicates": False,
            "min_line_length": 10,
            "normalize_timestamp": True
        }

        rules = self.get("cleaning_rules", {})
        return {
            "remove_empty_lines": rules.get("remove_empty_lines", default_rules["remove_empty_lines"]),
            "trim_whitespace": rules.get("trim_whitespace", default_rules["trim_whitespace"]),
            "remove_duplicates": rules.get("remove_duplicates", default_rules["remove_duplicates"]),
            "min_line_length": rules.get("min_line_length", default_rules["min_line_length"]),
            "normalize_timestamp": rules.get("normalize_timestamp", default_rules["normalize_timestamp"])
        }

    def get_report_config(self) -> Dict[str, Any]:
        """
        获取报告生成配置。

        Returns:
            报告配置字典
        """
        default_report = {
            "title": "日志清洗与分析报告",
            "include_file_list": True,
            "include_cleaning_stats": True,
            "include_keyword_details": True,
            "include_anomaly_details": True,
            "max_anomaly_display": 100
        }

        report = self.get("report", {})
        return {
            "title": report.get("title", default_report["title"]),
            "include_file_list": report.get("include_file_list", default_report["include_file_list"]),
            "include_cleaning_stats": report.get("include_cleaning_stats", default_report["include_cleaning_stats"]),
            "include_keyword_details": report.get("include_keyword_details", default_report["include_keyword_details"]),
            "include_anomaly_details": report.get("include_anomaly_details", default_report["include_anomaly_details"]),
            "max_anomaly_display": report.get("max_anomaly_display", default_report["max_anomaly_display"])
        }

    @property
    def config(self) -> Dict[str, Any]:
        """
        获取完整配置字典。

        Returns:
            完整配置字典
        """
        if not self._loaded:
            self.load()
        return self._config
