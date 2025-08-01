#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理模块

提供统一的路径管理功能，包括路径验证、创建、清理等操作。

作者: Assistant
版本: 1.0.0
"""

import os
import shutil
from pathlib import Path
from typing import Union, List, Optional
from datetime import datetime

from .logger import get_logger
from .config import Config

logger = get_logger(__name__)

class PathManager:
    """
    路径管理器
    
    提供统一的路径管理功能，包括：
    - 路径验证和规范化
    - 目录创建和清理
    - 文件路径生成
    - 安全检查
    """
    
    def __init__(self, base_dir: Union[str, Path] = None):
        """
        初始化路径管理器
        
        Args:
            base_dir: 基础目录路径
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.base_dir = self.base_dir.resolve()
        
        logger.debug(f"PathManager 初始化，基础目录: {self.base_dir}")
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        规范化路径
        
        Args:
            path: 输入路径
            
        Returns:
            规范化后的 Path 对象
        """
        path = Path(path)
        
        # 如果是相对路径，相对于基础目录
        if not path.is_absolute():
            path = self.base_dir / path
        
        return path.resolve()
    
    def ensure_dir(self, dir_path: Union[str, Path], 
                   parents: bool = True, exist_ok: bool = True) -> Path:
        """
        确保目录存在
        
        Args:
            dir_path: 目录路径
            parents: 是否创建父目录
            exist_ok: 目录已存在时是否报错
            
        Returns:
            创建的目录路径
        """
        dir_path = self.normalize_path(dir_path)
        
        try:
            dir_path.mkdir(parents=parents, exist_ok=exist_ok)
            logger.debug(f"目录已确保存在: {dir_path}")
            return dir_path
        except Exception as e:
            logger.error(f"创建目录失败 {dir_path}: {e}")
            raise
    
    def safe_filename(self, filename: str, max_length: int = None) -> str:
        """
        生成安全的文件名
        
        Args:
            filename: 原始文件名
            max_length: 最大长度，如果为None则使用配置中的默认值
            
        Returns:
            安全的文件名
        """
        # 如果未指定最大长度，使用配置中的默认值
        if max_length is None:
            # 从配置中获取默认值
            max_length = Config.DIRECTORY_NAMING['filename_limits']['max_filename_length']
        
        # 移除或替换不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # 移除控制字符
        safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
        
        # 限制长度
        if len(safe_name) > max_length:
            name_part, ext_part = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext_part)
            safe_name = name_part[:max_name_length] + ext_part
        
        # 确保不为空
        if not safe_name.strip():
            safe_name = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return safe_name
    
    def generate_unique_path(self, base_path: Union[str, Path], 
                           suffix: str = None) -> Path:
        """
        生成唯一的文件路径
        
        Args:
            base_path: 基础路径
            suffix: 后缀（如果文件已存在）
            
        Returns:
            唯一的文件路径
        """
        base_path = self.normalize_path(base_path)
        
        if not base_path.exists():
            return base_path
        
        # 文件已存在，生成唯一名称
        stem = base_path.stem
        suffix_part = suffix or datetime.now().strftime('_%Y%m%d_%H%M%S')
        ext = base_path.suffix
        
        counter = 1
        while True:
            if counter == 1:
                new_name = f"{stem}{suffix_part}{ext}"
            else:
                new_name = f"{stem}{suffix_part}_{counter}{ext}"
            
            new_path = base_path.parent / new_name
            if not new_path.exists():
                return new_path
            
            counter += 1
            if counter > 1000:  # 防止无限循环
                raise ValueError(f"无法生成唯一路径: {base_path}")
    
    def is_safe_path(self, path: Union[str, Path], 
                     allowed_dirs: List[Union[str, Path]] = None) -> bool:
        """
        检查路径是否安全
        
        Args:
            path: 要检查的路径
            allowed_dirs: 允许的目录列表
            
        Returns:
            路径是否安全
        """
        path = self.normalize_path(path)
        
        # 检查是否在基础目录内
        try:
            path.relative_to(self.base_dir)
        except ValueError:
            logger.warning(f"路径不在基础目录内: {path}")
            return False
        
        # 检查是否在允许的目录内
        if allowed_dirs:
            allowed_paths = [self.normalize_path(d) for d in allowed_dirs]
            for allowed_path in allowed_paths:
                try:
                    path.relative_to(allowed_path)
                    return True
                except ValueError:
                    continue
            logger.warning(f"路径不在允许的目录内: {path}")
            return False
        
        return True
    
    def clean_empty_dirs(self, root_dir: Union[str, Path], 
                        keep_root: bool = True) -> int:
        """
        清理空目录
        
        Args:
            root_dir: 根目录
            keep_root: 是否保留根目录
            
        Returns:
            删除的目录数量
        """
        root_dir = self.normalize_path(root_dir)
        
        if not root_dir.exists() or not root_dir.is_dir():
            return 0
        
        deleted_count = 0
        
        # 从最深层开始删除
        for dir_path in sorted(root_dir.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                if not keep_root or dir_path != root_dir:
                    try:
                        dir_path.rmdir()
                        deleted_count += 1
                        logger.debug(f"删除空目录: {dir_path}")
                    except Exception as e:
                        logger.warning(f"删除空目录失败 {dir_path}: {e}")
        
        return deleted_count
    
    def copy_file(self, src: Union[str, Path], dst: Union[str, Path], 
                  overwrite: bool = False) -> Path:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            目标文件路径
        """
        src = self.normalize_path(src)
        dst = self.normalize_path(dst)
        
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        if dst.exists() and not overwrite:
            dst = self.generate_unique_path(dst)
        
        # 确保目标目录存在
        self.ensure_dir(dst.parent)
        
        try:
            shutil.copy2(src, dst)
            logger.debug(f"文件复制成功: {src} -> {dst}")
            return dst
        except Exception as e:
            logger.error(f"文件复制失败 {src} -> {dst}: {e}")
            raise
    
    def move_file(self, src: Union[str, Path], dst: Union[str, Path], 
                  overwrite: bool = False) -> Path:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            overwrite: 是否覆盖已存在的文件
            
        Returns:
            目标文件路径
        """
        src = self.normalize_path(src)
        dst = self.normalize_path(dst)
        
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        if dst.exists() and not overwrite:
            dst = self.generate_unique_path(dst)
        
        # 确保目标目录存在
        self.ensure_dir(dst.parent)
        
        try:
            shutil.move(str(src), str(dst))
            logger.debug(f"文件移动成功: {src} -> {dst}")
            return dst
        except Exception as e:
            logger.error(f"文件移动失败 {src} -> {dst}: {e}")
            raise
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        file_path = self.normalize_path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        stat = file_path.stat()
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'stem': file_path.stem,
            'suffix': file_path.suffix,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'parent': str(file_path.parent)
        }
    
    def list_files(self, directory: Union[str, Path], 
                   pattern: str = '*', recursive: bool = False) -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            recursive: 是否递归搜索
            
        Returns:
            文件路径列表
        """
        directory = self.normalize_path(directory)
        
        if not directory.exists() or not directory.is_dir():
            return []
        
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # 只返回文件，不包括目录
        return [f for f in files if f.is_file()]
    
    def __str__(self) -> str:
        return f"PathManager(base_dir={self.base_dir})"
    
    def __repr__(self) -> str:
        return self.__str__()