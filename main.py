#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkItDown 文档转换工具主程序

基于 Microsoft MarkItDown 库的文档转换工具，支持多种格式文档转换为 Markdown。
主要功能：
- 批量文档转换（基于 Microsoft MarkItDown v0.1.2+）
- 智能图片提取和路径修复
- PDF 格式优化和错误修复
- 完整的日志记录和进度显示
- 可选的 LLM 集成用于图片描述

支持格式：PDF, Word, PowerPoint, Excel, 图片, 音频, HTML, CSV, JSON, XML, ZIP 等

作者: Assistant
版本: 2.0.0
依赖: Microsoft MarkItDown >= 0.1.2
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.logger import MarkItDownLogger
from src.converter import DocumentConverter


def setup_directories() -> None:
    """
    设置必要的目录结构
    
    创建输入、输出、图片、日志和临时目录（如果不存在）
    """
    directories = [
        Config.INPUT_DIR,
        Config.OUTPUT_DIR, 
        Config.IMAGES_DIR,
        Config.LOGS_DIR,
        Config.TEMP_DIR
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def get_input_files(input_path: str) -> List[Path]:
    """
    获取输入文件列表
    
    Args:
        input_path: 输入路径（文件或目录）
        
    Returns:
        文件路径列表
        
    Raises:
        FileNotFoundError: 输入路径不存在
        ValueError: 输入路径无效
    """
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"输入路径不存在: {input_path}")
    
    if path.is_file():
        # MarkItDown 支持的格式更广泛，这里简化检查
        return [path]
    
    elif path.is_dir():
        # 获取目录中的所有文件（MarkItDown 会自动判断格式）
        files = []
        for file_path in path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append(file_path)
        return sorted(files)
    
    else:
        raise ValueError(f"无效的输入路径: {input_path}")


def convert_single_file(converter: DocumentConverter, file_path: Path, logger: MarkItDownLogger) -> bool:
    """
    转换单个文件
    
    Args:
        converter: 文档转换器实例
        file_path: 文件路径
        logger: 日志记录器
        
    Returns:
        转换是否成功
    """
    try:
        logger.info(f"开始转换文件: {file_path}")
        
        # 执行转换
        result = converter.convert_document(str(file_path))
        
        if result['success']:
            logger.info(f"文件转换成功: {file_path} -> {result['output_file']}")
            if result.get('images_extracted', 0) > 0:
                logger.info(f"提取图片数量: {result['images_extracted']}")
            if result.get('format_optimized', False):
                logger.info("已应用格式优化")
            return True
        else:
            logger.error(f"文件转换失败: {file_path} - {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"转换文件时发生异常: {file_path} - {str(e)}")
        return False


def convert_batch_files(converter: DocumentConverter, files: List[Path], logger: MarkItDownLogger) -> Dict[str, Any]:
    """
    批量转换文件
    
    Args:
        converter: 文档转换器实例
        files: 文件路径列表
        logger: 日志记录器
        
    Returns:
        转换结果统计
    """
    results = {
        'total': len(files),
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'total_images': 0,
        'errors': [],
        'processed_files': []
    }
    
    logger.info(f"开始批量转换 {len(files)} 个文件")
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"处理进度: {i}/{len(files)} - {file_path.name}")
        
        # 检查文件大小
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > Config.MAX_FILE_SIZE:
                logger.warning(f"文件过大，跳过: {file_path} ({file_size_mb:.1f}MB)")
                results['skipped'] += 1
                continue
        except Exception as e:
            logger.warning(f"无法获取文件大小: {file_path} - {e}")
        
        if convert_single_file(converter, file_path, logger):
            results['success'] += 1
            results['processed_files'].append(str(file_path))
        else:
            results['failed'] += 1
            results['errors'].append(str(file_path))
    
    return results


def print_summary(results: Dict[str, Any], logger: MarkItDownLogger) -> None:
    """
    打印转换结果摘要
    
    Args:
        results: 转换结果统计
        logger: 日志记录器
    """
    logger.info("=" * 60)
    logger.info("📊 转换完成摘要")
    logger.info("=" * 60)
    logger.info(f"📁 总文件数: {results['total']}")
    logger.info(f"✅ 成功转换: {results['success']}")
    logger.info(f"❌ 转换失败: {results['failed']}")
    logger.info(f"⏭️  跳过文件: {results['skipped']}")
    
    if results.get('total_images', 0) > 0:
        logger.info(f"🖼️  提取图片: {results['total_images']}")
    
    if results['errors']:
        logger.warning("❌ 失败的文件:")
        for error_file in results['errors']:
            logger.warning(f"   • {error_file}")
    
    if results['processed_files']:
        logger.info("✅ 成功处理的文件:")
        for processed_file in results['processed_files'][:5]:  # 只显示前5个
            logger.info(f"   • {processed_file}")
        if len(results['processed_files']) > 5:
            logger.info(f"   ... 还有 {len(results['processed_files']) - 5} 个文件")
    
    logger.info("=" * 60)


def main():
    """
    主程序入口
    """
    parser = argparse.ArgumentParser(
        description="MarkItDown 文档转换工具 - 基于 Microsoft MarkItDown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 示例用法:
  python main.py input/document.pdf                    # 转换单个文件
  python main.py input/                               # 转换整个目录
  python main.py input/ --verbose                     # 详细输出模式
  python main.py input/ --enable-llm                  # 启用 LLM 图片描述
  python main.py input/ --use-azure-doc-intel         # 使用 Azure 文档智能

🔧 支持格式:
  • 文档: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx)
  • 图片: PNG, JPG, GIF, BMP, TIFF (支持 OCR)
  • 音频: WAV, MP3 (支持语音转录)
  • 网页: HTML, XML
  • 数据: CSV, JSON
  • 压缩: ZIP (递归处理)
  • 其他: YouTube URLs, EPub 等
        """
    )
    
    parser.add_argument(
        'input_path',
        help='输入文件或目录路径'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='启用详细输出模式'
    )
    
    parser.add_argument(
        '--enable-llm',
        action='store_true',
        help='启用 LLM 集成用于图片描述生成（需要配置 API 密钥）'
    )
    
    parser.add_argument(
        '--use-azure-doc-intel',
        action='store_true',
        help='使用 Azure 文档智能进行高质量 PDF 处理'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='指定输出目录路径（默认为 output/）'
    )
    
    parser.add_argument(
        '--keep-data-uris',
        action='store_true',
        help='保留 base64 编码的图片数据（默认会截断）'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='MarkItDown 文档转换工具 v2.0.0 (基于 Microsoft MarkItDown)'
    )
    
    args = parser.parse_args()
    
    try:
        # 设置目录结构
        setup_directories()
        
        # 初始化日志记录器
        logger = MarkItDownLogger(
            log_level='DEBUG' if args.verbose else 'INFO'
        )
        
        # 记录系统信息和启动参数
        logger.log_system_info()
        logger.info(f"🚀 启动参数: {' '.join(sys.argv[1:])}")
        
        # 记录配置信息
        logger.log_config_info(Config.get_config_dict())
        
        # 设置输出目录
        if args.output:
            # 临时修改配置中的输出目录
            original_output_dir = Config.OUTPUT_DIR
            Config.OUTPUT_DIR = args.output
            # 确保输出目录存在
            os.makedirs(args.output, exist_ok=True)
            logger.info(f"📁 使用自定义输出目录: {args.output}")
        
        # 初始化转换器
        converter = DocumentConverter(
            logger=logger,
            enable_llm=args.enable_llm,
            use_azure_doc_intel=args.use_azure_doc_intel
        )
        
        # 获取输入文件
        files = get_input_files(args.input_path)
        
        if not files:
            logger.warning("⚠️  未找到可处理的文件")
            return 1
        
        logger.info(f"📂 发现 {len(files)} 个文件待处理")
        
        # 执行转换
        if len(files) == 1:
            # 单文件转换
            success = convert_single_file(converter, files[0], logger)
            if success:
                logger.info("🎉 单文件转换完成")
            return 0 if success else 1
        else:
            # 批量转换
            results = convert_batch_files(converter, files, logger)
            print_summary(results, logger)
            
            # 根据结果确定退出码
            if results['failed'] == 0:
                logger.info("🎉 所有文件转换成功！")
                return 0
            elif results['success'] > 0:
                logger.warning("⚠️  部分文件转换失败")
                return 2
            else:
                logger.error("❌ 所有文件转换失败")
                return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
        return 130
    except Exception as e:
        print(f"💥 程序执行出错: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())