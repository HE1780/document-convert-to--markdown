#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录管理器模块

统一管理项目中所有目录的创建和命名逻辑，特别是图片目录的命名规范。
提供灵活的配置支持，确保目录命名的一致性和可维护性。

主要功能：
1. 统一的图片目录创建和命名
2. 支持多种命名策略和模板
3. 文档类型特定的目录配置
4. 目录名规范化和验证

Author: AI Assistant
Date: 2025-01-27
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union

from ..config import Config
from ..logger import get_logger
from .filename_normalizer import FilenameNormalizer


class DirectoryManager:
    """
    统一的目录命名和管理器
    
    负责根据配置创建和管理项目中的各种目录，特别是图片存储目录。
    支持灵活的命名策略和模板系统。
    """
    
    def __init__(self):
        """初始化目录管理器"""
        self.logger = get_logger()
        self.config = Config.DIRECTORY_NAMING
    
    @classmethod
    def get_image_directory_path(cls, doc_name: str, doc_type: str = 'default', 
                                base_dir: Optional[str] = None) -> Path:
        """
        根据配置生成图片目录路径
        
        Args:
            doc_name: 文档名称
            doc_type: 文档类型 (pdf, docx, pptx, xlsx等)
            base_dir: 基础目录路径，如果为None则使用配置中的默认值
            
        Returns:
            Path: 生成的图片目录路径
        """
        manager = cls()
        return manager._generate_directory_path(doc_name, doc_type, base_dir)
    
    @classmethod
    def create_document_image_dir(cls, doc_name: str, doc_type: str = 'default', 
                                 base_dir: Optional[str] = None) -> Path:
        """
        创建文档专属图片目录
        
        Args:
            doc_name: 文档名称
            doc_type: 文档类型
            base_dir: 基础目录路径
            
        Returns:
            Path: 创建的图片目录路径
        """
        manager = cls()
        dir_path = manager._generate_directory_path(doc_name, doc_type, base_dir)
        
        # 创建目录
        dir_path.mkdir(parents=True, exist_ok=True)
        manager.logger.debug(f"创建图片目录: {dir_path}")
        
        return dir_path
    
    @classmethod
    def normalize_directory_name(cls, name: str, doc_type: str = 'default') -> str:
        """
        根据配置规范化目录名
        
        Args:
            name: 原始目录名
            doc_type: 文档类型
            
        Returns:
            str: 规范化后的目录名
        """
        manager = cls()
        return manager._normalize_name(name, doc_type)
    
    def _generate_directory_path(self, doc_name: str, doc_type: str, 
                                base_dir: Optional[str]) -> Path:
        """
        生成目录路径的内部方法
        
        Args:
            doc_name: 文档名称
            doc_type: 文档类型
            base_dir: 基础目录
            
        Returns:
            Path: 生成的目录路径
        """
        # 获取基础目录
        if base_dir is None:
            base_dir = self.config['image_directories']['base_dir']
        
        # 规范化文档名
        normalized_doc_name = self._normalize_name(doc_name, doc_type)
        
        # 应用文档类型特定配置
        final_doc_name = self._apply_document_type_config(normalized_doc_name, doc_type)
        
        # 生成完整路径
        template = self.config['image_directories']['structure_template']
        
        # 替换模板变量
        path_str = template.format(
            base_dir=base_dir,
            doc_name=final_doc_name,
            doc_type=doc_type
        )
        
        return Path(path_str)
    
    def _normalize_name(self, name: str, doc_type: str) -> str:
        self.logger.debug(f"Normalizing directory name: '{name}', doc_type: {doc_type}")

        """
        规范化名称的内部方法
        
        Args:
            name: 原始名称
            doc_type: 文档类型
            
        Returns:
            str: 规范化后的名称
        """
        strategy = self.config['image_directories']['naming_strategy']
        
        if strategy == 'normalized':
            # 使用FilenameNormalizer进行规范化
            if Config.FILENAME_NORMALIZATION['enabled']:
                # 重要：目录名不应该使用os.path.splitext，避免将点号后的内容误判为扩展名
                # 直接使用原始名称进行规范化
                
                # 使用与文件名相同的规范化逻辑，确保目录名和文件名一致
                # 传递 is_document_title=True 来避免截断，因为目录名需要完整保留
                temp_filename = FilenameNormalizer.normalize_filename(name, is_document_title=True)
                
                # 目录名和文件名使用相同的规范化结果，不再应用额外的长度限制
                # 确保目录名和文件名保持一致
                self.logger.debug(f"Normalized directory name: '{temp_filename}'")
                return temp_filename
            else:
                result = self._sanitize_name(name)
            return result
        
        elif strategy == 'original':
            # 保持原始名称，只做基本清理
            return self._sanitize_name(name)
        
        elif strategy == 'custom':
            # 自定义策略，可以在这里扩展
            return self._custom_normalize(name, doc_type)
        
        else:
            # 默认使用规范化策略
            self.logger.warning(f"未知的命名策略: {strategy}，使用默认规范化")
            return self._sanitize_name(name)
    
    def _apply_document_type_config(self, name: str, doc_type: str) -> str:
        """
        应用文档类型特定的配置
        
        Args:
            name: 规范化后的名称
            doc_type: 文档类型
            
        Returns:
            str: 应用配置后的名称
        """
        # 获取文档类型配置
        type_config = self.config['document_type_configs'].get(doc_type.lower(), {})
        
        # 应用前缀
        prefix = type_config.get('dir_prefix', '')
        if prefix:
            name = f"{prefix}_{name}"
        

        
        return name
    
    def _sanitize_name(self, name: str) -> str:
        """
        基本的名称清理方法
        
        Args:
            name: 原始名称（应该已经是不带扩展名的文档名）
            
        Returns:
            str: 清理后的名称
        """
        import re
        
        # 注意：传入的name应该已经是不带扩展名的文档名，
        # 不应该再使用Path.stem，否则会错误地将包含'.'的文档名截断
        # 例如：'EDC建库端_V1.0_用户手册' 会被错误截断为 'EDC建库端_V1'
        
        # 替换不安全字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe_name = re.sub(r'[\s_]+', '_', safe_name).strip('_')
        
        # 应用目录名长度限制（使用更宽松的长度限制）
        max_length = self._get_max_dir_name_length()
        if len(safe_name) > max_length:
            # 智能截断：保留前后部分，中间用...连接
            if max_length > 10:
                # 保留前一半和后一半，中间用...连接
                half = (max_length - 3) // 2
                safe_name = safe_name[:half] + '...' + safe_name[-(max_length - half - 3):]
            else:
                # 如果限制太短，直接截断
                safe_name = safe_name[:max_length]
        
        return safe_name
    
    def _get_max_dir_name_length(self) -> int:
        """
        获取目录名最大长度限制
        
        Returns:
            int: 目录名最大长度
        """
        # 直接使用配置中的目录名长度限制
        max_length = Config.DIRECTORY_NAMING.get('image_directories', {}).get('max_dir_name_length', 255)
        
        # 确保长度限制合理
        if max_length < 50:
            max_length = 255  # 使用更合理的默认值
        
        return max_length
    
    def _custom_normalize(self, name: str, doc_type: str) -> str:
        """
        自定义规范化方法，可以根据需要扩展
        
        Args:
            name: 原始名称
            doc_type: 文档类型
            
        Returns:
            str: 自定义规范化后的名称
        """
        # 这里可以实现自定义的规范化逻辑
        # 例如：根据文档类型使用不同的规范化规则
        
        if doc_type.lower() == 'pdf':
            # PDF文档的特殊处理
            return self._sanitize_name(name)
        elif doc_type.lower() == 'docx':
            # Word文档的特殊处理
            return self._sanitize_name(name)
        else:
            # 默认处理
            return self._sanitize_name(name)
    
    @classmethod
    def get_supported_templates(cls) -> Dict[str, str]:
        """
        获取支持的目录结构模板
        
        Returns:
            Dict[str, str]: 模板名称到模板字符串的映射
        """
        return {
            'default': '{base_dir}/{doc_name}',
            'type_based': '{base_dir}/{doc_type}/{doc_name}',
            'date_based': '{base_dir}/{year}/{month}/{doc_name}',
            'flat': '{base_dir}',
            'nested': '{base_dir}/{doc_type}/{doc_name}'
        }
    
    @classmethod
    def validate_template(cls, template: str) -> bool:
        """
        验证目录模板的有效性
        
        Args:
            template: 模板字符串
            
        Returns:
            bool: 模板是否有效
        """
        try:
            # 尝试格式化模板
            test_vars = {
                'base_dir': 'test',
                'doc_name': 'test_doc',
                'doc_type': 'pdf',
                'year': '2025',
                'month': '01'
            }
            template.format(**test_vars)
            return True
        except (KeyError, ValueError) as e:
            return False
    
    def cleanup_empty_directories(self, base_path: Union[str, Path]) -> int:
        """
        清理空的目录
        
        Args:
            base_path: 要清理的基础路径
            
        Returns:
            int: 清理的目录数量
        """
        base_path = Path(base_path)
        cleaned_count = 0
        
        try:
            if not base_path.exists():
                return 0
            
            # 递归清理空目录
            for dir_path in base_path.rglob('*'):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    cleaned_count += 1
                    self.logger.debug(f"删除空目录: {dir_path}")
            
            self.logger.info(f"清理完成，删除了 {cleaned_count} 个空目录")
            
        except Exception as e:
            self.logger.error(f"清理空目录失败: {e}")
        
        return cleaned_count


if __name__ == '__main__':
    # 测试目录管理器
    manager = DirectoryManager()
    
    # 测试目录创建
    test_doc_name = "测试文档.pdf"
    test_dir = manager.create_document_image_dir(test_doc_name, 'pdf', 'test_output/images')
    print(f"创建的测试目录: {test_dir}")
    
    # 测试模板验证
    templates = manager.get_supported_templates()
    for name, template in templates.items():
        is_valid = manager.validate_template(template)
        print(f"模板 {name}: {template} - {'有效' if is_valid else '无效'}")