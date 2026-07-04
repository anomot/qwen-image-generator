#!/usr/bin/env python3
"""
Z-Image-Turbo Generation Script
支持使用 z-image-turbo 模型进行：
- 文生图 (Text-to-Image)

注：z-image-turbo 不支持图生图和图片编辑，需要这些功能请使用 wan2.7 或 qwen-image-2.0

特点：
- 超高速生成（速度优先）
- 电影感、胶片质感强
- 真实照片级细节
- 详细场景描述能力强

使用方法:
    python z_image_gen.py text2img "一只可爱的橘猫在草地上玩耍"
"""

import sys
from pathlib import Path
from typing import Optional

# 导入基类
sys.path.insert(0, str(Path(__file__).parent))
from base_generator import BaseImageGenerator

from dashscope import MultiModalConversation


class ZImageTurboGenerator(BaseImageGenerator):
    """Z-Image-Turbo 图片生成器"""
    
    MODELS = {
        "default": "z-image-turbo"
    }
    
    SIZES = {
        "1k": "1024*1024",
        "portrait": "1120*1440",
        "landscape": "1440*1120",
        "square": "1024*1024",
        "hd": "1440*1440"
    }
    
    def text_to_image(
        self,
        prompt: str,
        model: str = "default",
        n: int = 1,
        size: str = "1k",
        prompt_extend: bool = False,
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
                prompt_extend=prompt_extend
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
                "extra_params": {"prompt_extend": prompt_extend}
            }
            
            return self._process_response(response, "text2img", filename_prefix, metadata)
            
        except Exception as e:
            self._stop_progress()
            print(f"❌ 生成失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="z-image-turbo 图片生成器")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # text2img
    p_t2i = subparsers.add_parser("text2img", help="文生图")
    p_t2i.add_argument("prompt", help="提示词")
    p_t2i.add_argument("--n", type=int, default=1, help="生成数量 1-4 (默认: 1)")
    p_t2i.add_argument("--size", default="1k", help="尺寸: 1k/portrait/landscape/square/hd (默认: 1k)")
    p_t2i.add_argument("--negative-prompt", default=None, help="负向提示词")
    p_t2i.add_argument("--seed", type=int, default=None, help="随机种子")
    p_t2i.add_argument("--prompt-extend", action="store_true", help="启用提示词扩展")
    p_t2i.add_argument("--filename-prefix", default=None, help="文件名前缀")
    
    # img2img (not supported)
    p_i2i = subparsers.add_parser("img2img", help="图生图（不支持）")
    p_i2i.add_argument("prompt", nargs="?", default="")
    p_i2i.add_argument("image", nargs="?", default="")
    
    # edit (not supported)
    p_edit = subparsers.add_parser("edit", help="图片编辑（不支持）")
    p_edit.add_argument("prompt", nargs="?", default="")
    p_edit.add_argument("image", nargs="?", default="")
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command in ("img2img", "edit"):
        print(f"⚠️  z-image-turbo 不支持{args.command}功能。")
        print("   请使用 wan2.7 或 qwen-image-2.0 模型。")
        sys.exit(1)
    
    try:
        generator = ZImageTurboGenerator()
    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    
    prefix = args.filename_prefix
    
    if args.command == "text2img":
        result = generator.text_to_image(
            args.prompt, n=args.n, size=args.size,
            negative_prompt=args.negative_prompt,
            seed=args.seed,
            prompt_extend=args.prompt_extend,
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
