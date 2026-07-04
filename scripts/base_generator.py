#!/usr/bin/env python3
"""
Base Image Generator - 三个生成脚本的公共基类

抽取了以下通用逻辑：
- API Key 初始化 + workspace 配置
- 输出目录创建（按日期分目录）
- 图片文件编码 (base64)
- API 响应处理 + 图片下载
- 元数据 sidecar JSON 生成
- 下载重试 + API 重试机制
- filename_prefix 校验
- 生成进度反馈（心跳输出）
- 下载后图片验证 (PIL.Image.verify)
"""

import os
import sys
import re
import json
import base64
import time
import threading
import io
import requests
from pathlib import Path
from typing import List, Optional, Union, Callable, Any
from datetime import datetime

import dashscope
from PIL import Image


class BaseImageGenerator:
    """图片生成器基类
    
    子类需要定义：
    - MODELS: dict 模型映射
    - SIZES: dict 尺寸映射
    - 各自的 text_to_image / image_to_image 等方法
    """
    
    # 子类必须覆盖
    MODELS: dict = {}
    SIZES: dict = {}
    
    # 下载重试配置
    DOWNLOAD_MAX_RETRIES = 3
    DOWNLOAD_RETRY_DELAY = 1.0  # 秒，指数退避基数
    
    # API 重试配置
    API_MAX_RETRIES = 2
    API_RETRY_DELAY = 2.0  # 秒，指数退避基数
    # 可重试的 HTTP 状态码
    API_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
    
    # 进度反馈配置
    PROGRESS_INTERVAL = 5.0  # 秒，心跳间隔
    
    def __init__(self, api_key: Optional[str] = None, workspace: Optional[str] = None):
        """
        初始化图片生成器
        
        Args:
            api_key: DashScope API Key，默认从环境变量 Qwen_DASHSCOPE_API_KEY 读取
            workspace: Workspace ID，用于自定义端点
        """
        self.api_key = api_key or os.getenv("Qwen_DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("API Key 未设置，请传入 api_key 或设置 Qwen_DASHSCOPE_API_KEY 环境变量")
        
        self.workspace = workspace
        
        # 设置自定义端点（如果提供了 workspace）
        if workspace:
            dashscope.base_http_api_url = f'https://{workspace}.cn-beijing.maas.aliyuncs.com/api/v1'
        
        # 创建输出目录（按日期分目录）
        # 优先级：1. 当前工作目录下的 output/  2. ~/Pictures/qwen-image-generator/（保底）
        cwd_output = Path.cwd() / "output"
        fallback_output = Path.home() / "Pictures" / "qwen-image-generator"
        try:
            cwd_output.mkdir(exist_ok=True)
            self._base_output_dir = cwd_output
        except (PermissionError, OSError):
            fallback_output.mkdir(parents=True, exist_ok=True)
            self._base_output_dir = fallback_output
        
        # output_dir 指向当前日期的子目录
        self.output_dir = self._get_dated_output_dir()
    
    def _get_dated_output_dir(self) -> Path:
        """获取按日期分目录的输出路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        dated_dir = self._base_output_dir / date_str
        dated_dir.mkdir(exist_ok=True)
        return dated_dir
    
    @staticmethod
    def validate_filename_prefix(prefix: Optional[str]) -> Optional[str]:
        """
        校验并清理 filename_prefix，替换不安全的字符为下划线
        
        Args:
            prefix: 用户输入的文件名前缀
        
        Returns:
            清理后的前缀，或 None（如果输入为 None）
        """
        if prefix is None:
            return None
        # 允许：中文、英文字母、数字、下划线、连字符
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', prefix)
        # 去除连续下划线
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
        if not cleaned:
            return None
        return cleaned
    
    def _prepare_image(self, image_path: str) -> str:
        """
        读取本地图片或 URL，返回 base64 data URI
        
        Args:
            image_path: 本地文件路径或 HTTP(S) URL
        
        Returns:
            base64 data URI 字符串
        """
        if image_path.startswith(('http://', 'https://')):
            return image_path
        
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 读取并编码为 base64
        with open(path, 'rb') as f:
            img_data = f.read()
        
        b64_data = base64.b64encode(img_data).decode('utf-8')
        
        # 根据后缀判断 MIME 类型
        suffix = path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_map.get(suffix, 'image/jpeg')
        
        return f"data:{mime_type};base64,{b64_data}"
    
    # ================================================================
    # 进度反馈
    # ================================================================
    
    def _start_progress(self, label: str = "生成中"):
        """启动进度心跳线程"""
        self._progress_stop = threading.Event()
        self._progress_label = label
        
        def _heartbeat():
            elapsed = 0
            while not self._progress_stop.is_set():
                self._progress_stop.wait(self.PROGRESS_INTERVAL)
                if not self._progress_stop.is_set():
                    elapsed += int(self.PROGRESS_INTERVAL)
                    print(f"   ⏳ {label}... ({elapsed}s)")
        
        self._progress_thread = threading.Thread(target=_heartbeat, daemon=True)
        self._progress_thread.start()
    
    def _stop_progress(self):
        """停止进度心跳线程"""
        if hasattr(self, '_progress_stop'):
            self._progress_stop.set()
        if hasattr(self, '_progress_thread'):
            self._progress_thread.join(timeout=2)
    
    # ================================================================
    # API 重试
    # ================================================================
    
    def _call_api_with_retry(self, api_func: Callable, **kwargs) -> Any:
        """
        调用 API，支持超时/429/5xx 指数退避重试
        
        Args:
            api_func: API 调用函数（如 ImageGeneration.call）
            **kwargs: 传给 API 函数的参数
        
        Returns:
            API 响应对象
        
        Raises:
            Exception: 超过重试次数后仍然失败
        """
        last_error = None
        
        for attempt in range(self.API_MAX_RETRIES + 1):
            try:
                # 启动进度心跳
                self._start_progress()
                
                response = api_func(**kwargs)
                
                # 停止进度
                self._stop_progress()
                
                # 检查是否需要重试（检查响应状态码）
                status_code = (
                    getattr(response, 'status_code', None)
                    if hasattr(response, 'status_code')
                    else response.get('status_code') if isinstance(response, dict) else None
                )
                status_value = status_code.value if hasattr(status_code, 'value') else status_code
                
                if status_value in self.API_RETRYABLE_STATUS and attempt < self.API_MAX_RETRIES:
                    delay = self.API_RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️  API 返回 {status_value}，{delay:.0f} 秒后重试 ({attempt + 1}/{self.API_MAX_RETRIES})...")
                    time.sleep(delay)
                    continue
                
                return response
                
            except Exception as e:
                self._stop_progress()
                last_error = e
                
                # 判断是否为可重试的异常
                is_retryable = (
                    isinstance(e, requests.exceptions.Timeout) or
                    isinstance(e, requests.exceptions.ConnectionError) or
                    "timeout" in str(e).lower() or
                    "502" in str(e) or
                    "503" in str(e) or
                    "504" in str(e) or
                    "429" in str(e)
                )
                
                if is_retryable and attempt < self.API_MAX_RETRIES:
                    delay = self.API_RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️  API 异常: {type(e).__name__}，{delay:.0f} 秒后重试 ({attempt + 1}/{self.API_MAX_RETRIES})...")
                    time.sleep(delay)
                    continue
                
                raise
        
        raise last_error or Exception("API 调用失败，超过重试次数")
    
    # ================================================================
    # 图片下载 + 验证
    # ================================================================
    
    def _verify_image(self, image_data: bytes) -> bool:
        """
        验证图片数据是否为有效图片
        
        Args:
            image_data: 图片二进制数据
        
        Returns:
            True 有效图片，False 无效
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            return True
        except Exception:
            return False
    
    def _download_image(self, url: str, save_path: Path, max_retries: int = None) -> bool:
        """
        下载图片，支持指数退避重试 + PIL 验证
        
        Args:
            url: 图片 URL
            save_path: 保存路径
            max_retries: 最大重试次数（默认 DOWNLOAD_MAX_RETRIES）
        
        Returns:
            True 下载成功，False 下载失败
        """
        if max_retries is None:
            max_retries = self.DOWNLOAD_MAX_RETRIES
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                # 验证是否为有效图片
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type and len(response.content) < 1000:
                    raise ValueError(f"响应不是有效图片 (content-type: {content_type})")
                
                # PIL 验证
                if not self._verify_image(response.content):
                    raise ValueError("文件不是有效图片 (PIL verify 失败)")
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                return True
                
            except Exception as e:
                if attempt < max_retries:
                    delay = self.DOWNLOAD_RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️  下载失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    print(f"   {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                else:
                    print(f"⚠️  下载失败 (已重试 {max_retries} 次): {e}")
                    return False
        
        return False
    
    def _save_sidecar(
        self,
        image_path: Path,
        model: str,
        prompt: str,
        size: str,
        n: int,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        api_url: Optional[str] = None,
        extra_params: Optional[dict] = None
    ) -> Optional[Path]:
        """
        保存元数据 sidecar JSON 文件
        
        Args:
            image_path: 图片文件路径
            model: 使用的模型名
            prompt: 提示词
            size: 图片尺寸
            n: 生成数量
            seed: 随机种子
            negative_prompt: 负向提示词
            api_url: API 返回的图片 URL
            extra_params: 额外参数
        
        Returns:
            sidecar JSON 路径，失败返回 None
        """
        sidecar_path = image_path.with_suffix('.json')
        
        metadata = {
            "image": image_path.name,
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
            "generated_at": datetime.now().isoformat(),
        }
        
        if seed is not None:
            metadata["seed"] = seed
        if negative_prompt:
            metadata["negative_prompt"] = negative_prompt
        if api_url:
            metadata["api_image_url"] = api_url
        if extra_params:
            metadata.update(extra_params)
        
        try:
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return sidecar_path
        except Exception as e:
            print(f"⚠️  元数据保存失败: {e}")
            return None
    
    # ================================================================
    # 响应处理
    # ================================================================
    
    def _process_response(
        self,
        response,
        task_type: str,
        filename_prefix: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        处理 API 响应，提取图片 URL、下载保存、生成元数据
        
        Args:
            response: API 返回的响应对象
            task_type: 任务类型标识
            filename_prefix: 自定义文件名前缀
            metadata: 生成参数，用于保存 sidecar JSON
        
        Returns:
            处理后的结果字典
        """
        result = {
            "success": False,
            "images": [],
            "saved_paths": [],
            "raw_response": None
        }
        
        try:
            # === 校验 filename_prefix ===
            filename_prefix = self.validate_filename_prefix(filename_prefix)
            
            # === 检查响应状态 ===
            status_code = (
                getattr(response, 'status_code', None) 
                if hasattr(response, 'status_code')
                else response.get('status_code') if isinstance(response, dict) else None
            )
            
            status_value = status_code.value if hasattr(status_code, 'value') else status_code
            if status_value != 200:
                error_code = (
                    getattr(response, 'code', 'Unknown')
                    if hasattr(response, 'code')
                    else response.get('code', 'Unknown') if isinstance(response, dict) else 'Unknown'
                )
                error_msg = (
                    getattr(response, 'message', 'Unknown error')
                    if hasattr(response, 'message')
                    else response.get('message', 'Unknown error') if isinstance(response, dict) else 'Unknown error'
                )
                print(f"❌ API 错误: {error_code} - {error_msg}")
                result["error"] = f"{error_code}: {error_msg}"
                result["raw_response"] = str(response)
                return result
            
            # === 提取图片 URL ===
            image_urls = []
            
            if hasattr(response, 'output'):
                output = response.output
                choices = getattr(output, 'choices', []) if hasattr(output, 'choices') else []
            else:
                output = response.get('output', {}) if isinstance(response, dict) else {}
                choices = output.get('choices', [])
            
            if not choices:
                print("⚠️  未找到生成的图片")
                result["error"] = "No images generated"
                result["raw_response"] = str(response)
                return result
            
            for choice in choices:
                if hasattr(choice, 'message'):
                    message = choice.message
                    content = getattr(message, 'content', []) if hasattr(message, 'content') else []
                else:
                    message = choice.get('message', {})
                    content = message.get('content', [])
                
                for item in content:
                    if isinstance(item, dict) and 'image' in item:
                        image_urls.append(item['image'])
            
            if not image_urls:
                print("⚠️  未找到生成的图片 URL")
                result["error"] = "No image URLs in response"
                result["raw_response"] = str(response)
                return result
            
            # === 刷新输出目录（确保使用当天日期） ===
            self.output_dir = self._get_dated_output_dir()
            
            # === 下载并保存图片 ===
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for idx, url in enumerate(image_urls, 1):
                print(f"📥 下载图片 {idx}/{len(image_urls)}...")
                
                # 生成文件名
                name_prefix = filename_prefix if filename_prefix else task_type
                if len(image_urls) > 1:
                    filename = f"{name_prefix}_{timestamp}_seq{idx:02d}.png"
                else:
                    filename = f"{name_prefix}_{timestamp}.png"
                save_path = self.output_dir / filename
                
                # 下载图片（带重试 + PIL 验证）
                if self._download_image(url, save_path):
                    print(f"✅ 已保存: {save_path}")
                    
                    # 保存元数据 sidecar
                    if metadata:
                        sidecar_path = self._save_sidecar(
                            save_path,
                            model=metadata.get('model', ''),
                            prompt=metadata.get('prompt', ''),
                            size=metadata.get('size', ''),
                            n=metadata.get('n', 1),
                            seed=metadata.get('seed'),
                            negative_prompt=metadata.get('negative_prompt'),
                            api_url=url,
                            extra_params=metadata.get('extra_params')
                        )
                        if sidecar_path:
                            print(f"📋 元数据: {sidecar_path}")
                    
                    result["images"].append({
                        "url": url,
                        "index": idx,
                        "filename": filename
                    })
                    result["saved_paths"].append(str(save_path))
                else:
                    result["images"].append({
                        "url": url,
                        "index": idx,
                        "error": "Download failed after retries"
                    })
            
            result["success"] = len(result["saved_paths"]) > 0
            result["count"] = len(result["saved_paths"])
            
            if result["success"]:
                print(f"\n✅ 生成完成！共 {result['count']} 张图片")
                print(f"📁 保存位置: {self.output_dir}")
            else:
                result["error"] = "All downloads failed"
            
        except Exception as e:
            print(f"❌ 处理响应失败: {e}")
            result["error"] = str(e)
            result["raw_response"] = str(response)
        
        return result
