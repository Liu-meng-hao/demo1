import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class FileWriter:
    """
    文件写入器，负责输出清洗文件、生成Markdown分析报告。
    """

    CLEANED_FILE_PREFIX = "cleaned_"
    REPORT_FILE_PREFIX = "report_"
    REPORT_FILE_EXTENSION = ".md"
    CLEANED_FILE_EXTENSION = ".txt"

    def __init__(
        self,
        cleaned_logs_path: str = "./logs/cleaned/",
        reports_path: str = "./reports/"
    ):
        """
        初始化文件写入器。

        Args:
            cleaned_logs_path: 清洗后文件输出目录（相对路径）
            reports_path: 分析报告输出目录（相对路径）
        """
        self.cleaned_logs_path = cleaned_logs_path
        self.reports_path = reports_path

        self._ensure_directories()

    def _ensure_directories(self):
        """
        确保输出目录存在。
        """
        os.makedirs(self.cleaned_logs_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)

    def write_cleaned_file(self, file_name: str, lines: List[str]) -> str:
        """
        写入清洗后的日志文件。

        Args:
            file_name: 原始文件名
            lines: 清洗后的日志行列表

        Returns:
            输出文件路径
        """
        base_name = os.path.splitext(file_name)[0]
        output_name = f"{self.CLEANED_FILE_PREFIX}{base_name}{self.CLEANED_FILE_EXTENSION}"
        output_path = os.path.join(self.cleaned_logs_path, output_name)

        with open(output_path, "w", encoding="utf-8") as file:
            for line in lines:
                file.write(line + "\n")

        return output_path

    def write_cleaned_files(self, cleaned_contents: Dict[str, List[str]]) -> List[str]:
        """
        批量写入清洗后的日志文件。

        Args:
            cleaned_contents: 清洗后的文件内容字典，键为原始文件路径，值为行列表

        Returns:
            输出文件路径列表
        """
        output_paths = []
        for original_path, lines in cleaned_contents.items():
            file_name = os.path.basename(original_path)
            output_path = self.write_cleaned_file(file_name, lines)
            output_paths.append(output_path)
        return output_paths

    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        cleaning_stats: Dict[str, int],
        file_info_list: List[Dict[str, Any]],
        anomaly_logs: List[Dict[str, Any]],
        keyword_stats: Dict[str, int],
        report_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成Markdown分析报告。

        Args:
            analysis_result: 分析结果字典
            cleaning_stats: 清洗统计信息
            file_info_list: 文件信息列表
            anomaly_logs: 异常日志列表
            keyword_stats: 关键词统计字典
            report_config: 报告配置

        Returns:
            报告文件路径
        """
        report_config = report_config or {}
        title = report_config.get("title", "日志清洗与分析报告")
        include_file_list = report_config.get("include_file_list", True)
        include_cleaning_stats = report_config.get("include_cleaning_stats", True)
        include_keyword_details = report_config.get("include_keyword_details", True)
        include_anomaly_details = report_config.get("include_anomaly_details", True)
        max_anomaly_display = report_config.get("max_anomaly_display", 100)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"{self.REPORT_FILE_PREFIX}{timestamp}{self.REPORT_FILE_EXTENSION}"
        report_path = os.path.join(self.reports_path, report_name)

        lines = []
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        lines.append("## 执行概要")
        lines.append("")
        lines.append(f"- **处理文件数**: {len(file_info_list)}")
        lines.append(f"- **总日志行数**: {analysis_result.get('total_lines', 0)}")
        lines.append(f"- **异常日志数**: {analysis_result.get('anomaly_count', 0)}")
        lines.append(f"- **错误日志数**: {analysis_result.get('error_count', 0)}")
        lines.append(f"- **警告日志数**: {analysis_result.get('warning_count', 0)}")
        lines.append("")

        if include_cleaning_stats:
            lines.append("## 清洗统计")
            lines.append("")
            lines.append("| 统计项 | 数量 |")
            lines.append("|--------|------|")
            lines.append(f"| 原始行数 | {cleaning_stats.get('total_lines', 0)} |")
            lines.append(f"| 去除空行 | {cleaning_stats.get('removed_empty', 0)} |")
            lines.append(f"| 去除无效格式 | {cleaning_stats.get('removed_invalid', 0)} |")
            lines.append(f"| 去除短行 | {cleaning_stats.get('removed_short', 0)} |")
            lines.append(f"| 去除重复 | {cleaning_stats.get('removed_duplicates', 0)} |")
            lines.append(f"| 时间戳规范化 | {cleaning_stats.get('normalized_timestamp', 0)} |")
            lines.append(f"| 保留行数 | {cleaning_stats.get('kept_lines', 0)} |")
            lines.append("")

        if include_file_list and file_info_list:
            lines.append("## 处理文件清单")
            lines.append("")
            lines.append("| 文件名 | 大小(字节) | 行数 |")
            lines.append("|--------|------------|------|")
            for info in file_info_list:
                lines.append(
                    f"| {info.get('file_name', 'N/A')} | "
                    f"{info.get('size_bytes', 0)} | "
                    f"{info.get('line_count', 0)} |"
                )
            lines.append("")

        if include_keyword_details and keyword_stats:
            lines.append("## 关键词统计")
            lines.append("")
            sorted_keywords = sorted(
                keyword_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )
            lines.append("| 关键词 | 出现频次 |")
            lines.append("|--------|----------|")
            for keyword, count in sorted_keywords:
                lines.append(f"| {keyword} | {count} |")
            lines.append("")

        if include_anomaly_details and anomaly_logs:
            lines.append("## 异常日志清单")
            lines.append("")
            display_logs = anomaly_logs[:max_anomaly_display] if max_anomaly_display > 0 else anomaly_logs

            if max_anomaly_display > 0 and len(anomaly_logs) > max_anomaly_display:
                lines.append(f"_注：仅显示前 {max_anomaly_display} 条异常日志，共 {len(anomaly_logs)} 条_")
                lines.append("")

            lines.append("| 类型 | 来源文件 | 行号 | 内容 |")
            lines.append("|------|----------|------|------|")
            for log in display_logs:
                content = log.get('content', '')[:80]
                if len(log.get('content', '')) > 80:
                    content += "..."
                content = content.replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {log.get('anomaly_type', 'N/A')} | "
                    f"{os.path.basename(log.get('source_file', 'N/A'))} | "
                    f"{log.get('line_number', 0)} | "
                    f"{content} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*报告由日志清洗与统计分析工具自动生成*")

        with open(report_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        return report_path

    def write_anomaly_archive(
        self,
        anomaly_logs: List[Dict[str, Any]],
        archive_name: Optional[str] = None
    ) -> str:
        """
        将异常日志单独归档到文件。

        Args:
            anomaly_logs: 异常日志列表
            archive_name: 归档文件名（可选）

        Returns:
            归档文件路径
        """
        if archive_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"anomalies_{timestamp}.txt"

        archive_path = os.path.join(self.cleaned_logs_path, archive_name)

        with open(archive_path, "w", encoding="utf-8") as file:
            for log in anomaly_logs:
                file.write(f"[{log.get('anomaly_type', 'UNKNOWN')}] ")
                file.write(f"{os.path.basename(log.get('source_file', 'unknown'))}:")
                file.write(f"{log.get('line_number', 0)} - ")
                file.write(f"{log.get('content', '')}\n")

        return archive_path

    def get_report_files(self) -> List[str]:
        """
        获取已生成的报告文件列表。

        Returns:
            报告文件路径列表
        """
        if not os.path.exists(self.reports_path):
            return []

        reports = []
        for entry in os.listdir(self.reports_path):
            if entry.endswith(self.REPORT_FILE_EXTENSION):
                reports.append(os.path.join(self.reports_path, entry))

        return sorted(reports, reverse=True)

    def get_cleaned_files(self) -> List[str]:
        """
        获取已生成的清洗文件列表。

        Returns:
            清洗文件路径列表
        """
        if not os.path.exists(self.cleaned_logs_path):
            return []

        cleaned = []
        for entry in os.listdir(self.cleaned_logs_path):
            if entry.startswith(self.CLEANED_FILE_PREFIX):
                cleaned.append(os.path.join(self.cleaned_logs_path, entry))

        return sorted(cleaned)
