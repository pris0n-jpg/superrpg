"""
测试结果聚合器

负责收集、聚合和分析各种测试结果，包括：
- 单元测试结果
- 集成测试结果
- 端到端测试结果
- 性能测试结果
- 覆盖率数据
- 错误分析
"""

import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import re


@dataclass
class TestCaseResult:
    """测试用例结果"""
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    class_name: Optional[str] = None
    module_name: Optional[str] = None
    markers: List[str] = field(default_factory=list)


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    name: str
    test_cases: List[TestCaseResult]
    duration: float
    setup_time: float = 0.0
    teardown_time: float = 0.0
    status: str = "passed"  # passed, failed, error
    errors: List[str] = field(default_factory=list)


@dataclass
class CoverageData:
    """覆盖率数据"""
    total_lines: int
    covered_lines: int
    missed_lines: int
    coverage_percentage: float
    file_coverage: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    baseline: Optional[float] = None
    threshold: Optional[float] = None
    status: str = "unknown"  # good, warning, critical


@dataclass
class TestReport:
    """测试报告"""
    timestamp: datetime
    test_environment: Dict[str, str]
    test_suites: List[TestSuiteResult]
    coverage: Optional[CoverageData] = None
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TestResultAggregator:
    """测试结果聚合器"""
    
    def __init__(self, output_dir: str = "test_reports"):
        """
        初始化测试结果聚合器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_reports: List[TestReport] = []
        self.current_report: Optional[TestReport] = None
    
    def create_new_report(self, test_environment: Dict[str, str]) -> TestReport:
        """
        创建新的测试报告
        
        Args:
            test_environment: 测试环境信息
            
        Returns:
            新创建的测试报告
        """
        self.current_report = TestReport(
            timestamp=datetime.now(),
            test_environment=test_environment,
            test_suites=[]
        )
        
        return self.current_report
    
    def add_test_suite_result(self, suite_result: TestSuiteResult) -> None:
        """
        添加测试套件结果
        
        Args:
            suite_result: 测试套件结果
        """
        if self.current_report:
            self.current_report.test_suites.append(suite_result)
    
    def add_coverage_data(self, coverage_data: CoverageData) -> None:
        """
        添加覆盖率数据
        
        Args:
            coverage_data: 覆盖率数据
        """
        if self.current_report:
            self.current_report.coverage = coverage_data
    
    def add_performance_metric(self, metric: PerformanceMetric) -> None:
        """
        添加性能指标
        
        Args:
            metric: 性能指标
        """
        if self.current_report:
            self.current_report.performance_metrics.append(metric)
    
    def finalize_report(self) -> TestReport:
        """
        完成报告并生成摘要
        
        Returns:
            完成的测试报告
        """
        if not self.current_report:
            raise ValueError("没有活跃的测试报告")
        
        # 生成摘要
        self._generate_summary()
        
        # 完成报告
        self.test_reports.append(self.current_report)
        report = self.current_report
        self.current_report = None
        
        return report
    
    def _generate_summary(self) -> None:
        """生成测试摘要"""
        if not self.current_report:
            return
        
        report = self.current_report
        
        # 统计测试用例
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        error_tests = 0
        total_duration = 0.0
        
        for suite in report.test_suites:
            total_duration += suite.duration
            for test_case in suite.test_cases:
                total_tests += 1
                
                if test_case.status == "passed":
                    passed_tests += 1
                elif test_case.status == "failed":
                    failed_tests += 1
                elif test_case.status == "skipped":
                    skipped_tests += 1
                elif test_case.status == "error":
                    error_tests += 1
        
        # 计算成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 收集所有错误
        all_errors = []
        for suite in report.test_suites:
            all_errors.extend(suite.errors)
            for test_case in suite.test_cases:
                if test_case.status in ["failed", "error"] and test_case.message:
                    all_errors.append(f"{test_case.name}: {test_case.message}")
        
        # 性能指标摘要
        performance_summary = {}
        for metric in report.performance_metrics:
            performance_summary[metric.name] = {
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status
            }
        
        # 覆盖率摘要
        coverage_summary = {}
        if report.coverage:
            coverage_summary = {
                "total_lines": report.coverage.total_lines,
                "covered_lines": report.coverage.covered_lines,
                "missed_lines": report.coverage.missed_lines,
                "coverage_percentage": report.coverage.coverage_percentage
            }
        
        # 生成摘要
        report.summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "error_tests": error_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "test_suites_count": len(report.test_suites),
            "performance_metrics_count": len(report.performance_metrics),
            "has_coverage": report.coverage is not None,
            "performance_summary": performance_summary,
            "coverage_summary": coverage_summary
        }
        
        # 收集所有错误和警告
        report.errors = all_errors
        report.warnings = []
        
        # 添加警告
        if success_rate < 90:
            report.warnings.append(f"测试成功率较低: {success_rate:.2f}%")
        
        if report.coverage and report.coverage.coverage_percentage < 80:
            report.warnings.append(f"代码覆盖率较低: {report.coverage.coverage_percentage:.2f}%")
        
        for metric in report.performance_metrics:
            if metric.status == "warning":
                report.warnings.append(f"性能指标警告: {metric.name} = {metric.value}{metric.unit}")
            elif metric.status == "critical":
                report.warnings.append(f"性能指标严重: {metric.name} = {metric.value}{metric.unit}")
    
    def parse_pytest_json(self, json_file: Union[str, Path]) -> TestSuiteResult:
        """
        解析pytest JSON报告
        
        Args:
            json_file: JSON报告文件路径
            
        Returns:
            测试套件结果
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_cases = []
        total_duration = 0.0
        
        for test_item in data.get('tests', []):
            # 提取测试用例信息
            node_id = test_item.get('nodeid', '')
            outcome = test_item.get('outcome', 'unknown')
            duration = test_item.get('duration', 0.0)
            
            total_duration += duration
            
            # 解析测试名称和文件路径
            file_path, test_name = self._parse_pytest_node_id(node_id)
            
            # 提取调用信息
            call = test_item.get('call', {})
            message = call.get('longrepr', '')
            traceback = call.get('traceback', '')
            
            # 提取标记
            markers = [marker.get('name', '') for marker in test_item.get('markers', [])]
            
            test_case = TestCaseResult(
                name=test_name,
                status=outcome,
                duration=duration,
                message=message,
                traceback=traceback,
                file_path=file_path,
                markers=markers
            )
            
            test_cases.append(test_case)
        
        # 确定套件状态
        status = "passed"
        errors = []
        
        for test_case in test_cases:
            if test_case.status == "failed":
                status = "failed"
                errors.append(f"测试失败: {test_case.name} - {test_case.message}")
            elif test_case.status == "error":
                status = "error"
                errors.append(f"测试错误: {test_case.name} - {test_case.message}")
        
        return TestSuiteResult(
            name="pytest_results",
            test_cases=test_cases,
            duration=total_duration,
            status=status,
            errors=errors
        )
    
    def parse_coverage_xml(self, xml_file: Union[str, Path]) -> CoverageData:
        """
        解析覆盖率XML报告
        
        Args:
            xml_file: XML报告文件路径
            
        Returns:
            覆盖率数据
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 计算总体覆盖率
        total_lines = 0
        covered_lines = 0
        missed_lines = 0
        file_coverage = {}
        
        for packages in root.findall('packages'):
            for package in packages.findall('package'):
                for classes in package.findall('classes'):
                    for class_ in classes.findall('class'):
                        filename = class_.get('filename', '')
                        
                        class_total_lines = 0
                        class_covered_lines = 0
                        class_missed_lines = 0
                        
                        for lines in class_.findall('lines'):
                            for line in lines.findall('line'):
                                line_hits = int(line.get('hits', 0))
                                class_total_lines += 1
                                
                                if line_hits > 0:
                                    class_covered_lines += 1
                                else:
                                    class_missed_lines += 1
                        
                        total_lines += class_total_lines
                        covered_lines += class_covered_lines
                        missed_lines += class_missed_lines
                        
                        # 计算文件覆盖率
                        class_coverage = (class_covered_lines / class_total_lines * 100) if class_total_lines > 0 else 0
                        
                        file_coverage[filename] = {
                            "total_lines": class_total_lines,
                            "covered_lines": class_covered_lines,
                            "missed_lines": class_missed_lines,
                            "coverage_percentage": class_coverage
                        }
        
        # 计算总体覆盖率
        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        return CoverageData(
            total_lines=total_lines,
            covered_lines=covered_lines,
            missed_lines=missed_lines,
            coverage_percentage=coverage_percentage,
            file_coverage=file_coverage
        )
    
    def parse_performance_json(self, json_file: Union[str, Path]) -> List[PerformanceMetric]:
        """
        解析性能测试JSON报告
        
        Args:
            json_file: JSON报告文件路径
            
        Returns:
            性能指标列表
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metrics = []
        
        # 解析基准测试结果
        benchmarks = data.get('benchmarks', [])
        
        for benchmark in benchmarks:
            name = benchmark.get('name', 'unknown')
            stats = benchmark.get('stats', {})
            
            # 主要指标：平均响应时间
            mean_value = stats.get('mean', 0)
            metric = PerformanceMetric(
                name=f"{name}_mean",
                value=mean_value,
                unit="ms"
            )
            
            # 检查阈值和基线
            if 'threshold' in benchmark:
                metric.threshold = benchmark['threshold']
                if mean_value > metric.threshold:
                    metric.status = "critical"
                else:
                    metric.status = "good"
            
            if 'baseline' in benchmark:
                metric.baseline = benchmark['baseline']
                if metric.status == "good" and metric.baseline:
                    change_percent = ((mean_value - metric.baseline) / metric.baseline) * 100
                    if change_percent > 10:  # 性能下降超过10%
                        metric.status = "warning"
            
            metrics.append(metric)
            
            # 添加其他指标
            for stat_name, stat_value in stats.items():
                if stat_name not in ['min', 'max', 'mean', 'median', 'stddev', 'rounds', 'iterations']:
                    continue
                
                metric = PerformanceMetric(
                    name=f"{name}_{stat_name}",
                    value=stat_value,
                    unit="ms" if stat_name in ['min', 'max', 'mean', 'median', 'stddev'] else "count"
                )
                metrics.append(metric)
        
        return metrics
    
    def _parse_pytest_node_id(self, node_id: str) -> tuple:
        """
        解析pytest节点ID
        
        Args:
            node_id: pytest节点ID
            
        Returns:
            (文件路径, 测试名称)
        """
        # 示例: tests/test_example.py::TestExample::test_method
        parts = node_id.split('::')
        
        if len(parts) >= 1:
            file_path = parts[0]
        else:
            file_path = ""
        
        if len(parts) >= 2:
            test_name = "::".join(parts[1:])
        else:
            test_name = node_id
        
        return file_path, test_name
    
    def save_report(self, report: TestReport, format: str = "json") -> Path:
        """
        保存测试报告
        
        Args:
            report: 测试报告
            format: 报告格式 (json, xml, html)
            
        Returns:
            保存的文件路径
        """
        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            filename = f"test_report_{timestamp_str}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._report_to_dict(report), f, ensure_ascii=False, indent=2, default=str)
        
        elif format == "xml":
            filename = f"test_report_{timestamp_str}.xml"
            filepath = self.output_dir / filename
            
            root = self._report_to_xml(report)
            tree = ET.ElementTree(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        elif format == "html":
            filename = f"test_report_{timestamp_str}.html"
            filepath = self.output_dir / filename
            
            html_content = self._report_to_html(report)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        else:
            raise ValueError(f"不支持的报告格式: {format}")
        
        return filepath
    
    def _report_to_dict(self, report: TestReport) -> Dict[str, Any]:
        """将测试报告转换为字典"""
        return {
            "timestamp": report.timestamp.isoformat(),
            "test_environment": report.test_environment,
            "test_suites": [
                {
                    "name": suite.name,
                    "status": suite.status,
                    "duration": suite.duration,
                    "setup_time": suite.setup_time,
                    "teardown_time": suite.teardown_time,
                    "errors": suite.errors,
                    "test_cases": [
                        {
                            "name": test.name,
                            "status": test.status,
                            "duration": test.duration,
                            "message": test.message,
                            "traceback": test.traceback,
                            "file_path": test.file_path,
                            "line_number": test.line_number,
                            "class_name": test.class_name,
                            "module_name": test.module_name,
                            "markers": test.markers
                        }
                        for test in suite.test_cases
                    ]
                }
                for suite in report.test_suites
            ],
            "coverage": {
                "total_lines": report.coverage.total_lines,
                "covered_lines": report.coverage.covered_lines,
                "missed_lines": report.coverage.missed_lines,
                "coverage_percentage": report.coverage.coverage_percentage,
                "file_coverage": report.coverage.file_coverage
            } if report.coverage else None,
            "performance_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "baseline": metric.baseline,
                    "threshold": metric.threshold,
                    "status": metric.status
                }
                for metric in report.performance_metrics
            ],
            "summary": report.summary,
            "errors": report.errors,
            "warnings": report.warnings
        }
    
    def _report_to_xml(self, report: TestReport) -> ET.Element:
        """将测试报告转换为XML"""
        root = ET.Element("test_report")
        
        # 基本信息
        ET.SubElement(root, "timestamp").text = report.timestamp.isoformat()
        
        env = ET.SubElement(root, "test_environment")
        for key, value in report.test_environment.items():
            env_elem = ET.SubElement(env, "property")
            env_elem.set("name", key)
            env_elem.text = value
        
        # 测试套件
        suites_elem = ET.SubElement(root, "test_suites")
        for suite in report.test_suites:
            suite_elem = ET.SubElement(suites_elem, "test_suite")
            suite_elem.set("name", suite.name)
            suite_elem.set("status", suite.status)
            suite_elem.set("duration", str(suite.duration))
            
            for test_case in suite.test_cases:
                test_elem = ET.SubElement(suite_elem, "test_case")
                test_elem.set("name", test_case.name)
                test_elem.set("status", test_case.status)
                test_elem.set("duration", str(test_case.duration))
                
                if test_case.message:
                    ET.SubElement(test_elem, "message").text = test_case.message
                
                if test_case.traceback:
                    ET.SubElement(test_elem, "traceback").text = test_case.traceback
        
        # 覆盖率
        if report.coverage:
            coverage_elem = ET.SubElement(root, "coverage")
            coverage_elem.set("percentage", str(report.coverage.coverage_percentage))
            coverage_elem.set("total_lines", str(report.coverage.total_lines))
            coverage_elem.set("covered_lines", str(report.coverage.covered_lines))
            coverage_elem.set("missed_lines", str(report.coverage.missed_lines))
        
        # 性能指标
        if report.performance_metrics:
            perf_elem = ET.SubElement(root, "performance_metrics")
            for metric in report.performance_metrics:
                metric_elem = ET.SubElement(perf_elem, "metric")
                metric_elem.set("name", metric.name)
                metric_elem.set("value", str(metric.value))
                metric_elem.set("unit", metric.unit)
                metric_elem.set("status", metric.status)
        
        # 摘要
        summary_elem = ET.SubElement(root, "summary")
        for key, value in report.summary.items():
            summary_sub_elem = ET.SubElement(summary_elem, key)
            if isinstance(value, (dict, list)):
                summary_sub_elem.text = json.dumps(value, ensure_ascii=False)
            else:
                summary_sub_elem.text = str(value)
        
        return root
    
    def _report_to_html(self, report: TestReport) -> str:
        """将测试报告转换为HTML"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>测试报告 - {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                .header {{
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .summary {{
                    background-color: #e9f7fe;
                    padding: 20px;
                    border-radius: 6px;
                    margin-bottom: 30px;
                }}
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-top: 15px;
                }}
                .summary-item {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 4px;
                    text-align: center;
                }}
                .summary-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #007acc;
                }}
                .summary-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .status-passed {{
                    color: #28a745;
                }}
                .status-failed {{
                    color: #dc3545;
                }}
                .status-skipped {{
                    color: #ffc107;
                }}
                .status-error {{
                    color: #fd7e14;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .test-suite {{
                    margin-bottom: 30px;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    overflow: hidden;
                }}
                .test-suite-header {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-bottom: 1px solid #ddd;
                }}
                .test-cases {{
                    max-height: 400px;
                    overflow-y: auto;
                }}
                .error-message {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                    font-family: monospace;
                    font-size: 0.9em;
                }}
                .warning {{
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                }}
                .coverage-bar {{
                    width: 100%;
                    height: 20px;
                    background-color: #e9ecef;
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .coverage-fill {{
                    height: 100%;
                    background-color: #28a745;
                }}
                .performance-metric {{
                    display: inline-block;
                    margin: 5px;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                .metric-good {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .metric-warning {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                .metric-critical {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>测试报告</h1>
                    <p><strong>测试时间:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>测试环境:</strong> {', '.join([f'{k}: {v}' for k, v in report.test_environment.items()])}</p>
                </div>
                
                <div class="summary">
                    <h2>测试摘要</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value">{report.summary.get('total_tests', 0)}</div>
                            <div class="summary-label">总测试数</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value status-passed">{report.summary.get('passed_tests', 0)}</div>
                            <div class="summary-label">通过</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value status-failed">{report.summary.get('failed_tests', 0)}</div>
                            <div class="summary-label">失败</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value status-skipped">{report.summary.get('skipped_tests', 0)}</div>
                            <div class="summary-label">跳过</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{report.summary.get('success_rate', 0):.1f}%</div>
                            <div class="summary-label">成功率</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{report.summary.get('total_duration', 0):.2f}s</div>
                            <div class="summary-label">总耗时</div>
                        </div>
                    </div>
                </div>
        """
        
        # 添加覆盖率信息
        if report.coverage:
            coverage = report.coverage
            html_content += f"""
                <h2>代码覆盖率</h2>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: {coverage.coverage_percentage}%"></div>
                </div>
                <p>总覆盖率: {coverage.coverage_percentage:.2f}% ({coverage.covered_lines}/{coverage.total_lines} 行)</p>
            """
        
        # 添加性能指标
        if report.performance_metrics:
            html_content += "<h2>性能指标</h2>"
            for metric in report.performance_metrics:
                status_class = f"metric-{metric.status}"
                html_content += f"""
                    <div class="performance-metric {status_class}">
                        {metric.name}: {metric.value}{metric.unit}
                    </div>
                """
        
        # 添加警告
        if report.warnings:
            html_content += "<h2>警告</h2>"
            for warning in report.warnings:
                html_content += f'<div class="warning">{warning}</div>'
        
        # 添加测试套件详情
        html_content += "<h2>测试套件详情</h2>"
        for suite in report.test_suites:
            status_class = f"status-{suite.status}"
            html_content += f"""
                <div class="test-suite">
                    <div class="test-suite-header">
                        <h3>{suite.name} <span class="{status_class}">({suite.status.upper()})</span></h3>
                        <p>耗时: {suite.duration:.2f}s | 测试数: {len(suite.test_cases)}</p>
                    </div>
                    <div class="test-cases">
                        <table>
                            <tr>
                                <th>测试名称</th>
                                <th>状态</th>
                                <th>耗时</th>
                                <th>错误信息</th>
                            </tr>
            """
            
            for test_case in suite.test_cases:
                status_class = f"status-{test_case.status}"
                error_message = test_case.message or ""
                
                html_content += f"""
                    <tr>
                        <td>{test_case.name}</td>
                        <td class="{status_class}">{test_case.status.upper()}</td>
                        <td>{test_case.duration:.3f}s</td>
                        <td>{error_message[:100]}{'...' if len(error_message) > 100 else ''}</td>
                    </tr>
                """
            
            html_content += """
                        </table>
                    </div>
                </div>
            """
        
        # 添加错误详情
        if report.errors:
            html_content += "<h2>错误详情</h2>"
            for error in report.errors:
                html_content += f'<div class="error-message">{error}</div>'
        
        html_content += """
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center;">
                    <p>SuperRPG 测试报告工具</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def compare_reports(self, report1: TestReport, report2: TestReport) -> Dict[str, Any]:
        """
        比较两个测试报告
        
        Args:
            report1: 第一个测试报告
            report2: 第二个测试报告
            
        Returns:
            比较结果
        """
        comparison = {
            "timestamp1": report1.timestamp.isoformat(),
            "timestamp2": report2.timestamp.isoformat(),
            "test_summary_comparison": {},
            "coverage_comparison": {},
            "performance_comparison": {}
        }
        
        # 比较测试摘要
        summary1 = report1.summary
        summary2 = report2.summary
        
        comparison["test_summary_comparison"] = {
            "total_tests_change": summary2.get("total_tests", 0) - summary1.get("total_tests", 0),
            "passed_tests_change": summary2.get("passed_tests", 0) - summary1.get("passed_tests", 0),
            "failed_tests_change": summary2.get("failed_tests", 0) - summary1.get("failed_tests", 0),
            "success_rate_change": summary2.get("success_rate", 0) - summary1.get("success_rate", 0),
            "duration_change": summary2.get("total_duration", 0) - summary1.get("total_duration", 0)
        }
        
        # 比较覆盖率
        if report1.coverage and report2.coverage:
            comparison["coverage_comparison"] = {
                "coverage_percentage_change": report2.coverage.coverage_percentage - report1.coverage.coverage_percentage,
                "total_lines_change": report2.coverage.total_lines - report1.coverage.total_lines,
                "covered_lines_change": report2.coverage.covered_lines - report1.coverage.covered_lines
            }
        
        # 比较性能指标
        perf1 = {metric.name: metric.value for metric in report1.performance_metrics}
        perf2 = {metric.name: metric.value for metric in report2.performance_metrics}
        
        performance_comparison = {}
        for name in set(perf1.keys()).union(set(perf2.keys())):
            value1 = perf1.get(name, 0)
            value2 = perf2.get(name, 0)
            
            if value1 > 0:
                change_percent = ((value2 - value1) / value1) * 100
                performance_comparison[name] = {
                    "value1": value1,
                    "value2": value2,
                    "change": value2 - value1,
                    "change_percent": change_percent
                }
        
        comparison["performance_comparison"] = performance_comparison
        
        return comparison


# 便捷函数

def aggregate_test_results(
    pytest_json_path: Union[str, Path],
    coverage_xml_path: Optional[Union[str, Path]] = None,
    performance_json_path: Optional[Union[str, Path]] = None,
    output_dir: str = "test_reports"
) -> TestReport:
    """
    聚合测试结果的便捷函数
    
    Args:
        pytest_json_path: pytest JSON报告路径
        coverage_xml_path: 覆盖率XML报告路径
        performance_json_path: 性能测试JSON报告路径
        output_dir: 输出目录
        
    Returns:
        聚合后的测试报告
    """
    aggregator = TestResultAggregator(output_dir)
    
    # 创建测试报告
    test_environment = {
        "python_version": os.sys.version,
        "platform": os.name,
        "working_directory": os.getcwd()
    }
    
    report = aggregator.create_new_report(test_environment)
    
    # 解析pytest结果
    if pytest_json_path and Path(pytest_json_path).exists():
        suite_result = aggregator.parse_pytest_json(pytest_json_path)
        aggregator.add_test_suite_result(suite_result)
    
    # 解析覆盖率结果
    if coverage_xml_path and Path(coverage_xml_path).exists():
        coverage_data = aggregator.parse_coverage_xml(coverage_xml_path)
        aggregator.add_coverage_data(coverage_data)
    
    # 解析性能测试结果
    if performance_json_path and Path(performance_json_path).exists():
        performance_metrics = aggregator.parse_performance_json(performance_json_path)
        for metric in performance_metrics:
            aggregator.add_performance_metric(metric)
    
    # 完成报告
    finalized_report = aggregator.finalize_report()
    
    # 保存报告
    aggregator.save_report(finalized_report, "json")
    aggregator.save_report(finalized_report, "html")
    
    return finalized_report


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python test_result_aggregator.py <pytest_json_file> [coverage_xml_file] [performance_json_file]")
        sys.exit(1)
    
    pytest_json = sys.argv[1]
    coverage_xml = sys.argv[2] if len(sys.argv) > 2 else None
    performance_json = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        report = aggregate_test_results(pytest_json, coverage_xml, performance_json)
        print(f"测试报告已生成，成功率: {report.summary.get('success_rate', 0):.2f}%")
        
        if report.coverage:
            print(f"代码覆盖率: {report.coverage.coverage_percentage:.2f}%")
        
        if report.warnings:
            print("警告:")
            for warning in report.warnings:
                print(f"  - {warning}")
        
        if report.errors:
            print("错误:")
            for error in report.errors[:5]:  # 只显示前5个错误
                print(f"  - {error}")
            if len(report.errors) > 5:
                print(f"  ... 还有 {len(report.errors) - 5} 个错误")
    
    except Exception as e:
        print(f"聚合测试结果时出错: {str(e)}")
        sys.exit(1)