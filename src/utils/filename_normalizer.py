# -*- coding: utf-8 -*-
"""
文件名规范化工具类

提供统一的文件名规范化、alt文本处理和相对路径确保功能，
解决中文字符和特殊符号在不同工具中的兼容性问题。

Author: AI Assistant
Date: 2025-01-01
"""

import re
import os
import logging
from typing import Dict, Optional
from pypinyin import lazy_pinyin, Style


logger = logging.getLogger(__name__)

class FilenameNormalizer:
    """
    文件名规范化工具类
    
    提供统一的文件名处理、alt文本生成和路径规范化功能
    """
    
    # 文件名替换字符映射
    FILENAME_REPLACEMENT_CHARS: Dict[str, str] = {
        '（': '(',
        '）': ')',
        '：': '_',
        '；': '_',
        '，': '_',
        '。': '.',
        '？': '',
        '！': '',
        '【': '[',
        '】': ']',
        '《': '',
        '》': '',
        '"': '',
        "'": '',
        '\\': '_',
        '/': '_',
        '*': '_',
        '?': '',
        '<': '',
        '>': '',
        '|': '_',
        ' ': '_',
        '　': '_',  # 添加全角空格替换
        '\t': '_',
        '\n': '_',
        '\r': '_'
    }
    
    # 文件名最大长度限制（从配置读取）
    @classmethod
    def get_max_filename_length(cls):
        """获取文件名最大长度限制
        
        Returns:
            int: 文件名最大长度
        """
        from ..config import Config
        # 优先使用FILENAME_NORMALIZATION中的配置
        if 'max_filename_length' in Config.FILENAME_NORMALIZATION:
            return Config.FILENAME_NORMALIZATION['max_filename_length']
        # 回退到DIRECTORY_NAMING中的filename_limits配置
        return Config.DIRECTORY_NAMING.get('filename_limits', {}).get('max_filename_length', 50)
    
    # 最大alt文本长度
    MAX_ALT_TEXT_LENGTH = 30
    
    @staticmethod
    def normalize_filename(filename: str, is_document_title: bool = False) -> str:
        """
        统一文件名规范化：根据配置决定是否进行中文转拼音，并确保空格替换为下划线
        
        Args:
            filename (str): 原始文件名
            is_document_title (bool): 是否为文档标题
            
        Returns:
            str: 规范化后的文件名
        """
        logger.debug(f"Normalizing filename: '{filename}', is_document_title: {is_document_title}")
        if not filename:
            return "unnamed"
        
        # 导入配置
        from ..config import Config
        
        # 对于文档标题，不分离扩展名，直接处理整个字符串
        if is_document_title:
            name = filename
            ext = ''
        else:
            # 分离文件名和扩展名
            name, ext = os.path.splitext(filename)

        # 替换特殊字符，包括强制替换空格为下划线
        for old_char, new_char in FilenameNormalizer.FILENAME_REPLACEMENT_CHARS.items():
            name = name.replace(old_char, new_char)
        name = name.replace(' ', '_')  # 额外确保空格替换
        
        # 根据配置决定是否进行中文转拼音
        if (Config.FILENAME_NORMALIZATION.get('convert_chinese_to_pinyin', True) and 
            ext.lower() != '.md'):
            # 中文转拼音（非MD文件且配置启用）
            name = FilenameNormalizer._chinese_to_pinyin(name)
        
        # 移除多余的下划线和点
        name = re.sub(r'_+', '_', name)  # 多个下划线合并为一个
        name = re.sub(r'\.+', '.', name)  # 多个点合并为一个
        name = name.strip('_.')  # 移除首尾的下划线和点
        
        # 仅在不是文档标题时应用长度限制
        if not is_document_title:
            # 长度限制 - 考虑扩展名长度
            max_length = FilenameNormalizer.get_max_filename_length()
            # 为扩展名预留空间
            available_length = max_length - len(ext)
            if available_length > 0 and len(name) > available_length:
                name = name[:available_length]
            elif available_length <= 0:
                # 如果扩展名太长，至少保留一些主文件名
                min_name_length = min(10, max_length // 2)
                name = name[:min_name_length]
        
        # 确保文件名不为空
        if not name:
            name = "unnamed"
        
        normalized_filename = name + ext
        logger.debug(f"Final normalized filename: '{normalized_filename}'")
        return normalized_filename
    
    @staticmethod
    def _chinese_to_pinyin(text: str) -> str:
        """
        将中文字符转换为拼音
        
        Args:
            text (str): 包含中文的文本
            
        Returns:
            str: 转换后的拼音文本
        """
        # 检查是否包含中文字符
        if re.search(r'[\u4e00-\u9fff]', text):
            # 转换为拼音，使用下划线连接
            pinyin_list = lazy_pinyin(text, style=Style.NORMAL)
            # 只转换中文部分，保留其他字符
            result = []
            i = 0
            for char in text:
                if '\u4e00' <= char <= '\u9fff':  # 中文字符
                    if i < len(pinyin_list):
                        result.append(pinyin_list[i])
                        i += 1
                else:
                    result.append(char)
            return ''.join(result)
        return text
    
    @staticmethod
    def normalize_alt_text(text: str) -> str:
        """
        统一alt文本规范化：移除特殊字符、长度限制
        
        Args:
            text (str): 原始alt文本
            
        Returns:
            str: 规范化后的alt文本
        """
        if not text:
            return "image"
        
        # 移除特殊字符，只保留字母、数字、下划线
        normalized = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '', text)
        
        # 长度限制
        if len(normalized) > FilenameNormalizer.MAX_ALT_TEXT_LENGTH:
            normalized = normalized[:FilenameNormalizer.MAX_ALT_TEXT_LENGTH]
        
        # 如果为空，返回默认值
        if not normalized:
            return "image"
        
        return normalized
    
    @staticmethod
    def ensure_relative_path(path: str, base_dir: str) -> str:
        """
        确保相对路径的正确性
        
        Args:
            path (str): 原始路径
            base_dir (str): 基础目录
            
        Returns:
            str: 规范化的相对路径
        """
        if not path:
            return ""
        
        # 确保使用正斜杠
        path = path.replace('\\', '/')
        base_dir = base_dir.replace('\\', '/')
        
        # 如果是绝对路径，转换为相对路径
        if os.path.isabs(path):
            try:
                path = os.path.relpath(path, base_dir)
                path = path.replace('\\', '/')
            except ValueError:
                # 如果无法计算相对路径，返回原路径
                pass
        
        # 移除开头的 ./
        if path.startswith('./'):
            path = path[2:]
        
        return path
    
    @staticmethod
    def generate_simple_alt_text() -> str:
        """
        生成简单的alt文本（统一使用"image"）
        
        Returns:
            str: 固定返回"image"
        """
        return "image"