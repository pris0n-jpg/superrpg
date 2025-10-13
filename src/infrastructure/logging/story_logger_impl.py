"""
故事日志实现

提供故事日志记录的具体实现，基于现有的eventlog模块。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from ...core.interfaces import Logger as ILogger
from ...core.events import DomainEvent


class StoryLoggerImpl(ILogger):
    """故事日志实现
    
    基于现有eventlog.story_logger模块的故事日志记录实现。
    遵循单一职责原则，专门负责故事日志的记录和管理。
    """
    
    def __init__(self, 
                 story_file: Optional[Path] = None,
                 enable_filtering: bool = True,
                 max_story_length: int = 1000000):
        """初始化故事日志
        
        Args:
            story_file: 故事日志文件路径
            enable_filtering: 是否启用内容过滤
            max_story_length: 最大故事长度
        """
        self._story_file = story_file or Path("logs/story.log")
        self._enable_filtering = enable_filtering
        self._max_story_length = max_story_length
        self._lock = Lock()
        
        # 过滤设置
        self._filtered_phases = {
            "context:",  # 上下文提示
            "round-start",  # 回合开始横幅
        }
        
        # 状态跟踪
        self._printed_initial_world_summary = False
        self._story_entries: List[Dict[str, Any]] = []
        self._character_dialogues: Dict[str, List[str]] = {}
        self._story_events: List[Dict[str, Any]] = []
        
        # 初始化文件
        self._prepare_file()
    
    def _prepare_file(self) -> None:
        """准备日志文件"""
        self._story_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件不存在，创建新文件
        if not self._story_file.exists():
            self._story_file.touch()
    
    def _should_filter_event(self, event_data: Dict[str, Any]) -> bool:
        """判断是否应该过滤事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            bool: 是否应该过滤
        """
        if not self._enable_filtering:
            return False
        
        phase = event_data.get('phase', '').strip()
        
        # 检查过滤阶段
        for filtered_phase in self._filtered_phases:
            if phase.startswith(filtered_phase):
                return True
        
        # 检查世界摘要（只保留第一个）
        if phase == "world-summary":
            if self._printed_initial_world_summary:
                return True
            self._printed_initial_world_summary = True
        
        return False
    
    def _format_story_entry(self, event_data: Dict[str, Any]) -> str:
        """格式化故事条目
        
        Args:
            event_data: 事件数据
            
        Returns:
            str: 格式化的故事条目
        """
        text = event_data.get('text', '')
        actor = event_data.get('actor', 'system')
        timestamp = event_data.get('timestamp', datetime.now())
        
        if isinstance(timestamp, str):
            timestamp_str = timestamp
        else:
            timestamp_str = timestamp.isoformat() if timestamp else ''
        
        event_id = event_data.get('event_id', '')
        turn = event_data.get('turn', '')
        
        # 构建故事条目
        parts = []
        if event_id:
            parts.append(f"[{event_id}]")
        if timestamp_str:
            parts.append(f"{timestamp_str}")
        if turn:
            parts.append(f"回合{turn}")
        if actor != 'system':
            parts.append(f"{actor}:")
        
        parts.append(text)
        
        return " ".join(parts)
    
    def _write_to_file(self, content: str) -> None:
        """写入文件
        
        Args:
            content: 要写入的内容
        """
        try:
            with self._lock:
                with open(self._story_file, 'a', encoding='utf-8') as f:
                    f.write(content + '\n')
                    f.flush()
        except Exception:
            # 静默处理写入错误
            pass
    
    def _add_story_entry(self, event_data: Dict[str, Any]) -> None:
        """添加故事条目
        
        Args:
            event_data: 事件数据
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event_data': event_data,
            'entry_id': len(self._story_entries)
        }
        
        self._story_entries.append(entry)
        
        # 限制内存中的条目数量
        if len(self._story_entries) > 10000:
            self._story_entries = self._story_entries[-5000:]
    
    def _track_character_dialogue(self, character: str, dialogue: str) -> None:
        """跟踪角色对话
        
        Args:
            character: 角色名称
            dialogue: 对话内容
        """
        if character not in self._character_dialogues:
            self._character_dialogues[character] = []
        
        self._character_dialogues[character].append(dialogue)
        
        # 限制每个角色的对话记录数量
        if len(self._character_dialogues[character]) > 1000:
            self._character_dialogues[character] = self._character_dialogues[character][-500:]
    
    def _add_story_event(self, event_type: str, description: str, **kwargs) -> None:
        """添加故事事件
        
        Args:
            event_type: 事件类型
            description: 事件描述
            **kwargs: 额外的事件数据
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'description': description,
            **kwargs
        }
        
        self._story_events.append(event)
        
        # 限制事件数量
        if len(self._story_events) > 5000:
            self._story_events = self._story_events[-2500:]
    
    # 实现Logger接口方法
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': message,
            'event_type': kwargs.get('event_type', 'narrative'),
            'actor': kwargs.get('actor', 'system'),
            'timestamp': datetime.now(),
            **kwargs
        }
        
        # 检查是否应该过滤
        if self._should_filter_event(event_data):
            return
        
        # 格式化并写入
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        
        # 添加到内存记录
        self._add_story_entry(event_data)
        
        # 跟踪角色对话
        if event_data.get('actor') and event_data.get('actor') != 'system':
            self._track_character_dialogue(event_data['actor'], message)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        # 故事日志中警告作为特殊事件处理
        self._add_story_event('warning', message, **kwargs)
        
        # 也写入故事文件，但标记为警告
        event_data = {
            'text': f"[警告] {message}",
            'event_type': 'warning',
            'actor': 'system',
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        # 故事日志中错误作为特殊事件处理
        self._add_story_event('error', message, **kwargs)
        
        # 也写入故事文件，但标记为错误
        event_data = {
            'text': f"[错误] {message}",
            'event_type': 'error',
            'actor': 'system',
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        # 故事日志通常不记录调试信息，除非明确启用
        if kwargs.get('include_in_story', False):
            event_data = {
                'text': f"[调试] {message}",
                'event_type': 'debug',
                'actor': 'system',
                'timestamp': datetime.now(),
                **kwargs
            }
            
            formatted_entry = self._format_story_entry(event_data)
            self._write_to_file(formatted_entry)
            self._add_story_entry(event_data)
    
    # 扩展方法
    
    def log_narrative(self, text: str, actor: Optional[str] = None, **kwargs) -> None:
        """记录叙述文本
        
        Args:
            text: 叙述文本
            actor: 说话者
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': text,
            'event_type': 'narrative',
            'actor': actor or 'narrator',
            'timestamp': datetime.now(),
            **kwargs
        }
        
        if self._should_filter_event(event_data):
            return
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        self._add_story_entry(event_data)
    
    def log_dialogue(self, character: str, dialogue: str, **kwargs) -> None:
        """记录角色对话
        
        Args:
            character: 角色名称
            dialogue: 对话内容
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': dialogue,
            'event_type': 'dialogue',
            'actor': character,
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        self._add_story_entry(event_data)
        self._track_character_dialogue(character, dialogue)
    
    def log_action(self, character: str, action: str, **kwargs) -> None:
        """记录角色动作
        
        Args:
            character: 角色名称
            action: 动作描述
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': f"{character} {action}",
            'event_type': 'action',
            'actor': character,
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        self._add_story_entry(event_data)
    
    def log_scene_change(self, scene_description: str, **kwargs) -> None:
        """记录场景变化
        
        Args:
            scene_description: 场景描述
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': f"[场景变化] {scene_description}",
            'event_type': 'scene_change',
            'actor': 'system',
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        self._add_story_entry(event_data)
    
    def log_combat_event(self, combat_description: str, **kwargs) -> None:
        """记录战斗事件
        
        Args:
            combat_description: 战斗描述
            **kwargs: 额外的日志数据
        """
        event_data = {
            'text': f"[战斗] {combat_description}",
            'event_type': 'combat',
            'actor': 'system',
            'timestamp': datetime.now(),
            **kwargs
        }
        
        formatted_entry = self._format_story_entry(event_data)
        self._write_to_file(formatted_entry)
        self._add_story_entry(event_data)
    
    def get_story_summary(self) -> Dict[str, Any]:
        """获取故事摘要
        
        Returns:
            Dict[str, Any]: 故事摘要信息
        """
        with self._lock:
            total_entries = len(self._story_entries)
            total_events = len(self._story_events)
            character_count = len(self._character_dialogues)
            
            # 计算总对话数
            total_dialogues = sum(len(dialogues) for dialogues in self._character_dialogues.values())
            
            # 获取最活跃的角色
            most_active_character = None
            max_dialogues = 0
            for character, dialogues in self._character_dialogues.items():
                if len(dialogues) > max_dialogues:
                    max_dialogues = len(dialogues)
                    most_active_character = character
            
            return {
                'total_entries': total_entries,
                'total_events': total_events,
                'total_dialogues': total_dialogues,
                'character_count': character_count,
                'most_active_character': most_active_character,
                'story_file': str(self._story_file),
                'filtering_enabled': self._enable_filtering,
                'last_entry_time': self._story_entries[-1]['timestamp'] if self._story_entries else None,
            }
    
    def get_character_dialogues(self, character: str, limit: Optional[int] = None) -> List[str]:
        """获取角色对话
        
        Args:
            character: 角色名称
            limit: 限制数量
            
        Returns:
            List[str]: 对话列表
        """
        dialogues = self._character_dialogues.get(character, [])
        if limit:
            return dialogues[-limit:]
        return dialogues
    
    def get_recent_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的故事条目
        
        Args:
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 故事条目列表
        """
        with self._lock:
            return self._story_entries[-limit:] if limit > 0 else self._story_entries
    
    def search_story(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """搜索故事内容
        
        Args:
            keyword: 搜索关键词
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 匹配的故事条目
        """
        results = []
        keyword_lower = keyword.lower()
        
        for entry in self._story_entries:
            text = entry['event_data'].get('text', '').lower()
            actor = entry['event_data'].get('actor', '').lower()
            
            if keyword_lower in text or keyword_lower in actor:
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def export_story(self, format_type: str = 'txt', start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> str:
        """导出故事
        
        Args:
            format_type: 导出格式 ('txt', 'json', 'markdown')
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            str: 导出的故事内容
        """
        # 过滤条目
        filtered_entries = []
        for entry in self._story_entries:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            
            if start_time and entry_time < start_time:
                continue
            if end_time and entry_time > end_time:
                continue
            
            filtered_entries.append(entry)
        
        if format_type == 'txt':
            return self._export_as_text(filtered_entries)
        elif format_type == 'json':
            return self._export_as_json(filtered_entries)
        elif format_type == 'markdown':
            return self._export_as_markdown(filtered_entries)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def _export_as_text(self, entries: List[Dict[str, Any]]) -> str:
        """导出为纯文本"""
        lines = []
        for entry in entries:
            formatted = self._format_story_entry(entry['event_data'])
            lines.append(formatted)
        return '\n'.join(lines)
    
    def _export_as_json(self, entries: List[Dict[str, Any]]) -> str:
        """导出为JSON"""
        return json.dumps(entries, ensure_ascii=False, indent=2)
    
    def _export_as_markdown(self, entries: List[Dict[str, Any]]) -> str:
        """导出为Markdown"""
        lines = ["# 故事日志\n"]
        
        for entry in entries:
            event_data = entry['event_data']
            timestamp = event_data.get('timestamp', '')
            actor = event_data.get('actor', 'system')
            text = event_data.get('text', '')
            
            lines.append(f"## {timestamp} - {actor}")
            lines.append(f"{text}\n")
        
        return '\n'.join(lines)
    
    def clear_story(self) -> None:
        """清空故事日志"""
        with self._lock:
            # 清空内存数据
            self._story_entries.clear()
            self._character_dialogues.clear()
            self._story_events.clear()
            self._printed_initial_world_summary = False
            
            # 清空文件
            try:
                with open(self._story_file, 'w', encoding='utf-8') as f:
                    f.write('')
            except Exception:
                pass
    
    def set_filtering(self, enabled: bool) -> None:
        """设置过滤状态
        
        Args:
            enabled: 是否启用过滤
        """
        self._enable_filtering = enabled
    
    def add_filtered_phase(self, phase: str) -> None:
        """添加过滤阶段
        
        Args:
            phase: 要过滤的阶段
        """
        self._filtered_phases.add(phase)
    
    def remove_filtered_phase(self, phase: str) -> None:
        """移除过滤阶段
        
        Args:
            phase: 要移除的过滤阶段
        """
        self._filtered_phases.discard(phase)
    
    def get_filtered_phases(self) -> Set[str]:
        """获取过滤阶段列表
        
        Returns:
            Set[str]: 过滤阶段集合
        """
        return self._filtered_phases.copy()