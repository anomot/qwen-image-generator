#!/usr/bin/env python3
"""
图片处理工具函数 - 供 Skill 使用

功能:
- 图片压缩
- 文件名生成
- base64 转换
- URL 下载与重试
"""

import os
import sys
import re
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from io import BytesIO

try:
    import requests
    from PIL import Image
except ImportError:
    print("请安装依赖: pip install requests pillow")
    sys.exit(1)


def compress_image(input_path: str, target_size_mb: float = 9.5, output_path: str = None) -> str:
    """
    压缩图片到指定大小以内。
    
    Args:
        input_path: 输入图片路径
        target_size_mb: 目标大小（MB），默认 9.5（为 qwen-image-2.0 留余量）
        output_path: 输出路径，默认在原文件同目录加 _compressed 后缀
    
    Returns:
        str: 压缩后的文件路径
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {input_path}")
    
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_compressed.jpg"
    else:
        output_path = Path(output_path)
    
    # 检查原始大小
    original_size_mb = input_path.stat().st_size / (1024 * 1024)
    if original_size_mb <= target_size_mb:
        # 已经是目标大小以内，转为 JPEG
        img = Image.open(input_path)
        img.save(output_path, 'JPEG', quality=95)
        return str(output_path)
    
    img = Image.open(input_path)
    
    # 策略1: 降低 JPEG 质量
    for quality in [85, 70, 50, 30]:
        img.save(output_path, 'JPEG', quality=quality)
        current_size_mb = output_path.stat().st_size / (1024 * 1024)
        if current_size_mb <= target_size_mb:
            print(f"📦 压缩完成: {original_size_mb:.1f}MB → {current_size_mb:.1f}MB (JPEG q{quality})")
            return str(output_path)
    
    # 策略2: 缩小分辨率
    max_dim = 2048
    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        new_size = (int(w * ratio), int(h * ratio))
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        
        for quality in [85, 70, 50]:
            img_resized.save(output_path, 'JPEG', quality=quality)
            current_size_mb = output_path.stat().st_size / (1024 * 1024)
            if current_size_mb <= target_size_mb:
                print(f"📦 压缩+缩放完成: {original_size_mb:.1f}MB → {current_size_mb:.1f}MB ({new_size[0]}x{new_size[1]}, q{quality})")
                return str(output_path)
    
    current_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"⚠️ 压缩后仍为 {current_size_mb:.1f}MB，超出 {target_size_mb}MB 限制")
    return str(output_path)


def image_to_base64(image_path: str) -> str:
    """
    将本地图片转为 data URI base64 格式。
    
    Args:
        image_path: 本地图片路径
    
    Returns:
        str: data:image/xxx;base64,... 格式的字符串
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {path}")
    
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
    }
    
    mime_type = mime_map.get(path.suffix.lower(), 'image/jpeg')
    
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{b64}"


def is_url(s: str) -> bool:
    """判断字符串是否为 URL"""
    return s.startswith(('http://', 'https://'))


def prepare_image_input(image_path_or_url: str, target_model: str = "qwen-image-2.0") -> str:
    """
    准备图片输入：URL 直传或本地文件转 base64。
    
    Args:
        image_path_or_url: 图片路径或 URL
        target_model: 目标模型，用于确定文件大小限制
    
    Returns:
        str: 可直接传给 API 的图片值（URL 或 data:image/...;base64,...）
    """
    if is_url(image_path_or_url):
        return image_path_or_url
    
    path = Path(image_path_or_url)
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {path}")
    
    # 检查文件大小
    size_mb = path.stat().st_size / (1024 * 1024)
    limit_mb = 20.0 if "wan" in target_model else 10.0
    
    if size_mb > limit_mb:
        print(f"📦 图片 {size_mb:.1f}MB 超出 {target_model} 限制 ({limit_mb}MB)，正在压缩...")
        compressed = compress_image(str(path), target_size_mb=limit_mb - 0.5)
        path = Path(compressed)
        new_size_mb = path.stat().st_size / (1024 * 1024)
        if new_size_mb > limit_mb:
            raise ValueError(f"压缩后仍为 {new_size_mb:.1f}MB，超出 {target_model} 的 {limit_mb}MB 限制")
    
    return image_to_base64(str(path))


def generate_filename(prompt: str, scene: str = "", style: str = "", seed: int = None) -> str:
    """
    生成图片文件名。
    
    格式：主体_场景_风格_时间戳.png
    
    Args:
        prompt: 提示词（提取主体）
        scene: 场景描述（可选）
        style: 风格描述（可选）
        seed: 种子值（可选）
    
    Returns:
        str: 文件名
    """
    # 提取主体：提示词前20字，去除特殊字符
    subject = re.sub(r'[^\w\u4e00-\u9fff]', '', prompt[:20]).strip()
    if not subject:
        subject = "image"
    
    parts = [subject]
    if scene:
        scene_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', scene[:10]).strip()
        if scene_clean:
            parts.append(scene_clean)
    if style:
        style_clean = re.sub(r'[^\w\u4e00-\u9fff]', '', style[:10]).strip()
        if style_clean:
            parts.append(style_clean)
    
    suffix = f"seed{seed}" if seed else datetime.now().strftime("%Y%m%d_%H%M%S")
    parts.append(suffix)
    
    return "_".join(parts) + ".png"


def download_image_with_retry(url: str, output_path: str, max_retries: int = 3) -> bool:
    """
    下载图片，失败重试。
    
    Args:
        url: 图片 URL
        output_path: 保存路径
        max_retries: 最大重试次数
    
    Returns:
        bool: 是否成功
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"  下载失败 (第{attempt}次): {e}")
            if attempt < max_retries:
                print(f"  重试中...")
    
    return False


def get_output_dir(work_dir: str = None) -> str:
    """
    获取输出目录。
    
    优先级:
    1. 当前工作目录下的 output/（用户在项目中使用时）
    2. ~/Pictures/qwen-image-generator/（保底，跨平台统一）
    
    Args:
        work_dir: 工作目录（可选，默认使用 cwd）
    
    Returns:
        str: 输出目录路径
    """
    cwd_output = Path(work_dir) / "output" if work_dir else Path.cwd() / "output"
    fallback_output = Path.home() / "Pictures" / "qwen-image-generator"
    
    try:
        cwd_output.mkdir(parents=True, exist_ok=True)
        return str(cwd_output)
    except (PermissionError, OSError):
        fallback_output.mkdir(parents=True, exist_ok=True)
        return str(fallback_output)


if __name__ == "__main__":
    # 快速测试
    if len(sys.argv) < 2:
        print("用法:")
        print("  python image_utils.py compress <图片路径> [目标MB]")
        print("  python image_utils.py base64 <图片路径>")
        print("  python image_utils.py filename <提示词> [场景] [风格]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "compress" and len(sys.argv) >= 3:
        target_mb = float(sys.argv[3]) if len(sys.argv) > 3 else 9.5
        result = compress_image(sys.argv[2], target_mb)
        print(f"输出: {result}")
    
    elif cmd == "base64" and len(sys.argv) >= 3:
        result = image_to_base64(sys.argv[2])
        print(f"data URI 长度: {len(result)} 字符")
    
    elif cmd == "filename" and len(sys.argv) >= 3:
        scene = sys.argv[3] if len(sys.argv) > 3 else ""
        style = sys.argv[4] if len(sys.argv) > 4 else ""
        result = generate_filename(sys.argv[2], scene, style)
        print(f"文件名: {result}")
    
    else:
        print(f"未知命令: {cmd}")
