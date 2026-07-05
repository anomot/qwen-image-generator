#!/usr/bin/env python3
"""
Qwen Image 2.0 Generation Script
支持使用 qwen-image-2.0 系列模型进行：
- 文生图 (Text-to-Image)
- 图生图 (Image-to-Image)  
- 图片编辑 (Image Editing)
- 多图融合 (Multi-Image Fusion)

支持模型：
- default (qwen-image-2.0) — 加速版，效果与性能平衡
- pro (qwen-image-2.0-pro-2026-06-22) — 满血版，最强文字渲染 + 细腻质感

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

import sys
from pathlib import Path
from typing import List, Optional

# 导入基类
sys.path.insert(0, str(Path(__file__).parent))
from base_generator import BaseImageGenerator

from dashscope import MultiModalConversation


class QwenImage20Generator(BaseImageGenerator):
    """Qwen Image 2.0 图片生成器"""
    
    MODELS = {
        "default": "qwen-image-2.0",
        "pro": "qwen-image-2.0-pro-2026-06-22"
    }
    
    SIZES = {
        "2k": "2048*2048",
        "1k": "1024*1024",
        "512": "512*512",
        "portrait": "1152*2048",
        "landscape": "2048*1152",
        "square": "2048*2048"
    }
    
    def text_to_image(
        self,
        prompt: str,
        model: str = "default",
        n: int = 1,
        size: str = "2k",
        watermark: bool = False,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """文生图：根据文本描述生成图片"""
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        messages = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]
        
        print(f"🎨 文生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            call_kwargs = dict(
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
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = self._call_api_with_retry(MultiModalConversation.call, **call_kwargs)
            
            metadata = {
                "model": model_name,
                "prompt": prompt,
                "size": size_value,
                "n": n,
                "seed": seed,
                "negative_prompt": negative_prompt,
                "extra_params": {"watermark": watermark}
            }
            
            return self._process_response(response, "text2img", filename_prefix, metadata)
            
        except Exception as e:
            self._stop_progress()
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def image_to_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "default",
        n: int = 1,
        size: str = "2k",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """图生图：基于输入图片和文本描述生成新图片"""
        model_name = self.MODELS.get(model, model)
        size_value = self._validate_resolution(size, "qwen")
        
        image_url = self._prepare_image(image_path)
        messages = [{
            "role": "user",
            "content": [
                {"image": image_url},
                {"text": prompt}
            ]
        }]
        
        print(f"🖼️  图生图 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"📷 输入图片: {image_path}")
        print("⏳ 生成中，请稍候...")
        
        try:
            call_kwargs = dict(
                api_key=self.api_key,
                model=model_name,
                messages=messages,
                result_format='message',
                stream=False,
                n=n,
                size=size_value,
                watermark=False,
                negative_prompt=negative_prompt if negative_prompt else ""
            )
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = self._call_api_with_retry(MultiModalConversation.call, **call_kwargs)
            
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
            self._stop_progress()
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}
    
    def edit_image(
        self,
        prompt: str,
        image_path: str,
        model: str = "default",
        n: int = 1,
        size: str = "2k",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """图片编辑：对输入图片进行编辑修改"""
        return self.image_to_image(
            prompt, image_path, model=model, n=n, size=size,
            negative_prompt=negative_prompt,
            seed=seed,
            filename_prefix=filename_prefix
        )
    
    def multi_image_fusion(
        self,
        prompt: str,
        image_paths: List[str],
        model: str = "default",
        n: int = 1,
        size: str = "2k",
        seed: Optional[int] = None,
        filename_prefix: Optional[str] = None
    ) -> dict:
        """多图融合：将多张图片融合为一张"""
        model_name = self.MODELS.get(model, model)
        size_value = self.SIZES.get(size, size)
        
        content = []
        for idx, path in enumerate(image_paths, 1):
            image_url = self._prepare_image(path)
            content.append({"image": image_url})
            print(f"📷 加载图片 {idx}/{len(image_paths)}: {path}")
        content.append({"text": prompt})
        
        messages = [{"role": "user", "content": content}]
        
        print(f"🔀 多图融合 - 模型: {model_name}, 数量: {n}, 尺寸: {size_value}")
        print(f"📝 融合指令: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print("⏳ 生成中，请稍候...")
        
        try:
            call_kwargs = dict(
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
            if seed is not None:
                call_kwargs["seed"] = seed
            
            response = self._call_api_with_retry(MultiModalConversation.call, **call_kwargs)
            
            metadata = {
                "model": model_name,
                "prompt": prompt,
                "size": size_value,
                "n": n,
                "seed": seed,
                "extra_params": {"input_images": image_paths}
            }
            
            return self._process_response(response, "multi", filename_prefix, metadata)
            
        except Exception as e:
            self._stop_progress()
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="qwen-image-2.0 图片生成器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # text2img
    p_t2i = subparsers.add_parser("text2img", help="文生图")
    p_t2i.add_argument("prompt", help="提示词")
    p_t2i.add_argument("--n", type=int, default=1, help="生成数量 1-6 (默认: 1)")
    p_t2i.add_argument("--size", default="2k", help="尺寸: 2k/1k/512/portrait/landscape/square (默认: 2k)")
    p_t2i.add_argument("--negative-prompt", default=None, help="负向提示词")
    p_t2i.add_argument("--seed", type=int, default=None, help="随机种子")
    p_t2i.add_argument("--model", default="default", choices=["default", "pro"], help="模型: default=加速版, pro=满血版 (默认: default)")
    p_t2i.add_argument("--watermark", action="store_true", help="添加水印（默认关闭）")
    p_t2i.add_argument("--filename-prefix", default=None, help="文件名前缀（如：春日海报_花朵）")
    
    # img2img
    p_i2i = subparsers.add_parser("img2img", help="图生图")
    p_i2i.add_argument("prompt", help="提示词")
    p_i2i.add_argument("image", help="输入图片路径或URL")
    p_i2i.add_argument("--model", default="default", choices=["default", "pro"], help="模型: default=加速版, pro=满血版")
    p_i2i.add_argument("--n", type=int, default=1)
    p_i2i.add_argument("--size", default="2k")
    p_i2i.add_argument("--negative-prompt", default=None)
    p_i2i.add_argument("--seed", type=int, default=None)
    p_i2i.add_argument("--filename-prefix", default=None)
    
    # edit
    p_edit = subparsers.add_parser("edit", help="图片编辑")
    p_edit.add_argument("prompt", help="编辑指令")
    p_edit.add_argument("image", help="输入图片路径或URL")
    p_edit.add_argument("--model", default="default", choices=["default", "pro"], help="模型: default=加速版, pro=满血版")
    p_edit.add_argument("--n", type=int, default=1)
    p_edit.add_argument("--size", default="2k")
    p_edit.add_argument("--negative-prompt", default=None)
    p_edit.add_argument("--seed", type=int, default=None)
    p_edit.add_argument("--filename-prefix", default=None)
    
    # multi
    p_multi = subparsers.add_parser("multi", help="多图融合")
    p_multi.add_argument("prompt", help="融合描述")
    p_multi.add_argument("images", nargs="+", help="输入图片路径或URL（至少2张）")
    p_multi.add_argument("--model", default="default", choices=["default", "pro"], help="模型: default=加速版, pro=满血版")
    p_multi.add_argument("--n", type=int, default=1)
    p_multi.add_argument("--size", default="2k")
    p_multi.add_argument("--seed", type=int, default=None)
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
            args.prompt, model=args.model, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            watermark=args.watermark,
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
            seed=args.seed,
            filename_prefix=prefix
        )
    elif args.command == "multi":
        if len(args.images) < 2:
            print("❌ 多图融合至少需要 2 张图片")
            sys.exit(1)
        result = generator.multi_image_fusion(
            args.prompt, args.images, model=args.model, n=args.n, size=args.size,
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
