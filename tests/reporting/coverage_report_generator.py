"""
覆盖率报告生成器

负责生成详细的代码覆盖率报告，包括：
- 覆盖率数据收集
- 覆盖率趋势分析
- 覆盖率热力图
- 覆盖率改进建议
- 覆盖率目标跟踪
"""

import json
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import re


@dataclass
class FileCoverage:
    """文件覆盖率"""
    file_path: str
    total_lines: int
    covered_lines: int
    missed_lines: int
    coverage_percentage: float
    functions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    classes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    branches: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CoverageSummary:
    """覆盖率摘要"""
    total_lines: int
    covered_lines: int
    missed_lines: int
    coverage_percentage: float
    total_functions: int
    covered_functions: int
    total_branches: int
    covered_branches: int
    file_coverage: Dict[str, FileCoverage] = field(default_factory=dict)


@dataclass
class CoverageTarget:
    """覆盖率目标"""
    name: str
    target_percentage: float
    current_percentage: float
    achieved: bool
    description: str = ""


@dataclass
class CoverageTrend:
    """覆盖率趋势"""
    date: datetime
    overall_coverage: float
    file_coverage: Dict[str, float]
    metrics: Dict[str, float]


class CoverageReportGenerator:
    """覆盖率报告生成器"""
    
    def __init__(self, output_dir: str = "coverage_reports"):
        """
        初始化覆盖率报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.coverage_history: List[CoverageTrend] = []
        self.targets: List[CoverageTarget] = []
        
        # 默认覆盖率目标
        self._init_default_targets()
    
    def _init_default_targets(self) -> None:
        """初始化默认覆盖率目标"""
        self.targets = [
            CoverageTarget(
                name="整体覆盖率",
                target_percentage=80.0,
                current_percentage=0.0,
                achieved=False,
                description="整体代码覆盖率目标"
            ),
            CoverageTarget(
                name="核心模块覆盖率",
                target_percentage=90.0,
                current_percentage=0.0,
                achieved=False,
                description="核心模块代码覆盖率目标"
            ),
            CoverageTarget(
                name="函数覆盖率",
                target_percentage=85.0,
                current_percentage=0.0,
                achieved=False,
                description="函数覆盖率目标"
            ),
            CoverageTarget(
                name="分支覆盖率",
                target_percentage=75.0,
                current_percentage=0.0,
                achieved=False,
                description="分支覆盖率目标"
            )
        ]
    
    def parse_coverage_xml(self, xml_file: Path) -> CoverageSummary:
        """
        解析覆盖率XML报告
        
        Args:
            xml_file: XML报告文件路径
            
        Returns:
            覆盖率摘要
        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 初始化统计数据
        total_lines = 0
        covered_lines = 0
        missed_lines = 0
        total_functions = 0
        covered_functions = 0
        total_branches = 0
        covered_branches = 0
        file_coverage = {}
        
        # 解析源文件
        for sources in root.findall('sources'):
            for source in sources.findall('source'):
                source_path = source.text or ""
                
                for classes in source.findall('classes'):
                    for class_ in classes.findall('class'):
                        filename = class_.get('filename', '')
                        full_path = os.path.join(source_path, filename)
                        
                        # 解析行覆盖率
                        lines = class_.find('lines')
                        if lines is not None:
                            file_total_lines = 0
                            file_covered_lines = 0
                            file_missed_lines = 0
                            
                            for line in lines.findall('line'):
                                line_hits = int(line.get('hits', 0))
                                file_total_lines += 1
                                total_lines += 1
                                
                                if line_hits > 0:
                                    file_covered_lines += 1
                                    covered_lines += 1
                                else:
                                    file_missed_lines += 1
                                    missed_lines += 1
                            
                            # 计算文件覆盖率
                            file_coverage_percentage = (file_covered_lines / file_total_lines * 100) if file_total_lines > 0 else 0
                            
                            file_coverage[full_path] = FileCoverage(
                                file_path=full_path,
                                total_lines=file_total_lines,
                                covered_lines=file_covered_lines,
                                missed_lines=file_missed_lines,
                                coverage_percentage=file_coverage_percentage
                            )
                        
                        # 解析函数覆盖率
                        methods = class_.find('methods')
                        if methods is not None:
                            for method in methods.findall('method'):
                                total_functions += 1
                                method_lines = method.find('lines')
                                if method_lines is not None:
                                    method_covered = False
                                    for line in method_lines.findall('line'):
                                        if int(line.get('hits', 0)) > 0:
                                            method_covered = True
                                            break
                                    
                                    if method_covered:
                                        covered_functions += 1
                        
                        # 解析分支覆盖率
                        branches = class_.find('branches')
                        if branches is not None:
                            for branch in branches.findall('branch'):
                                total_branches += 1
                                if int(branch.get('hits', 0)) > 0:
                                    covered_branches += 1
        
        # 计算总体覆盖率
        overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        function_coverage = (covered_functions / total_functions * 100) if total_functions > 0 else 0
        branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
        
        # 更新目标状态
        for target in self.targets:
            if target.name == "整体覆盖率":
                target.current_percentage = overall_coverage
                target.achieved = overall_coverage >= target.target_percentage
            elif target.name == "函数覆盖率":
                target.current_percentage = function_coverage
                target.achieved = function_coverage >= target.target_percentage
            elif target.name == "分支覆盖率":
                target.current_percentage = branch_coverage
                target.achieved = branch_coverage >= target.target_percentage
        
        return CoverageSummary(
            total_lines=total_lines,
            covered_lines=covered_lines,
            missed_lines=missed_lines,
            coverage_percentage=overall_coverage,
            total_functions=total_functions,
            covered_functions=covered_functions,
            total_branches=total_branches,
            covered_branches=covered_branches,
            file_coverage=file_coverage
        )
    
    def parse_coverage_json(self, json_file: Path) -> CoverageSummary:
        """
        解析覆盖率JSON报告
        
        Args:
            json_file: JSON报告文件路径
            
        Returns:
            覆盖率摘要
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取总体覆盖率
        totals = data.get('totals', {})
        total_lines = totals.get('covered_lines', 0) + totals.get('missing_lines', 0)
        covered_lines = totals.get('covered_lines', 0)
        missed_lines = totals.get('missing_lines', 0)
        overall_coverage = totals.get('percent_covered', 0.0)
        
        # 提取函数覆盖率
        function_totals = data.get('functions', {})
        total_functions = function_totals.get('covered', 0) + function_totals.get('missing', 0)
        covered_functions = function_totals.get('covered', 0)
        
        # 提取分支覆盖率
        branch_totals = data.get('branches', {})
        total_branches = branch_totals.get('covered', 0) + branch_totals.get('missing', 0)
        covered_branches = branch_totals.get('covered', 0)
        
        # 解析文件覆盖率
        files_data = data.get('files', {})
        file_coverage = {}
        
        for file_path, file_data in files_data.items():
            summary = file_data.get('summary', {})
            file_total_lines = summary.get('covered_lines', 0) + summary.get('missing_lines', 0)
            file_covered_lines = summary.get('covered_lines', 0)
            file_missed_lines = summary.get('missing_lines', 0)
            file_coverage_percentage = summary.get('percent_covered', 0.0)
            
            file_coverage[file_path] = FileCoverage(
                file_path=file_path,
                total_lines=file_total_lines,
                covered_lines=file_covered_lines,
                missed_lines=file_missed_lines,
                coverage_percentage=file_coverage_percentage
            )
        
        # 更新目标状态
        for target in self.targets:
            if target.name == "整体覆盖率":
                target.current_percentage = overall_coverage
                target.achieved = overall_coverage >= target.target_percentage
            elif target.name == "函数覆盖率":
                function_coverage = (covered_functions / total_functions * 100) if total_functions > 0 else 0
                target.current_percentage = function_coverage
                target.achieved = function_coverage >= target.target_percentage
            elif target.name == "分支覆盖率":
                branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
                target.current_percentage = branch_coverage
                target.achieved = branch_coverage >= target.target_percentage
        
        return CoverageSummary(
            total_lines=total_lines,
            covered_lines=covered_lines,
            missed_lines=missed_lines,
            coverage_percentage=overall_coverage,
            total_functions=total_functions,
            covered_functions=covered_functions,
            total_branches=total_branches,
            covered_branches=covered_branches,
            file_coverage=file_coverage
        )
    
    def load_historical_coverage(self, historical_dir: Path) -> None:
        """
        加载历史覆盖率数据
        
        Args:
            historical_dir: 历史数据目录
        """
        if not historical_dir.exists():
            return
        
        for json_file in historical_dir.glob("coverage_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取日期
                filename = json_file.stem
                date_str = filename.replace("coverage_", "")
                date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                
                # 提取覆盖率数据
                summary = data.get('summary', {})
                overall_coverage = summary.get('coverage_percentage', 0.0)
                
                # 提取文件覆盖率
                file_coverage = {}
                file_data = data.get('file_coverage', {})
                for file_path, coverage_info in file_data.items():
                    file_coverage[file_path] = coverage_info.get('coverage_percentage', 0.0)
                
                # 提取其他指标
                metrics = {
                    'function_coverage': summary.get('function_coverage', 0.0),
                    'branch_coverage': summary.get('branch_coverage', 0.0)
                }
                
                trend = CoverageTrend(
                    date=date,
                    overall_coverage=overall_coverage,
                    file_coverage=file_coverage,
                    metrics=metrics
                )
                
                self.coverage_history.append(trend)
                
            except Exception as e:
                print(f"加载历史覆盖率数据失败 {json_file}: {str(e)}")
        
        # 按日期排序
        self.coverage_history.sort(key=lambda x: x.date)
    
    def analyze_coverage_trends(self) -> Dict[str, Any]:
        """
        分析覆盖率趋势
        
        Returns:
            趋势分析结果
        """
        if len(self.coverage_history) < 2:
            return {}
        
        # 提取整体覆盖率趋势
        overall_coverage_values = [t.overall_coverage for t in self.coverage_history]
        dates = [t.date for t in self.coverage_history]
        
        # 计算趋势
        first_coverage = overall_coverage_values[0]
        latest_coverage = overall_coverage_values[-1]
        overall_change = latest_coverage - first_coverage
        
        # 计算平均变化率
        if len(overall_coverage_values) > 1:
            changes = [overall_coverage_values[i] - overall_coverage_values[i-1] for i in range(1, len(overall_coverage_values))]
            avg_change = sum(changes) / len(changes)
        else:
            avg_change = 0
        
        # 分析文件级别的趋势
        file_trends = {}
        all_files = set()
        for trend in self.coverage_history:
            all_files.update(trend.file_coverage.keys())
        
        for file_path in all_files:
            file_values = []
            for trend in self.coverage_history:
                if file_path in trend.file_coverage:
                    file_values.append(trend.file_coverage[file_path])
            
            if len(file_values) >= 2:
                first_file_coverage = file_values[0]
                latest_file_coverage = file_values[-1]
                file_change = latest_file_coverage - first_file_coverage
                
                file_trends[file_path] = {
                    'change': file_change,
                    'first_coverage': first_file_coverage,
                    'latest_coverage': latest_file_coverage,
                    'trend': 'improving' if file_change > 1 else 'degrading' if file_change < -1 else 'stable'
                }
        
        return {
            'overall_change': overall_change,
            'avg_change': avg_change,
            'first_coverage': first_coverage,
            'latest_coverage': latest_coverage,
            'trend_direction': 'improving' if overall_change > 1 else 'degrading' if overall_change < -1 else 'stable',
            'file_trends': file_trends,
            'data_points': len(self.coverage_history)
        }
    
    def identify_low_coverage_files(self, threshold: float = 50.0) -> List[FileCoverage]:
        """
        识别低覆盖率文件
        
        Args:
            threshold: 覆盖率阈值
            
        Returns:
            低覆盖率文件列表
        """
        low_coverage_files = []
        
        for target in self.targets:
            if hasattr(target, 'file_coverage'):
                for file_path, file_cov in target.file_coverage.items():
                    if file_cov.coverage_percentage < threshold:
                        low_coverage_files.append(file_cov)
        
        # 按覆盖率排序
        low_coverage_files.sort(key=lambda x: x.coverage_percentage)
        
        return low_coverage_files
    
    def generate_coverage_improvement_suggestions(self, coverage_summary: CoverageSummary) -> List[str]:
        """
        生成覆盖率改进建议
        
        Args:
            coverage_summary: 覆盖率摘要
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 检查整体覆盖率
        overall_coverage = coverage_summary.coverage_percentage
        if overall_coverage < 80:
            suggestions.append(f"整体覆盖率({overall_coverage:.1f}%)低于推荐值(80%)，建议增加测试用例")
        elif overall_coverage < 90:
            suggestions.append(f"整体覆盖率({overall_coverage:.1f}%)接近推荐值，可以继续优化")
        
        # 检查函数覆盖率
        if coverage_summary.total_functions > 0:
            function_coverage = (coverage_summary.covered_functions / coverage_summary.total_functions * 100)
            if function_coverage < 85:
                suggestions.append(f"函数覆盖率({function_coverage:.1f}%)较低，建议为未覆盖的函数添加单元测试")
        
        # 检查分支覆盖率
        if coverage_summary.total_branches > 0:
            branch_coverage = (coverage_summary.covered_branches / coverage_summary.total_branches * 100)
            if branch_coverage < 75:
                suggestions.append(f"分支覆盖率({branch_coverage:.1f}%)较低，建议增加边界条件和异常情况的测试")
        
        # 识别低覆盖率文件
        low_coverage_files = self.identify_low_coverage_files()
        if low_coverage_files:
            top_low_files = low_coverage_files[:5]  # 只显示前5个
            suggestions.append(f"以下文件覆盖率较低，建议优先添加测试: {', '.join([f.name for f in top_low_files])}")
        
        # 检查核心模块覆盖率
        core_modules = ['src/core', 'src/domain', 'src/application']
        core_coverage_files = []
        
        for file_path, file_cov in coverage_summary.file_coverage.items():
            for module in core_modules:
                if module in file_path:
                    core_coverage_files.append(file_cov)
                    break
        
        if core_coverage_files:
            core_total_lines = sum(f.total_lines for f in core_coverage_files)
            core_covered_lines = sum(f.covered_lines for f in core_coverage_files)
            core_coverage = (core_covered_lines / core_total_lines * 100) if core_total_lines > 0 else 0
            
            if core_coverage < 90:
                suggestions.append(f"核心模块覆盖率({core_coverage:.1f}%)低于推荐值(90%)，建议优先测试核心功能")
        
        # 通用建议
        if not suggestions:
            suggestions.append("当前覆盖率表现良好，建议保持并持续监控")
        else:
            suggestions.append("建议将覆盖率检查集成到CI/CD流程中，设置最低覆盖率阈值")
            suggestions.append("考虑使用代码覆盖率工具识别未测试的代码路径")
        
        return suggestions
    
    def generate_report(self, coverage_summary: CoverageSummary, report_format: str = "html") -> Path:
        """
        生成覆盖率报告
        
        Args:
            coverage_summary: 覆盖率摘要
            report_format: 报告格式 (html, json, markdown)
            
        Returns:
            报告文件路径
        """
        # 分析趋势
        trend_analysis = self.analyze_coverage_trends()
        
        # 生成改进建议
        suggestions = self.generate_coverage_improvement_suggestions(coverage_summary)
        
        # 保存当前覆盖率数据到历史
        self._save_current_coverage(coverage_summary)
        
        # 根据格式生成报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if report_format == "html":
            report_file = self.output_dir / f"coverage_report_{timestamp}.html"
            self._generate_html_report(report_file, coverage_summary, trend_analysis, suggestions)
        elif report_format == "json":
            report_file = self.output_dir / f"coverage_report_{timestamp}.json"
            self._generate_json_report(report_file, coverage_summary, trend_analysis, suggestions)
        elif report_format == "markdown":
            report_file = self.output_dir / f"coverage_report_{timestamp}.md"
            self._generate_markdown_report(report_file, coverage_summary, trend_analysis, suggestions)
        else:
            raise ValueError(f"不支持的报告格式: {report_format}")
        
        return report_file
    
    def _save_current_coverage(self, coverage_summary: CoverageSummary) -> None:
        """保存当前覆盖率数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = self.output_dir / f"coverage_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_lines": coverage_summary.total_lines,
                "covered_lines": coverage_summary.covered_lines,
                "missed_lines": coverage_summary.missed_lines,
                "coverage_percentage": coverage_summary.coverage_percentage,
                "total_functions": coverage_summary.total_functions,
                "covered_functions": coverage_summary.covered_functions,
                "total_branches": coverage_summary.total_branches,
                "covered_branches": coverage_summary.covered_branches,
                "function_coverage": (coverage_summary.covered_functions / coverage_summary.total_functions * 100) if coverage_summary.total_functions > 0 else 0,
                "branch_coverage": (coverage_summary.covered_branches / coverage_summary.total_branches * 100) if coverage_summary.total_branches > 0 else 0
            },
            "file_coverage": {
                file_path: {
                    "total_lines": file_cov.total_lines,
                    "covered_lines": file_cov.covered_lines,
                    "missed_lines": file_cov.missed_lines,
                    "coverage_percentage": file_cov.coverage_percentage
                }
                for file_path, file_cov in coverage_summary.file_coverage.items()
            }
        }
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _generate_html_report(self, report_file: Path, coverage_summary: CoverageSummary, 
                            trend_analysis: Dict[str, Any], suggestions: List[str]) -> None:
        """生成HTML覆盖率报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>代码覆盖率报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
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
                .coverage-bar {{
                    width: 100%;
                    height: 30px;
                    background-color: #e9ecef;
                    border-radius: 15px;
                    overflow: hidden;
                    margin: 10px 0;
                }}
                .coverage-fill {{
                    height: 100%;
                    background-color: #28a745;
                }}
                .coverage-fill-low {{
                    background-color: #dc3545;
                }}
                .coverage-fill-medium {{
                    background-color: #ffc107;
                }}
                .target-status {{
                    padding: 10px;
                    border-radius: 6px;
                    margin: 10px 0;
                }}
                .target-achieved {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .target-not-achieved {{
                    background-color: #f8d7da;
                    color: #721c24;
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
                .file-coverage-low {{
                    background-color: #f8d7da;
                }}
                .file-coverage-medium {{
                    background-color: #fff3cd;
                }}
                .file-coverage-high {{
                    background-color: #d4edda;
                }}
                .suggestions {{
                    background-color: #d1ecf1;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .suggestions h3 {{
                    margin-top: 0;
                    color: #0c5460;
                }}
                .suggestion-item {{
                    margin: 10px 0;
                    padding-left: 20px;
                    position: relative;
                }}
                .suggestion-item:before {{
                    content: "•";
                    position: absolute;
                    left: 0;
                    color: #0c5460;
                    font-weight: bold;
                }}
                .trend-indicator {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .trend-improving {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .trend-degrading {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .trend-stable {{
                    background-color: #e9ecef;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>代码覆盖率报告</h1>
                    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>总文件数:</strong> {len(coverage_summary.file_coverage)}</p>
                </div>
                
                <div class="summary">
                    <h2>覆盖率摘要</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value">{coverage_summary.coverage_percentage:.1f}%</div>
                            <div class="summary-label">整体覆盖率</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{coverage_summary.covered_lines}</div>
                            <div class="summary-label">覆盖行数</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{coverage_summary.missed_lines}</div>
                            <div class="summary-label">未覆盖行数</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{coverage_summary.total_lines}</div>
                            <div class="summary-label">总行数</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <h3>整体覆盖率</h3>
                        <div class="coverage-bar">
                            <div class="coverage-fill {'coverage-fill-low' if coverage_summary.coverage_percentage < 60 else 'coverage-fill-medium' if coverage_summary.coverage_percentage < 80 else ''}" 
                                 style="width: {coverage_summary.coverage_percentage}%"></div>
                        </div>
                        <p>{coverage_summary.coverage_percentage:.1f}% ({coverage_summary.covered_lines}/{coverage_summary.total_lines} 行)</p>
                    </div>
                </div>
        """
        
        # 添加覆盖率目标
        html_content += """
                <h2>覆盖率目标</h2>
        """
        
        for target in self.targets:
            status_class = "target-achieved" if target.achieved else "target-not-achieved"
            status_text = "已达成" if target.achieved else "未达成"
            
            html_content += f"""
                <div class="target-status {status_class}">
                    <h3>{target.name}</h3>
                    <p><strong>目标:</strong> {target.target_percentage}%</p>
                    <p><strong>当前:</strong> {target.current_percentage:.1f}%</p>
                    <p><strong>状态:</strong> {status_text}</p>
                    <p><strong>描述:</strong> {target.description}</p>
                </div>
            """
        
        # 添加文件覆盖率详情
        html_content += """
                <h2>文件覆盖率详情</h2>
                <table>
                    <tr>
                        <th>文件路径</th>
                        <th>覆盖率</th>
                        <th>覆盖行数</th>
                        <th>总行数</th>
                        <th>未覆盖行数</th>
                    </tr>
        """
        
        # 按覆盖率排序文件
        sorted_files = sorted(coverage_summary.file_coverage.items(), 
                            key=lambda x: x[1].coverage_percentage, reverse=True)
        
        for file_path, file_cov in sorted_files:
            coverage_class = ""
            if file_cov.coverage_percentage < 60:
                coverage_class = "file-coverage-low"
            elif file_cov.coverage_percentage < 80:
                coverage_class = "file-coverage-medium"
            else:
                coverage_class = "file-coverage-high"
            
            html_content += f"""
                    <tr class="{coverage_class}">
                        <td>{file_path}</td>
                        <td>{file_cov.coverage_percentage:.1f}%</td>
                        <td>{file_cov.covered_lines}</td>
                        <td>{file_cov.total_lines}</td>
                        <td>{file_cov.missed_lines}</td>
                    </tr>
            """
        
        html_content += """
                </table>
        """
        
        # 添加趋势分析
        if trend_analysis:
            html_content += """
                <h2>覆盖率趋势分析</h2>
            """
            
            trend_direction = trend_analysis.get('trend_direction', 'stable')
            trend_class = f"trend-{trend_direction}"
            trend_text = {
                'improving': '改善',
                'degrading': '下降',
                'stable': '稳定'
            }.get(trend_direction, '未知')
            
            html_content += f"""
                <div class="trend-indicator {trend_class}">
                    趋势方向: {trend_text}
                </div>
                <p><strong>数据点数:</strong> {trend_analysis.get('data_points', 0)}</p>
                <p><strong>首次覆盖率:</strong> {trend_analysis.get('first_coverage', 0):.1f}%</p>
                <p><strong>最新覆盖率:</strong> {trend_analysis.get('latest_coverage', 0):.1f}%</p>
                <p><strong>总体变化:</strong> {trend_analysis.get('overall_change', 0):.1f}%</p>
                <p><strong>平均变化:</strong> {trend_analysis.get('avg_change', 0):.2f}%</p>
            """
        
        # 添加改进建议
        if suggestions:
            html_content += """
                <h2>改进建议</h2>
                <div class="suggestions">
                    <h3>覆盖率改进建议</h3>
            """
            
            for suggestion in suggestions:
                html_content += f'<div class="suggestion-item">{suggestion}</div>'
            
            html_content += """
                </div>
            """
        
        # 结束HTML
        html_content += """
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center;">
                    <p>SuperRPG 覆盖率报告工具</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_json_report(self, report_file: Path, coverage_summary: CoverageSummary, 
                            trend_analysis: Dict[str, Any], suggestions: List[str]) -> None:
        """生成JSON覆盖率报告"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_lines": coverage_summary.total_lines,
                "covered_lines": coverage_summary.covered_lines,
                "missed_lines": coverage_summary.missed_lines,
                "coverage_percentage": coverage_summary.coverage_percentage,
                "total_functions": coverage_summary.total_functions,
                "covered_functions": coverage_summary.covered_functions,
                "total_branches": coverage_summary.total_branches,
                "covered_branches": coverage_summary.covered_branches,
                "function_coverage": (coverage_summary.covered_functions / coverage_summary.total_functions * 100) if coverage_summary.total_functions > 0 else 0,
                "branch_coverage": (coverage_summary.covered_branches / coverage_summary.total_branches * 100) if coverage_summary.total_branches > 0 else 0
            },
            "targets": [
                {
                    "name": target.name,
                    "target_percentage": target.target_percentage,
                    "current_percentage": target.current_percentage,
                    "achieved": target.achieved,
                    "description": target.description
                }
                for target in self.targets
            ],
            "file_coverage": {
                file_path: {
                    "total_lines": file_cov.total_lines,
                    "covered_lines": file_cov.covered_lines,
                    "missed_lines": file_cov.missed_lines,
                    "coverage_percentage": file_cov.coverage_percentage
                }
                for file_path, file_cov in coverage_summary.file_coverage.items()
            },
            "trend_analysis": trend_analysis,
            "suggestions": suggestions
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    def _generate_markdown_report(self, report_file: Path, coverage_summary: CoverageSummary, 
                                trend_analysis: Dict[str, Any], suggestions: List[str]) -> None:
        """生成Markdown覆盖率报告"""
        md_content = f"""# 代码覆盖率报告

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 摘要

- **整体覆盖率:** {coverage_summary.coverage_percentage:.1f}%
- **覆盖行数:** {coverage_summary.covered_lines}
- **未覆盖行数:** {coverage_summary.missed_lines}
- **总行数:** {coverage_summary.total_lines}
- **总文件数:** {len(coverage_summary.file_coverage)}

## 覆盖率目标

"""
        
        for target in self.targets:
            status = "✅ 已达成" if target.achieved else "❌ 未达成"
            md_content += f"""### {target.name}

- **目标:** {target.target_percentage}%
- **当前:** {target.current_percentage:.1f}%
- **状态:** {status}
- **描述:** {target.description}

"""
        
        # 添加文件覆盖率详情
        md_content += """## 文件覆盖率详情

| 文件路径 | 覆盖率 | 覆盖行数 | 总行数 | 未覆盖行数 |
|---------|--------|----------|--------|------------|
"""
        
        # 按覆盖率排序文件
        sorted_files = sorted(coverage_summary.file_coverage.items(), 
                            key=lambda x: x[1].coverage_percentage, reverse=True)
        
        for file_path, file_cov in sorted_files:
            md_content += f"| {file_path} | {file_cov.coverage_percentage:.1f}% | {file_cov.covered_lines} | {file_cov.total_lines} | {file_cov.missed_lines} |\n"
        
        # 添加趋势分析
        if trend_analysis:
            md_content += """
## 覆盖率趋势分析

"""
            
            trend_direction = trend_analysis.get('trend_direction', 'stable')
            trend_text = {
                'improving': '改善',
                'degrading': '下降',
                'stable': '稳定'
            }.get(trend_direction, '未知')
            
            md_content += f"""- **趋势方向:** {trend_text}
- **数据点数:** {trend_analysis.get('data_points', 0)}
- **首次覆盖率:** {trend_analysis.get('first_coverage', 0):.1f}%
- **最新覆盖率:** {trend_analysis.get('latest_coverage', 0):.1f}%
- **总体变化:** {trend_analysis.get('overall_change', 0):.1f}%
- **平均变化:** {trend_analysis.get('avg_change', 0):.2f}%

"""
        
        # 添加改进建议
        if suggestions:
            md_content += """## 改进建议

"""
            for i, suggestion in enumerate(suggestions, 1):
                md_content += f"{i}. {suggestion}\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)


# 便捷函数

def generate_coverage_report(
    coverage_file: Union[str, Path],
    historical_dir: Optional[Union[str, Path]] = None,
    output_dir: str = "coverage_reports",
    report_format: str = "html"
) -> Path:
    """
    生成覆盖率报告的便捷函数
    
    Args:
        coverage_file: 覆盖率文件路径
        historical_dir: 历史数据目录
        output_dir: 输出目录
        report_format: 报告格式
        
    Returns:
        报告文件路径
    """
    generator = CoverageReportGenerator(output_dir)
    
    # 加载历史数据
    if historical_dir:
        generator.load_historical_coverage(Path(historical_dir))
    
    # 解析覆盖率文件
    coverage_path = Path(coverage_file)
    if coverage_path.suffix == '.xml':
        coverage_summary = generator.parse_coverage_xml(coverage_path)
    elif coverage_path.suffix == '.json':
        coverage_summary = generator.parse_coverage_json(coverage_path)
    else:
        raise ValueError(f"不支持的覆盖率文件格式: {coverage_path.suffix}")
    
    # 生成报告
    return generator.generate_report(coverage_summary, report_format)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python coverage_report_generator.py <coverage_file> [historical_dir] [output_dir]")
        sys.exit(1)
    
    coverage_file = sys.argv[1]
    historical_dir = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "coverage_reports"
    
    try:
        report_file = generate_coverage_report(coverage_file, historical_dir, output_dir)
        print(f"覆盖率报告已生成: {report_file}")
        
        # 显示摘要
        generator = CoverageReportGenerator(output_dir)
        
        if historical_dir:
            generator.load_historical_coverage(Path(historical_dir))
        
        coverage_path = Path(coverage_file)
        if coverage_path.suffix == '.xml':
            coverage_summary = generator.parse_coverage_xml(coverage_path)
        else:
            coverage_summary = generator.parse_coverage_json(coverage_path)
        
        print(f"整体覆盖率: {coverage_summary.coverage_percentage:.1f}%")
        print(f"覆盖行数: {coverage_summary.covered_lines}/{coverage_summary.total_lines}")
        
        # 显示目标状态
        for target in generator.targets:
            status = "已达成" if target.achieved else "未达成"
            print(f"{target.name}: {target.current_percentage:.1f}% ({status})")
        
    except Exception as e:
        print(f"生成覆盖率报告时出错: {str(e)}")
        sys.exit(1)