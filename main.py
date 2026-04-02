import sys
from typing import Optional

from config_loader import ConfigLoader
from log_reader import LogReader
from data_cleaner import DataCleaner
from data_analyzer import DataAnalyzer
from file_writer import FileWriter


class LogProcessor:
    """
    日志处理器，程序主入口，负责调度所有模块、管理执行流程。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化日志处理器。

        Args:
            config_path: 配置文件路径，默认为 ./config.yaml
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load()

        paths = self.config_loader.get_paths()
        self.raw_logs_path = paths["raw_logs"]
        self.cleaned_logs_path = paths["cleaned_logs"]
        self.reports_path = paths["reports"]

        self.log_reader: Optional[LogReader] = None
        self.data_cleaner: Optional[DataCleaner] = None
        self.data_analyzer: Optional[DataAnalyzer] = None
        self.file_writer: Optional[FileWriter] = None

        self._cleaning_stats: dict = {}
        self._analysis_result: dict = {}
        self._file_info_list: list = []

    def _initialize_components(self):
        """
        初始化各功能组件。
        """
        self.log_reader = LogReader(self.raw_logs_path)

        cleaning_rules = self.config_loader.get_cleaning_rules()
        self.data_cleaner = DataCleaner(
            timestamp_formats=self.config_loader.get_timestamp_formats(),
            output_timestamp_format=self.config_loader.get_output_timestamp_format(),
            log_line_pattern=self.config_loader.get_log_line_pattern(),
            cleaning_rules=cleaning_rules
        )

        keywords_config = self.config_loader.get_keywords_config()
        keywords = keywords_config.get("custom_keywords", [])
        keywords_file = keywords_config.get("keywords_file", "./keywords.txt")

        self.data_analyzer = DataAnalyzer(
            keywords=keywords,
            anomaly_markers=self.config_loader.get_anomaly_markers(),
            keywords_file=keywords_file if keywords_config.get("load_from_file", True) else None
        )

        self.file_writer = FileWriter(
            cleaned_logs_path=self.cleaned_logs_path,
            reports_path=self.reports_path
        )

    def run(self) -> bool:
        """
        执行完整的日志处理流程。

        Returns:
            是否成功完成
        """
        try:
            print("=" * 60)
            print("日志清洗与统计分析工具")
            print("=" * 60)

            self._initialize_components()
            print("\n[1/5] 组件初始化完成")

            log_files = self.log_reader.discover_files()
            if not log_files:
                print(f"\n[!] 未在 {self.raw_logs_path} 目录下发现 .log 文件")
                return False

            print(f"\n[2/5] 发现 {len(log_files)} 个日志文件:")
            for file_path in log_files:
                print(f"    - {file_path}")

            self._file_info_list = self.log_reader.get_all_files_info()
            raw_contents = self.log_reader.read_all_files()

            print(f"\n[3/5] 开始数据清洗...")
            cleaned_contents = {}
            total_cleaning_stats = {
                "total_lines": 0,
                "removed_empty": 0,
                "removed_invalid": 0,
                "removed_short": 0,
                "removed_duplicates": 0,
                "normalized_timestamp": 0,
                "kept_lines": 0
            }

            for file_path, lines in raw_contents.items():
                cleaned_lines = self.data_cleaner.clean(lines)
                cleaned_contents[file_path] = cleaned_lines

                stats = self.data_cleaner.get_stats()
                for key in total_cleaning_stats:
                    total_cleaning_stats[key] += stats.get(key, 0)

                print(f"    ✓ {file_path}: {stats['total_lines']} 行 -> {stats['kept_lines']} 行")

            self._cleaning_stats = total_cleaning_stats

            cleaned_output_paths = self.file_writer.write_cleaned_files(cleaned_contents)
            print(f"\n    已生成 {len(cleaned_output_paths)} 个清洗文件到 {self.cleaned_logs_path}")

            print(f"\n[4/5] 开始数据分析...")
            all_lines = []
            for lines in cleaned_contents.values():
                all_lines.extend(lines)

            self._analysis_result = self.data_analyzer.analyze(all_lines, "ALL_FILES")

            keyword_stats = self.data_analyzer.get_keyword_stats()
            print(f"    ✓ 关键词统计: 发现 {len(keyword_stats)} 个关键词")

            anomaly_logs = self.data_analyzer.get_anomaly_logs()
            print(f"    ✓ 异常检测: {len(anomaly_logs)} 条异常日志")
            print(f"      - 错误: {self._analysis_result.get('error_count', 0)}")
            print(f"      - 警告: {self._analysis_result.get('warning_count', 0)}")

            if anomaly_logs:
                anomaly_archive_path = self.file_writer.write_anomaly_archive(anomaly_logs)
                print(f"    ✓ 异常日志已归档: {anomaly_archive_path}")

            print(f"\n[5/5] 生成分析报告...")
            report_path = self.file_writer.generate_report(
                analysis_result=self._analysis_result,
                cleaning_stats=self._cleaning_stats,
                file_info_list=self._file_info_list,
                anomaly_logs=anomaly_logs,
                keyword_stats=keyword_stats,
                report_config=self.config_loader.get_report_config()
            )
            print(f"    ✓ 报告已生成: {report_path}")

            print("\n" + "=" * 60)
            print("处理完成!")
            print("=" * 60)
            print(f"清洗文件目录: {self.cleaned_logs_path}")
            print(f"分析报告目录: {self.reports_path}")
            print("=" * 60)

            return True

        except FileNotFoundError as e:
            print(f"\n[!] 文件错误: {e}")
            return False
        except Exception as e:
            print(f"\n[!] 处理过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_summary(self) -> dict:
        """
        获取处理摘要信息。

        Returns:
            摘要信息字典
        """
        return {
            "files_processed": len(self._file_info_list),
            "cleaning_stats": self._cleaning_stats,
            "analysis_result": self._analysis_result
        }


def main():
    """
    程序入口函数。
    """
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    processor = LogProcessor(config_path)
    success = processor.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
