#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

定义项目的全局配置参数，包括目录路径、文件格式支持、
处理限制等配置项。

Author: MarkItDown Team
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """项目配置类
    
    包含所有项目相关的配置参数，支持环境变量覆盖。
    """
    
    # 基础目录配置
    PROJECT_ROOT = Path(__file__).parent.parent
    INPUT_DIR = os.getenv('MARKITDOWN_INPUT_DIR', 'input')
    OUTPUT_DIR = os.getenv('MARKITDOWN_OUTPUT_DIR', 'output')
    IMAGES_DIR = os.getenv('MARKITDOWN_IMAGES_DIR', 'output/images')
    LOGS_DIR = os.getenv('MARKITDOWN_LOGS_DIR', 'logs')
    TEMP_DIR = os.getenv('MARKITDOWN_TEMP_DIR', 'temp')
    
    # 文件处理配置
    MAX_FILE_SIZE = int(os.getenv('MARKITDOWN_MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
    MAX_IMAGE_SIZE = int(os.getenv('MARKITDOWN_MAX_IMAGE_SIZE', 10 * 1024 * 1024))   # 10MB
    
    # 支持的文件格式
    SUPPORTED_FORMATS = [
        # 文档格式
        '.pdf',
        '.docx', '.doc',
        '.pptx', '.ppt',
        '.xlsx', '.xls',
        
        # 图片格式
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
        
        # 文本格式
        '.txt', '.rtf',
        
        # 网页格式
        '.html', '.htm',
        
        # 其他格式
        '.csv', '.tsv',
        '.xml',
        '.json',
        '.md', '.markdown'
    ]
    
    # 图片格式配置
    IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    
    # 输出图片格式（统一转换为此格式）
    OUTPUT_IMAGE_FORMAT = 'png'
    
    # 图片质量设置
    IMAGE_QUALITY = 85  # JPEG质量 (1-100)
    
    # 图片尺寸限制
    MAX_IMAGE_WIDTH = 2048
    MAX_IMAGE_HEIGHT = 2048
    
    # 文本处理配置
    DEFAULT_ENCODING = 'utf-8'
    
    # PDF处理配置
    PDF_CONFIG = {
        'extract_images': True,
        'preserve_layout': False,
        'merge_paragraphs': True,
        'fix_line_breaks': True,
        'remove_headers_footers': True
    }
    
    # Word文档处理配置
    DOCX_CONFIG = {
        'extract_images': True,
        'preserve_formatting': True,
        'include_tables': True,
        'include_headers_footers': False
    }
    
    # PowerPoint处理配置
    PPTX_CONFIG = {
        'extract_images': True,
        'include_slide_notes': True,
        'slide_separator': '\n\n---\n\n',
        'preserve_slide_order': True
    }
    
    # Excel处理配置
    XLSX_CONFIG = {
        'include_all_sheets': True,
        'sheet_separator': '\n\n## ',
        'table_format': 'markdown',
        'include_formulas': False
    }
    
    # 日志配置
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_max_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
        'console_output': True
    }
    
    # 进度显示配置
    PROGRESS_CONFIG = {
        'show_progress_bar': True,
        'update_interval': 0.1,  # 秒
        'bar_length': 50
    }
    
    # 错误处理配置
    ERROR_CONFIG = {
        'max_retries': 3,
        'retry_delay': 1.0,  # 秒
        'continue_on_error': True,
        'save_error_files': True
    }
    
    # 性能配置
    PERFORMANCE_CONFIG = {
        'max_workers': 4,  # 并发处理数
        'chunk_size': 1024 * 1024,  # 1MB
        'memory_limit': 512 * 1024 * 1024,  # 512MB
        'enable_caching': True
    }
    
    # 输出格式配置
    MARKDOWN_CONFIG = {
        'line_ending': '\n',
        'heading_style': 'atx',  # atx (#) 或 setext (===)
        'bullet_style': '-',     # -, *, +
        'emphasis_style': '*',   # * 或 _
        'strong_style': '**',    # ** 或 __
        'code_fence': '```',     # ``` 或 ~~~
        'table_alignment': 'left'
    }
    
    # 图片命名配置
    IMAGE_NAMING = {
        'prefix': 'image_',
        'start_index': 1,
        'zero_padding': 3,  # image_001, image_002, ...
        'preserve_extension': True,
        'fallback_extension': 'png'
    }
    
    # 路径配置
    PATH_CONFIG = {
        'use_relative_paths': True,
        'path_separator': '/',
        'normalize_paths': True,
        'case_sensitive': False
    }
    
    # 目录命名配置
    DIRECTORY_NAMING = {
        'image_directories': {
            'base_dir': 'images',
            'structure_template': '{base_dir}/{doc_name}',
            'naming_strategy': 'normalized',
            'max_dir_name_length': 100
        },
        'document_type_configs': {
            'pdf': {'dir_prefix': 'PDF'},
            'docx': {'dir_prefix': 'Word'}
        },
    }

    # 文件名规范化配置
    FILENAME_NORMALIZATION = {
        'enabled': True,
        'max_filename_length': 200,  # 增加到200以支持更长的中文文件名
        'convert_chinese_to_pinyin': False,
        'remove_special_chars': True,
        'replacement_chars': {
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
            '\t': '_',
            '\n': '_',
            '\r': '_'
        }
    }
    
    # Alt文本配置
    ALT_TEXT_CONFIG = {
        'use_simple_alt': True,  # 统一使用"image"作为alt文本
        'simple_alt_text': 'image',
        'max_alt_length': 30,
        'preserve_original': False
    }
    
    # 目录命名配置
    DIRECTORY_NAMING = {
        # 图片目录配置
        'image_directories': {
            'base_dir': 'images',  # 基础图片目录名
            'structure_template': '{base_dir}/{doc_name}',  # 目录结构模板
            'naming_strategy': 'normalized',  # 命名策略：normalized, original, custom
            'use_document_type_prefix': False,  # 是否使用文档类型前缀
            'max_dir_name_length': 255,  # 目录名最大长度（增加到100以支持更长的中文文件名）
        },
        
        # 文件名长度配置
        'filename_limits': {
            'max_filename_length': 200,  # 文件名最大长度（统一配置）
            'max_dir_name_length': 255,  # 目录名最大长度（与image_directories保持一致）
        },
        
        # 不同文档类型的特殊配置
        'document_type_configs': {
            'pdf': {
                'dir_prefix': '',
                'use_page_info': False,
            },
            'docx': {
                'dir_prefix': '',
                'preserve_media_structure': False,
            },
            'pptx': {
                'dir_prefix': '',
                'slide_based_naming': False,
            },
            'xlsx': {
                'dir_prefix': '',
                'sheet_based_naming': False,
            }
        },
        
        # 通用目录配置
        'sync_with_filename': True,  # 图片目录名与MD文件名保持一致
        'normalize_directory_names': True,
        'use_normalized_names': True,
        'fallback_naming': 'sanitized'  # 规范化失败时的备用策略
    }
    
    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path:
        """获取相对于项目根目录的绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            Path: 绝对路径对象
        """
        return cls.PROJECT_ROOT / relative_path
    
    @classmethod
    def is_supported_format(cls, file_path: str) -> bool:
        """检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持该格式
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in cls.SUPPORTED_FORMATS
    
    @classmethod
    def is_image_format(cls, file_path: str) -> bool:
        """检查是否为图片格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为图片格式
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in cls.IMAGE_FORMATS
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取所有配置的字典表示
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        config_dict = {}
        
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                attr_value = getattr(cls, attr_name)
                if not attr_name.startswith('get_') and not attr_name.startswith('is_'):
                    config_dict[attr_name] = attr_value
        
        return config_dict
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """验证配置的有效性
        
        Returns:
            List[str]: 验证错误信息列表
        """
        errors = []
        
        # 检查文件大小限制
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE 必须大于 0")
        
        if cls.MAX_IMAGE_SIZE <= 0:
            errors.append("MAX_IMAGE_SIZE 必须大于 0")
        
        # 检查图片尺寸限制
        if cls.MAX_IMAGE_WIDTH <= 0 or cls.MAX_IMAGE_HEIGHT <= 0:
            errors.append("图片尺寸限制必须大于 0")
        
        # 检查图片质量设置
        if not (1 <= cls.IMAGE_QUALITY <= 100):
            errors.append("IMAGE_QUALITY 必须在 1-100 之间")
        
        # 检查支持格式列表
        if not cls.SUPPORTED_FORMATS:
            errors.append("SUPPORTED_FORMATS 不能为空")
        
        # 检查性能配置
        if cls.PERFORMANCE_CONFIG['max_workers'] <= 0:
            errors.append("max_workers 必须大于 0")
        
        return errors
    
    @classmethod
    def print_config(cls) -> None:
        """打印当前配置信息"""
        print("当前配置信息:")
        print("=" * 50)
        
        config_dict = cls.get_config_dict()
        for key, value in config_dict.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                print(f"{key}: {', '.join(map(str, value[:5]))}{'...' if len(value) > 5 else ''}")
            else:
                print(f"{key}: {value}")
        
        print("=" * 50)


# 创建全局配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    config.print_config()
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("\n配置验证错误:")
        for error in errors:
            print(f"- {error}")
    else:
        print("\n✅ 配置验证通过")