---
name: qwen-image-generator
description: "阿里云百炼 AI 生图助手，支持 wan2.7、qwen-image-2.0（加速版/满血版）、z-image-turbo 模型。智能选择最佳模型、自动优化提示词、支持文生图、图生图、多图融合。当用户需要生成图片、编辑图片、设计海报、制作信息图时使用此 Skill。"
---


# ⚠️ 关键规则（必读，违反会出错）

> **生成图片后，Agent 必须遵守以下规则：**

1. **不要自己下载图片** - 脚本已完成下载，输出中的 `✅ 已保存: <路径>` 就是最终路径
2. **不要写代码访问 output_dir** - 脚本已处理好一切，直接用输出的路径展示图片
3. **图片在日期子目录中** - 路径格式是 `output/YYYY-MM-DD/filename.png`，不要移动到 `output/` 根目录
4. **用户指定模型优先** - 用户说"用 qwen 最强"就必须用 pro，不要用提示词关键词重新匹配

**正确做法**：读取脚本输出的路径，直接展示给用户。  
**错误做法**：脚本成功后，再写代码下载、移动或重新处理图片。

---



# Qwen Image Generator

智能 AI 生图工具，集成阿里云百炼三个主流生图模型，自动选择最佳模型并优化提示词。

## 核心工作流程

```
用户请求 → 意图理解 → 模型推荐 → 提示词处理 → 图片处理 → 生成 → 保存
```

### 1. 意图理解（Agent 自身模型）

分析用户请求，提取：
- **任务类型**：文生图 / 图生图 / 多图融合 / 图片编辑
- **场景描述**：主体、环境、氛围
- **风格偏好**：写实 / 插画 / 卡通 / 电影感
- **尺寸需求**：竖版海报 / 横版封面 / 方形图标
- **输入图片**：URL 或本地路径（图生图时）

### 2. 模型推荐

根据场景自动选择最佳模型：

> **Qwen 系列两个版本**：
> - `qwen-image-2.0`（加速版）：效果与性能平衡，日常使用首选
> - `qwen-image-2.0-pro`（满血版，ID: `qwen-image-2.0-pro-2026-06-22`）：系列最强，文字渲染 + 真实质感最佳，生成较慢

| 触发条件 | 推荐模型 | 理由 |
|---------|---------|------|
| "文字"/"排版"/"信息图"/"中文"/"PPT"/"海报" | **qwen-image-2.0-pro** (满血版) | 文字渲染最强，排版最精确 |
| "写实照片"/"真实感"/"高清细节"/"摄影" | **qwen-image-2.0-pro** (满血版) | 真实质感最细腻 |
| "组图"/"连环画"/"故事系列" | **wan2.7** | 支持顺序生成，风格一致 |
| "快速"/"电影感"/"胶片风" | **z-image-turbo** | 速度最快，电影感强 |
| 需要图生图/图片编辑（质量优先） | **qwen-image-2.0-pro** (满血版) | 编辑细节更好 |
| 需要图生图/图片编辑（速度优先） | **qwen-image-2.0** (加速版) | 速度快，够用 |
| 需要多图融合 | **qwen-image-2.0** (加速版) | 唯一支持，融合对速度敏感 |
| 无特殊要求 | **qwen-image-2.0** (加速版) | 日常使用，速度效果平衡 |

**⚠️ 模型选择优先级（严格遵守，违反会选错模型）**：

> **用户明确指定模型 → 直接使用，不要用提示词关键词重新匹配**

**第一优先级：用户显式指定模型（必须遵守）**
- 用户说"qwen 最强"/"qwen pro"/"满血版"/"最高质量"/"最好效果" → `qwen-image-2.0-pro`
- 用户说"qwen"/"默认"/"正常生成" → `qwen-image-2.0`
- 用户说"wan"/"万相" → `wan2.7`
- 用户说"z-image"/"turbo"/"快速" → `z-image-turbo`

**第二优先级：仅当用户未指定模型时，才根据场景关键词自动推荐**
- 根据上方"触发条件"表格中的关键词选择模型
- 注意：即使用户指定了 pro 模型，提示词中包含"文字"/"排版"等关键词时，**仍然用 pro**，不要降级到加速版

**错误示范（必须避免）**：
```
用户: "使用 qwen 最强模型，帮我做一张知识卡片"
错误: 检测到"知识"关键词 → 推荐 qwen-image-2.0（加速版）❌
正确: 用户已指定"qwen 最强" → 使用 qwen-image-2.0-pro ✅
```

**排除规则**：
- 图生图/图片编辑任务 → 排除 z-image-turbo
- 多图融合任务 → 只能用 qwen-image-2.0 系列

### 3. 提示词处理（两阶段）

#### 阶段一：诊断与增强

使用 Agent 自身模型 评估提示词完整度（0-100）：

**评估维度**：
- 画面主体是否清晰
- 场景/环境是否描述
- 光线/氛围是否指定
- 风格/调性是否明确
- 构图/视角是否说明

**处理逻辑**：
- 用户说"不要优化"/"直接使用" → 跳过增强
- 完整度 ≥ 80 → 仅做风格适配
- 完整度 < 80 → 增强 + 风格适配
- 检测到矛盾 → 询问用户

#### 阶段二：风格适配

根据目标模型调整提示词风格：

| 模型 | 风格要求 | 示例 |
|------|---------|------|
| **wan2.7** | 自然中文，像跟朋友说话 | "画一只橘猫趴在窗台上晒太阳，阳光暖暖的洒下来" |
| **qwen-image-2.0** (加速版) | 结构化中文，分要素描述 | "画面主体：橘猫；姿态：趴在窗台；场景：阳光充足；光线：温暖午后；风格：治愈系" |
| **qwen-image-2.0-pro** (满血版) | 结构化中文，更精细的细节描述 | "画面主体：橘猫，毛发细腻；姿态：慵懒趴着；场景：阳光充足，光影斑驳；光线：温暖午后金色光；风格：超写实，高清毛发细节" |
| **z-image-turbo** | 英文 + 电影感关键词 | "film grain, cinematic lighting, Kodak Portra 400, a tabby cat on windowsill, warm golden hour" |

**电影感关键词**：film grain, cinematic lighting, shallow depth of field, bokeh background, analog film texture, Kodak Portra 400

### 4. 图片处理（图生图时）

#### 输入处理

| 输入类型 | 处理方式 |
|---------|---------|
| HTTP/HTTPS URL | **直接传给 API**，不下载 |
| 本地文件 | 转 base64 data URI |
| 文件超限 | 自动压缩（JPEG q85 → 缩小分辨率） |

**文件大小限制**：
- wan2.7: ~20MB
- qwen-image-2.0: 10MB
- z-image-turbo: 不支持图生图

#### 压缩策略

```python
# 1. 先尝试降低 JPEG 质量（q85 → q70 → q50 → q30）
# 2. 仍超限则缩小分辨率到 2048×2048 以内
# 3. 压缩后告知用户：原始大小 → 压缩后大小
```

### 5. 智能分辨率推荐

**重要**：必须根据用户提到的场景关键词选择对应的 `size` 参数值（如 `"portrait"`），而不是直接传入像素值。

| 场景关键词 | 推荐比例 | size 参数值 | 实际像素 |
|-----------|---------|------------|---------|
| "海报"/"朋友圈"/"手机壁纸"/"竖版" | 竖版 9:16 | `"portrait"` | wan: 768×1152, qwen: 1152×2048, z-image: 1120×1440 |
| "公众号封面"/"横幅"/"横版" | 横版 16:9 | `"landscape"` | wan: 1152×768, qwen: 2048×1152, z-image: 1440×1120 |
| "头像"/"图标"/"方形" | 方形 1:1 | `"1k"` 或 `"square"` | 1024×1024 |
| "高清"/"2K"/无明确偏好 | 最大方形 | `"2k"` | wan: 2048×2048, qwen: 2048×2048, z-image: 1440×1440 |

**调用示例**：
```bash
# 用户说"竖版海报" → 使用 size="portrait"
python scripts/qwen_image_gen.py text2img "提示词" --size portrait

# 用户说"横版封面" → 使用 size="landscape"  
python scripts/wan_image_gen.py text2img "提示词" --size landscape

# 无特殊要求 → 使用 size="1k" (默认方形)
python scripts/z_image_gen.py text2img "提示词" --size 1k
```

**注意**：wan2.7 像素总量可超 4K（4096×4096），但无标准 4K 比例（3840×2160）。

### 6. 生成与保存

#### 调用脚本

**基本格式**：
```bash
# wan2.7
python scripts/wan_image_gen.py text2img "提示词" --size [size_value] --n [数量] --filename_prefix "[命名前缀]"

# qwen-image-2.0
python scripts/qwen_image_gen.py text2img "提示词" --size [size_value] --n [数量] --filename_prefix "[命名前缀]"

# z-image-turbo
python scripts/z_image_gen.py text2img "提示词" --size [size_value] --n [数量] --filename_prefix "[命名前缀]"
```

**完整示例**：
```bash
# 示例1：用户要求"生成一张竖版春日海报，要有花朵和阳光"
# → 推荐 qwen-image-2.0（无特殊需求），竖版用 portrait
python scripts/qwen_image_gen.py text2img   "画面主体：春日花园；场景：花朵盛开，阳光明媚；光线：温暖的自然光；风格：清新治愈"   --size portrait --n 1 --filename_prefix "春日海报_花朵阳光_清新治愈"

# 示例2：用户要求"用 wan2.7 生成一组小猫日常的连环画"
# → 使用 wan2.7，组图用 n=3，启用顺序生成
python scripts/wan_image_gen.py text2img   "一只小橘猫的日常：早上起床、中午玩耍、晚上睡觉"   --size landscape --n 3 --enable_sequential --filename_prefix "小猫日常_连环画"

# 示例3：用户要求"快速生成一张电影感的城市夜景"
# → 使用 z-image-turbo（快速+电影感），英文提示词
python scripts/z_image_gen.py text2img   "film grain, cinematic lighting, cyberpunk city at night, neon lights"   --size hd --n 1 --filename_prefix "城市夜景_赛博朋克_电影感"
```

#### 图片命名

使用 `filename_prefix` 参数传入命名前缀，格式：`主体_场景_风格`

**命名规则**：
- 从提示词提取关键词作为文件名前缀（中文或英文均可）
- 用下划线 `_` 分隔不同要素
- wan2.7 组图时自动添加 `_seq01`、`_seq02` 等序列号

**调用示例**：
```bash
# 单张图片
python scripts/qwen_image_gen.py text2img "一只可爱的橘猫趴在窗台上"   --filename_prefix "可爱橘猫_窗台_温暖治愈"

# 生成文件：可爱橘猫_窗台_温暖治愈_20260704_120000.png

# wan2.7 组图（自动加序列号）
python scripts/wan_image_gen.py text2img "小猫的一天" --n 3   --filename_prefix "小猫日常"

# 生成文件：
# 小猫日常_20260704_120000_seq01.png
# 小猫日常_20260704_120000_seq02.png  
# 小猫日常_20260704_120000_seq03.png
```

**注意事项**：
- 文件名前缀建议控制在 20 字以内
- 避免使用特殊字符（如 `/`、`\`、`:`）
- 如果不传 `filename_prefix`，则使用默认的任务类型（如 `text2img`）

#### 保存位置

脚本自动将图片保存到 **日期子目录**：`output/YYYY-MM-DD/filename.png`

**优先级**：
1. 当前工作目录下的 `output/YYYY-MM-DD/` 目录（自动创建日期子目录）
2. `~/Pictures/qwen-image-generator/YYYY-MM-DD/`（保底，跨平台统一位置）

> macOS: `~/Pictures/qwen-image-generator/YYYY-MM-DD/`
> Windows: `C:\Users\<用户名>\Pictures\qwen-image-generator\YYYY-MM-DD\`
> Linux: `~/Pictures/qwen-image-generator/YYYY-MM-DD/`

**⚠️ Agent 必须遵守的保存规则（违反会导致文件丢失）**：
1. **不要自己下载图片**：脚本已经完成了下载和保存，Agent 绝不需要再下载或保存图片
2. **不要自己创建文件**：Agent 不应使用 `exec_command` 的 `curl`、`wget` 或其他工具下载图片
3. **直接使用脚本输出路径**：读取脚本输出的 `✅ 已保存: <路径>` 行，用这个路径展示图片给用户
4. **不要复制到 output/**：图片已在日期子目录中，不需要额外移动
5. **如果脚本报错**：展示错误信息给用户，不要尝试"自己下载"作为 fallback

## 对比模式

| 用户表达 | 处理方式 |
|---------|---------|
| "生成一张图片" | 使用推荐模型生成 1 张 |
| "对比一下"/"用其他模型试试" | 额外生成其他模型的结果 |
| "三个模型都试试"/"全模型对比" | 三个模型同时生成 |

对比时每个模型使用各自风格适配后的提示词。



## 生成元数据

每张图片生成后会自动保存一个 `.json` sidecar 文件，记录生成参数：

```json
{
  "image": "可爱橘猫_窗台_20260704_222226.png",
  "model": "wan2.7-image-pro",
  "prompt": "画一只橘猫趴在窗台上，阳光透过玻璃...",
  "size": "1024*1024",
  "n": 1,
  "seed": 42,
  "negative_prompt": "模糊，低质量",
  "generated_at": "2026-07-04T22:22:27.255399",
  "api_image_url": "https://dashscope-7c2c.oss-accelerate.aliyuncs.com/..."
}
```

**用途**：
- 回溯上次生成参数，方便微调
- 复现相同的图片效果
- 批量管理生成历史

## 健壮性特性

- **下载重试**：图片下载失败时自动重试 3 次（指数退避）
- **文件名校验**：`filename_prefix` 自动清理非法字符（`/`, `:`, `\` 等替换为 `_`）
- **响应兼容性**：同时支持 SDK 对象响应和字典响应两种格式

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| API 调用失败 | 直接报错，不做降级（共用同一 API Key） |
| 图片下载失败 | 重试 3 次，仍失败则告知用户并提供 URL |
| 生成质量差 | 展示给用户，让用户决定是否重新生成 |
| 输入 URL 不可达 | 告知用户检查链接 |
| 输入图片过大 | 自动压缩，仍超限则告知用户 |
| z-image-turbo 用于图生图 | 自动排除，提示不支持 |

## Seed 参数说明

- 三个模型都接受 `seed` 参数
- **均不保证复现性**：相同 seed + 相同提示词会产生不同图片
- 如需复现，需保存生成的图片文件本身
- 文件命名时可包含 seed 值便于追溯

## 使用工具函数

脚本 `scripts/image_utils.py` 提供了以下辅助功能，供图生图等场景使用：

### 图生图大图处理流程

当用户传入本地大图（>10MB）做图生图时，需要**两步操作**：

**步骤 1**：先用 image_utils 压缩图片

```bash
python scripts/image_utils.py compress "path/to/big_image.jpg"
# 输出压缩后的文件路径，如：path/to/big_image_compressed.jpg
```

**步骤 2**：将压缩后的路径传给脚本

```bash
python scripts/wan_image_gen.py img2img "转换为水彩画风格" "path/to/big_image_compressed.jpg"
```

### 其他工具函数

```python
# 如需在 Python 代码中使用，可通过绝对路径导入
import sys
sys.path.insert(0, '<skill_install_dir>/scripts')
from image_utils import (
    compress_image,      # 压缩图片
    image_to_base64,     # 本地文件转 base64 data URI
    prepare_image_input, # 自动检测并压缩超限图片
    generate_filename,   # 生成规范文件名
    get_output_dir       # 获取输出目录路径
)
```

## 环境变量

- `Qwen_DASHSCOPE_API_KEY`: 阿里云百炼 API Key（必需）

## 参考资料

- **模型详细对比**：`references/model_comparison.md`
- **提示词示例**：`references/prompt_examples.md`

## 限制说明

| 限制 | 说明 |
|------|------|
| Seed 不复现 | 三个模型均不保证相同 seed 产生相同图片 |
| z-image-turbo 无图生图 | 需要图生图/图片编辑时自动排除 |
| 图片大小限制 | qwen < 10MB, wan < 20MB |
| 不支持 4K 标准分辨率 | 无 3840×2160 预设比例 |
| API Key 共用 | 三个模型使用同一个 Key，不做降级 |
| 多图融合限制 | 仅 qwen-image-2.0 支持 |

