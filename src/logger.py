#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供统一的日志记录功能，支持文件日志、控制台日志、
日志轮转和不同级别的日志输出。

Author: MarkItDown Team
Version: 1.0.0
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import Config


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器
    
    为不同级别的日志添加颜色，提高可读性。
    """
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        """格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            str: 格式化后的日志字符串
        """
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 添加颜色（仅在终端输出时）
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            level_name = record.levelname
            color = self.COLORS.get(level_name, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # 为级别名称添加颜色
            colored_level = f"{color}{level_name}{reset}"
            log_message = log_message.replace(level_name, colored_level, 1)
        
        return log_message


class MarkItDownLogger:
    """MarkItDown 专用日志管理器
    
    提供统一的日志配置和管理功能。
    """
    
    def __init__(self, name: str = 'markitdown', 
                 level: str = "INFO",
                 log_level: str = None,  # 兼容参数
                 log_file: str = None,
                 console_output: bool = True,
                 file_output: bool = True,
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """初始化日志管理器
        
        Args:
            name: 日志器名称
            level: 日志级别
            log_level: 兼容参数
            log_file: 日志文件路径
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_bytes: 日志文件最大字节数
            backup_count: 备份文件数量
        """
        self.name = name
        # 使用 log_level 参数（如果提供）或 level 参数
        self.level = log_level or level
        self.log_file = log_file
        self.console_output = console_output
        self.file_output = file_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.level.upper()))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """设置日志处理器"""
        # 控制台处理器
        if self.console_output:
            console_handler = self._create_console_handler()
            self.logger.addHandler(console_handler)
        
        # 文件处理器
        if self.file_output:
            if self.log_file:
                log_file_path = Path(self.log_file)
            else:
                log_dir = Path('logs')
                log_dir.mkdir(exist_ok=True)
                log_file_path = log_dir / f'{self.name}.log'
            
            # 确保日志文件目录存在
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = self._create_file_handler(
                log_file_path,
                level=logging.DEBUG
            )
            self.logger.addHandler(file_handler)
    
    def _create_file_handler(self, log_file: Path, level: int) -> logging.Handler:
        """创建文件日志处理器
        
        Args:
            log_file: 日志文件路径
            level: 日志级别
            
        Returns:
            logging.Handler: 文件处理器
        """
        # 使用轮转文件处理器
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        handler.setLevel(level)
        
        # 设置格式
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_console_handler(self) -> logging.Handler:
        """创建控制台日志处理器
        
        Returns:
            logging.Handler: 控制台处理器
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.level.upper()))
        
        # 使用带颜色的格式化器
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self) -> logging.Logger:
        """
        获取日志器实例
        
        Returns:
            日志器实例
        """
        return self.logger
    
    # 代理日志方法
    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录信息"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误"""
        self.logger.critical(message, *args, **kwargs)
    
    def set_level(self, level: int) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        self.logger.setLevel(level)
        
        # 同时设置所有处理器的级别
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                # 控制台处理器
                handler.setLevel(level)
    
    def add_file_handler(self, log_file: str, level: int = logging.INFO) -> None:
        """添加额外的文件处理器
        
        Args:
            log_file: 日志文件路径
            level: 日志级别
        """
        handler = self._create_file_handler(Path(log_file), level)
        self.logger.addHandler(handler)
    
    def remove_console_output(self) -> None:
        """移除控制台输出"""
        handlers_to_remove = []
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handlers_to_remove.append(handler)
        
        for handler in handlers_to_remove:
            self.logger.removeHandler(handler)
    
    def log_system_info(self) -> None:
        """记录系统信息"""
        import platform
        import psutil
        
        self.logger.info("=" * 50)
        self.logger.info("系统信息")
        self.logger.info("=" * 50)
        self.logger.info(f"操作系统: {platform.system()} {platform.release()}")
        self.logger.info(f"Python版本: {platform.python_version()}")
        self.logger.info(f"CPU核心数: {psutil.cpu_count()}")
        self.logger.info(f"内存总量: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        self.logger.info(f"可用内存: {psutil.virtual_memory().available / (1024**3):.1f} GB")
        self.logger.info("=" * 50)
    
    def log_config_info(self, config_dict: dict = None) -> None:
        """记录配置信息
        
        Args:
            config_dict: 配置字典
        """
        self.logger.info("=" * 50)
        self.logger.info("配置信息")
        self.logger.info("=" * 50)
        
        if config_dict is None:
            try:
                from .config import Config
                config_dict = Config.get_config_dict()
            except ImportError:
                self.logger.warning("无法导入配置模块")
                return
        
        for section, settings in config_dict.items():
            self.logger.info(f"[{section}]")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    self.logger.info(f"  {key}: {value}")
            else:
                self.logger.info(f"  {settings}")
            self.logger.info("")
    
    def log_performance_metrics(self, start_time: datetime, end_time: datetime, 
                              files_processed: int, files_success: int) -> None:
        """记录性能指标
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            files_processed: 处理的文件数
            files_success: 成功处理的文件数
        """
        duration = (end_time - start_time).total_seconds()
        success_rate = (files_success / files_processed * 100) if files_processed > 0 else 0
        avg_time_per_file = duration / files_processed if files_processed > 0 else 0
        
        self.logger.info("性能指标:")
        self.logger.info(f"总耗时: {duration:.2f} 秒")
        self.logger.info(f"处理文件数: {files_processed}")
        self.logger.info(f"成功文件数: {files_success}")
        self.logger.info(f"成功率: {success_rate:.1f}%")
        self.logger.info(f"平均处理时间: {avg_time_per_file:.2f} 秒/文件")


# 全局日志管理器实例
_logger_instance: Optional[MarkItDownLogger] = None


def setup_logger(level: int = logging.INFO, name: str = 'markitdown') -> logging.Logger:
    """设置并获取日志器
    
    Args:
        level: 日志级别
        name: 日志器名称
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = MarkItDownLogger(name)
    
    _logger_instance.set_level(level)
    return _logger_instance.get_logger()


def get_logger(name: str = 'markitdown') -> logging.Logger:
    """获取日志器实例
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    if _logger_instance is None:
        return setup_logger(name=name)
    return _logger_instance.get_logger()


def log_function_call(func):
    """函数调用日志装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        
        # 记录函数调用开始
        logger.debug(f"开始执行函数: {func_name}")
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录函数调用成功
            logger.debug(f"函数执行成功: {func_name}")
            return result
            
        except Exception as e:
            # 记录函数调用异常
            logger.error(f"函数执行异常: {func_name}, 错误: {str(e)}")
            raise
    
    return wrapper


def log_processing_progress(current: int, total: int, item_name: str = "项目") -> None:
    """记录处理进度
    
    Args:
        current: 当前处理数量
        total: 总数量
        item_name: 项目名称
    """
    logger = get_logger()
    progress = (current / total * 100) if total > 0 else 0
    logger.info(f"处理进度: {progress:.1f}% ({current}/{total} {item_name})")


if __name__ == '__main__':
    # 测试日志功能
    logger = setup_logger(logging.DEBUG)
    
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息")
    logger.warning("这是一条警告")
    logger.error("这是一条错误")
    logger.critical("这是一条严重错误")
    
    # 测试装饰器
    @log_function_call
    def test_function():
        """测试函数"""
        return "测试成功"
    
    result = test_function()
    print(f"函数返回: {result}")
    
    # 测试进度记录
    for i in range(1, 6):
        log_processing_progress(i, 5, "文件")