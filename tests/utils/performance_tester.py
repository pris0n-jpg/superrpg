"""
性能测试工具

提供用于性能测试的工具和框架，包括：
- 负载测试
- 压力测试
- 并发测试
- 性能基准测试
- 性能指标收集和分析
"""

import time
import asyncio
import statistics
import threading
import concurrent.futures
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import csv
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from tests.utils.api_test_client import APITestClient, TestConfig, TestResult


@dataclass
class PerformanceTestConfig:
    """性能测试配置"""
    name: str
    description: str
    duration: int = 60  # 测试持续时间（秒）
    concurrent_users: int = 10  # 并发用户数
    ramp_up_time: int = 10  # 启动时间（秒）
    think_time: float = 1.0  # 思考时间（秒）
    requests_per_second: Optional[int] = None  # 每秒请求数限制
    timeout: int = 30  # 请求超时时间
    warmup_time: int = 10  # 预热时间（秒）
    cooldown_time: int = 10  # 冷却时间（秒）
    target_url: str = "http://localhost:3010"
    api_version: str = "v1"
    output_dir: str = "performance_results"


@dataclass
class PerformanceMetrics:
    """性能指标"""
    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors_per_second: float
    throughput: float
    error_rate: float
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_io: Optional[Dict[str, float]] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestResult:
    """请求结果"""
    timestamp: datetime
    success: bool
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    request_size: int = 0
    response_size: int = 0


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self, config: PerformanceTestConfig):
        """
        初始化性能测试器
        
        Args:
            config: 性能测试配置
        """
        self.config = config
        self.results: List[RequestResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_running = False
        self.workers: List[threading.Thread] = []
        
        # 创建输出目录
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
    
    def run_test(self, test_function: Callable) -> PerformanceMetrics:
        """
        运行性能测试
        
        Args:
            test_function: 测试函数
            
        Returns:
            性能指标
        """
        print(f"开始性能测试: {self.config.name}")
        print(f"描述: {self.config.description}")
        print(f"持续时间: {self.config.duration}秒")
        print(f"并发用户数: {self.config.concurrent_users}")
        print(f"目标URL: {self.config.target_url}")
        
        # 重置结果
        self.results.clear()
        
        # 预热
        if self.config.warmup_time > 0:
            print(f"预热 {self.config.warmup_time} 秒...")
            self._warmup(test_function)
        
        # 启动性能监控
        self.performance_monitor.start()
        
        # 记录开始时间
        self.start_time = datetime.now()
        self.is_running = True
        
        # 启动工作线程
        self._start_workers(test_function)
        
        # 等待测试完成
        self._wait_for_completion()
        
        # 记录结束时间
        self.end_time = datetime.now()
        self.is_running = False
        
        # 停止性能监控
        self.performance_monitor.stop()
        
        # 冷却
        if self.config.cooldown_time > 0:
            print(f"冷却 {self.config.cooldown_time} 秒...")
            time.sleep(self.config.cooldown_time)
        
        # 计算性能指标
        metrics = self._calculate_metrics()
        
        # 保存结果
        self._save_results(metrics)
        
        # 生成报告
        self._generate_report(metrics)
        
        print(f"性能测试完成: {self.config.name}")
        print(f"总请求数: {metrics.total_requests}")
        print(f"成功率: {100 - metrics.error_rate:.2f}%")
        print(f"平均响应时间: {metrics.avg_response_time:.2f}ms")
        print(f"吞吐量: {metrics.requests_per_second:.2f} req/s")
        
        return metrics
    
    def _warmup(self, test_function: Callable) -> None:
        """
        预热系统
        
        Args:
            test_function: 测试函数
        """
        warmup_end = time.time() + self.config.warmup_time
        
        # 使用少量并发进行预热
        with ThreadPoolExecutor(max_workers=3) as executor:
            while time.time() < warmup_end:
                futures = [executor.submit(test_function) for _ in range(3)]
                
                # 等待完成
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass  # 预热期间的错误忽略
                
                time.sleep(0.5)
    
    def _start_workers(self, test_function: Callable) -> None:
        """
        启动工作线程
        
        Args:
            test_function: 测试函数
        """
        def worker(worker_id: int) -> None:
            """工作线程函数"""
            # 计算启动延迟（实现渐进式启动）
            delay = (worker_id / self.config.concurrent_users) * self.config.ramp_up_time
            time.sleep(delay)
            
            test_client = APITestClient(TestConfig(
                base_url=self.config.target_url,
                api_version=self.config.api_version,
                timeout=self.config.timeout
            ))
            
            try:
                while self.is_running:
                    request_start = time.time()
                    
                    try:
                        # 执行测试函数
                        result = test_function(test_client)
                        
                        # 记录请求结果
                        request_result = RequestResult(
                            timestamp=datetime.now(),
                            success=result.success,
                            response_time=result.response_time * 1000,  # 转换为毫秒
                            status_code=result.status_code,
                            error_message=result.error_message
                        )
                        
                        self.results.append(request_result)
                        
                    except Exception as e:
                        # 记录错误结果
                        request_result = RequestResult(
                            timestamp=datetime.now(),
                            success=False,
                            response_time=(time.time() - request_start) * 1000,
                            status_code=0,
                            error_message=str(e)
                        )
                        
                        self.results.append(request_result)
                    
                    # 思考时间
                    if self.config.think_time > 0:
                        time.sleep(self.config.think_time)
                    
                    # 请求速率限制
                    if self.config.requests_per_second:
                        interval = 1.0 / self.config.requests_per_second
                        elapsed = time.time() - request_start
                        if elapsed < interval:
                            time.sleep(interval - elapsed)
            
            finally:
                test_client.close()
        
        # 创建并启动工作线程
        for i in range(self.config.concurrent_users):
            worker_thread = threading.Thread(target=worker, args=(i,))
            worker_thread.daemon = True
            worker_thread.start()
            self.workers.append(worker_thread)
    
    def _wait_for_completion(self) -> None:
        """等待测试完成"""
        end_time = time.time() + self.config.duration
        
        while time.time() < end_time:
            time.sleep(1)
        
        # 停止测试
        self.is_running = False
        
        # 等待所有工作线程完成
        for worker in self.workers:
            worker.join(timeout=5)
    
    def _calculate_metrics(self) -> PerformanceMetrics:
        """
        计算性能指标
        
        Returns:
            性能指标
        """
        if not self.results:
            raise ValueError("没有测试结果可用于计算指标")
        
        # 基本统计
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r.success])
        failed_requests = total_requests - successful_requests
        
        response_times = [r.response_time for r in self.results if r.success]
        
        if not response_times:
            # 如果没有成功请求，使用所有响应时间
            response_times = [r.response_time for r in self.results]
        
        # 响应时间统计
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # 百分位数
        sorted_times = sorted(response_times)
        p50_response_time = sorted_times[int(len(sorted_times) * 0.5)]
        p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
        p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        # 计算测试持续时间
        test_duration = (self.end_time - self.start_time).total_seconds()
        
        # 吞吐量
        requests_per_second = total_requests / test_duration if test_duration > 0 else 0
        errors_per_second = failed_requests / test_duration if test_duration > 0 else 0
        
        # 错误率
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 获取系统资源使用情况
        system_metrics = self.performance_monitor.get_metrics()
        
        return PerformanceMetrics(
            test_name=self.config.name,
            start_time=self.start_time,
            end_time=self.end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            errors_per_second=errors_per_second,
            throughput=requests_per_second,  # 吞吐量等于每秒请求数
            error_rate=error_rate,
            cpu_usage=system_metrics.get("cpu_usage"),
            memory_usage=system_metrics.get("memory_usage"),
            network_io=system_metrics.get("network_io"),
            custom_metrics=system_metrics.get("custom_metrics", {})
        )
    
    def _save_results(self, metrics: PerformanceMetrics) -> None:
        """
        保存测试结果
        
        Args:
            metrics: 性能指标
        """
        # 保存原始结果
        results_file = self.output_dir / f"{self.config.name}_raw_results.json"
        
        raw_results = {
            "test_config": {
                "name": self.config.name,
                "description": self.config.description,
                "duration": self.config.duration,
                "concurrent_users": self.config.concurrent_users,
                "ramp_up_time": self.config.ramp_up_time,
                "think_time": self.config.think_time,
                "requests_per_second": self.config.requests_per_second,
                "target_url": self.config.target_url
            },
            "metrics": {
                "test_name": metrics.test_name,
                "start_time": metrics.start_time.isoformat(),
                "end_time": metrics.end_time.isoformat(),
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "avg_response_time": metrics.avg_response_time,
                "min_response_time": metrics.min_response_time,
                "max_response_time": metrics.max_response_time,
                "p50_response_time": metrics.p50_response_time,
                "p95_response_time": metrics.p95_response_time,
                "p99_response_time": metrics.p99_response_time,
                "requests_per_second": metrics.requests_per_second,
                "errors_per_second": metrics.errors_per_second,
                "throughput": metrics.throughput,
                "error_rate": metrics.error_rate,
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "network_io": metrics.network_io,
                "custom_metrics": metrics.custom_metrics
            },
            "raw_results": [
                {
                    "timestamp": result.timestamp.isoformat(),
                    "success": result.success,
                    "response_time": result.response_time,
                    "status_code": result.status_code,
                    "error_message": result.error_message
                }
                for result in self.results
            ]
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(raw_results, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式的结果
        csv_file = self.output_dir / f"{self.config.name}_results.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "success", "response_time", "status_code", "error_message"
            ])
            
            for result in self.results:
                writer.writerow([
                    result.timestamp.isoformat(),
                    result.success,
                    result.response_time,
                    result.status_code,
                    result.error_message or ""
                ])
        
        print(f"测试结果已保存到: {results_file}")
        print(f"CSV结果已保存到: {csv_file}")
    
    def _generate_report(self, metrics: PerformanceMetrics) -> None:
        """
        生成性能测试报告
        
        Args:
            metrics: 性能指标
        """
        # 创建图表
        self._create_charts(metrics)
        
        # 生成HTML报告
        self._create_html_report(metrics)
    
    def _create_charts(self, metrics: PerformanceMetrics) -> None:
        """
        创建性能图表
        
        Args:
            metrics: 性能指标
        """
        try:
            # 响应时间分布图
            plt.figure(figsize=(12, 8))
            
            # 子图1: 响应时间趋势
            plt.subplot(2, 2, 1)
            timestamps = [r.timestamp for r in self.results]
            response_times = [r.response_time for r in self.results]
            
            plt.plot(timestamps, response_times, 'b-', alpha=0.7)
            plt.title('响应时间趋势')
            plt.xlabel('时间')
            plt.ylabel('响应时间 (ms)')
            plt.grid(True)
            
            # 子图2: 响应时间分布直方图
            plt.subplot(2, 2, 2)
            plt.hist(response_times, bins=50, alpha=0.7, color='blue')
            plt.title('响应时间分布')
            plt.xlabel('响应时间 (ms)')
            plt.ylabel('频次')
            plt.grid(True)
            
            # 子图3: 成功率饼图
            plt.subplot(2, 2, 3)
            success_count = metrics.successful_requests
            failure_count = metrics.failed_requests
            
            plt.pie([success_count, failure_count], 
                   labels=['成功', '失败'],
                   colors=['green', 'red'],
                   autopct='%1.1f%%')
            plt.title('请求成功率')
            
            # 子图4: 每秒请求数
            plt.subplot(2, 2, 4)
            
            # 计算每秒请求数
            time_buckets = {}
            for result in self.results:
                second = result.timestamp.replace(microsecond=0)
                if second not in time_buckets:
                    time_buckets[second] = {"total": 0, "success": 0}
                
                time_buckets[second]["total"] += 1
                if result.success:
                    time_buckets[second]["success"] += 1
            
            seconds = sorted(time_buckets.keys())
            total_rps = [time_buckets[s]["total"] for s in seconds]
            success_rps = [time_buckets[s]["success"] for s in seconds]
            
            plt.plot(seconds, total_rps, 'b-', label='总请求')
            plt.plot(seconds, success_rps, 'g-', label='成功请求')
            plt.title('每秒请求数')
            plt.xlabel('时间')
            plt.ylabel('请求数')
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
            
            # 保存图表
            chart_file = self.output_dir / f"{self.config.name}_charts.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"性能图表已保存到: {chart_file}")
            
        except ImportError:
            print("matplotlib未安装，跳过图表生成")
        except Exception as e:
            print(f"生成图表时出错: {str(e)}")
    
    def _create_html_report(self, metrics: PerformanceMetrics) -> None:
        """
        创建HTML报告
        
        Args:
            metrics: 性能指标
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>性能测试报告 - {metrics.test_name}</title>
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
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .metric-card {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 6px;
                    border-left: 4px solid #007acc;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #007acc;
                }}
                .metric-label {{
                    color: #666;
                    margin-bottom: 5px;
                }}
                .status-success {{
                    color: #28a745;
                }}
                .status-warning {{
                    color: #ffc107;
                }}
                .status-error {{
                    color: #dc3545;
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
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>性能测试报告</h1>
                    <p><strong>测试名称:</strong> {metrics.test_name}</p>
                    <p><strong>测试时间:</strong> {metrics.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {metrics.end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>持续时间:</strong> {(metrics.end_time - metrics.start_time).total_seconds():.2f} 秒</p>
                </div>
                
                <h2>性能指标概览</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">总请求数</div>
                        <div class="metric-value">{metrics.total_requests}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">成功率</div>
                        <div class="metric-value {'status-success' if metrics.error_rate < 5 else 'status-warning' if metrics.error_rate < 10 else 'status-error'}">{100 - metrics.error_rate:.2f}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">平均响应时间</div>
                        <div class="metric-value">{metrics.avg_response_time:.2f} ms</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">吞吐量</div>
                        <div class="metric-value">{metrics.requests_per_second:.2f} req/s</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">P95响应时间</div>
                        <div class="metric-value">{metrics.p95_response_time:.2f} ms</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">P99响应时间</div>
                        <div class="metric-value">{metrics.p99_response_time:.2f} ms</div>
                    </div>
                </div>
                
                <h2>详细指标</h2>
                <table>
                    <tr>
                        <th>指标</th>
                        <th>值</th>
                    </tr>
                    <tr>
                        <td>成功请求数</td>
                        <td>{metrics.successful_requests}</td>
                    </tr>
                    <tr>
                        <td>失败请求数</td>
                        <td>{metrics.failed_requests}</td>
                    </tr>
                    <tr>
                        <td>错误率</td>
                        <td>{metrics.error_rate:.2f}%</td>
                    </tr>
                    <tr>
                        <td>最小响应时间</td>
                        <td>{metrics.min_response_time:.2f} ms</td>
                    </tr>
                    <tr>
                        <td>最大响应时间</td>
                        <td>{metrics.max_response_time:.2f} ms</td>
                    </tr>
                    <tr>
                        <td>P50响应时间</td>
                        <td>{metrics.p50_response_time:.2f} ms</td>
                    </tr>
                    <tr>
                        <td>每秒错误数</td>
                        <td>{metrics.errors_per_second:.2f}</td>
                    </tr>
                </table>
                
                {f'<h2>系统资源使用</h2><table><tr><th>指标</th><th>值</th></tr><tr><td>CPU使用率</td><td>{metrics.cpu_usage:.2f}%</td></tr><tr><td>内存使用率</td><td>{metrics.memory_usage:.2f}%</td></tr></table>' if metrics.cpu_usage is not None else ''}
                
                <div class="chart-container">
                    <h2>性能图表</h2>
                    <img src="{self.config.name}_charts.png" alt="性能图表">
                </div>
                
                <div class="footer">
                    <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>SuperRPG 性能测试工具</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        report_file = self.output_dir / f"{self.config.name}_report.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML报告已保存到: {report_file}")


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics_data: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
    
    def start(self) -> None:
        """开始监控"""
        self.is_monitoring = True
        self.start_time = datetime.now()
        self.metrics_data.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop(self) -> None:
        """停止监控"""
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()
                
                if metrics:
                    self.metrics_data.append(metrics)
                
                time.sleep(1)  # 每秒收集一次
                
            except Exception as e:
                print(f"性能监控错误: {str(e)}")
                time.sleep(1)
    
    def _collect_system_metrics(self) -> Optional[Dict[str, Any]]:
        """
        收集系统指标
        
        Returns:
            系统指标字典
        """
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "network_io": network_io
            }
            
        except ImportError:
            # psutil未安装，返回基本指标
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": None,
                "memory_usage": None,
                "network_io": None
            }
        except Exception as e:
            print(f"收集系统指标时出错: {str(e)}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取聚合指标
        
        Returns:
            聚合指标字典
        """
        if not self.metrics_data:
            return {}
        
        # 计算平均值
        cpu_values = [m["cpu_usage"] for m in self.metrics_data if m["cpu_usage"] is not None]
        memory_values = [m["memory_usage"] for m in self.metrics_data if m["memory_usage"] is not None]
        
        avg_cpu = statistics.mean(cpu_values) if cpu_values else None
        avg_memory = statistics.mean(memory_values) if memory_values else None
        
        # 网络IO变化
        if len(self.metrics_data) >= 2:
            first_network = self.metrics_data[0]["network_io"]
            last_network = self.metrics_data[-1]["network_io"]
            
            if first_network and last_network:
                network_io = {
                    "bytes_sent_delta": last_network["bytes_sent"] - first_network["bytes_sent"],
                    "bytes_recv_delta": last_network["bytes_recv"] - first_network["bytes_recv"],
                    "packets_sent_delta": last_network["packets_sent"] - first_network["packets_sent"],
                    "packets_recv_delta": last_network["packets_recv"] - first_network["packets_recv"]
                }
            else:
                network_io = None
        else:
            network_io = None
        
        return {
            "cpu_usage": avg_cpu,
            "memory_usage": avg_memory,
            "network_io": network_io,
            "custom_metrics": {
                "monitoring_duration": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "sample_count": len(self.metrics_data)
            }
        }


# 预定义测试函数

def test_api_health(client: APITestClient) -> TestResult:
    """测试API健康检查"""
    return client.health_check()


def test_character_creation(client: APITestClient) -> TestResult:
    """测试角色卡创建"""
    character_data = {
        "name": "性能测试角色",
        "race": "人类",
        "class": "战士",
        "level": 1,
        "attributes": {
            "力量": 16,
            "敏捷": 14,
            "体质": 15,
            "智力": 12,
            "感知": 13,
            "魅力": 11
        }
    }
    
    return client.create_character(character_data)


def test_lorebook_search(client: APITestClient) -> TestResult:
    """测试传说书搜索"""
    return client.search_lorebook(["测试", "性能"])


def test_prompt_assembly(client: APITestClient) -> TestResult:
    """测试提示组装"""
    return client.assemble_prompt("test_template", {
        "character_name": "测试角色",
        "race": "人类",
        "class": "战士"
    })


# 测试套件

class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self, base_url: str = "http://localhost:3010", output_dir: str = "performance_results"):
        """
        初始化性能测试套件
        
        Args:
            base_url: 基础URL
            output_dir: 输出目录
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.results: List[PerformanceMetrics] = []
    
    def run_load_test(self) -> PerformanceMetrics:
        """运行负载测试"""
        config = PerformanceTestConfig(
            name="load_test",
            description="负载测试 - 模拟正常用户负载",
            duration=60,
            concurrent_users=10,
            ramp_up_time=10,
            think_time=1.0,
            target_url=self.base_url,
            output_dir=self.output_dir
        )
        
        tester = PerformanceTester(config)
        metrics = tester.run_test(test_api_health)
        self.results.append(metrics)
        
        return metrics
    
    def run_stress_test(self) -> PerformanceMetrics:
        """运行压力测试"""
        config = PerformanceTestConfig(
            name="stress_test",
            description="压力测试 - 模拟高负载情况",
            duration=120,
            concurrent_users=50,
            ramp_up_time=30,
            think_time=0.5,
            target_url=self.base_url,
            output_dir=self.output_dir
        )
        
        tester = PerformanceTester(config)
        metrics = tester.run_test(test_api_health)
        self.results.append(metrics)
        
        return metrics
    
    def run_spike_test(self) -> PerformanceMetrics:
        """运行峰值测试"""
        config = PerformanceTestConfig(
            name="spike_test",
            description="峰值测试 - 模拟突发流量",
            duration=60,
            concurrent_users=100,
            ramp_up_time=5,
            think_time=0.2,
            target_url=self.base_url,
            output_dir=self.output_dir
        )
        
        tester = PerformanceTester(config)
        metrics = tester.run_test(test_api_health)
        self.results.append(metrics)
        
        return metrics
    
    def run_endurance_test(self) -> PerformanceMetrics:
        """运行耐久测试"""
        config = PerformanceTestConfig(
            name="endurance_test",
            description="耐久测试 - 长时间运行测试",
            duration=300,  # 5分钟
            concurrent_users=5,
            ramp_up_time=10,
            think_time=2.0,
            target_url=self.base_url,
            output_dir=self.output_dir
        )
        
        tester = PerformanceTester(config)
        metrics = tester.run_test(test_api_health)
        self.results.append(metrics)
        
        return metrics
    
    def run_functional_test(self) -> PerformanceMetrics:
        """运行功能性能测试"""
        config = PerformanceTestConfig(
            name="functional_test",
            description="功能性能测试 - 测试各个API端点",
            duration=120,
            concurrent_users=20,
            ramp_up_time=20,
            think_time=1.5,
            target_url=self.base_url,
            output_dir=self.output_dir
        )
        
        def mixed_workload(client: APITestClient) -> TestResult:
            """混合工作负载"""
            import random
            
            test_functions = [
                test_api_health,
                test_character_creation,
                test_lorebook_search,
                test_prompt_assembly
            ]
            
            # 随机选择一个测试函数
            test_func = random.choice(test_functions)
            return test_func(client)
        
        tester = PerformanceTester(config)
        metrics = tester.run_test(mixed_workload)
        self.results.append(metrics)
        
        return metrics
    
    def run_all_tests(self) -> Dict[str, PerformanceMetrics]:
        """运行所有性能测试"""
        print("开始运行完整的性能测试套件...")
        
        results = {}
        
        try:
            print("1. 运行负载测试...")
            results["load_test"] = self.run_load_test()
            
            print("2. 运行功能性能测试...")
            results["functional_test"] = self.run_functional_test()
            
            print("3. 运行压力测试...")
            results["stress_test"] = self.run_stress_test()
            
            print("4. 运行峰值测试...")
            results["spike_test"] = self.run_spike_test()
            
            print("5. 运行耐久测试...")
            results["endurance_test"] = self.run_endurance_test()
            
        except KeyboardInterrupt:
            print("\n测试被用户中断")
        except Exception as e:
            print(f"测试过程中出现错误: {str(e)}")
        
        # 生成综合报告
        self._generate_comprehensive_report(results)
        
        print("\n性能测试套件完成!")
        return results
    
    def _generate_comprehensive_report(self, results: Dict[str, PerformanceMetrics]) -> None:
        """
        生成综合报告
        
        Args:
            results: 测试结果字典
        """
        if not results:
            return
        
        # 创建DataFrame用于比较
        comparison_data = []
        
        for test_name, metrics in results.items():
            comparison_data.append({
                "测试名称": test_name,
                "总请求数": metrics.total_requests,
                "成功率 (%)": 100 - metrics.error_rate,
                "平均响应时间 (ms)": metrics.avg_response_time,
                "P95响应时间 (ms)": metrics.p95_response_time,
                "吞吐量 (req/s)": metrics.requests_per_second
            })
        
        df = pd.DataFrame(comparison_data)
        
        # 保存比较结果
        comparison_file = Path(self.output_dir) / "performance_comparison.csv"
        df.to_csv(comparison_file, index=False, encoding='utf-8-sig')
        
        # 生成HTML比较报告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>性能测试综合报告</title>
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
                h1, h2 {{
                    color: #333;
                }}
                .header {{
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
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
                .summary {{
                    background-color: #e9f7fe;
                    padding: 20px;
                    border-radius: 6px;
                    margin-bottom: 30px;
                }}
                .test-links {{
                    margin: 20px 0;
                }}
                .test-links a {{
                    display: inline-block;
                    margin-right: 15px;
                    padding: 8px 16px;
                    background-color: #007acc;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .test-links a:hover {{
                    background-color: #005a9e;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>性能测试综合报告</h1>
                    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>测试目标:</strong> {self.base_url}</p>
                </div>
                
                <div class="summary">
                    <h2>测试概览</h2>
                    <p>本次性能测试套件包含 {len(results)} 个测试，总共执行了 {sum(m.total_requests for m in results.values())} 个请求。</p>
                    <p>平均成功率为 {sum(100 - m.error_rate for m in results.values()) / len(results):.2f}%</p>
                    <p>平均吞吐量为 {sum(m.requests_per_second for m in results.values()) / len(results):.2f} req/s</p>
                </div>
                
                <h2>性能指标对比</h2>
                {df.to_html(index=False, escape=False, classes='table')}
                
                <div class="test-links">
                    <h2>详细报告</h2>
                    {"".join([f'<a href="{test_name}_report.html">{test_name}</a>' for test_name in results.keys()])}
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center;">
                    <p>SuperRPG 性能测试工具 - 综合报告</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        report_file = Path(self.output_dir) / "comprehensive_report.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"综合报告已保存到: {report_file}")
        print(f"性能对比数据已保存到: {comparison_file}")


if __name__ == "__main__":
    # 示例用法
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3010"
    
    print(f"开始对 {base_url} 进行性能测试...")
    
    suite = PerformanceTestSuite(base_url)
    results = suite.run_all_tests()
    
    print("\n性能测试完成!")
    print(f"结果保存在: {suite.output_dir}")