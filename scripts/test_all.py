#!/usr/bin/env python3
"""
端到端测试脚本 - 验证三个生成器的所有 CLI 路径

用法:
    python test_all.py                    # 运行所有测试（需要 API Key）
    python test_all.py --dry-run          # 只验证导入和方法签名（不消耗 API 额度）
    python test_all.py --image /path/to/image.jpg  # 指定测试图片（img2img/edit 需要）

退出码:
    0 = 全部通过
    1 = 有测试失败
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 确保能导入同目录的模块
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试所有模块能否正常导入"""
    print("📦 测试模块导入...")
    
    try:
        from base_generator import BaseImageGenerator
        print("  ✅ base_generator.BaseImageGenerator")
    except ImportError as e:
        print(f"  ❌ base_generator: {e}")
        return False
    
    try:
        from wan_image_gen import WanImageGenerator
        print("  ✅ wan_image_gen.WanImageGenerator")
    except ImportError as e:
        print(f"  ❌ wan_image_gen: {e}")
        return False
    
    try:
        from qwen_image_gen import QwenImage20Generator
        print("  ✅ qwen_image_gen.QwenImage20Generator")
    except ImportError as e:
        print(f"  ❌ qwen_image_gen: {e}")
        return False
    
    try:
        from z_image_gen import ZImageTurboGenerator
        print("  ✅ z_image_gen.ZImageTurboGenerator")
    except ImportError as e:
        print(f"  ❌ z_image_gen: {e}")
        return False
    
    return True


def test_inheritance():
    """测试继承关系"""
    print("\n🏗️  测试继承关系...")
    
    from base_generator import BaseImageGenerator
    from wan_image_gen import WanImageGenerator
    from qwen_image_gen import QwenImage20Generator
    from z_image_gen import ZImageTurboGenerator
    
    for cls in [WanImageGenerator, QwenImage20Generator, ZImageTurboGenerator]:
        if issubclass(cls, BaseImageGenerator):
            print(f"  ✅ {cls.__name__} → BaseImageGenerator")
        else:
            print(f"  ❌ {cls.__name__} 未继承 BaseImageGenerator")
            return False
    
    return True


def test_method_signatures():
    """测试所有方法签名一致性"""
    print("\n🔍 测试方法签名...")
    
    import inspect
    from wan_image_gen import WanImageGenerator
    from qwen_image_gen import QwenImage20Generator
    from z_image_gen import ZImageTurboGenerator
    
    # 检查所有生成器都有的方法
    required_methods = ['text_to_image']
    shared_methods = ['image_to_image', 'edit_image']
    
    all_pass = True
    
    # wan 和 qwen 应该有 img2img/edit
    for cls in [WanImageGenerator, QwenImage20Generator]:
        for method_name in shared_methods:
            if hasattr(cls, method_name):
                sig = inspect.signature(getattr(cls, method_name))
                params = list(sig.parameters.keys())
                
                # 必须有 filename_prefix
                if 'filename_prefix' not in params:
                    print(f"  ❌ {cls.__name__}.{method_name} 缺少 filename_prefix 参数")
                    all_pass = False
                    continue
                
                # 检查 seed 参数
                if method_name != 'edit_image' or cls.__name__ == 'WanImageGenerator':
                    # wan.edit_image 委托给 image_to_image，可以没有 seed
                    if 'seed' not in params and method_name != 'edit_image':
                        print(f"  ❌ {cls.__name__}.{method_name} 缺少 seed 参数")
                        all_pass = False
                        continue
                
                print(f"  ✅ {cls.__name__}.{method_name} 签名正确")
            else:
                print(f"  ❌ {cls.__name__} 缺少 {method_name} 方法")
                all_pass = False
    
    # z-image 只需检查 text_to_image
    if hasattr(ZImageTurboGenerator, 'text_to_image'):
        sig = inspect.signature(ZImageTurboGenerator.text_to_image)
        params = list(sig.parameters.keys())
        if 'filename_prefix' in params and 'seed' in params:
            print(f"  ✅ ZImageTurboGenerator.text_to_image 签名正确")
        else:
            print(f"  ❌ ZImageTurboGenerator.text_to_image 参数不完整")
            all_pass = False
    
    # 检查特殊方法
    if hasattr(WanImageGenerator, 'generate_story_images'):
        sig = inspect.signature(WanImageGenerator.generate_story_images)
        if 'seed' in sig.parameters and 'filename_prefix' in sig.parameters:
            print(f"  ✅ WanImageGenerator.generate_story_images 签名正确")
        else:
            print(f"  ❌ WanImageGenerator.generate_story_images 参数不完整")
            all_pass = False
    
    if hasattr(QwenImage20Generator, 'multi_image_fusion'):
        sig = inspect.signature(QwenImage20Generator.multi_image_fusion)
        if 'seed' in sig.parameters and 'filename_prefix' in sig.parameters:
            print(f"  ✅ QwenImage20Generator.multi_image_fusion 签名正确")
        else:
            print(f"  ❌ QwenImage20Generator.multi_image_fusion 参数不完整")
            all_pass = False
    
    # 检查基类新特性
    from base_generator import BaseImageGenerator
    if hasattr(BaseImageGenerator, '_call_api_with_retry'):
        print(f"  ✅ BaseImageGenerator._call_api_with_retry (API 重试)")
    else:
        print(f"  ❌ BaseImageGenerator 缺少 _call_api_with_retry")
        all_pass = False
    
    if hasattr(BaseImageGenerator, '_verify_image'):
        print(f"  ✅ BaseImageGenerator._verify_image (PIL 验证)")
    else:
        print(f"  ❌ BaseImageGenerator 缺少 _verify_image")
        all_pass = False
    
    if hasattr(BaseImageGenerator, '_start_progress'):
        print(f"  ✅ BaseImageGenerator._start_progress (进度心跳)")
    else:
        print(f"  ❌ BaseImageGenerator 缺少 _start_progress")
        all_pass = False
    
    if hasattr(BaseImageGenerator, '_get_dated_output_dir'):
        print(f"  ✅ BaseImageGenerator._get_dated_output_dir (日期分目录)")
    else:
        print(f"  ❌ BaseImageGenerator 缺少 _get_dated_output_dir")
        all_pass = False
    
    return all_pass


def test_filename_validation():
    """测试 filename_prefix 校验"""
    print("\n🔒 测试 filename_prefix 校验...")
    
    from base_generator import BaseImageGenerator
    
    test_cases = [
        ("正常前缀", "正常前缀"),
        ("可爱/橘猫:窗台", "可爱_橘猫_窗台"),
        ("hello world", "hello_world"),
        ("test/../path", "test_path"),
        ("", None),
        (None, None),
        ("---___---", "---_---"),  # 连字符和下划线都允许
        ("///:::", None),  # 全是非法字符，清理后为空
    ]
    
    all_pass = True
    for input_val, expected in test_cases:
        result = BaseImageGenerator.validate_filename_prefix(input_val)
        if result == expected:
            print(f"  ✅ '{input_val}' → '{result}'")
        else:
            print(f"  ❌ '{input_val}' → '{result}' (期望: '{expected}')")
            all_pass = False
    
    return all_pass


def test_instantiation():
    """测试实例化"""
    print("\n🔧 测试实例化...")
    
    api_key = os.getenv("Qwen_DASHSCOPE_API_KEY")
    if not api_key:
        print("  ⚠️  未设置 Qwen_DASHSCOPE_API_KEY，跳过实例化测试")
        return True
    
    from wan_image_gen import WanImageGenerator
    from qwen_image_gen import QwenImage20Generator
    from z_image_gen import ZImageTurboGenerator
    
    try:
        gen = WanImageGenerator(api_key=api_key)
        # 验证日期分目录
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        if date_str in str(gen.output_dir):
            print(f"  ✅ WanImageGenerator (output: {gen.output_dir})")
            print(f"  ✅ 日期分目录生效 ({date_str})")
        else:
            print(f"  ⚠️  WanImageGenerator (output: {gen.output_dir})")
            print(f"  ⚠️  日期分目录未生效? 期望包含 {date_str}")
    except Exception as e:
        print(f"  ❌ WanImageGenerator: {e}")
        return False
    
    try:
        gen = QwenImage20Generator(api_key=api_key)
        print(f"  ✅ QwenImage20Generator (output: {gen.output_dir})")
    except Exception as e:
        print(f"  ❌ QwenImage20Generator: {e}")
        return False
    
    try:
        gen = ZImageTurboGenerator(api_key=api_key)
        print(f"  ✅ ZImageTurboGenerator (output: {gen.output_dir})")
    except Exception as e:
        print(f"  ❌ ZImageTurboGenerator: {e}")
        return False
    
    return True


def test_api_calls(test_image: str = None):
    """真实 API 调用测试（消耗额度）"""
    print("\n🌐 测试真实 API 调用...")
    
    api_key = os.getenv("Qwen_DASHSCOPE_API_KEY")
    if not api_key:
        print("  ⚠️  未设置 Qwen_DASHSCOPE_API_KEY，跳过 API 测试")
        return True
    
    if not test_image or not Path(test_image).exists():
        print("  ⚠️  未提供测试图片 (--image)，跳过 img2img/edit 测试")
        # 至少测试 text2img
        test_image = None
    
    from wan_image_gen import WanImageGenerator
    from qwen_image_gen import QwenImage20Generator
    from z_image_gen import ZImageTurboGenerator
    
    results = []
    
    # wan text2img
    print("\n  [1/7] wan text2img...")
    try:
        gen = WanImageGenerator(api_key=api_key)
        r = gen.text_to_image("测试橘猫", size="1k", n=1, filename_prefix="test_wan_t2i")
        results.append(("wan text2img", r["success"]))
        if r["success"]:
            # 检查 sidecar
            for sp in r["saved_paths"]:
                sidecar = Path(sp).with_suffix('.json')
                if sidecar.exists():
                    print(f"    ✅ 生成成功 + sidecar 存在")
                else:
                    print(f"    ⚠️  生成成功但缺少 sidecar")
        else:
            print(f"    ❌ {r.get('error', 'unknown')}")
    except Exception as e:
        print(f"    ❌ {e}")
        results.append(("wan text2img", False))
    
    # wan img2img (需要图片)
    if test_image:
        print("\n  [2/7] wan img2img...")
        try:
            r = gen.image_to_image("转水彩", test_image, size="1k", filename_prefix="test_wan_i2i")
            results.append(("wan img2img", r["success"]))
            print(f"    {'✅' if r['success'] else '❌'} {'成功' if r['success'] else r.get('error', 'unknown')}")
        except Exception as e:
            print(f"    ❌ {e}")
            results.append(("wan img2img", False))
    else:
        print("\n  [2/7] wan img2img... 跳过 (无图片)")
        results.append(("wan img2img", None))
    
    # qwen text2img
    print("\n  [3/7] qwen text2img...")
    try:
        gen = QwenImage20Generator(api_key=api_key)
        r = gen.text_to_image("测试橘猫", size="512", n=1, filename_prefix="test_qwen_t2i")
        results.append(("qwen text2img", r["success"]))
        if r["success"]:
            for sp in r["saved_paths"]:
                sidecar = Path(sp).with_suffix('.json')
                if sidecar.exists():
                    print(f"    ✅ 生成成功 + sidecar 存在")
                else:
                    print(f"    ⚠️  生成成功但缺少 sidecar")
        else:
            print(f"    ❌ {r.get('error', 'unknown')}")
    except Exception as e:
        print(f"    ❌ {e}")
        results.append(("qwen text2img", False))
    
    # qwen img2img
    if test_image:
        print("\n  [4/7] qwen img2img...")
        try:
            r = gen.image_to_image("转油画", test_image, size="1k", filename_prefix="test_qwen_i2i")
            results.append(("qwen img2img", r["success"]))
            print(f"    {'✅' if r['success'] else '❌'} {'成功' if r['success'] else r.get('error', 'unknown')}")
        except Exception as e:
            print(f"    ❌ {e}")
            results.append(("qwen img2img", False))
    else:
        print("\n  [4/7] qwen img2img... 跳过 (无图片)")
        results.append(("qwen img2img", None))
    
    # qwen edit
    if test_image:
        print("\n  [5/7] qwen edit...")
        try:
            r = gen.edit_image("加蝴蝶结", test_image, size="1k", filename_prefix="test_qwen_edit")
            results.append(("qwen edit", r["success"]))
            print(f"    {'✅' if r['success'] else '❌'} {'成功' if r['success'] else r.get('error', 'unknown')}")
        except Exception as e:
            print(f"    ❌ {e}")
            results.append(("qwen edit", False))
    else:
        print("\n  [5/7] qwen edit... 跳过 (无图片)")
        results.append(("qwen edit", None))
    
    # z-image text2img
    print("\n  [6/7] z-image text2img...")
    try:
        gen = ZImageTurboGenerator(api_key=api_key)
        r = gen.text_to_image("test orange cat", size="1k", n=1, filename_prefix="test_zimg_t2i")
        results.append(("z-image text2img", r["success"]))
        if r["success"]:
            for sp in r["saved_paths"]:
                sidecar = Path(sp).with_suffix('.json')
                if sidecar.exists():
                    print(f"    ✅ 生成成功 + sidecar 存在")
                else:
                    print(f"    ⚠️  生成成功但缺少 sidecar")
        else:
            print(f"    ❌ {r.get('error', 'unknown')}")
    except Exception as e:
        print(f"    ❌ {e}")
        results.append(("z-image text2img", False))
    
    # wan story
    print("\n  [7/7] wan story...")
    try:
        gen = WanImageGenerator(api_key=api_key)
        r = gen.generate_story_images(["小猫的四季"], size="1k", filename_prefix="test_wan_story")
        results.append(("wan story", r["success"]))
        print(f"    {'✅' if r['success'] else '❌'} {'成功' if r['success'] else r.get('error', 'unknown')}")
    except Exception as e:
        print(f"    ❌ {e}")
        results.append(("wan story", False))
    
    # 汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    all_pass = True
    for name, passed in results:
        if passed is None:
            status = "⏭️  跳过"
        elif passed:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
            all_pass = False
        print(f"  {status}  {name}")
    
    return all_pass


def main():
    parser = argparse.ArgumentParser(description="qwen-image-generator 端到端测试")
    parser.add_argument("--dry-run", action="store_true", help="只验证导入和签名，不调用 API")
    parser.add_argument("--image", default=None, help="测试图片路径（用于 img2img/edit 测试）")
    args = parser.parse_args()
    
    print(f"🧪 qwen-image-generator 端到端测试")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   模式: {'dry-run (不调用 API)' if args.dry_run else '完整测试'}")
    print("=" * 50)
    
    all_pass = True
    
    # 阶段 1: 导入测试
    if not test_imports():
        all_pass = False
    
    # 阶段 2: 继承测试
    if not test_inheritance():
        all_pass = False
    
    # 阶段 3: 方法签名测试
    if not test_method_signatures():
        all_pass = False
    
    # 阶段 4: filename 校验测试
    if not test_filename_validation():
        all_pass = False
    
    # 阶段 5: 实例化测试
    if not test_instantiation():
        all_pass = False
    
    if not args.dry_run:
        # 阶段 6: 真实 API 调用
        if not test_api_calls(args.image):
            all_pass = False
    
    print("\n" + "=" * 50)
    if all_pass:
        print("🎉 全部测试通过！")
        sys.exit(0)
    else:
        print("💥 有测试失败，请检查上方输出")
        sys.exit(1)


if __name__ == "__main__":
    main()
