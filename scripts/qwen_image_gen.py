#!/usr/bin/env python3
"""
Qwen Image 2.0 Generation Script
支持使用 qwen-image-2.0 模型进行：
- 文生图 (Text-to-Image)
- 图生图 (Image-to-Image)  
- 图片编辑 (Image Editing)
- 多图融合 (Multi-Image Fusion)

特点：
- 原生 2K 分辨率（最高 2048*2048）
- 复杂的文字渲染能力（中文、英文）
- 信息图、PPT 等专业内容生成
- 多图输入融合编辑

使用方法:
    python qwen_image_gen.py text2img "一只可爱的橘猫在草地上玩耍"
    python qwen_image_gen.py img2img "将图片转换为水彩画风格" input.jpg
    python qwen_image_gen.py edit "给图片添加圣诞帽" input.jpg
    python qwen_image_gen.py multi "融合描述" img1.jpg img2.jpg img3.jpg
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime

import dashscope
from dashscope import MultiModalConversation


class QwenImage20Generator:
    """Qwen Image 2.0 图片生成器"""
    
    # 支持的模型
    MODELS = {
        "default": "qwen-image-2.0"
    }
    
    # 支持的尺寸 (qwen-image-2.0 支持 512-2048 范围)
    SIZES = {
        "2k": "2048*2048",
        "1k": "1024*1024",
        "512": "512*512",
        "portrait": "1152*2048",      # 竖版高清
        "landscape": "2048*1152",     # 横版高清
        "square": "2048*2048"
    }
    
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
        
        # 创建输出目录
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def text_to_image(
        self,
        prompt: str,
        model: str = "default",
        n: int = 1,
        size: str = "1k",
        watermark: bool = False,
        negative_prompt: Optional[str] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """
        文生图：根据文本描述生成图片
        
        Args:
            prompt: 图片描述文本
            model: 模型选择（目前只有 default = qwen-image-2.0）
            n: 生成图片数量 (1-6)
            size: 图片尺寸，支持 "2k", "1k", "512", "portrait", "landscape", "square"
            watermark: 是否添加水印
            negative_prompt: 负向提示词（不希望出现的元素）
        
        Returns:
            dict: 包含生成结果和保存路径的字典
        """
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        # 构建消息内容
        content = []
        
        # 添加文本提示
        text_content = prompt
        if negative_prompt:
            text_content += f"\n\n负面提示: {negative_prompt}"
        
        content.append({"text": text_content})
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        print(f"🎨 文生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = MultiModalConversation.call(
                api_key=self.api_key,
                model=model_name,
                messages=messages,
                result_format='message',
                stream=False,
                n=n,
                size=size_value,
                watermark=watermark,
                negative_prompt=negative_prompt if negative_prompt else ""
            )
            
            return self._process_response(response, "text2img", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def image_to_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "default",
        n: int = 1,
        size: str = "2k"
    ,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """
        图生图：基于输入图片和文本描述生成新图片
        
        Args:
            prompt: 图片描述/转换指令
            image_path: 输入图片路径
            model: 模型选择
            n: 生成图片数量
            size: 输出图片尺寸
        
        Returns:
            dict: 包含生成结果和保存路径的字典
        """
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        # 读取并编码输入图片
        image_url = self._prepare_image(image_path)
        
        # 构建消息内容
        content = [
            {"image": image_url},
            {"text": prompt}
        ]
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        print(f"🖼️  图生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"📷 输入图片: {image_path}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = MultiModalConversation.call(
                api_key=self.api_key,
                model=model_name,
                messages=messages,
                result_format='message',
                stream=False,
                n=n,
                size=size_value,
                watermark=False,
                negative_prompt=""
            )
            
            return self._process_response(response, "img2img", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def edit_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "default",
        n: int = 1,
        size: str = "2k"
    ,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """
        图片编辑：对输入图片进行编辑修改
        
        Args:
            prompt: 编辑指令
            image_path: 输入图片路径
            model: 模型选择
            n: 生成图片数量
            size: 输出图片尺寸
        
        Returns:
            dict: 包含生成结果和保存路径的字典
        """
        # 编辑本质上是图生图的一种形式
        return self.image_to_image(prompt, image_path, model, n, size)
    
    def multi_image_fusion(
        self,
        prompt: str,
        image_paths: List[str],
        model: str = "default",
        n: int = 1,
        size: str = "2k"
    ,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """
        多图融合：基于多张输入图片和文本描述生成新图片
        
        Args:
            prompt: 融合描述/指令
            image_paths: 输入图片路径列表
            model: 模型选择
            n: 生成图片数量
            size: 输出图片尺寸
        
        Returns:
            dict: 包含生成结果和保存路径的字典
        """
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        # 构建消息内容
        content = []
        
        # 添加所有输入图片
        for idx, img_path in enumerate(image_paths, 1):
            print(f"📷 加载图片 {idx}/{len(image_paths)}: {img_path}")
            image_url = self._prepare_image(img_path)
            content.append({"image": image_url})
        
        # 添加文本指令
        content.append({"text": prompt})
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        print(f"🔀 多图融合 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 融合指令: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = MultiModalConversation.call(
                api_key=self.api_key,
                model=model_name,
                messages=messages,
                result_format='message',
                stream=False,
                n=n,
                size=size_value,
                watermark=False,
                negative_prompt=""
            )
            
            return self._process_response(response, "multi_fusion", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _prepare_image(self, image_path: str) -> str:
        """
        准备图片：如果是本地路径则转为 base64，否则返回 URL
        
        Args:
            image_path: 图片路径或 URL
        
        Returns:
            str: 可用的图片 URL 或 base64 数据
        """
        # 如果是 HTTP/HTTPS URL，直接返回
        if image_path.startswith(('http://', 'https://')):
            return image_path
        
        # 本地文件转 base64
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 读取并编码为 base64
        with open(path, 'rb') as f:
            img_data = f.read()
        
        b64_data = base64.b64encode(img_data).decode('utf-8')
        
        # 根据扩展名确定 MIME 类型
        ext = path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')
        
        return f"data:{mime_type};base64,{b64_data}"
    
    def _process_response(self, response, task_type: str, filename_prefix: str = None) -> dict:
        """
        处理 API 响应
        
        Args:
            response: API 返回的响应对象
            task_type: 任务类型标识（用于文件命名）
        
        Returns:
            dict: 处理后的结果字典
        """
        result = {
            "success": False,
            "images": [],
            "saved_paths": [],
            "raw_response": None
        }
        
        try:
            # 检查响应状态
            if response.get('status_code') != 200:
                error_code = response.get('code', 'Unknown')
                error_msg = response.get('message', 'Unknown error')
                print(f"❌ API 错误: {error_code} - {error_msg}")
                result["error"] = f"{error_code}: {error_msg}"
                result["raw_response"] = str(response)
                return result
            
            # 提取图片 URL
            image_urls = []
            output = response.get('output', {})
            choices = output.get('choices', [])
            
            if not choices:
                print("⚠️  未找到生成的图片")
                result["error"] = "No images generated"
                result["raw_response"] = str(response)
                return result
            
            # 遍历所有 choices 提取图片
            for choice in choices:
                message = choice.get('message', {})
                content = message.get('content', [])
                
                for item in content:
                    if 'image' in item:
                        image_urls.append(item['image'])
            
            if not image_urls:
                print("⚠️  未找到生成的图片 URL")
                result["error"] = "No image URLs in response"
                result["raw_response"] = str(response)
                return result
            
            # 下载并保存图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for idx, url in enumerate(image_urls, 1):
                print(f"📥 下载图片 {idx}/{len(image_urls)}...")
                
                # 生成文件名
                # 使用自定义前缀或默认任务类型
                name_prefix = filename_prefix if filename_prefix else task_type
                if len(image_urls) > 1:
                    filename = f"{name_prefix}_{timestamp}_{idx:02d}.png"
                else:
                    filename = f"{name_prefix}_{timestamp}.png"
                save_path = self.output_dir / filename
                
                # 下载图片
                try:
                    img_response = requests.get(url, timeout=60)
                    img_response.raise_for_status()
                    
                    # 保存图片
                    with open(save_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    print(f"✅ 已保存: {save_path}")
                    
                    result["images"].append({
                        "url": url,
                        "index": idx,
                        "filename": filename
                    })
                    result["saved_paths"].append(str(save_path))
                    
                except Exception as e:
                    print(f"⚠️  下载失败: {e}")
                    result["images"].append({
                        "url": url,
                        "index": idx,
                        "error": str(e)
                    })
            
            result["success"] = True
            result["count"] = len(image_urls)
            
            print(f"\n✅ 生成完成！共 {len(image_urls)} 张图片")
            print(f"📁 保存位置: {self.output_dir}")
            
        except Exception as e:
            print(f"❌ 处理响应失败: {e}")
            result["error"] = str(e)
            result["raw_response"] = str(response)
        
        return result


def main():
    """命令行入口（argparse）"""
    import argparse
    
    parser = argparse.ArgumentParser(description="qwen-image-2.0 图片生成器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # text2img
    p_t2i = subparsers.add_parser("text2img", help="文生图")
    p_t2i.add_argument("prompt", help="提示词")
    p_t2i.add_argument("--n", type=int, default=1, help="生成数量 1-6 (默认: 1)")
    p_t2i.add_argument("--size", default="1k", help="尺寸: 2k/1k/512/portrait/landscape/square (默认: 1k)")
    p_t2i.add_argument("--negative-prompt", default=None, help="负向提示词")
    p_t2i.add_argument("--filename-prefix", default=None, help="文件名前缀（如：春日海报_花朵）")
    
    # img2img
    p_i2i = subparsers.add_parser("img2img", help="图生图")
    p_i2i.add_argument("prompt", help="提示词")
    p_i2i.add_argument("image", help="输入图片路径或URL")
    p_i2i.add_argument("--n", type=int, default=1)
    p_i2i.add_argument("--size", default="1k")
    p_i2i.add_argument("--negative-prompt", default=None)
    p_i2i.add_argument("--filename-prefix", default=None)
    
    # edit
    p_edit = subparsers.add_parser("edit", help="图片编辑")
    p_edit.add_argument("prompt", help="编辑指令")
    p_edit.add_argument("image", help="输入图片路径或URL")
    p_edit.add_argument("--n", type=int, default=1)
    p_edit.add_argument("--size", default="1k")
    p_edit.add_argument("--negative-prompt", default=None)
    p_edit.add_argument("--filename-prefix", default=None)
    
    # multi
    p_multi = subparsers.add_parser("multi", help="多图融合")
    p_multi.add_argument("prompt", help="融合描述")
    p_multi.add_argument("images", nargs="+", help="输入图片路径或URL（至少2张）")
    p_multi.add_argument("--n", type=int, default=1)
    p_multi.add_argument("--size", default="1k")
    p_multi.add_argument("--filename-prefix", default=None)
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        generator = QwenImage20Generator()
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    prefix = args.filename_prefix
    
    if args.command == "text2img":
        result = generator.text_to_image(
            args.prompt, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "img2img":
        result = generator.image_to_image(
            args.prompt, args.image, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "edit":
        result = generator.edit_image(
            args.prompt, args.image, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "multi":
        if len(args.images) < 2:
            print("❌ 多图融合至少需要 2 张图片")
            sys.exit(1)
        result = generator.multi_image_fusion(
            args.prompt, args.images, n=args.n, size=args.size,
            filename_prefix=prefix
        )
    else:
        parser.print_help()
        sys.exit(1)
        return
    
    if result["success"]:
        print(f"\n📊 结果摘要:")
        print(f"  - 成功生成: {result['count']} 张图片")
        for p in result["saved_paths"]:
            print(f"  - {p}")
    else:
        print(f"\n❌ 生成失败: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
