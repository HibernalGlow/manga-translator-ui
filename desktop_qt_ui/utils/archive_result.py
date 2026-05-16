"""
翻译结果归档工具
将翻译完成的文件/压缩包放回源文件路径
"""
import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple, List
import logging
import json

logger = logging.getLogger(__name__)

ARCHIVE_SOURCE_MARKER_FILENAME = '.archive_source.txt'
ARCHIVE_EXTENSIONS = {'.pdf', '.epub', '.cbz', '.cbr', '.zip'}
RESULT_DIR_NAME = 'result'
ORIGINAL_IMAGES_DIR_NAME = 'original_images'
TRANSLATION_MAP_FILENAME = 'translation_map.json'
TRANSLATED_PREFIX = '[#trans]'

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.avif', '.gif', '.tiff', '.tif', '.heic', '.heif'}


def decode_zip_filename(filename: str, flag_bits: int) -> str:
    """
    解码 ZIP 文件名，处理编码问题
    
    Args:
        filename: 原始文件名
        flag_bits: ZIP 文件的标志位
        
    Returns:
        解码后的文件名
    """
    # 检查 UTF-8 标志位（bit 11）
    if flag_bits & 0x800:
        # UTF-8 编码，直接返回
        return filename
    
    # 尝试 Shift-JIS 解码（日文 Windows 常见）
    try:
        # zipfile 默认使用 CP437 解码非 UTF-8 文件名
        # 我们需要先编码回原始字节，然后用正确的编码解码
        decoded = filename.encode('cp437').decode('shift_jis')
        return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    # 尝试 GBK 解码（中文 Windows 常见）
    try:
        decoded = filename.encode('cp437').decode('gbk')
        return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    # 尝试 Big5 解码（繁体中文 Windows 常见）
    try:
        decoded = filename.encode('cp437').decode('big5')
        return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    
    # 如果都失败，返回原始文件名
    return filename


def get_original_images_dir(result_dir: str) -> Optional[str]:
    """
    获取 original_images 目录路径
    
    Args:
        result_dir: 翻译结果目录路径（可能在 original_images/manga_translator_work/result 下）
        
    Returns:
        original_images 目录路径，如果不存在则返回 None
    """
    # result_dir 可能是：
    # 1. output/test/result
    # 2. output/test/original_images/manga_translator_work/result
    
    # 先检查父目录是否是 original_images
    parent_dir = os.path.dirname(result_dir)
    
    # 如果父目录是 manga_translator_work，再上一级是 original_images
    if os.path.basename(parent_dir) == 'manga_translator_work':
        original_images_dir = os.path.dirname(parent_dir)
        if os.path.basename(original_images_dir) == ORIGINAL_IMAGES_DIR_NAME:
            return original_images_dir
    
    # 否则检查同级目录是否有 original_images
    original_images_dir = os.path.join(parent_dir, ORIGINAL_IMAGES_DIR_NAME)
    if os.path.exists(original_images_dir):
        return original_images_dir
    
    # 再上一级查找
    grandparent_dir = os.path.dirname(parent_dir)
    original_images_dir = os.path.join(grandparent_dir, ORIGINAL_IMAGES_DIR_NAME)
    if os.path.exists(original_images_dir):
        return original_images_dir
    
    return None


def read_archive_source(result_dir: str) -> Optional[str]:
    """
    读取归档源文件路径
    
    Args:
        result_dir: 翻译结果目录路径
        
    Returns:
        源文件路径，如果不存在则返回 None
    """
    # result_dir 可能是：
    # 1. output/test/result -> marker 在 output/test/.archive_source.txt
    # 2. output/test/original_images/manga_translator_work/result -> marker 在 output/test/.archive_source.txt
    
    # 先获取 original_images 目录
    original_images_dir = get_original_images_dir(result_dir)
    
    if original_images_dir:
        # marker 文件在 original_images 的父目录
        marker_path = os.path.join(os.path.dirname(original_images_dir), ARCHIVE_SOURCE_MARKER_FILENAME)
    else:
        # 兼容旧逻辑
        marker_path = os.path.join(os.path.dirname(result_dir), ARCHIVE_SOURCE_MARKER_FILENAME)
    
    if not os.path.exists(marker_path):
        return None
    
    try:
        with open(marker_path, 'r', encoding='utf-8') as f:
            source_path = f.read().strip()
        
        if source_path and os.path.exists(source_path):
            return source_path
    except Exception as e:
        logger.warning(f"读取归档源文件失败: {e}")
    
    return None


def read_translation_map(original_images_dir: str) -> Optional[dict]:
    """
    读取 translation_map.json
    
    Args:
        original_images_dir: original_images 目录路径
        
    Returns:
        翻译映射字典，如果不存在则返回 None
    """
    map_path = os.path.join(original_images_dir, TRANSLATION_MAP_FILENAME)
    
    if not os.path.exists(map_path):
        return None
    
    try:
        with open(map_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"读取 translation_map.json 失败: {e}")
    
    return None


def get_image_files(directory: str) -> List[str]:
    """
    获取目录中的所有图片文件
    
    Args:
        directory: 目录路径
        
    Returns:
        图片文件列表
    """
    if not os.path.exists(directory):
        return []
    
    image_files = []
    for file in os.listdir(directory):
        ext = os.path.splitext(file)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            image_files.append(file)
    
    return sorted(image_files)


def complete_result_directory(result_dir: str) -> Tuple[int, int]:
    """
    补全 result 目录（从 original_images 复制缺失的原图）
    
    Args:
        result_dir: 翻译结果目录路径
        
    Returns:
        (复制的文件数量, 缺失的文件数量)
    """
    original_images_dir = get_original_images_dir(result_dir)
    
    if not original_images_dir:
        logger.info("未找到 original_images 目录，跳过补全")
        return 0, 0
    
    original_files = get_image_files(original_images_dir)
    result_files = get_image_files(result_dir)
    
    original_set = set(original_files)
    result_set = set(result_files)
    
    missing_files = original_set - result_set
    
    if not missing_files:
        logger.info("result 目录已完整，无需补全")
        return 0, 0
    
    copied_count = 0
    for filename in missing_files:
        src_file = os.path.join(original_images_dir, filename)
        dst_file = os.path.join(result_dir, filename)
        
        try:
            shutil.copy2(src_file, dst_file)
            copied_count += 1
            logger.info(f"已补全缺失文件: {filename}")
        except Exception as e:
            logger.warning(f"复制文件失败 {filename}: {e}")
    
    return copied_count, len(missing_files)


def is_archive_file(file_path: str) -> bool:
    """检查文件是否是压缩包格式"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in ARCHIVE_EXTENSIONS


def get_archive_extension(file_path: str) -> str:
    """获取压缩包扩展名（包含点号）"""
    return os.path.splitext(file_path)[1].lower()


def create_archive_from_result(result_dir: str, output_path: str) -> bool:
    """
    将翻译结果目录打包成压缩包
    
    Args:
        result_dir: 翻译结果目录路径
        output_path: 输出压缩包路径
        
    Returns:
        是否成功
    """
    try:
        if not os.path.exists(result_dir):
            logger.error(f"结果目录不存在: {result_dir}")
            return False
        
        # 使用 UTF-8 编码创建 ZIP 文件，确保跨平台兼容性
        # Python 3.11+ 默认使用 UTF-8，但显式设置以确保兼容性
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(result_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, result_dir)
                    
                    # 写入文件，Python 3.11+ 会自动设置 UTF-8 标志位
                    zf.write(file_path, arcname)
        
        logger.info(f"成功创建压缩包: {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"创建压缩包失败: {e}")
        return False


def archive_translated_result(
    result_dir: str,
    source_path: Optional[str] = None,
    prefix: str = TRANSLATED_PREFIX,
    delete_result: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    归档翻译结果到源文件路径
    
    Args:
        result_dir: 翻译结果目录路径
        source_path: 源文件路径（如果为 None 则从 .archive_source.txt 读取）
        prefix: 输出文件名前缀
        delete_result: 是否删除结果目录
        
    Returns:
        (是否成功, 输出文件路径)
    """
    if not os.path.exists(result_dir):
        logger.error(f"结果目录不存在: {result_dir}")
        return False, None
    
    # 先补全 result 目录
    copied_count, missing_count = complete_result_directory(result_dir)
    if copied_count > 0:
        logger.info(f"已补全 {copied_count} 个缺失文件")
    
    if source_path is None:
        source_path = read_archive_source(result_dir)
    
    if not source_path:
        logger.info("未找到归档源文件，跳过归档")
        return False, None
    
    if not os.path.exists(source_path):
        logger.warning(f"源文件不存在: {source_path}")
        return False, None
    
    source_dir = os.path.dirname(source_path)
    source_name = os.path.basename(source_path)
    source_ext = get_archive_extension(source_path)
    
    output_name = f"{prefix}{source_name}"
    output_path = os.path.join(source_dir, output_name)
    
    if os.path.exists(output_path):
        logger.warning(f"输出文件已存在，跳过: {output_path}")
        return False, output_path
    
    if is_archive_file(source_path):
        success = create_archive_from_result(result_dir, output_path)
    else:
        try:
            if os.path.isdir(source_path):
                shutil.copytree(result_dir, output_path)
                success = True
            elif os.path.isfile(source_path):
                # 单图情况：复制结果目录中的对应文件
                result_files = get_image_files(result_dir)
                if result_files:
                    # 找到与源文件同名或第一个图片文件
                    source_name = os.path.basename(source_path)
                    result_file = None
                    
                    # 优先查找同名文件
                    if source_name in result_files:
                        result_file = os.path.join(result_dir, source_name)
                    else:
                        # 否则使用第一个图片文件
                        result_file = os.path.join(result_dir, result_files[0])
                    
                    if result_file and os.path.exists(result_file):
                        shutil.copy2(result_file, output_path)
                        success = True
                        logger.info(f"已复制单图: {result_file} -> {output_path}")
                    else:
                        logger.warning(f"结果目录中未找到图片文件")
                        return False, None
                else:
                    logger.warning(f"结果目录为空")
                    return False, None
            else:
                logger.warning(f"源路径不存在: {source_path}")
                return False, None
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False, None
    
    if success and delete_result:
        try:
            shutil.rmtree(result_dir)
            logger.info(f"已删除结果目录: {result_dir}")
        except Exception as e:
            logger.warning(f"删除结果目录失败: {e}")
    
    return success, output_path


def batch_archive_results(
    root_dir: str,
    prefix: str = TRANSLATED_PREFIX,
    delete_result: bool = False
) -> Tuple[int, int, list]:
    """
    批量归档翻译结果
    
    Args:
        root_dir: 根目录路径
        prefix: 输出文件名前缀
        delete_result: 是否删除结果目录
        
    Returns:
        (成功数量, 失败数量, 输出文件列表)
    """
    success_count = 0
    failed_count = 0
    output_files = []
    
    for root, dirs, files in os.walk(root_dir):
        if RESULT_DIR_NAME in dirs:
            result_dir = os.path.join(root, RESULT_DIR_NAME)
            
            success, output_path = archive_translated_result(
                result_dir=result_dir,
                prefix=prefix,
                delete_result=delete_result
            )
            
            if success:
                success_count += 1
                output_files.append(output_path)
            elif output_path:
                pass
            else:
                failed_count += 1
    
    return success_count, failed_count, output_files
