#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理模块

本模块负责协调不同文档类型的图片处理流程。
通过使用专门的文档处理器类来处理不同类型的文档，
确保处理逻辑的分离和代码的可维护性。

主要功能：
1. 协调文档处理器的创建和使用
2. 提供统一的图片处理接口
3. 管理图片提取和插入的整体流程

Author: AI Assistant
Date: 2025-08-01
"""

import os
from pathlib import Path
from typing import Tuple

from .document_processors import DocumentProcessorFactory
from .logger import get_logger
from .utils.directory_manager import DirectoryManager


class ImageProcessor:
    """
    图片处理器类
    
    负责协调不同文档类型的图片处理流程。
    通过委托给专门的文档处理器来实现具体的处理逻辑。
    """
    
    def __init__(self, images_dir: str = "images"):
        """
        初始化图片处理器
        
        Args:
            images_dir: 图片存储根目录
        """
        self.images_dir = images_dir
        self.logger = get_logger()
        self.directory_manager = DirectoryManager()
        
        # 确保图片目录存在
        Path(self.images_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"图片处理器初始化完成 - 图片目录: {self.images_dir}")
    
    def process_images(self, content: str, doc_name: str, original_file_path: str = None) -> Tuple[str, int]:
        """
        处理文档中的所有图片
        
        Args:
            content: Markdown 内容
            doc_name: 文档名称
            original_file_path: 原始文档路径（用于直接提取图片）
            
        Returns:
            Tuple[str, int]: (更新后的内容, 图片数量)
        """
        self.logger.info(f"开始处理图片: {doc_name}")
        
        # 如果没有提供原始文件路径，只返回原始内容
        if not original_file_path or not os.path.exists(original_file_path):
            self.logger.warning(f"未提供有效的原始文件路径: {original_file_path}")
            return content, 0
        
        try:
            # 根据文件类型创建相应的文档处理器
            processor = DocumentProcessorFactory.create_processor(
                original_file_path, self.images_dir, self.directory_manager
            )
            
            # 创建文档专属的图片目录
            doc_image_dir = processor._create_document_image_dir(doc_name)
            
            # 清理旧的图片目录（如果存在）
            self._cleanup_old_images(doc_image_dir)
            
            # 从原始文档中提取图片
            extracted_images = processor.extract_images(original_file_path, doc_image_dir, doc_name)
            
            # 处理文档内容，插入图片
            updated_content, processed_count = processor.process_content(content, doc_name, extracted_images)
            
            self.logger.info(f"图片处理完成: {doc_name}, 总计 {processed_count} 张图片")
            
            return updated_content, processed_count
            
        except ValueError as e:
            self.logger.error(f"不支持的文档类型: {e}")
            return content, 0
        except Exception as e:
            self.logger.error(f"图片处理失败: {e}")
            return content, 0
    
    def _cleanup_old_images(self, doc_image_dir: Path) -> None:
        """
        清理旧的图片目录
        
        Args:
            doc_image_dir: 文档图片目录
        """
        if doc_image_dir.exists():
            import shutil
            shutil.rmtree(doc_image_dir)
            self.logger.debug(f"清理旧图片目录: {doc_image_dir}")
    
    def get_image_stats(self, doc_name: str, doc_type: str = 'default') -> dict:
        """
        获取图片处理统计信息
        
        Args:
            doc_name: 文档名称
            doc_type: 文档类型
            
        Returns:
            dict: 统计信息
        """
        try:
            # 使用DirectoryManager获取目录路径
            doc_image_dir = self.directory_manager.get_image_directory_path(
                doc_name, doc_type, self.images_dir
            )
            
            if doc_image_dir.exists():
                image_files = list(doc_image_dir.glob("*.png")) + \
                             list(doc_image_dir.glob("*.jpg")) + \
                             list(doc_image_dir.glob("*.jpeg")) + \
                             list(doc_image_dir.glob("*.gif")) + \
                             list(doc_image_dir.glob("*.bmp")) + \
                             list(doc_image_dir.glob("*.webp"))
                
                return {
                    'total_images': len(image_files),
                    'doc_image_dir_exists': True,
                    'image_dir_path': str(doc_image_dir)
                }
            else:
                return {
                    'total_images': 0,
                    'doc_image_dir_exists': False,
                    'image_dir_path': str(doc_image_dir)
                }
        except Exception as e:
            self.logger.error(f"获取图片统计信息失败: {e}")
            return {
                'total_images': 0,
                'doc_image_dir_exists': False,
                'image_dir_path': 'unknown'
            }
    
    def cleanup_empty_directories(self) -> int:
        """
        清理空的图片目录
        
        Returns:
            int: 清理的目录数量
        """
        try:
            # 使用DirectoryManager的清理功能
            cleaned_count = self.directory_manager.cleanup_empty_directories(self.images_dir)
            
            self.logger.info(f"空目录清理完成，删除了 {cleaned_count} 个目录")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理空目录失败: {str(e)}")
            return 0


if __name__ == '__main__':
    # 测试图片处理器
    processor = ImageProcessor()
    
    # 测试内容
    test_content = """
# 测试文档

这是一个测试文档，用于验证图片处理功能。

## 第一章

这里应该有一些图片。

## 第二章

更多内容和图片。
"""
    
    print("测试图片处理...")
    updated_content, image_count = processor.process_images(
        test_content, 
        "test_document", 
        "test.pdf"  # 假设的测试文件
    )
    
    print(f"处理结果:")
    print(f"图片数量: {image_count}")
    print(f"更新后的内容:")
    print(updated_content)