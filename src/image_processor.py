#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理器模块

负责从文档中提取图片、重新组织存储结构、
更新图片引用路径等图片相关的处理功能。

Author: MarkItDown Team
Version: 1.0.0
"""

import os
import re
import base64
import hashlib
import zipfile
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from urllib.parse import urlparse
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    print("警告: 未找到 Pillow 库，请运行: pip install Pillow")
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    print("警告: 未找到 PyMuPDF 库，请运行: pip install PyMuPDF")
    fitz = None

from .config import Config
from .logger import get_logger, log_function_call
from .path_manager import PathManager


class ImageInfo:
    """图片信息类
    
    存储图片的相关信息，包括原始数据、格式、尺寸等。
    """
    
    def __init__(self, data: bytes, format_type: str, original_path: str = ""):
        """初始化图片信息
        
        Args:
            data: 图片二进制数据
            format_type: 图片格式
            original_path: 原始路径
        """
        self.data = data
        self.format_type = format_type.lower()
        self.original_path = original_path
        self.size = len(data)
        self.width = 0
        self.height = 0
        self.hash = self._calculate_hash()
        
        # 尝试获取图片尺寸
        self._extract_dimensions()
    
    def _calculate_hash(self) -> str:
        """计算图片数据的哈希值
        
        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(self.data).hexdigest()[:8]
    
    def _extract_dimensions(self) -> None:
        """提取图片尺寸信息"""
        if Image is None:
            return
        
        try:
            with Image.open(BytesIO(self.data)) as img:
                self.width, self.height = img.size
        except Exception:
            # 如果无法读取尺寸，保持默认值
            pass
    
    def is_valid(self) -> bool:
        """检查图片是否有效
        
        Returns:
            bool: 图片是否有效
        """
        return (
            len(self.data) > 0 and
            self.size <= Config.MAX_IMAGE_SIZE and
            self.format_type in [fmt.lstrip('.') for fmt in Config.IMAGE_FORMATS]
        )
    
    def get_file_extension(self) -> str:
        """获取文件扩展名
        
        Returns:
            str: 文件扩展名
        """
        if self.format_type in ['jpeg', 'jpg']:
            return '.jpg'
        elif self.format_type == 'png':
            return '.png'
        elif self.format_type == 'gif':
            return '.gif'
        elif self.format_type == 'bmp':
            return '.bmp'
        elif self.format_type == 'webp':
            return '.webp'
        else:
            return f'.{Config.IMAGE_NAMING["fallback_extension"]}'


class ImageProcessor:
    """图片处理器类
    
    负责处理文档中的图片，包括提取、保存、路径更新等功能。
    """
    
    def __init__(self, images_dir: str = None, base_dir: str = None, logger = None):
        """初始化图片处理器
        
        Args:
            images_dir: 图片保存目录
            base_dir: 基础目录
            logger: 日志器实例
        """
        self.logger = logger or get_logger()
        self.images_dir = images_dir or Config.IMAGES_DIR
        self.path_manager = PathManager()
        
        # 图片计数器
        self.image_counter = {}
        
        # 支持的图片模式
        self.base64_pattern = re.compile(
            r'!\[([^\]]*)\]\(data:image/([^;]+);base64,([A-Za-z0-9+/=]+)\)',
            re.IGNORECASE
        )
        
        self.url_pattern = re.compile(
            r'!\[([^\]]*)\]\(([^)]+\.(png|jpg|jpeg|gif|bmp|webp|tiff))\)',
            re.IGNORECASE
        )
        
        self.logger.debug(f"图片处理器初始化完成 - 图片目录: {self.images_dir}")
    
    @log_function_call
    def process_images(self, content: str, doc_name: str, original_file_path: str = None) -> Tuple[str, int]:
        """处理文档中的所有图片
        
        Args:
            content: Markdown 内容
            doc_name: 文档名称
            original_file_path: 原始文档路径（用于直接提取图片）
            
        Returns:
            Tuple[str, int]: (更新后的内容, 图片数量)
        """
        self.logger.info(f"开始处理图片: {doc_name}")
        
        # 重置计数器
        self.image_counter[doc_name] = 0
        
        # 清理旧的图片目录（如果存在）
        safe_doc_name = self._sanitize_filename(doc_name)
        old_doc_image_dir = Path(self.images_dir) / safe_doc_name
        if old_doc_image_dir.exists():
            import shutil
            shutil.rmtree(old_doc_image_dir)
            self.logger.debug(f"清理旧图片目录: {old_doc_image_dir}")
        
        # 创建文档专属图片目录
        doc_image_dir = self._create_document_image_dir(doc_name)
        
        # 如果提供了原始文件路径，尝试直接提取图片
        extracted_images = {}
        if original_file_path and os.path.exists(original_file_path):
            extracted_images = self._extract_images_from_source(original_file_path, doc_image_dir)
        
        # 处理 base64 编码的图片（包括截断的）
        content, base64_count = self._process_base64_images(content, doc_name, doc_image_dir, extracted_images)
        
        # 处理 URL 引用的图片
        content, url_count = self._process_url_images(content, doc_name, doc_image_dir)
        
        # 处理现有的相对路径图片引用（如 media/image1.png）
        content, path_count = self._process_existing_image_paths(content, doc_name, doc_image_dir)
        
        total_images = base64_count + url_count + path_count
        
        self.logger.info(f"图片处理完成: {doc_name}, 总计 {total_images} 张图片")
        self.logger.debug(f"  Base64图片: {base64_count}")
        self.logger.debug(f"  URL图片: {url_count}")
        self.logger.debug(f"  路径图片: {path_count}")
        
        return content, total_images
    
    def _create_document_image_dir(self, doc_name: str) -> Path:
        """创建文档专属的图片目录
        
        Args:
            doc_name: 文档名称
            
        Returns:
            Path: 图片目录路径
        """
        # 清理文档名称，移除不安全字符
        safe_doc_name = self._sanitize_filename(doc_name)
        doc_image_dir = Path(self.images_dir) / safe_doc_name
        
        # 创建目录
        doc_image_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"创建图片目录: {doc_image_dir}")
        return doc_image_dir
    
    def _extract_images_from_source(self, file_path: str, output_dir: Path) -> Dict[str, str]:
        """从原始文档中直接提取图片
        
        Args:
            file_path: 原始文档路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        extracted_images = {}
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.docx':
                extracted_images = self._extract_from_docx(file_path, output_dir)
            elif file_ext == '.pdf':
                extracted_images = self._extract_from_pdf(file_path, output_dir)
            else:
                self.logger.debug(f"不支持从 {file_ext} 格式直接提取图片")
        except Exception as e:
            self.logger.error(f"从原始文档提取图片失败: {e}")
        
        return extracted_images
    
    def _extract_from_docx(self, docx_path: str, output_dir: Path) -> Dict[str, str]:
        """从 DOCX 文档中提取图片
        
        Args:
            docx_path: DOCX 文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        extracted_images = {}
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # 获取所有媒体文件
                media_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
                
                self.logger.debug(f"在 DOCX 中发现 {len(media_files)} 个媒体文件")
                
                for i, media_file in enumerate(media_files, 1):
                    # 提取文件扩展名
                    original_name = Path(media_file).name
                    file_ext = Path(media_file).suffix.lower()
                    
                    # 检查是否为支持的图片格式
                    if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                        # 生成新的文件名
                        new_filename = f"image_{i:03d}{file_ext}"
                        output_path = output_dir / new_filename
                        
                        # 提取并保存图片
                        with docx_zip.open(media_file) as source:
                            with open(output_path, 'wb') as target:
                                target.write(source.read())
                        
                        # 记录映射关系（使用原始文件名作为键）
                        extracted_images[original_name] = str(output_path)
                        extracted_images[f"image{i}"] = str(output_path)  # 备用索引
                        
                        self.logger.debug(f"提取图片: {original_name} -> {new_filename}")
                        
        except Exception as e:
            self.logger.error(f"从 DOCX 提取图片失败: {e}")
        
        return extracted_images
    
    def _extract_from_pdf(self, pdf_path: str, output_dir: Path) -> Dict[str, str]:
        """从 PDF 文档中提取图片
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片索引到文件路径的映射
        """
        extracted_images = {}
        
        if fitz is None:
            self.logger.warning("PyMuPDF 未安装，无法从 PDF 提取图片")
            return extracted_images
        
        try:
            doc = fitz.open(pdf_path)
            image_count = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    image_count += 1
                    
                    # 获取图片数据
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # 确保不是 CMYK
                        # 生成文件名
                        img_ext = ".png"
                        new_filename = f"image_{image_count:03d}{img_ext}"
                        output_path = output_dir / new_filename
                        
                        # 保存图片
                        pix.save(str(output_path))
                        
                        # 记录映射关系
                        extracted_images[f"image{image_count}"] = str(output_path)
                        
                        self.logger.debug(f"从 PDF 提取图片: 页面{page_num+1} -> {new_filename}")
                    
                    pix = None
            
            doc.close()
            self.logger.debug(f"从 PDF 提取了 {image_count} 张图片")
            
        except Exception as e:
            self.logger.error(f"从 PDF 提取图片失败: {e}")
        
        return extracted_images
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换不安全字符（包括括号）
        unsafe_chars = r'[<>:"/\\|?*()]'
        safe_name = re.sub(unsafe_chars, '_', filename)
        
        # 移除多余的空格和点
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        safe_name = safe_name.strip('.')
        
        # 确保不为空
        if not safe_name:
            safe_name = 'unnamed_document'
        
        return safe_name
    
    def _process_base64_images(self, content: str, doc_name: str, doc_image_dir: Path, extracted_images: Dict[str, str] = None) -> Tuple[str, int]:
        """处理 base64 编码的图片（包括截断的）
        
        Args:
            content: Markdown 内容
            doc_name: 文档名称
            doc_image_dir: 图片目录
            extracted_images: 从原始文档提取的图片映射
            
        Returns:
            Tuple[str, int]: (更新后的内容, 处理的图片数量)
        """
        extracted_images = extracted_images or {}
        processed_count = 0
        
        # 处理截断的 base64 图片
        truncated_pattern = re.compile(
            r'!\[([^\]]*)\]\(data:image/([^;]+);base64\.\.\.\)',
            re.IGNORECASE
        )
        
        def replace_truncated_image(match):
            nonlocal processed_count
            
            original_alt_text = match.group(1) or "图片"
            format_type = match.group(2)
            
            # 尝试从提取的图片中找到对应的图片
            image_path = None
            
            # 尝试不同的键来匹配图片
            possible_keys = [
                f"image{processed_count + 1}.{format_type}",
                f"image{processed_count + 1:03d}.{format_type}",
                f"image{processed_count + 1}",
                f"image{len(extracted_images)}"
            ]
            
            for key in possible_keys:
                if key in extracted_images:
                    image_path = extracted_images[key]
                    break
            
            if image_path and os.path.exists(image_path):
                # 使用提取的图片
                relative_path = self._get_relative_image_path(doc_name, Path(image_path).name)
                processed_count += 1
                # 生成新的 alt 文本格式: image_文件名
                alt_text = f"image_{doc_name}_{processed_count:03d}"
                self.logger.debug(f"替换截断的图片引用: {original_alt_text} -> {Path(image_path).name}")
                return f"![{alt_text}]({relative_path})"
            else:
                self.logger.warning(f"无法找到截断图片的对应文件: {alt_text}")
                return match.group(0)
        
        # 先处理截断的图片
        content = truncated_pattern.sub(replace_truncated_image, content)
        
        def replace_base64_image(match):
            nonlocal processed_count
            
            original_alt_text = match.group(1) or "图片"
            image_format = match.group(2)
            base64_data = match.group(3)
            
            try:
                # 解码 base64 数据
                image_data = base64.b64decode(base64_data)
                
                # 创建图片信息对象
                image_info = ImageInfo(image_data, image_format)
                
                if not image_info.is_valid():
                    self.logger.warning(f"无效的图片数据，跳过处理: {doc_name}")
                    return match.group(0)  # 返回原始内容
                
                # 生成图片文件名
                image_filename = self._generate_image_filename(doc_name, image_info)
                image_path = doc_image_dir / image_filename
                
                # 保存图片
                if self._save_image(image_info, image_path):
                    # 生成新的 Markdown 引用
                    relative_path = self._get_relative_image_path(doc_name, image_filename)
                    processed_count += 1
                    
                    # 生成新的 alt 文本格式: image_文件名
                    alt_text = f"image_{doc_name}_{processed_count:03d}"
                    new_reference = f"![{alt_text}]({relative_path})"
                    self.logger.debug(f"处理 base64 图片: {image_filename}")
                    
                    return new_reference
                else:
                    self.logger.error(f"保存图片失败: {image_filename}")
                    return match.group(0)
                    
            except Exception as e:
                self.logger.error(f"处理 base64 图片异常: {str(e)}")
                return match.group(0)
        
        # 替换所有完整的 base64 图片
        updated_content = self.base64_pattern.sub(replace_base64_image, content)
        
        return updated_content, processed_count
    
    def _process_url_images(self, content: str, doc_name: str, doc_image_dir: Path) -> Tuple[str, int]:
        """处理 URL 引用的图片
        
        Args:
            content: Markdown 内容
            doc_name: 文档名称
            doc_image_dir: 图片目录
            
        Returns:
            Tuple[str, int]: (更新后的内容, 处理的图片数量)
        """
        processed_count = 0
        
        def replace_url_image(match):
            nonlocal processed_count
            
            original_alt_text = match.group(1) or "图片"
            image_url = match.group(2)
            image_extension = match.group(3)
            
            try:
                # 检查是否为本地文件
                if self._is_local_file(image_url):
                    # 处理本地文件
                    local_path = Path(image_url)
                    if local_path.exists() and local_path.is_file():
                        # 读取本地图片文件
                        with open(local_path, 'rb') as f:
                            image_data = f.read()
                        
                        image_info = ImageInfo(image_data, image_extension, str(local_path))
                        
                        if image_info.is_valid():
                            # 生成新的文件名并保存
                            image_filename = self._generate_image_filename(doc_name, image_info)
                            image_path = doc_image_dir / image_filename
                            
                            if self._save_image(image_info, image_path):
                                relative_path = self._get_relative_image_path(doc_name, image_filename)
                                processed_count += 1
                                
                                # 生成新的 alt 文本格式: image_文件名
                                alt_text = f"image_{doc_name}_{processed_count:03d}"
                                new_reference = f"![{alt_text}]({relative_path})"
                                self.logger.debug(f"处理本地图片: {image_filename}")
                                
                                return new_reference
                
                # 对于网络 URL，暂时保持原样（可以扩展为下载功能）
                self.logger.debug(f"保持网络图片引用: {image_url}")
                return match.group(0)
                
            except Exception as e:
                self.logger.error(f"处理 URL 图片异常: {image_url}, 错误: {str(e)}")
                return match.group(0)
        
        # 替换所有 URL 图片
        updated_content = self.url_pattern.sub(replace_url_image, content)
        
        return updated_content, processed_count
    
    def _is_local_file(self, url: str) -> bool:
        """检查 URL 是否为本地文件
        
        Args:
            url: 图片 URL
            
        Returns:
            bool: 是否为本地文件
        """
        parsed = urlparse(url)
        return not parsed.scheme or parsed.scheme == 'file'
    
    def _generate_image_filename(self, doc_name: str, image_info: ImageInfo) -> str:
        """生成图片文件名
        
        Args:
            doc_name: 文档名称
            image_info: 图片信息
            
        Returns:
            str: 图片文件名
        """
        # 获取当前计数
        self.image_counter[doc_name] += 1
        current_index = self.image_counter[doc_name]
        
        # 生成文件名
        prefix = Config.IMAGE_NAMING['prefix']
        padding = Config.IMAGE_NAMING['zero_padding']
        extension = image_info.get_file_extension()
        
        filename = f"{prefix}{current_index:0{padding}d}{extension}"
        
        return filename
    
    def _save_image(self, image_info: ImageInfo, image_path: Path) -> bool:
        """保存图片到文件
        
        Args:
            image_info: 图片信息
            image_path: 保存路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            image_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查是否需要图片处理
            if Image is not None and self._should_process_image(image_info):
                # 使用 PIL 处理图片
                processed_data = self._process_image_with_pil(image_info)
                if processed_data:
                    image_data = processed_data
                else:
                    image_data = image_info.data
            else:
                image_data = image_info.data
            
            # 写入文件
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            self.logger.debug(f"图片保存成功: {image_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存图片失败: {image_path}, 错误: {str(e)}")
            return False
    
    def _should_process_image(self, image_info: ImageInfo) -> bool:
        """判断是否需要处理图片
        
        Args:
            image_info: 图片信息
            
        Returns:
            bool: 是否需要处理
        """
        # 检查尺寸是否超限
        if (image_info.width > Config.MAX_IMAGE_WIDTH or 
            image_info.height > Config.MAX_IMAGE_HEIGHT):
            return True
        
        # 检查是否需要格式转换
        if Config.OUTPUT_IMAGE_FORMAT and image_info.format_type != Config.OUTPUT_IMAGE_FORMAT:
            return True
        
        return False
    
    def _process_image_with_pil(self, image_info: ImageInfo) -> Optional[bytes]:
        """使用 PIL 处理图片
        
        Args:
            image_info: 图片信息
            
        Returns:
            Optional[bytes]: 处理后的图片数据
        """
        try:
            with Image.open(BytesIO(image_info.data)) as img:
                # 处理CMYK模式
                if img.mode == 'CMYK':
                    img = img.convert('RGB')
                
                # 转换模式（如果需要）
                if img.mode in ('RGBA', 'LA', 'P') and Config.OUTPUT_IMAGE_FORMAT == 'jpg':
                    # JPEG 不支持透明度，转换为 RGB
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # 调整尺寸（如果需要）
                if (img.width > Config.MAX_IMAGE_WIDTH or 
                    img.height > Config.MAX_IMAGE_HEIGHT):
                    img.thumbnail((Config.MAX_IMAGE_WIDTH, Config.MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                
                # 保存到字节流
                output = BytesIO()
                save_format = Config.OUTPUT_IMAGE_FORMAT.upper() if Config.OUTPUT_IMAGE_FORMAT else image_info.format_type.upper()
                
                if save_format == 'JPG':
                    save_format = 'JPEG'
                
                save_kwargs = {}
                if save_format == 'JPEG':
                    save_kwargs['quality'] = Config.IMAGE_QUALITY
                    save_kwargs['optimize'] = True
                
                img.save(output, format=save_format, **save_kwargs)
                return output.getvalue()
                
        except Exception as e:
            self.logger.error(f"PIL 图片处理失败: {str(e)}")
            return None
    
    def _process_existing_image_paths(self, content: str, doc_name: str, doc_image_dir: Path) -> Tuple[str, int]:
        """处理现有的图片路径引用（如 media/image1.png）
        
        Args:
            content: Markdown 内容
            doc_name: 文档名称
            doc_image_dir: 图片目录
            
        Returns:
            Tuple[str, int]: (更新后的内容, 处理的图片数量)
        """
        processed_count = 0
        
        # 匹配各种图片路径格式
        # 包括: media/image1.png, ./media/image1.png, images/image1.png 等
        path_pattern = re.compile(
            r'!\[([^\]]*)\]\(([^)]*(?:media|images|image)/[^)]+\.(png|jpg|jpeg|gif|bmp|svg|webp))\)',
            re.IGNORECASE
        )
        
        def replace_image_path(match):
            nonlocal processed_count
            
            original_alt_text = match.group(1) or "图片"
            original_path = match.group(2)
            file_extension = match.group(3)
            
            # 提取原始文件名
            original_filename = Path(original_path).name
            
            # 检查图片目录中是否有对应的图片文件
            # 尝试多种可能的文件名格式
            possible_files = list(doc_image_dir.glob("*.png")) + \
                           list(doc_image_dir.glob("*.jpg")) + \
                           list(doc_image_dir.glob("*.jpeg")) + \
                           list(doc_image_dir.glob("*.gif")) + \
                           list(doc_image_dir.glob("*.bmp")) + \
                           list(doc_image_dir.glob("*.svg")) + \
                           list(doc_image_dir.glob("*.webp"))
            
            # 按文件名排序，确保一致的匹配顺序
            possible_files.sort()
            
            if possible_files:
                # 尝试根据原始文件名匹配
                matched_file = None
                
                # 首先尝试精确匹配
                for file_path in possible_files:
                    if file_path.name.lower() == original_filename.lower():
                        matched_file = file_path
                        break
                
                # 如果没有精确匹配，尝试按顺序匹配
                if not matched_file and possible_files:
                    # 提取原始文件名中的数字
                    import re as regex
                    number_match = regex.search(r'(\d+)', original_filename)
                    if number_match:
                        try:
                            original_number = int(number_match.group(1))
                            # 尝试找到对应序号的文件
                            for file_path in possible_files:
                                file_number_match = regex.search(r'(\d+)', file_path.name)
                                if file_number_match:
                                    file_number = int(file_number_match.group(1))
                                    if file_number == original_number:
                                        matched_file = file_path
                                        break
                        except ValueError:
                            pass
                    
                    # 如果还是没有匹配，使用第一个文件
                    if not matched_file:
                        matched_file = possible_files[min(processed_count, len(possible_files) - 1)]
                
                if matched_file:
                    # 生成新的相对路径
                    relative_path = self._get_relative_image_path(doc_name, matched_file.name)
                    processed_count += 1
                    
                    # 生成新的 alt 文本格式: image_文件名
                    alt_text = f"image_{doc_name}_{processed_count:03d}"
                    
                    self.logger.debug(f"替换图片路径: {original_path} -> {relative_path}")
                    return f"![{alt_text}]({relative_path})"
            
            # 如果没有找到对应的图片文件，保持原样
            self.logger.warning(f"未找到对应的图片文件: {original_path}")
            return match.group(0)
        
        # 替换所有匹配的图片路径
        updated_content = path_pattern.sub(replace_image_path, content)
        
        return updated_content, processed_count
    
    def _get_relative_image_path(self, doc_name: str, image_filename: str) -> str:
        """获取图片的相对路径
        
        Args:
            doc_name: 文档名称
            image_filename: 图片文件名
            
        Returns:
            str: 相对路径
        """
        safe_doc_name = self._sanitize_filename(doc_name)
        
        if Config.PATH_CONFIG['use_relative_paths']:
            separator = Config.PATH_CONFIG['path_separator']
            # 由于图片目录现在在output/images下，Markdown文件也在output目录中，使用相对路径
            return f"images{separator}{safe_doc_name}{separator}{image_filename}"
        else:
            return str(Path(self.images_dir) / safe_doc_name / image_filename)
    
    def get_image_stats(self, doc_name: str) -> Dict[str, int]:
        """获取图片处理统计信息
        
        Args:
            doc_name: 文档名称
            
        Returns:
            Dict[str, int]: 统计信息
        """
        return {
            'total_images': self.image_counter.get(doc_name, 0),
            'doc_image_dir_exists': self._check_doc_image_dir_exists(doc_name)
        }
    
    def _check_doc_image_dir_exists(self, doc_name: str) -> bool:
        """检查文档图片目录是否存在
        
        Args:
            doc_name: 文档名称
            
        Returns:
            bool: 目录是否存在
        """
        safe_doc_name = self._sanitize_filename(doc_name)
        doc_image_dir = Path(self.images_dir) / safe_doc_name
        return doc_image_dir.exists() and doc_image_dir.is_dir()
    
    def cleanup_empty_directories(self) -> None:
        """清理空的图片目录"""
        try:
            images_path = Path(self.images_dir)
            if not images_path.exists():
                return
            
            for doc_dir in images_path.iterdir():
                if doc_dir.is_dir():
                    # 检查目录是否为空
                    if not any(doc_dir.iterdir()):
                        doc_dir.rmdir()
                        self.logger.debug(f"删除空目录: {doc_dir}")
            
            self.logger.info("空目录清理完成")
            
        except Exception as e:
            self.logger.error(f"清理空目录失败: {str(e)}")


if __name__ == '__main__':
    # 测试图片处理器
    processor = ImageProcessor()
    
    # 测试 base64 图片处理
    test_content = """
# 测试文档

这是一个测试图片：
![测试图片](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==)

文档结束。
"""
    
    print("测试图片处理...")
    updated_content, image_count = processor.process_images(test_content, "test_document")
    
    print(f"处理结果:")
    print(f"图片数量: {image_count}")
    print(f"更新后的内容:")
    print(updated_content)