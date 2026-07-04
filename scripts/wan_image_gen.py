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

import sys
from pathlib import Path
from typing import List, Optional

# 导入基类
sys.path.insert(0, str(Path(__file__).parent))
from base_generator import BaseImageGenerator

from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message


class WanImageGenerator(BaseImageGenerator):
    """通义万相图片生成器"""
    
    MODELS = {
        "pro": "wan2.7-image-pro",
        "std": "wan2.7-image"
    }
    
    SIZES = {
        "1k": "1024*1024",
        "2k": "2048*2048",
        "portrait": "768*1152",
        "landscape": "1152*768",
        "square": "1024*1024"
    }
    
    def text_to_image(
        self,
        prompt: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k",
        enable_sequential: bool = False,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """文生图：根据文本描述生成图片"""
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        content = [{"text": prompt}]
        message = Message(role="user", content=content)
        
        print(f"🎨 文生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        if negative_prompt:
            print(f"🚫 负向提示词: {negative_prompt[:50]}")
        print("⏳ 生成中，请稍候...")
        
        try:
            call_kwargs = dict(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                enable_sequential=enable_sequential,
                n=n,
                size=size_value
            )
            if negative_prompt:
                call_kwargs["negative_prompt"] = negative_prompt
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = ImageGeneration.call(**call_kwargs)
            
            metadata = {
                "model": model_name,
                "prompt": prompt,
                "size": size_value,
                "n": n,
                "seed": seed,
                "negative_prompt": negative_prompt,
                "extra_params": {"enable_sequential": enable_sequential}
            }
            
            return self._process_response(response, "text2img", filename_prefix, metadata)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def image_to_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """图生图：基于输入图片和文本描述生成新图片"""
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        image_url = self._prepare_image(image_path)
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
            call_kwargs = dict(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                n=n,
                size=size_value
            )
            if negative_prompt:
                call_kwargs["negative_prompt"] = negative_prompt
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = ImageGeneration.call(**call_kwargs)
            
            metadata = {
                "model": model_name,
                "prompt": prompt,
                "size": size_value,
                "n": n,
                "seed": seed,
                "negative_prompt": negative_prompt,
                "extra_params": {"input_image": image_path}
            }
            
            return self._process_response(response, "img2img", filename_prefix, metadata)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def edit_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "pro",
        n: int = 1,
        size: str = "1k",
        negative_prompt: Optional[str] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """图片编辑：对输入图片进行编辑修改"""
        return self.image_to_image(
            prompt, image_path, model=model, n=n, size=size,
            negative_prompt=negative_prompt,
            filename_prefix=filename_prefix
        )
    
    def generate_story_images(
        self,
        prompts: List[str],
        model: str = "pro",
        size: str = "2k",
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """组图生成：生成一组相关的图片"""
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        combined_prompt = "；".join(prompts)
        content = [{"text": combined_prompt}]
        message = Message(role="user", content=content)
        
        print(f"📚 组图生成 - 模型: {model_name}, 数量: {len(prompts)}, 尺寸: {size_value}")
        print(f"📝 主题: {combined_prompt[:100]}{'...' if len(combined_prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            call_kwargs = dict(
                model=model_name,
                api_key=self.api_key,
                messages=[message],
                enable_sequential=True,
                n=len(prompts),
                size=size_value
            )
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = ImageGeneration.call(**call_kwargs)
            
            metadata = {
                "model": model_name,
                "prompt": combined_prompt,
                "size": size_value,
                "n": len(prompts),
                "seed": seed,
                "extra_params": {"enable_sequential": True, "individual_prompts": prompts}
            }
            
            return self._process_response(response, "story", filename_prefix, metadata)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """命令行入口"""
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
    p_t2i.add_argument("--seed", type=int, default=None, help="随机种子")
    p_t2i.add_argument("--filename-prefix", default=None, help="文件名前缀（如：可爱橘猫_窗台）")
    
    # img2img
    p_i2i = subparsers.add_parser("img2img", help="图生图")
    p_i2i.add_argument("prompt", help="提示词")
    p_i2i.add_argument("image", help="输入图片路径或URL")
    p_i2i.add_argument("--model", default="pro", choices=["pro", "std"])
    p_i2i.add_argument("--n", type=int, default=1)
    p_i2i.add_argument("--size", default="1k")
    p_i2i.add_argument("--negative-prompt", default=None)
    p_i2i.add_argument("--seed", type=int, default=None)
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
    p_story.add_argument("--seed", type=int, default=None)
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
            seed=args.seed,
            filename_prefix=prefix
        )
    elif args.command == "img2img":
        result = generator.image_to_image(
            args.prompt, args.image, model=args.model, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            filename_prefix=prefix
        )
    elif args.command == "edit":
        result = generator.edit_image(
            args.prompt, args.image, model=args.model, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            filename_prefix=prefix
        )
    elif args.command == "story":
        result = generator.generate_story_images(
            [args.theme], model=args.model, size=args.size,
            seed=args.seed,
            filename_prefix=prefix
        )
    else:
        parser.print_help()
        sys.exit(1)
    
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
