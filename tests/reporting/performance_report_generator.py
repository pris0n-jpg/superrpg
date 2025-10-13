"""
性能报告生成器

负责生成详细的性能测试报告，包括：
- 性能指标分析
- 性能趋势图表
- 性能回归检测
- 性能基准对比
- 性能优化建议
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
import statistics
import math

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd
    import numpy
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


@dataclass
class PerformanceBenchmark:
    """性能基准"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """性能阈值"""
    name: str
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str = ""


@dataclass
class PerformanceRegression:
    """性能回归"""
    benchmark_name: str
    current_value: float
    baseline_value: float
    change_percent: float
    severity: str  # minor, major, critical
    description: str = ""


@dataclass
class PerformanceTrend:
    """性能趋势"""
    benchmark_name: str
    values: List[float]
    timestamps: List[datetime]
    trend_direction: str  # improving, degrading, stable
    trend_slope: float
    confidence: float


class PerformanceReportGenerator:
    """性能报告生成器"""
    
    def __init__(self, output_dir: str = "performance_reports"):
        """
        初始化性能报告生成器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.benchmarks: List[PerformanceBenchmark] = []
        self.thresholds: List[PerformanceThreshold] = []
        self.regressions: List[PerformanceRegression] = []
        self.trends: Dict[str, PerformanceTrend] = {}
        
        # 默认性能阈值
        self._init_default_thresholds()
    
    def _init_default_thresholds(self) -> None:
        """初始化默认性能阈值"""
        self.thresholds = [
            PerformanceThreshold(
                name="response_time",
                warning_threshold=500.0,  # 500ms
                critical_threshold=1000.0,  # 1000ms
                unit="ms",
                description="API响应时间"
            ),
            PerformanceThreshold(
                name="throughput",
                warning_threshold=100.0,  # 100 req/s
                critical_threshold=50.0,   # 50 req/s
                unit="req/s",
                description="API吞吐量"
            ),
            PerformanceThreshold(
                name="cpu_usage",
                warning_threshold=70.0,    # 70%
                critical_threshold=90.0,   # 90%
                unit="%",
                description="CPU使用率"
            ),
            PerformanceThreshold(
                name="memory_usage",
                warning_threshold=80.0,    # 80%
                critical_threshold=95.0,   # 95%
                unit="%",
                description="内存使用率"
            ),
            PerformanceThreshold(
                name="error_rate",
                warning_threshold=1.0,     # 1%
                critical_threshold=5.0,     # 5%
                unit="%",
                description="错误率"
            )
        ]
    
    def add_benchmark(self, benchmark: PerformanceBenchmark) -> None:
        """
        添加性能基准
        
        Args:
            benchmark: 性能基准
        """
        self.benchmarks.append(benchmark)
    
    def add_threshold(self, threshold: PerformanceThreshold) -> None:
        """
        添加性能阈值
        
        Args:
            threshold: 性能阈值
        """
        self.thresholds.append(threshold)
    
    def load_benchmarks_from_json(self, json_file: Path) -> None:
        """
        从JSON文件加载性能基准
        
        Args:
            json_file: JSON文件路径
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        benchmarks = data.get('benchmarks', [])
        
        for benchmark_data in benchmarks:
            benchmark = PerformanceBenchmark(
                name=benchmark_data.get('name', ''),
                value=benchmark_data.get('value', 0.0),
                unit=benchmark_data.get('unit', ''),
                timestamp=datetime.fromisoformat(benchmark_data.get('timestamp', datetime.now().isoformat())),
                metadata=benchmark_data.get('metadata', {})
            )
            
            self.add_benchmark(benchmark)
    
    def load_historical_data(self, historical_dir: Path) -> None:
        """
        加载历史性能数据
        
        Args:
            historical_dir: 历史数据目录
        """
        if not historical_dir.exists():
            return
        
        for json_file in historical_dir.glob("*.json"):
            try:
                self.load_benchmarks_from_json(json_file)
            except Exception as e:
                print(f"加载历史数据失败 {json_file}: {str(e)}")
    
    def detect_regressions(self, baseline_window_days: int = 7) -> List[PerformanceRegression]:
        """
        检测性能回归
        
        Args:
            baseline_window_days: 基线时间窗口（天）
            
        Returns:
            检测到的性能回归列表
        """
        self.regressions.clear()
        
        # 按基准名称分组
        benchmarks_by_name = {}
        for benchmark in self.benchmarks:
            if benchmark.name not in benchmarks_by_name:
                benchmarks_by_name[benchmark.name] = []
            benchmarks_by_name[benchmark.name].append(benchmark)
        
        # 对每个基准检测回归
        for name, benchmarks in benchmarks_by_name.items():
            if len(benchmarks) < 2:
                continue
            
            # 按时间排序
            benchmarks.sort(key=lambda x: x.timestamp)
            
            # 获取最新的基准
            latest = benchmarks[-1]
            
            # 计算基线值（过去N天的平均值）
            baseline_cutoff = latest.timestamp - timedelta(days=baseline_window_days)
            baseline_benchmarks = [b for b in benchmarks[:-1] if b.timestamp >= baseline_cutoff]
            
            if not baseline_benchmarks:
                continue
            
            baseline_values = [b.value for b in baseline_benchmarks]
            baseline_value = statistics.mean(baseline_values)
            
            # 计算变化百分比
            change_percent = ((latest.value - baseline_value) / baseline_value) * 100 if baseline_value > 0 else 0
            
            # 确定回归严重程度
            severity = "minor"
            if abs(change_percent) > 20:
                severity = "major"
            if abs(change_percent) > 50:
                severity = "critical"
            
            # 判断是否为回归（性能下降）
            if change_percent > 10:  # 性能下降超过10%
                regression = PerformanceRegression(
                    benchmark_name=name,
                    current_value=latest.value,
                    baseline_value=baseline_value,
                    change_percent=change_percent,
                    severity=severity,
                    description=f"{name}性能下降{change_percent:.2f}%，从{baseline_value:.2f}到{latest.value:.2f}"
                )
                
                self.regressions.append(regression)
        
        return self.regressions
    
    def analyze_trends(self, min_data_points: int = 5) -> Dict[str, PerformanceTrend]:
        """
        分析性能趋势
        
        Args:
            min_data_points: 最少数据点数量
            
        Returns:
            性能趋势字典
        """
        self.trends.clear()
        
        # 按基准名称分组
        benchmarks_by_name = {}
        for benchmark in self.benchmarks:
            if benchmark.name not in benchmarks_by_name:
                benchmarks_by_name[benchmark.name] = []
            benchmarks_by_name[benchmark.name].append(benchmark)
        
        # 对每个基准分析趋势
        for name, benchmarks in benchmarks_by_name.items():
            if len(benchmarks) < min_data_points:
                continue
            
            # 按时间排序
            benchmarks.sort(key=lambda x: x.timestamp)
            
            # 提取值和时间戳
            values = [b.value for b in benchmarks]
            timestamps = [b.timestamp for b in benchmarks]
            
            # 转换时间戳为数值（用于线性回归）
            timestamp_numbers = [(t - timestamps[0]).total_seconds() for t in timestamps]
            
            # 计算线性回归
            if len(timestamp_numbers) > 1:
                slope, intercept, r_value, p_value, std_err = self._linear_regression(
                    timestamp_numbers, values
                )
                
                # 确定趋势方向
                if abs(slope) < 0.001:  # 非常小的斜率认为是稳定
                    trend_direction = "stable"
                elif slope > 0:
                    trend_direction = "degrading"  # 值增加表示性能下降
                else:
                    trend_direction = "improving"  # 值减少表示性能提升
                
                # 计算置信度（基于R²值）
                confidence = r_value ** 2
                
                trend = PerformanceTrend(
                    benchmark_name=name,
                    values=values,
                    timestamps=timestamps,
                    trend_direction=trend_direction,
                    trend_slope=slope,
                    confidence=confidence
                )
                
                self.trends[name] = trend
        
        return self.trends
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float, float, float]:
        """
        计算线性回归
        
        Args:
            x: 自变量列表
            y: 因变量列表
            
        Returns:
            (斜率, 截距, R值, P值, 标准误差)
        """
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        
        # 计算均值
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        # 计算斜率和截距
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, y_mean, 0.0, 0.0, 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 计算R值
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_value = 0.0
        if ss_tot > 0:
            r_value = 1 - (ss_res / ss_tot)
            r_value = math.sqrt(max(0, r_value))
        
        # 简化的P值和标准误差计算
        p_value = 0.05  # 默认值
        std_err = math.sqrt(ss_res / (n - 2)) if n > 2 else 0.0
        
        return slope, intercept, r_value, p_value, std_err
    
    def generate_charts(self, chart_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        生成性能图表
        
        Args:
            chart_dir: 图表输出目录
            
        Returns:
            图表文件路径字典
        """
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib未安装，跳过图表生成")
            return {}
        
        if chart_dir is None:
            chart_dir = self.output_dir / "charts"
        
        chart_dir.mkdir(exist_ok=True)
        chart_files = {}
        
        # 按基准名称分组
        benchmarks_by_name = {}
        for benchmark in self.benchmarks:
            if benchmark.name not in benchmarks_by_name:
                benchmarks_by_name[benchmark.name] = []
            benchmarks_by_name[benchmark.name].append(benchmark)
        
        # 为每个基准生成趋势图
        for name, benchmarks in benchmarks_by_name.items():
            if len(benchmarks) < 2:
                continue
            
            # 按时间排序
            benchmarks.sort(key=lambda x: x.timestamp)
            
            timestamps = [b.timestamp for b in benchmarks]
            values = [b.value for b in benchmarks]
            unit = benchmarks[0].unit
            
            # 创建图表
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, values, 'b-o', linewidth=2, markersize=4)
            
            # 添加趋势线
            if name in self.trends:
                trend = self.trends[name]
                x_numeric = mdates.date2num(timestamps)
                z = numpy.polyfit(x_numeric, values, 1)
                p = numpy.poly1d(z)
                plt.plot(timestamps, p(x_numeric), "r--", alpha=0.7, label=f"趋势 ({trend.trend_direction})")
                plt.legend()
            
            # 设置标题和标签
            plt.title(f"{name} 性能趋势")
            plt.xlabel("时间")
            plt.ylabel(f"值 ({unit})")
            plt.grid(True, alpha=0.3)
            
            # 格式化x轴
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.gcf().autofmt_xdate()
            
            # 添加阈值线
            for threshold in self.thresholds:
                if threshold.name == name:
                    plt.axhline(y=threshold.warning_threshold, color='orange', 
                               linestyle='--', alpha=0.7, label=f"警告阈值 ({threshold.warning_threshold})")
                    plt.axhline(y=threshold.critical_threshold, color='red', 
                               linestyle='--', alpha=0.7, label=f"严重阈值 ({threshold.critical_threshold})")
                    plt.legend()
                    break
            
            plt.tight_layout()
            
            # 保存图表
            chart_file = chart_dir / f"{name}_trend.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            chart_files[name] = chart_file
        
        return chart_files
    
    def generate_report(self, report_format: str = "html") -> Path:
        """
        生成性能报告
        
        Args:
            report_format: 报告格式 (html, json, markdown)
            
        Returns:
            报告文件路径
        """
        # 检测回归
        self.detect_regressions()
        
        # 分析趋势
        self.analyze_trends()
        
        # 生成图表
        chart_files = self.generate_charts()
        
        # 根据格式生成报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if report_format == "html":
            report_file = self.output_dir / f"performance_report_{timestamp}.html"
            self._generate_html_report(report_file, chart_files)
        elif report_format == "json":
            report_file = self.output_dir / f"performance_report_{timestamp}.json"
            self._generate_json_report(report_file)
        elif report_format == "markdown":
            report_file = self.output_dir / f"performance_report_{timestamp}.md"
            self._generate_markdown_report(report_file, chart_files)
        else:
            raise ValueError(f"不支持的报告格式: {report_format}")
        
        return report_file
    
    def _generate_html_report(self, report_file: Path, chart_files: Dict[str, Path]) -> None:
        """生成HTML性能报告"""
        # 按基准名称分组
        benchmarks_by_name = {}
        for benchmark in self.benchmarks:
            if benchmark.name not in benchmarks_by_name:
                benchmarks_by_name[benchmark.name] = []
            benchmarks_by_name[benchmark.name].append(benchmark)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>性能测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
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
                .regression {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 15px 0;
                    border-left: 4px solid #dc3545;
                }}
                .regression-major {{
                    border-left-color: #fd7e14;
                    background-color: #fff3cd;
                    color: #856404;
                }}
                .regression-critical {{
                    border-left-color: #dc3545;
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .trend-improving {{
                    color: #28a745;
                }}
                .trend-degrading {{
                    color: #dc3545;
                }}
                .trend-stable {{
                    color: #6c757d;
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
                .chart-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .benchmark-card {{
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    margin: 20px 0;
                    overflow: hidden;
                }}
                .benchmark-header {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-bottom: 1px solid #ddd;
                }}
                .benchmark-content {{
                    padding: 15px;
                }}
                .metric-value {{
                    font-size: 1.2em;
                    font-weight: bold;
                }}
                .trend-indicator {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.9em;
                    font-weight: bold;
                }}
                .trend-good {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .trend-warning {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                .trend-bad {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .recommendations {{
                    background-color: #d1ecf1;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .recommendations h3 {{
                    margin-top: 0;
                    color: #0c5460;
                }}
                .recommendation-item {{
                    margin: 10px 0;
                    padding-left: 20px;
                    position: relative;
                }}
                .recommendation-item:before {{
                    content: "•";
                    position: absolute;
                    left: 0;
                    color: #0c5460;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>性能测试报告</h1>
                    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>测试基准数:</strong> {len(benchmarks_by_name)}</p>
                    <p><strong>总数据点:</strong> {len(self.benchmarks)}</p>
                </div>
                
                <div class="summary">
                    <h2>性能摘要</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value">{len(self.regressions)}</div>
                            <div class="summary-label">检测到的回归</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{len([t for t in self.trends.values() if t.trend_direction == 'degrading'])}</div>
                            <div class="summary-label">性能下降趋势</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{len([t for t in self.trends.values() if t.trend_direction == 'improving'])}</div>
                            <div class="summary-label">性能提升趋势</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{len([t for t in self.trends.values() if t.trend_direction == 'stable'])}</div>
                            <div class="summary-label">稳定趋势</div>
                        </div>
                    </div>
                </div>
        """
        
        # 添加性能回归部分
        if self.regressions:
            html_content += """
                <h2>性能回归</h2>
            """
            
            for regression in self.regressions:
                severity_class = f"regression-{regression.severity}"
                html_content += f"""
                    <div class="regression {severity_class}">
                        <h4>{regression.benchmark_name}</h4>
                        <p><strong>严重程度:</strong> {regression.severity.upper()}</p>
                        <p><strong>变化:</strong> {regression.change_percent:.2f}%</p>
                        <p><strong>基线值:</strong> {regression.baseline_value:.2f}</p>
                        <p><strong>当前值:</strong> {regression.current_value:.2f}</p>
                        <p><strong>描述:</strong> {regression.description}</p>
                    </div>
                """
        
        # 添加性能趋势部分
        if self.trends:
            html_content += """
                <h2>性能趋势分析</h2>
            """
            
            for name, trend in self.trends.items():
                trend_class = f"trend-{trend.trend_direction}"
                trend_text = {
                    "improving": "改善",
                    "degrading": "下降",
                    "stable": "稳定"
                }.get(trend.trend_direction, "未知")
                
                html_content += f"""
                    <div class="benchmark-card">
                        <div class="benchmark-header">
                            <h3>{name} <span class="{trend_class}">({trend_text})</span></h3>
                            <p>数据点: {len(trend.values)} | 置信度: {trend.confidence:.2f}</p>
                        </div>
                        <div class="benchmark-content">
                            <p><strong>趋势斜率:</strong> {trend.trend_slope:.6f}</p>
                            <p><strong>最新值:</strong> <span class="metric-value">{trend.values[-1]:.2f}</span></p>
                            <p><strong>平均值:</strong> {statistics.mean(trend.values):.2f}</p>
                            <p><strong>最小值:</strong> {min(trend.values):.2f}</p>
                            <p><strong>最大值:</strong> {max(trend.values):.2f}</p>
                        </div>
                    </div>
                """
        
        # 添加图表
        if chart_files:
            html_content += """
                <h2>性能图表</h2>
            """
            
            for name, chart_file in chart_files.items():
                html_content += f"""
                    <div class="chart-container">
                        <h3>{name} 趋势图</h3>
                        <img src="charts/{chart_file.name}" alt="{name} 趋势图">
                    </div>
                """
        
        # 添加性能建议
        html_content += self._generate_recommendations_html()
        
        html_content += """
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center;">
                    <p>SuperRPG 性能测试工具</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_json_report(self, report_file: Path) -> None:
        """生成JSON性能报告"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": [
                {
                    "name": b.name,
                    "value": b.value,
                    "unit": b.unit,
                    "timestamp": b.timestamp.isoformat(),
                    "metadata": b.metadata
                }
                for b in self.benchmarks
            ],
            "thresholds": [
                {
                    "name": t.name,
                    "warning_threshold": t.warning_threshold,
                    "critical_threshold": t.critical_threshold,
                    "unit": t.unit,
                    "description": t.description
                }
                for t in self.thresholds
            ],
            "regressions": [
                {
                    "benchmark_name": r.benchmark_name,
                    "current_value": r.current_value,
                    "baseline_value": r.baseline_value,
                    "change_percent": r.change_percent,
                    "severity": r.severity,
                    "description": r.description
                }
                for r in self.regressions
            ],
            "trends": {
                name: {
                    "benchmark_name": t.benchmark_name,
                    "trend_direction": t.trend_direction,
                    "trend_slope": t.trend_slope,
                    "confidence": t.confidence,
                    "values": t.values,
                    "timestamps": [ts.isoformat() for ts in t.timestamps]
                }
                for name, t in self.trends.items()
            },
            "recommendations": self._generate_recommendations()
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    def _generate_markdown_report(self, report_file: Path, chart_files: Dict[str, Path]) -> None:
        """生成Markdown性能报告"""
        md_content = f"""# 性能测试报告

**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 摘要

- 测试基准数: {len(self.benchmarks)}
- 检测到的回归: {len(self.regressions)}
- 性能下降趋势: {len([t for t in self.trends.values() if t.trend_direction == 'degrading'])}
- 性能提升趋势: {len([t for t in self.trends.values() if t.trend_direction == 'improving'])}
- 稳定趋势: {len([t for t in self.trends.values() if t.trend_direction == 'stable'])}

"""
        
        # 添加性能回归
        if self.regressions:
            md_content += "## 性能回归\n\n"
            
            for regression in self.regressions:
                md_content += f"""### {regression.benchmark_name}

- **严重程度:** {regression.severity.upper()}
- **变化:** {regression.change_percent:.2f}%
- **基线值:** {regression.baseline_value:.2f}
- **当前值:** {regression.current_value:.2f}
- **描述:** {regression.description}

"""
        
        # 添加性能趋势
        if self.trends:
            md_content += "## 性能趋势分析\n\n"
            
            for name, trend in self.trends.items():
                trend_text = {
                    "improving": "改善",
                    "degrading": "下降",
                    "stable": "稳定"
                }.get(trend.trend_direction, "未知")
                
                md_content += f"""### {name}

- **趋势:** {trend_text}
- **数据点:** {len(trend.values)}
- **置信度:** {trend.confidence:.2f}
- **趋势斜率:** {trend.trend_slope:.6f}
- **最新值:** {trend.values[-1]:.2f}
- **平均值:** {statistics.mean(trend.values):.2f}
- **最小值:** {min(trend.values):.2f}
- **最大值:** {max(trend.values):.2f}

"""
        
        # 添加图表
        if chart_files:
            md_content += "## 性能图表\n\n"
            
            for name, chart_file in chart_files.items():
                md_content += f"### {name} 趋势图\n\n"
                md_content += f"![{name} 趋势图](charts/{chart_file.name})\n\n"
        
        # 添加建议
        recommendations = self._generate_recommendations()
        if recommendations:
            md_content += "## 性能优化建议\n\n"
            
            for i, recommendation in enumerate(recommendations, 1):
                md_content += f"{i}. {recommendation}\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 基于回归的建议
        if self.regressions:
            critical_regressions = [r for r in self.regressions if r.severity == "critical"]
            major_regressions = [r for r in self.regressions if r.severity == "major"]
            
            if critical_regressions:
                recommendations.append(f"紧急处理 {len(critical_regressions)} 个严重性能回归，这些回归可能严重影响用户体验")
            
            if major_regressions:
                recommendations.append(f"优先处理 {len(major_regressions)} 个主要性能回归，防止问题进一步恶化")
        
        # 基于趋势的建议
        degrading_trends = [t for t in self.trends.values() if t.trend_direction == "degrading" and t.confidence > 0.7]
        
        if degrading_trends:
            recommendations.append(f"监控 {len(degrading_trends)} 个性能下降趋势，这些指标可能在未来变成问题")
        
        # 基于阈值的建议
        latest_benchmarks = {}
        for benchmark in self.benchmarks:
            if benchmark.name not in latest_benchmarks or benchmark.timestamp > latest_benchmarks[benchmark.name].timestamp:
                latest_benchmarks[benchmark.name] = benchmark
        
        for name, benchmark in latest_benchmarks.items():
            for threshold in self.thresholds:
                if threshold.name == name:
                    if benchmark.value >= threshold.critical_threshold:
                        recommendations.append(f"{name} 已超过严重阈值 ({threshold.critical_threshold}{threshold.unit})，需要立即优化")
                    elif benchmark.value >= threshold.warning_threshold:
                        recommendations.append(f"{name} 接近警告阈值 ({threshold.warning_threshold}{threshold.unit})，建议关注")
        
        # 通用建议
        if not recommendations:
            recommendations.append("当前性能表现良好，建议继续监控性能指标")
        else:
            recommendations.append("建议定期运行性能测试，建立性能基线，及时发现性能问题")
            recommendations.append("考虑将性能测试集成到CI/CD流程中，实现自动化性能监控")
        
        return recommendations
    
    def _generate_recommendations_html(self) -> str:
        """生成HTML格式的建议"""
        recommendations = self._generate_recommendations()
        
        if not recommendations:
            return ""
        
        html = """
            <div class="recommendations">
                <h3>性能优化建议</h3>
        """
        
        for recommendation in recommendations:
            html += f'<div class="recommendation-item">{recommendation}</div>'
        
        html += """
            </div>
        """
        
        return html


# 便捷函数

def generate_performance_report(
    benchmark_file: Union[str, Path],
    historical_dir: Optional[Union[str, Path]] = None,
    output_dir: str = "performance_reports",
    report_format: str = "html"
) -> Path:
    """
    生成性能报告的便捷函数
    
    Args:
        benchmark_file: 基准测试文件路径
        historical_dir: 历史数据目录
        output_dir: 输出目录
        report_format: 报告格式
        
    Returns:
        报告文件路径
    """
    generator = PerformanceReportGenerator(output_dir)
    
    # 加载基准数据
    generator.load_benchmarks_from_json(Path(benchmark_file))
    
    # 加载历史数据
    if historical_dir:
        generator.load_historical_data(Path(historical_dir))
    
    # 生成报告
    return generator.generate_report(report_format)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python performance_report_generator.py <benchmark_file> [historical_dir] [output_dir]")
        sys.exit(1)
    
    benchmark_file = sys.argv[1]
    historical_dir = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "performance_reports"
    
    try:
        report_file = generate_performance_report(benchmark_file, historical_dir, output_dir)
        print(f"性能报告已生成: {report_file}")
        
        # 显示摘要
        generator = PerformanceReportGenerator(output_dir)
        generator.load_benchmarks_from_json(Path(benchmark_file))
        
        if historical_dir:
            generator.load_historical_data(Path(historical_dir))
        
        regressions = generator.detect_regressions()
        trends = generator.analyze_trends()
        
        print(f"检测到 {len(regressions)} 个性能回归")
        print(f"分析出 {len(trends)} 个性能趋势")
        
    except Exception as e:
        print(f"生成性能报告时出错: {str(e)}")
        sys.exit(1)