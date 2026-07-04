#!/usr/bin/env python3
"""
Wan Image Generation Script
支持使用 wan2.7-image-pro 和 wan2.7-image 模型进行：
- 文生图 (Text-to-Image)
- 图生图 (Image-to-Image)  
- 图片编辑 (Image Editing)

使用方法:
    python wan_image_gen.py text2img "一只可爱的橘猫在草地上玩耍"
    python wan_image_gen.py img2img "将图片转换为水彩画风格" input.jpg
    python wan_image_gen.py edit "给图片添加圣诞帽" input.jpg
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
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message


class WanImageGenerator:
    """通义万相图片生成器"""
    
    # 支持的模型
    MODELS = {
        "pro": "wan2.7-image-pro",
        "std": "wan2.7-image"
    }
    
    # 支持的尺寸
    SIZES = {
        "1k": "1024*1024",
        "2k": "2K",
        "portrait": "768*1152",
        "landscape": "1152*768",
        "square": "1024*1024"
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
        # 优先级：1. 当前工作目录下的 output/  2. ~/Pictures/qwen-image-generator/（保底）
        cwd_output = Path.cwd() / "output"
        fallback_output = Path.home() / "Pictures" / "qwen-image-generator"
        try:
            cwd_output.mkdir(exist_ok=True)
            self.output_dir = cwd_output
        except (PermissionError, OSError):
            fallback_output.mkdir(parents=True, exist_ok=True)
            self.output_dir = fallback_output
    
    def text_to_image(
        self,
        prompt: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k",
        enable_sequential: bool = False,
        negative_prompt: Optional[str] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """
        文生图：根据文本描述生成图片
        
        Args:
            prompt: 图片描述文本
            model: 模型选择，"pro" 或 "std"
            n: 生成图片数量 (1-4)
            size: 图片尺寸，支持 "1k", "2k", "portrait", "landscape", "square"
            enable_sequential: 是否启用顺序生成（用于多图组图）
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
        
        message = Message(role="user", content=content)
        
        print(f"🎨 文生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = ImageGeneration.call(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                enable_sequential=enable_sequential,
                n=n,
                size=size_value
            )
            
            return self._process_response(response, "text2img", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def image_to_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k"
    ) -> dict:
        """
        图生图：基于输入图片和文本描述生成新图片
        
        Args:
            prompt: 图片描述/转换指令
            image_path: 输入图片路径
            model: 模型选择，"pro" 或 "std"
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
        
        message = Message(role="user", content=content)
        
        print(f"🖼️  图生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"📷 输入图片: {image_path}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = ImageGeneration.call(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                n=n,
                size=size_value
            )
            
            return self._process_response(response, "img2img", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def edit_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k"
    ) -> dict:
        """
        图片编辑：对输入图片进行编辑修改
        
        Args:
            prompt: 编辑指令（如"添加圣诞帽"、"转换为黑白"）
            image_path: 输入图片路径
            model: 模型选择，"pro" 或 "std"
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
        
        message = Message(role="user", content=content)
        
        print(f"✏️  图片编辑 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 编辑指令: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"📷 输入图片: {image_path}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = ImageGeneration.call(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                n=n,
                size=size_value
            )
            
            return self._process_response(response, "edit", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_story_images(
        self,
        prompts: List[str],
        model: str = "pro",
        size: str = "2k"
    ) -> dict:
        """
        组图生成：生成一组相关的图片（如四季主题）
        
        Args:
            prompts: 多个图片描述列表
            model: 模型选择
            size: 图片尺寸
        
        Returns:
            dict: 包含生成结果和保存路径的字典
        """
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        # 将所有提示合并为一个描述
        combined_prompt = "；".join(prompts)
        
        content = [{"text": combined_prompt}]
        message = Message(role="user", content=content)
        
        print(f"📚 组图生成 - 模型: {model_name}, 数量: {len(prompts)}, 尺寸: {size_value}")
        print(f"📝 主题: {combined_prompt[:100]}{'...' if len(combined_prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            response = ImageGeneration.call(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                enable_sequential=True,
                n=len(prompts),
                size=size_value
            )
            
            return self._process_response(response, "story", filename_prefix)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _prepare_image(self, image_path: str) -> str:
        """
        准备输入图片（支持本地文件和URL）
        
        Args:
            image_path: 图片路径或URL
        
        Returns:
            str: 图片URL或Base64编码
        """
        # 如果是URL，直接返回
        if image_path.startswith(('http://', 'https://')):
            return image_path
        
        # 读取本地文件并转换为Base64
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 读取文件
        with open(path, 'rb') as f:
            image_data = f.read()
        
        # 转换为Base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # 获取MIME类型
        suffix = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(suffix, 'image/jpeg')
        
        return f"data:{mime_type};base64,{base64_data}"
    
    def _process_response(self, response, task_type: str, filename_prefix: str = None) -> dict:
        """
        处理API响应并保存图片
        
        Args:
            response: API响应对象
            task_type: 任务类型（用于文件命名）
        
        Returns:
            dict: 处理后的结果
        """
        result = {
            "success": False,
            "images": [],
            "saved_paths": [],
            "raw_response": None
        }
        
        # 检查响应状态
        if response.status_code != 200:
            print(f"❌ API 错误: {response.code} - {response.message}")
            result["error"] = f"{response.code}: {response.message}"
            return result
        
        # 解析输出
        try:
            output = response.output
            
            # 提取图片URL
            image_urls = []
            
            if hasattr(output, 'choices') and output.choices:
                for choice in output.choices:
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and 'image' in item:
                                    image_urls.append(item['image'])
            
            if not image_urls:
                print("⚠️  未找到生成的图片")
                result["raw_response"] = str(response)
                return result
            
            # 下载并保存图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for idx, url in enumerate(image_urls, 1):
                print(f"📥 下载图片 {idx}/{len(image_urls)}...")
                
                # 生成文件名
                # 使用自定义前缀或默认任务类型，组图时自动加序列号
                name_prefix = filename_prefix if filename_prefix else task_type
                # wan2.7 组图时显示序列号（根据实际生成的图片数量判断）
                if len(image_urls) > 1 or task_type == "story":
                    filename = f"{name_prefix}_{timestamp}_seq{idx:02d}.png"
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
    
    parser = argparse.ArgumentParser(description="wan2.7 图片生成器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # text2img
    p_t2i = subparsers.add_parser("text2img", help="文生图")
    p_t2i.add_argument("prompt", help="提示词")
    p_t2i.add_argument("--model", default="pro", choices=["pro", "std"], help="模型 (默认: pro)")
    p_t2i.add_argument("--n", type=int, default=1, help="生成数量 1-4 (默认: 1)")
    p_t2i.add_argument("--size", default="1k", help="尺寸: 1k/2k/portrait/landscape/square (默认: 1k)")
    p_t2i.add_argument("--enable-sequential", action="store_true", help="启用顺序生成（组图用）")
    p_t2i.add_argument("--negative-prompt", default=None, help="负向提示词")
    p_t2i.add_argument("--filename-prefix", default=None, help="文件名前缀（如：可爱橘猫_窗台）")
    
    # img2img
    p_i2i = subparsers.add_parser("img2img", help="图生图")
    p_i2i.add_argument("prompt", help="提示词")
    p_i2i.add_argument("image", help="输入图片路径或URL")
    p_i2i.add_argument("--model", default="pro", choices=["pro", "std"])
    p_i2i.add_argument("--n", type=int, default=1)
    p_i2i.add_argument("--size", default="1k")
    p_i2i.add_argument("--negative-prompt", default=None)
    p_i2i.add_argument("--filename-prefix", default=None)
    
    # edit
    p_edit = subparsers.add_parser("edit", help="图片编辑")
    p_edit.add_argument("prompt", help="编辑指令")
    p_edit.add_argument("image", help="输入图片路径或URL")
    p_edit.add_argument("--model", default="pro", choices=["pro", "std"])
    p_edit.add_argument("--n", type=int, default=1)
    p_edit.add_argument("--size", default="1k")
    p_edit.add_argument("--negative-prompt", default=None)
    p_edit.add_argument("--filename-prefix", default=None)
    
    # story
    p_story = subparsers.add_parser("story", help="故事组图")
    p_story.add_argument("theme", help="故事主题")
    p_story.add_argument("--model", default="pro", choices=["pro", "std"])
    p_story.add_argument("--size", default="2k")
    p_story.add_argument("--filename-prefix", default=None)
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        generator = WanImageGenerator()
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    prefix = args.filename_prefix
    
    if args.command == "text2img":
        result = generator.text_to_image(
            args.prompt, model=args.model, n=args.n, size=args.size,
            enable_sequential=args.enable_sequential,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "img2img":
        result = generator.image_to_image(
            args.prompt, args.image, model=args.model, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "edit":
        result = generator.edit_image(
            args.prompt, args.image, model=args.model, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "story":
        result = generator.story_generation(
            args.theme, model=args.model, size=args.size,
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
