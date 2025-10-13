"""
关键词匹配服务

提供高效的关键词匹配功能，支持多种匹配类型和优化算法。
遵循SOLID原则，特别是单一职责原则(SRP)和开放封闭原则(OCP)。
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Set, Pattern
from dataclasses import dataclass, field
from collections import defaultdict
import time

from ...domain.models.lorebook import KeywordPattern, KeywordType, LorebookEntry
from ...core.interfaces import EventBus, Logger
from .base import ApplicationService


@dataclass
class MatchResult:
    """匹配结果
    
    封装关键词匹配的结果信息。
    遵循单一职责原则，专门负责匹配结果的表示。
    """
    pattern: KeywordPattern
    matched_text: str
    score: float
    start_position: int
    end_position: int
    groups: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.score < 0:
            self.score = 0.0
        elif self.score > 1.0:
            self.score = 1.0


@dataclass
class CompiledPattern:
    """编译后的模式
    
    封装预编译的正则表达式和其他优化数据。
    遵循单一职责原则，专门负责编译模式的表示。
    """
    original_pattern: KeywordPattern
    compiled_regex: Optional[Pattern] = None
    normalized_pattern: str = ""
    is_valid: bool = True
    error_message: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        self._compile_pattern()
    
    def _compile_pattern(self) -> None:
        """编译模式"""
        try:
            if self.original_pattern.type == KeywordType.REGEX:
                # 编译正则表达式
                flags = 0 if self.original_pattern.case_sensitive else re.IGNORECASE
                self.compiled_regex = re.compile(self.original_pattern.pattern, flags)
                self.normalized_pattern = self.original_pattern.pattern
            else:
                # 标准化普通模式
                self.normalized_pattern = (
                    self.original_pattern.pattern 
                    if self.original_pattern.case_sensitive 
                    else self.original_pattern.pattern.lower()
                )
        except re.error as e:
            self.is_valid = False
            self.error_message = str(e)
    
    def matches(self, text: str) -> List[MatchResult]:
        """匹配文本
        
        Args:
            text: 要匹配的文本
            
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        if not self.is_valid or not text:
            return []
        
        results = []
        
        if self.original_pattern.type == KeywordType.REGEX and self.compiled_regex:
            # 正则表达式匹配
            for match in self.compiled_regex.finditer(text):
                groups = match.groupdict() if match.re.groupindex else {}
                result = MatchResult(
                    pattern=self.original_pattern,
                    matched_text=match.group(0),
                    score=self.original_pattern.weight,
                    start_position=match.start(),
                    end_position=match.end(),
                    groups=groups
                )
                results.append(result)
        else:
            # 其他类型匹配
            search_text = (
                text 
                if self.original_pattern.case_sensitive 
                else text.lower()
            )
            
            if self.original_pattern.type == KeywordType.EXACT:
                if search_text == self.normalized_pattern:
                    result = MatchResult(
                        pattern=self.original_pattern,
                        matched_text=text,
                        score=self.original_pattern.weight,
                        start_position=0,
                        end_position=len(text)
                    )
                    results.append(result)
            elif self.original_pattern.type == KeywordType.PARTIAL:
                start = search_text.find(self.normalized_pattern)
                if start != -1:
                    end = start + len(self.normalized_pattern)
                    result = MatchResult(
                        pattern=self.original_pattern,
                        matched_text=text[start:end],
                        score=self.original_pattern.weight,
                        start_position=start,
                        end_position=end
                    )
                    results.append(result)
            elif self.original_pattern.type == KeywordType.WILDCARD:
                # 转换通配符模式为正则表达式
                regex_pattern = self.normalized_pattern.replace('*', '.*')
                regex_pattern = f'^{regex_pattern}$'
                flags = 0 if self.original_pattern.case_sensitive else re.IGNORECASE
                try:
                    wildcard_regex = re.compile(regex_pattern, flags)
                    if wildcard_regex.match(text):
                        result = MatchResult(
                            pattern=self.original_pattern,
                            matched_text=text,
                            score=self.original_pattern.weight,
                            start_position=0,
                            end_position=len(text)
                        )
                        results.append(result)
                except re.error:
                    # 如果转换失败，跳过此模式
                    pass
        
        return results


class KeywordMatcherService(ApplicationService):
    """关键词匹配服务
    
    提供高效的关键词匹配功能，支持多种匹配类型和优化算法。
    遵循单一职责原则，专门负责关键词匹配逻辑的管理。
    """
    
    def __init__(self, event_bus: EventBus, logger: Logger):
        """初始化关键词匹配服务
        
        Args:
            logger: 日志记录器
        """
        super().__init__(event_bus, logger)
        self._compiled_patterns: Dict[str, CompiledPattern] = {}
        self._pattern_index: Dict[str, Set[str]] = defaultdict(set)  # 索引：关键词 -> 模式ID集合
        self._performance_stats = {
            'total_matches': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def compile_pattern(self, pattern: KeywordPattern) -> str:
        """编译关键词模式
        
        Args:
            pattern: 关键词模式
            
        Returns:
            str: 模式ID
        """
        pattern_id = self._generate_pattern_id(pattern)
        
        if pattern_id not in self._compiled_patterns:
            compiled = CompiledPattern(pattern)
            self._compiled_patterns[pattern_id] = compiled
            
            # 更新索引
            if compiled.is_valid:
                self._update_pattern_index(pattern_id, pattern)
            
            self._logger.debug(f"Compiled pattern: {pattern.pattern} -> {pattern_id}")
        
        return pattern_id
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """移除编译的模式
        
        Args:
            pattern_id: 模式ID
            
        Returns:
            bool: 是否成功移除
        """
        if pattern_id in self._compiled_patterns:
            pattern = self._compiled_patterns[pattern_id].original_pattern
            del self._compiled_patterns[pattern_id]
            
            # 更新索引
            self._remove_from_pattern_index(pattern_id, pattern)
            
            self._logger.debug(f"Removed pattern: {pattern_id}")
            return True
        
        return False
    
    def match_patterns(self, pattern_ids: List[str], text: str) -> List[MatchResult]:
        """匹配多个模式
        
        Args:
            pattern_ids: 模式ID列表
            text: 要匹配的文本
            
        Returns:
            List[MatchResult]: 匹配结果列表，按分数排序
        """
        start_time = time.time()
        
        all_results = []
        
        for pattern_id in pattern_ids:
            if pattern_id in self._compiled_patterns:
                compiled = self._compiled_patterns[pattern_id]
                results = compiled.matches(text)
                all_results.extend(results)
        
        # 按分数和位置排序
        all_results.sort(key=lambda r: (-r.score, r.start_position))
        
        # 更新性能统计
        match_time = time.time() - start_time
        self._performance_stats['total_matches'] += 1
        self._performance_stats['total_time'] += match_time
        
        self._logger.debug(f"Matched {len(pattern_ids)} patterns in {match_time:.4f}s, found {len(all_results)} results")
        
        return all_results
    
    def find_best_matches(self, pattern_ids: List[str], text: str, max_results: int = 10) -> List[MatchResult]:
        """查找最佳匹配
        
        Args:
            pattern_ids: 模式ID列表
            text: 要匹配的文本
            max_results: 最大结果数
            
        Returns:
            List[MatchResult]: 最佳匹配结果列表
        """
        all_results = self.match_patterns(pattern_ids, text)
        return all_results[:max_results]
    
    def match_text(self, text: str, patterns: List[KeywordPattern] = None) -> List[MatchResult]:
        """匹配文本（使用提供的模式列表）
        
        Args:
            text: 要匹配的文本
            patterns: 关键词模式列表，如果为None则使用所有已编译的模式
            
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        if patterns is None:
            # 使用所有已编译的模式
            pattern_ids = list(self._compiled_patterns.keys())
        else:
            # 编译提供的模式
            pattern_ids = [self.compile_pattern(pattern) for pattern in patterns]
        
        return self.match_patterns(pattern_ids, text)
    
    def find_patterns_by_keyword(self, keyword: str) -> List[str]:
        """根据关键词查找相关模式
        
        Args:
            keyword: 关键词
            
        Returns:
            List[str]: 相关模式ID列表
        """
        # 简单的关键词匹配，可以扩展为更复杂的算法
        matching_ids = set()
        
        # 直接匹配
        if keyword in self._pattern_index:
            matching_ids.update(self._pattern_index[keyword])
        
        # 部分匹配
        for indexed_keyword, pattern_ids in self._pattern_index.items():
            if keyword in indexed_keyword or indexed_keyword in keyword:
                matching_ids.update(pattern_ids)
        
        return list(matching_ids)
    
    def optimize_for_text(self, text: str, pattern_ids: List[str] = None) -> List[str]:
        """为文本优化模式列表
        
        Args:
            text: 目标文本
            pattern_ids: 模式ID列表，如果为None则使用所有已编译的模式
            
        Returns:
            List[str]: 优化后的模式ID列表
        """
        if pattern_ids is None:
            pattern_ids = list(self._compiled_patterns.keys())
        
        # 简单的优化：根据文本特征过滤模式
        optimized_ids = []
        text_lower = text.lower()
        
        for pattern_id in pattern_ids:
            if pattern_id not in self._compiled_patterns:
                continue
            
            compiled = self._compiled_patterns[pattern_id]
            if not compiled.is_valid:
                continue
            
            pattern = compiled.original_pattern
            
            # 根据模式类型进行简单预过滤
            should_include = True
            
            if pattern.type == KeywordType.EXACT:
                # 精确匹配：检查文本长度
                if len(pattern.pattern) != len(text):
                    should_include = False
            elif pattern.type == KeywordType.PARTIAL:
                # 部分匹配：检查关键词是否在文本中
                search_pattern = (
                    pattern.pattern 
                    if pattern.case_sensitive 
                    else pattern.pattern.lower()
                )
                if search_pattern not in text_lower:
                    should_include = False
            
            if should_include:
                optimized_ids.append(pattern_id)
        
        return optimized_ids
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        stats = self._performance_stats.copy()
        
        if stats['total_matches'] > 0:
            stats['average_time'] = stats['total_time'] / stats['total_matches']
            stats['matches_per_second'] = stats['total_matches'] / stats['total_time'] if stats['total_time'] > 0 else 0
        else:
            stats['average_time'] = 0.0
            stats['matches_per_second'] = 0.0
        
        stats['compiled_patterns'] = len(self._compiled_patterns)
        stats['index_size'] = len(self._pattern_index)
        
        return stats
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._compiled_patterns.clear()
        self._pattern_index.clear()
        self._performance_stats = {
            'total_matches': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        self._logger.info("Keyword matcher cache cleared")
    
    def validate_pattern(self, pattern: KeywordPattern) -> List[str]:
        """验证关键词模式
        
        Args:
            pattern: 关键词模式
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not pattern.pattern or not pattern.pattern.strip():
            errors.append("模式不能为空")
        
        if pattern.type == KeywordType.REGEX:
            try:
                flags = 0 if pattern.case_sensitive else re.IGNORECASE
                re.compile(pattern.pattern, flags)
            except re.error as e:
                errors.append(f"无效的正则表达式: {str(e)}")
        
        if pattern.weight < 0:
            errors.append("权重不能小于0")
        
        return errors
    
    def _generate_pattern_id(self, pattern: KeywordPattern) -> str:
        """生成模式ID
        
        Args:
            pattern: 关键词模式
            
        Returns:
            str: 模式ID
        """
        # 使用模式的特征生成唯一ID
        import hashlib
        content = f"{pattern.pattern}:{pattern.type.value}:{pattern.case_sensitive}:{pattern.weight}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_pattern_index(self, pattern_id: str, pattern: KeywordPattern) -> None:
        """更新模式索引
        
        Args:
            pattern_id: 模式ID
            pattern: 关键词模式
        """
        if pattern.type == KeywordType.REGEX:
            # 对于正则表达式，尝试提取关键字
            try:
                flags = 0 if pattern.case_sensitive else re.IGNORECASE
                regex = re.compile(pattern.pattern, flags)
                
                # 简单的关键词提取：查找字母数字序列
                matches = re.findall(r'\b\w+\b', pattern.pattern)
                for match in matches:
                    self._pattern_index[match.lower()].add(pattern_id)
            except re.error:
                pass
        else:
            # 对于其他类型，直接使用模式作为索引
            index_key = pattern.pattern.lower()
            self._pattern_index[index_key].add(pattern_id)
            
            # 添加部分匹配的索引
            if len(pattern.pattern) > 3:
                for i in range(len(pattern.pattern) - 2):
                    substring = pattern.pattern[i:i+3].lower()
                    self._pattern_index[substring].add(pattern_id)
    
    def _remove_from_pattern_index(self, pattern_id: str, pattern: KeywordPattern) -> None:
        """从模式索引中移除
        
        Args:
            pattern_id: 模式ID
            pattern: 关键词模式
        """
        # 遍历所有索引项，移除对应的模式ID
        for keyword, pattern_ids in self._pattern_index.items():
            if pattern_id in pattern_ids:
                pattern_ids.remove(pattern_id)
        
        # 清理空的索引项
        empty_keys = [k for k, v in self._pattern_index.items() if not v]
        for key in empty_keys:
            del self._pattern_index[key]
    
    def get_suggestions(self, text: str, max_suggestions: int = 5) -> List[str]:
        """获取关键词建议
        
        Args:
            text: 输入文本
            max_suggestions: 最大建议数量
            
        Returns:
            List[str]: 关键词建议列表
        """
        suggestions = set()
        text_lower = text.lower()
        
        # 从索引中查找相关的关键词
        for keyword in self._pattern_index:
            if keyword.startswith(text_lower) or text_lower.startswith(keyword):
                suggestions.add(keyword)
        
        # 转换为列表并排序
        suggestion_list = list(suggestions)
        suggestion_list.sort(key=lambda x: (len(x), x))
        
        return suggestion_list[:max_suggestions]
    def _execute_command_internal(self, command: Any) -> Any:
        raise NotImplementedError("KeywordMatcherService does not support command execution")

    def _execute_query_internal(self, query: Any) -> Any:
        raise NotImplementedError("KeywordMatcherService does not support query execution")
