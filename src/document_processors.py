#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理器模块

本模块包含专门的文档处理器类，用于处理不同类型的文档（Word、PDF等）的图片提取和插入逻辑。
每种文档类型都有独立的处理器类，确保处理逻辑的分离和代码的可维护性。

主要功能：
1. 基础文档处理器抽象类
2. Word文档处理器
3. PDF文档处理器
4. 统一的文件命名和路径管理

Author: AI Assistant
Date: 2025-08-01
"""

import os
import re
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple, Dict, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    print("警告: 未找到 PyMuPDF 库，请运行: pip install PyMuPDF")
    fitz = None

from .logger import get_logger
from .config import Config
from .utils.filename_normalizer import FilenameNormalizer
from .utils.directory_manager import DirectoryManager


class BaseDocumentProcessor(ABC):
    """
    文档处理器基类
    
    定义了所有文档处理器的通用接口和方法，确保不同类型的文档处理器
    具有一致的行为和命名规范。
    """
    
    def __init__(self, images_dir: str = "images", directory_manager: 'DirectoryManager' = None):
        """
        初始化文档处理器
        
        Args:
            images_dir: 图片存储根目录
            directory_manager: 目录管理器实例
        """
        self.images_dir = Path(images_dir)
        self.logger = get_logger()
        self.directory_manager = directory_manager or DirectoryManager()
        
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不安全字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的安全文件名
        """
        # 使用FilenameNormalizer进行统一规范化
        if Config.FILENAME_NORMALIZATION['enabled']:
            return Path(FilenameNormalizer.normalize_filename(filename)).stem
        
        # 原有逻辑作为备用
        name_without_ext = Path(filename).stem
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name_without_ext)
        safe_name = re.sub(r'[\s_]+', '_', safe_name).strip('_')
        return safe_name
    
    def _normalize_document_name(self, filename: str) -> str:

        """
        使用FilenameNormalizer统一处理文档名
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 规范化后的文档名
        """
        if Config.FILENAME_NORMALIZATION['enabled']:
            # 使用与文件名相同的规范化逻辑
            # 直接处理原始文件名，不添加临时扩展名
            # 传递 is_document_title=True 来避免截断
            normalized = FilenameNormalizer.normalize_filename(filename, is_document_title=True)
            # 返回完整的规范化名称，不再使用Path.stem截断
            return normalized
        result = self._sanitize_filename(filename)

        return result
    
    def _generate_image_alt_text(self, doc_name: str, image_index: int) -> str:
        """
        生成标准化的alt文本
        
        Args:
            doc_name: 文档名称
            image_index: 图片序号
            
        Returns:
            str: 标准化的alt文本
        """
        if Config.ALT_TEXT_CONFIG['use_simple_alt']:
            return Config.ALT_TEXT_CONFIG['simple_alt_text']
        
        # 如果不使用简单alt文本，生成描述性文本
        normalized_name = FilenameNormalizer.normalize_alt_text(doc_name)
        return f"{normalized_name}_{image_index:03d}"
    
    def _get_normalized_relative_path(self, doc_name: str, image_filename: str, base_dir: str = "") -> str:
        """
        生成标准化的相对路径
        
        Args:
            doc_name: 文档名称
            image_filename: 图片文件名
            base_dir: 基础目录
            
        Returns:
            str: 标准化的相对路径
        """
        normalized_doc_name = self._normalize_document_name(doc_name)
        path = f"images/{normalized_doc_name}/{image_filename}"
        
        if base_dir:
            return FilenameNormalizer.ensure_relative_path(path, base_dir)
        return path
    
    def _create_document_image_dir(self, doc_name: str) -> Path:
        """
        创建文档专属的图片目录
        
        Args:
            doc_name: 文档名称
            
        Returns:
            Path: 创建的图片目录路径
        """
        # 获取文档类型
        doc_type = self.__class__.__name__.replace('DocumentProcessor', '').lower()
        
        # 使用统一的目录管理器创建目录
        return DirectoryManager.create_document_image_dir(
            doc_name, doc_type, str(self.images_dir)
        )
    
    def _generate_image_filename(self, index: int, extension: str = ".png") -> str:
        """
        生成标准化的图片文件名
        
        Args:
            index: 图片序号
            extension: 文件扩展名
            
        Returns:
            str: 标准化的图片文件名
        """
        return f"image_{index:03d}{extension}"
    
    def _get_relative_image_path(self, doc_name: str, image_filename: str) -> str:
        """
        获取图片的相对路径（用于Markdown链接）
        
        Args:
            doc_name: 文档名称
            image_filename: 图片文件名
            
        Returns:
            str: 图片的相对路径
        """
        # 获取文档类型
        doc_type = self.__class__.__name__.replace('DocumentProcessor', '').lower()
        
        # 使用DirectoryManager生成目录路径
        dir_path = DirectoryManager.get_image_directory_path(doc_name, doc_type)
        
        # 返回相对路径
        return f"{dir_path}/{image_filename}"
    
    def _extract_image_number(self, key: str) -> int:
        """
        从图片键值中提取数字编号
        
        Args:
            key: 图片键值
            
        Returns:
            int: 提取的数字编号
        """
        match = re.search(r'(\d+)', key)
        return int(match.group(1)) if match else 0
    
    @abstractmethod
    def extract_images(self, file_path: str, output_dir: Path, doc_name: str = None) -> Dict[str, str]:
        """
        从文档中提取图片
        
        Args:
            file_path: 文档文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        pass
    
    @abstractmethod
    def process_content(self, content: str, doc_name: str, extracted_images: Dict[str, str]) -> Tuple[str, int]:
        """
        处理文档内容，插入图片
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            extracted_images: 提取的图片映射
            
        Returns:
            Tuple[str, int]: (处理后的内容, 处理的图片数量)
        """
        pass


class WordDocumentProcessor(BaseDocumentProcessor):
    """
    Word文档处理器
    
    专门处理Word文档（.docx）的图片提取和内容处理。
    Word文档的特点是MarkItDown库已经在转换时正确插入了图片链接，
    因此只需要提取图片文件并保持原有的链接结构。
    """
    def __init__(self, images_dir: str = "images", directory_manager: 'DirectoryManager' = None):
        super().__init__(images_dir, directory_manager)
    
    def extract_images(self, file_path: str, output_dir: Path, doc_name: str = None) -> Dict[str, str]:
        """
        从Word文档中提取图片
        
        Args:
            file_path: Word文档路径
            output_dir: 输出目录（实际会使用DirectoryManager生成的路径）
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        extracted_images = {}
        
        try:
            # 如果没有提供doc_name，则从文件路径中获取
            if not doc_name:
                doc_name = Path(file_path).stem
            
            # 使用DirectoryManager创建正确的图片目录
            actual_output_dir = self._create_document_image_dir(doc_name)
            
            self.logger.info(f"开始从Word文档提取图片: {file_path}")
            self.logger.info(f"输出目录: {actual_output_dir}")
            
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                # 获取所有媒体文件
                media_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
                
                self.logger.info(f"在Word文档中发现 {len(media_files)} 个媒体文件")
                self.logger.debug(f"媒体文件列表: {media_files}")
                
                for i, media_file in enumerate(media_files, 1):
                    # 提取文件扩展名
                    file_ext = Path(media_file).suffix.lower()
                    
                    self.logger.debug(f"处理媒体文件 {i}: {media_file}, 扩展名: {file_ext}")
                    
                    # 检查是否为支持的图片格式
                    if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                        # 生成标准化的文件名
                        new_filename = self._generate_image_filename(i, file_ext)
                        output_path = actual_output_dir / new_filename
                        
                        self.logger.debug(f"准备保存图片到: {output_path}")
                        
                        # 确保输出目录存在
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 提取并保存图片
                        with docx_zip.open(media_file) as source:
                            with open(output_path, 'wb') as target:
                                target.write(source.read())
                        
                        # 验证文件是否成功保存
                        if output_path.exists():
                            self.logger.debug(f"图片保存成功: {output_path}")
                            # 记录提取的图片
                            key = f"image_{i:03d}"
                            extracted_images[key] = str(output_path)
                        else:
                            self.logger.error(f"图片保存失败: {output_path}")
                        
                        self.logger.debug(f"提取Word图片: {media_file} -> {new_filename}")
                    else:
                        self.logger.debug(f"跳过非图片文件: {media_file}")
                        
        except Exception as e:
            self.logger.error(f"提取Word文档图片失败: {e}")
            
        return extracted_images
    
    def process_content(self, content: str, doc_name: str, extracted_images: Dict[str, str]) -> Tuple[str, int]:
        """
        处理Word文档内容，应用文件名规范化
        
        将MarkItDown库插入的图片链接更新为规范化格式
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            extracted_images: 提取的图片映射
            
        Returns:
            Tuple[str, int]: (处理后的内容, 处理的图片数量)
        """
        processed_count = len([img for img in extracted_images.values() if os.path.exists(img)])
        
        # 规范化图片链接
        processed_content = self._normalize_image_links(content, doc_name, extracted_images)
        
        self.logger.info(f"Word文档图片已规范化处理，共{processed_count}张图片")
        
        return processed_content, processed_count
    
    def _normalize_image_links(self, content: str, doc_name: str, extracted_images: Dict[str, str]) -> str:
        """
        规范化Word文档中的图片链接
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            extracted_images: 提取的图片映射
            
        Returns:
            str: 规范化后的内容
        """
        if not extracted_images:
            return content
        
        # 查找所有图片链接模式
        import re
        
        # 匹配 ![...](media/image*.png) 或类似格式
        image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        
        # 用于跟踪base64图片的计数器
        base64_counter = 1
        
        def replace_image_link(match):
            nonlocal base64_counter
            alt_text = match.group(1)
            original_path = match.group(2)
            
            # 处理base64编码的图片
            if original_path.startswith('data:image'):
                # 查找对应的提取图片（按顺序匹配）
                sorted_images = sorted(extracted_images.items(), key=lambda x: self._extract_image_number(x[0]))
                if base64_counter <= len(sorted_images):
                    key, extracted_path = sorted_images[base64_counter - 1]
                    image_filename = Path(extracted_path).name
                    normalized_path = self._get_normalized_relative_path(doc_name, image_filename)
                    normalized_alt = alt_text if alt_text else self._generate_image_alt_text(doc_name, base64_counter)
                    
                    self.logger.info(f"替换base64图片 #{base64_counter}: {normalized_path}")
                    base64_counter += 1
                    return f"![{normalized_alt}]({normalized_path})"
                else:
                    base64_counter += 1
                    return match.group(0)
            
            # 处理media路径格式的图片
            image_num_match = re.search(r'image(\d+)', original_path)
            if image_num_match:
                image_num = int(image_num_match.group(1))
                
                # 查找对应的提取图片
                for key, extracted_path in extracted_images.items():
                    if f"image_{image_num:03d}" in key or f"image_{image_num}" in extracted_path:
                        # 生成规范化路径和alt文本
                        image_filename = Path(extracted_path).name
                        normalized_path = self._get_normalized_relative_path(doc_name, image_filename)
                        normalized_alt = self._generate_image_alt_text(doc_name, image_num)
                        
                        return f"![{normalized_alt}]({normalized_path})"
            
            # 如果没有找到匹配，保持原样
            return match.group(0)
        
        # 替换所有图片链接
        normalized_content = re.sub(image_pattern, replace_image_link, content)
        
        return normalized_content


class PDFDocumentProcessor(BaseDocumentProcessor):
    """
    PDF文档处理器
    
    专门处理PDF文档的图片提取和智能插入。
    PDF文档需要额外的处理逻辑来智能插入图片到正确位置。
    """
    def __init__(self, images_dir: str = "images", directory_manager: 'DirectoryManager' = None):
        super().__init__(images_dir, directory_manager)
        self.pdf_image_pages = {}  # 存储图片页面信息
    

    
    def extract_images(self, file_path: str, output_dir: Path, doc_name: str = None) -> Dict[str, str]:
        """
        从PDF文档中提取图片，并记录页面位置信息
        
        Args:
            file_path: PDF文档路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        extracted_images = {}
        
        if fitz is None:
            self.logger.warning("PyMuPDF 未安装，无法从 PDF 提取图片")
            return extracted_images
        
        try:
            self.logger.info(f"开始从PDF文档提取图片: {file_path}")
            self.logger.info(f"输出目录: {output_dir}")
            
            doc = fitz.open(file_path)
            image_count = 0
            
            # 重置图片页面信息
            self.pdf_image_pages = {}
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    image_count += 1
                    
                    # 获取图片数据
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # 确保不是 CMYK
                        # 生成标准化的文件名
                        new_filename = self._generate_image_filename(image_count, ".png")
                        output_path = output_dir / new_filename
                        
                        self.logger.debug(f"准备保存PDF图片到: {output_path}")
                        
                        # 确保输出目录存在
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 保存图片
                        pix.save(str(output_path))
                        
                        # 验证文件是否成功保存
                        if output_path.exists():
                            self.logger.debug(f"PDF图片保存成功: {output_path}")
                            # 记录图片和页面信息
                            key = f"image_{image_count:03d}"
                            extracted_images[key] = str(output_path)
                            self.pdf_image_pages[key] = page_num + 1  # 页面从1开始计数
                        else:
                            self.logger.error(f"PDF图片保存失败: {output_path}")
                        
                        self.logger.debug(f"提取PDF图片: 页面{page_num + 1} -> {new_filename}")
                    
                    pix = None  # 释放内存
            
            doc.close()
            
        except Exception as e:
            self.logger.error(f"提取PDF文档图片失败: {e}")
            
        return extracted_images
    
    def process_content(self, content: str, doc_name: str, extracted_images: Dict[str, str]) -> Tuple[str, int]:
        """
        处理PDF文档内容，智能插入图片
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            extracted_images: 提取的图片映射
            
        Returns:
            Tuple[str, int]: (处理后的内容, 处理的图片数量)
        """
        if not extracted_images:
            return content, 0
        
        # 按图片编号排序
        sorted_images = sorted(extracted_images.items(), key=lambda x: self._extract_image_number(x[0]))
        
        # 检查是否为图片型PDF（内容为空或只有少量文本）
        if not content.strip() or len(content.strip()) < 50:
            self.logger.info(f"检测到图片型PDF文档: {doc_name}，生成基于图片的Markdown结构")
            content = self._create_image_based_markdown(doc_name, sorted_images)
        else:
            # 使用智能插入逻辑
            content = self._insert_images_intelligently(content, doc_name, sorted_images)
        
        processed_count = len([img for img in sorted_images if os.path.exists(img[1])])
        
        return content, processed_count

    def _create_image_based_markdown(self, doc_name: str, sorted_images: List[Tuple[str, str]]) -> str:
        """
        为图片型PDF创建基于图片的Markdown结构
        
        Args:
            doc_name: 文档名称
            sorted_images: 排序后的图片列表
            
        Returns:
            str: 生成的Markdown内容
        """
        markdown_content = f"# {doc_name}\n\n"
        markdown_content += "**注意**: 这是一个图片型PDF文档，无法提取文本内容。以下是提取的图片：\n\n"
        
        # 按页面分组图片
        current_page = 1
        images_added_to_page = False
        
        for image_key, image_path in sorted_images:
            if not os.path.exists(image_path):
                continue
                
            # 获取图片对应的页面
            image_page = self.pdf_image_pages.get(image_key, current_page)
            
            # 如果是新页面，添加页面标题
            if image_page != current_page:
                current_page = image_page
                images_added_to_page = False
            
            if not images_added_to_page:
                markdown_content += f"## 第{current_page}页\n\n"
                images_added_to_page = True
            
            # 生成相对路径
            relative_path = self._get_relative_image_path(doc_name, os.path.basename(image_path))
            
            # 生成alt文本
            image_number = self._extract_image_number(image_key)
            alt_text = f"图片{image_number}"
            
            # 添加图片链接
            markdown_content += f"![{alt_text}]({relative_path})\n\n"
            
            self.logger.debug(f"添加图片到Markdown: {alt_text} -> {relative_path}")
        
        return markdown_content

    def _insert_images_intelligently(self, content: str, doc_name: str, sorted_images: List[Tuple[str, str]]) -> str:
        """
        智能插入图片到PDF内容中
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            sorted_images: 排序后的图片列表
            
        Returns:
            str: 插入图片后的内容
        """
        # 尝试基于图片引用进行精确插入
        content_with_images = self._insert_images_by_reference_patterns(content, doc_name, sorted_images)
        
        # 如果基于引用的插入成功，返回结果
        if content_with_images != content:
            return content_with_images
        
        # 回退到页面比例方法
        return self._insert_images_by_page_ratio(content, doc_name, sorted_images)
    
    def _insert_images_by_reference_patterns(self, content: str, doc_name: str, sorted_images: List[Tuple[str, str]]) -> str:
        """
        基于图片引用模式插入图片
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            sorted_images: 排序后的图片列表
            
        Returns:
            str: 插入图片后的内容
        """
        lines = content.split('\n')
        inserted_count = 0
        
        # 图片引用模式（优化匹配规则，增加专门的"图+数字"模式）
        patterns = [
            # 最高优先级：表格引用模式
            {'pattern': r'表\s*(\d+)\s*[-–—]\s*(\d+)', 'type': 'sequential'},  # 表格引用模式
            {'pattern': r'表\s*(\d+)\s*[._]\s*(\d+)', 'type': 'sequential'},
            {'pattern': r'表\s*(\d+)(?!\s*[-–—._]\d)', 'type': 'sequential'},
            # 图片引用模式
            {'pattern': r'图\s*(\d+)\s*[-–—]\s*(\d+)', 'type': 'sequential'},  # 专门匹配"图 2-1"格式
            {'pattern': r'图\s*(\d+)\s*[._]\s*(\d+)', 'type': 'sequential'},   # 匹配"图 2.1"或"图 2_1"格式
            {'pattern': r'图\s*(\d+)(?!\s*[-–—._]\d)', 'type': 'sequential'},  # 匹配单独的"图 2"格式
            {'pattern': r'Fig\s*(\d+)[-_\s]*(\d*)', 'type': 'sequential'},  # Fig 1-1, Fig1
            {'pattern': r'Figure\s*(\d+)[-_\s]*(\d*)', 'type': 'sequential'},  # Figure 1-1
            {'pattern': r'Table\s*(\d+)[-_\s]*(\d*)', 'type': 'sequential'},  # Table 1-1, Table1
            {'pattern': r'见图', 'type': 'keyword'},  # 见图
            {'pattern': r'如图', 'type': 'keyword'},  # 如图
            {'pattern': r'图示', 'type': 'keyword'},  # 图示
            {'pattern': r'上图', 'type': 'keyword'},  # 上图
            {'pattern': r'下图', 'type': 'keyword'},  # 下图
            {'pattern': r'如图所示', 'type': 'keyword'},  # 如图所示
            {'pattern': r'参见图', 'type': 'keyword'},  # 参见图
            {'pattern': r'详见图', 'type': 'keyword'},  # 详见图
            {'pattern': r'诊疗流程.*?图', 'type': 'keyword'},  # 诊疗流程图
            {'pattern': r'流程图', 'type': 'keyword'},  # 流程图
            {'pattern': r'示意图', 'type': 'keyword'},  # 示意图
            {'pattern': r'示例图', 'type': 'keyword'},  # 示例图
            {'pattern': r'附图', 'type': 'keyword'},  # 附图
            {'pattern': r'配图', 'type': 'keyword'},  # 配图
            {'pattern': r'右图', 'type': 'keyword'},  # 右图
            {'pattern': r'左图', 'type': 'keyword'},  # 左图
        ]
        
        # 先收集所有"图 X-Y"格式的引用位置
        figure_references = []
        for i, line in enumerate(lines):
            for pattern_info in patterns:
                if pattern_info['type'] == 'sequential':
                    pattern = pattern_info['pattern']
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if match.groups():
                            try:
                                ref_number = int(match.group(1))
                                second_number = None
                                if len(match.groups()) > 1 and match.group(2) and match.group(2).strip():
                                    second_number = int(match.group(2))
                                
                                # 计算权重分数
                                score = 0.5  # 基础分数
                                if second_number is not None:
                                    # "图 X-Y"格式，给予更高权重
                                    if '图' in line and ('-' in line or '–' in line or '—' in line):
                                        score = 0.85
                                    else:
                                        score = 0.75
                                    
                                    # 添加特殊关键词加权
                                    if any(keyword in line for keyword in ['诊疗', '流程', '示意', '获得性']):
                                        score += 0.1
                                else:
                                    # 单独的"图 X"格式
                                    score = 0.6
                                    if any(keyword in line for keyword in ['诊疗', '流程', '示意']):
                                        score += 0.15
                                
                                figure_references.append({
                                    'line_index': i,
                                    'ref_number': ref_number,
                                    'second_number': second_number,
                                    'score': score,
                                    'line_content': line
                                })
                            except (ValueError, IndexError):
                                pass
        
        # 按行号排序，确保按文档顺序处理
        figure_references.sort(key=lambda x: x['line_index'])
        
        # 按顺序为每个图片引用插入图片
        used_references = set()
        for idx, (key, image_path) in enumerate(sorted_images):
            if not os.path.exists(image_path):
                continue
            
            image_name = Path(image_path).name
            relative_path = self._get_normalized_relative_path(doc_name, image_name)
            
            # 生成图片引用
            image_number = self._extract_image_number(key)
            alt_text = self._generate_image_alt_text(doc_name, image_number)
            image_ref = f"![{alt_text}]({relative_path})"
            
            # 寻找最佳匹配的引用位置（按顺序且未使用过的）
            best_ref = None
            for ref in figure_references:
                if ref['line_index'] not in used_references and ref['score'] > 0.25:
                    best_ref = ref
                    break
            
            # 如果找到合适的引用位置，插入图片
            if best_ref:
                insert_pos = self._find_insert_position_after_reference(lines, best_ref['line_index'])
                # 调整插入位置，考虑之前插入的图片
                adjustment = sum(1 for used_line in used_references if used_line < best_ref['line_index']) * 2
                insert_pos += adjustment
                
                lines.insert(insert_pos, "")
                lines.insert(insert_pos + 1, image_ref)
                inserted_count += 1
                used_references.add(best_ref['line_index'])
                
                self.logger.info(f"基于引用模式插入图片 {image_name} 到第 {insert_pos + 1} 行，匹配分数: {best_ref['score']:.2f}，引用: {best_ref['line_content'].strip()[:50]}...")
        
        if inserted_count > 0:
            self.logger.info(f"成功基于引用模式插入 {inserted_count} 张图片")
            return '\n'.join(lines)
        
        return content
    
    def _calculate_match_score(self, match, image_number: int, line: str, pattern_type: str = 'normal') -> float:
        """
        计算图片引用匹配度分数
        
        Args:
            match: 正则匹配对象
            image_number: 图片编号
            line: 文本行
            pattern_type: 匹配模式类型 ('sequential' 表示顺序匹配)
            
        Returns:
            float: 匹配度分数 (0-1)
        """
        score = 0.2  # 基础分数
        
        # 如果匹配到数字，检查数字匹配度
        if match.groups():
            try:
                ref_number = int(match.group(1))
                
                # 对于顺序匹配模式，使用不同的匹配策略
                if pattern_type == 'sequential':
                    # 顺序匹配：按图片顺序匹配，不合并数字
                    if ref_number == image_number:
                        score += 0.6  # 顺序完全匹配
                    elif abs(ref_number - image_number) <= 2:
                        score += 0.4  # 顺序接近匹配
                    
                    # 处理第二个数字（如果存在）
                    if len(match.groups()) > 1 and match.group(2):
                        second_number = int(match.group(2))
                        # 对于"图 2-1"格式，检查是否为子图编号
                        if second_number == 1 and ref_number == image_number:
                            score += 0.2  # 子图匹配
                else:
                    # 原有的匹配逻辑
                    # 处理第二个数字（如果存在）
                    second_number = None
                    if len(match.groups()) > 1 and match.group(2):
                        second_number = int(match.group(2))
                        # 对于'图 2-1'格式，组合数字进行匹配
                        combined_ref = ref_number * 10 + second_number if second_number < 10 else ref_number * 100 + second_number
                        if combined_ref == image_number:
                            score += 0.6  # 组合数字完全匹配
                        elif abs(combined_ref - image_number) <= 3:
                            score += 0.4  # 组合数字接近
                    
                    # 第一个数字匹配
                    if ref_number == image_number:
                        score += 0.5  # 数字完全匹配
                    elif abs(ref_number - image_number) <= 5:  # 扩大匹配范围
                        score += 0.3  # 数字接近
                    elif abs(ref_number - image_number) <= 10:  # 更宽松的匹配
                        score += 0.1  # 数字相对接近
                    
            except (ValueError, IndexError):
                pass
        
        # 检查特殊关键词
        if any(keyword in line for keyword in ['诊疗', '流程', '示意', '图表', '图像', '插图', 'AHA', '止血']):
            score += 0.2
        
        # 检查是否包含"见图"等引用词
        if any(keyword in line for keyword in ['见图', '如图', '参见', '详见', '选择']):
            score += 0.15
        
        return min(score, 1.0)
    
    def _find_insert_position_after_reference(self, lines: List[str], ref_line: int) -> int:
        """
        在引用后找到最佳插入位置
        
        Args:
            lines: 文本行列表
            ref_line: 引用所在行
            
        Returns:
            int: 插入位置
        """
        # 从引用行开始向下查找，扩大搜索范围
        for i in range(ref_line + 1, min(ref_line + 10, len(lines))):
            line = lines[i].strip()
            
            # 如果是空行、段落结束或新章节开始，在此处插入
            if not line or line.startswith('#') or line.startswith('##') or line.startswith('###'):
                return i
            
            # 如果遇到句号结尾的行，在下一行插入
            if line.endswith('。') or line.endswith('.') or line.endswith('：') or line.endswith(':'):
                # 检查下一行是否为空或新段落
                if i + 1 < len(lines) and (not lines[i + 1].strip() or lines[i + 1].strip().startswith('#')):
                    return i + 1
        
        # 如果没找到合适位置，在引用行后插入
        return ref_line + 1
    
    def _insert_images_by_page_ratio(self, content: str, doc_name: str, sorted_images: List[Tuple[str, str]]) -> str:
        """
        基于页面比例插入图片（回退方法）
        
        Args:
            content: Markdown内容
            doc_name: 文档名称
            sorted_images: 排序后的图片列表
            
        Returns:
            str: 插入图片后的内容
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        # 估算文档总页数（基于内容长度）
        estimated_total_pages = max(10, total_lines // 50)  # 假设每页约50行
        
        for key, image_path in sorted_images:
            if not os.path.exists(image_path):
                continue
            
            page_num = self.pdf_image_pages.get(key, 1)
            image_name = Path(image_path).name
            relative_path = self._get_normalized_relative_path(doc_name, image_name)
            
            # 生成图片引用
            image_number = self._extract_image_number(key)
            alt_text = self._generate_image_alt_text(doc_name, image_number)
            image_ref = f"![{alt_text}]({relative_path})"
            
            # 根据页面比例计算插入位置
            estimated_line = int((page_num / estimated_total_pages) * total_lines)
            estimated_line = max(0, min(estimated_line, total_lines - 1))
            
            # 寻找更合适的插入位置（避免插入到段落中间）
            best_position = self._find_best_insertion_point(lines, estimated_line)
            
            # 插入图片
            lines.insert(best_position, "")
            lines.insert(best_position + 1, image_ref)
            
            self.logger.debug(f"基于页面比例插入图片 {image_name} 到第 {best_position + 1} 行")
        
        return '\n'.join(lines)
    
    def _find_best_insertion_point(self, lines: List[str], target_line: int) -> int:
        """
        在目标行附近找到最佳插入点
        
        Args:
            lines: 文本行列表
            target_line: 目标行号
            
        Returns:
            int: 最佳插入位置
        """
        # 在目标行前后搜索合适的插入点
        search_range = 10
        start = max(0, target_line - search_range)
        end = min(len(lines), target_line + search_range)
        
        # 优先寻找空行或段落结束
        for i in range(target_line, end):
            if i < len(lines):
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    return i
        
        # 向前搜索
        for i in range(target_line - 1, start - 1, -1):
            if i >= 0:
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    return i + 1
        
        # 如果没找到合适位置，返回目标行
        return target_line


class ImageDocumentProcessor(BaseDocumentProcessor):
    """
    图片文档处理器
    
    专门处理单个图片文件转换为Markdown的情况
    """
    
    def extract_images(self, file_path: str, output_dir: Path) -> Dict[str, str]:
        """
        对于图片文件，直接复制到目标目录
        
        Args:
            file_path: 图片文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片映射字典 {原始名称: 新文件名}
        """
        try:
            import shutil
            
            self.logger.info(f"开始复制图片文件: {file_path}")
            self.logger.info(f"目标输出目录: {output_dir}")
            
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"输出目录创建成功: {output_dir}")
            
            # 获取原始文件信息
            source_path = Path(file_path)
            if not source_path.exists():
                self.logger.error(f"源图片文件不存在: {file_path}")
                return {}
            
            # 生成目标文件名
            target_filename = self._generate_image_filename(1, source_path.suffix)
            target_path = output_dir / target_filename
            
            self.logger.info(f"目标文件路径: {target_path}")
            
            # 复制图片文件
            shutil.copy2(source_path, target_path)
            
            # 验证复制是否成功
            if target_path.exists():
                self.logger.info(f"图片文件已成功复制: {source_path.name} -> {target_filename}")
                self.logger.info(f"复制后文件大小: {target_path.stat().st_size} 字节")
            else:
                self.logger.error(f"图片文件复制失败，目标文件不存在: {target_path}")
                return {}
            
            return {source_path.name: target_filename}
            
        except Exception as e:
            self.logger.error(f"复制图片文件失败: {str(e)}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return {}
    
    def process_content(self, content: str, doc_name: str, extracted_images: Dict[str, str]) -> Tuple[str, int]:
        """
        处理图片文件的Markdown内容
        
        Args:
            content: 原始Markdown内容
            doc_name: 文档名称
            extracted_images: 提取的图片映射
            
        Returns:
            Tuple[str, int]: (处理后的内容, 图片数量)
        """
        if not extracted_images:
            return content, 0
        
        # 获取原始图片文件信息
        original_filename = list(extracted_images.keys())[0]
        image_filename = list(extracted_images.values())[0]
        image_path = self._get_normalized_relative_path(doc_name, Path(image_filename).name)
        
        # 尝试获取图片元数据
        try:
            from PIL import Image
            import os
            
            # 构建原始图片路径（假设在input目录）
            original_path = f"input/{original_filename}"
            if os.path.exists(original_path):
                with Image.open(original_path) as img:
                    width, height = img.size
                    format_info = img.format or "Unknown"
                    mode = img.mode
                    file_size = os.path.getsize(original_path)
                
                # 生成包含元数据的完整Markdown内容
                processed_content = f"""# {doc_name}

## 图片信息

- **文件名**: {original_filename}
- **尺寸**: {width} x {height} 像素
- **格式**: {format_info}
- **颜色模式**: {mode}
- **文件大小**: {file_size} 字节

## 图片预览

![{self._generate_image_alt_text(doc_name, 1)}]({image_path})

---

*此文档由 MarkItDown 自动生成*
"""
            else:
                # 如果找不到原始文件，使用简化版本
                processed_content = f"""# {doc_name}

## 图片文件

- **文件名**: {original_filename}

## 图片预览

![{self._generate_image_alt_text(doc_name, 1)}]({image_path})

---

*此文档由 MarkItDown 自动生成*
"""
                
        except ImportError:
            self.logger.warning("PIL 库未安装，使用简化的图片处理")
            # 生成简化的Markdown内容
            processed_content = f"""# {doc_name}

## 图片文件

- **文件名**: {original_filename}

## 图片预览

![{self._generate_image_alt_text(doc_name, 1)}]({image_path})

---

*此文档由 MarkItDown 自动生成*
"""
        except Exception as e:
            self.logger.warning(f"无法读取图片元数据: {e}")
            # 生成简化的Markdown内容
            processed_content = f"""# {doc_name}

## 图片文件

- **文件名**: {original_filename}

## 图片预览

![{self._generate_image_alt_text(doc_name, 1)}]({image_path})

---

*此文档由 MarkItDown 自动生成*
"""
        
        self.logger.info(f"图片内容处理完成，插入了 1 张图片")
        return processed_content, 1


class DocumentProcessorFactory:
    """
    文档处理器工厂类
    """
    
    @staticmethod
    def create_processor(file_path: str, images_dir: str = "images", directory_manager: 'DirectoryManager' = None) -> BaseDocumentProcessor:
        """
        根据文件类型创建文档处理器
        
        Args:
            file_path: 文件路径
            images_dir: 图片存储目录
            
        Returns:
            BaseDocumentProcessor: 对应的文档处理器实例
            
        Raises:
            ValueError: 不支持的文件类型
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.docx', '.doc']:
            return WordDocumentProcessor(images_dir, directory_manager)
        elif file_ext == '.pdf':
            return PDFDocumentProcessor(images_dir, directory_manager)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return ImageDocumentProcessor(images_dir, directory_manager)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")