# 生图模型对比文档

> 最后更新：2026-07-04  
> 对比模型：wan2.7-image-pro / wan2.7-image vs qwen-image-2.0 (加速版/满血版) vs z-image-turbo

---

## 一、模型概览

| 维度 | wan2.7 | qwen-image-2.0 | z-image-turbo |
|------|--------|----------------|---------------|
| **API** | `ImageGeneration.call()` | `MultiModalConversation.call()` | `MultiModalConversation.call()` |
| **SDK 模块** | `dashscope.aigc.image_generation` | `dashscope.MultiModalConversation` | `dashscope.MultiModalConversation` |
| **消息格式** | `Message` 对象 + `content` 列表 | 原生 dict `messages` 列表 | 原生 dict `messages` 列表 |
| **模型系列** | 通义万相 (Wan) | Qwen 视觉多模态 | Z-Image Turbo |
| **发布时间** | 2026 (较新) | 2026 (较新) | 2026 (较新) |
| **脚本路径** | `scripts/wan_image_gen.py` | `scripts/qwen_image_gen.py` | `scripts/z_image_gen.py` |



> **📌 Qwen-Image-2.0 系列两个版本**
> 
> | 维度 | qwen-image-2.0 (加速版) | qwen-image-2.0-pro (满血版) |
> |------|:------:|:------:|
> | **模型 ID** | `qwen-image-2.0` | `qwen-image-2.0-pro-2026-06-22` |
> | **CLI 别名** | `default` | `pro` |
> | **发布时间** | 2026 (较早) | 2026-06-22 (最新) |
> | **定位** | 效果与性能的最佳平衡 | 系列最强效果 |
> | **文字渲染** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (最强) |
> | **真实质感** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (最细腻) |
> | **生成速度** | ⭐⭐⭐⭐ (较快) | ⭐⭐⭐ (较慢) |
> | **API 调用** | `MultiModalConversation.call()` | `MultiModalConversation.call()` (相同) |
> | **参数支持** | 完全一致 | 完全一致 |
> | **适用场景** | 日常使用、快速迭代、批量生成 | 文字排版、海报、写实照片、高质量输出 |
> 
> **如何选择**：
> - 日常使用、快速生成 → 加速版 (`default`)
> - 文字渲染、排版设计、写实照片、质量优先 → 满血版 (`pro`)
> - 不确定时 → 先用加速版，不满意再切满血版

---

## 二、功能支持对比

### 2.1 核心功能

| 功能 | wan2.7 | qwen-image-2.0 | z-image-turbo | 备注 |
|------|:------:|:------:|:------:|------|
| 文生图 (Text-to-Image) | ✅ | ✅ | ✅ | 三者均支持 |
| 图生图 (Image-to-Image) | ✅ | ✅ | ❌ | z-image-turbo 不支持 |
| 图片编辑 (Image Edit) | ✅ | ✅ | ❌ | z-image-turbo 不支持 |
| 多图融合 (Multi-Image) | ❌ | ✅ | ❌ | qwen-image-2.0 独有 |
| 组图/故事图 (Story) | ✅ | ❌ | ❌ | wan 独有 |
| 顺序生成 (Sequential) | ✅ | ❌ | ❌ | wan 独有 |
| 文字渲染 (中/英文) | ⚠️ 一般 | ✅ 优秀 | ⚠️ 一般 | qwen-image-2.0 最强 |
| 信息图/图表生成 | ⚠️ 一般 | ✅ 优秀 | ❌ | qwen-image-2.0 擅长 |

### 2.2 参数对比

| 参数 | wan2.7 | qwen-image-2.0 | z-image-turbo | 说明 | 示例 |
|------|:------:|:------:|:------:|------|------|
| `n`（生成数量） | 1-4 | 1-6 | 1-4 | 单次生成图片数量 | `n=3` 一次生成3张图 |
| `size`（尺寸） | 1k/2k/portrait/landscape | 512-2048 总像素范围 | portrait/landscape/hd/1k | 输出图片分辨率（总像素限制） | `size="2048*2048"` |
| `enable_sequential` | ✅ | ❌ | ❌ | **顺序生成开关**：生成组图时保持风格一致性 | `enable_sequential=True` 生成连环画 |
| `negative_prompt` | ✅ | ✅ | ❌ | **负向提示词**：指定不希望出现的元素 | `negative_prompt="模糊,低质量,变形"` |
| `watermark` | ❌ | ✅ | ❌ | **水印控制**：是否添加官方水印 | `watermark=True` 添加通义万相水印 |
| `stream` | ❌ | ✅ | ✅ | **流式输出**：边生成边返回结果 | `stream=True` 适合长耗时任务 |
| `prompt_extend` | ❌ | ❌ | ✅ | **提示词扩展**：自动丰富简单的提示词 | `prompt_extend=True` 让"猫"变成"一只可爱的橘猫在草地上" |

### 2.3 分辨率对比

| 尺寸 | wan2.7 | qwen-image-2.0 | z-image-turbo | 备注 |
|------|:------:|:------:|:------:|------|
| 512×512 | ❌ | ✅ | ❌ | qwen-image-2.0 独有快速预览 |
| 768×1152 (竖版) | ✅ | ❌ | ❌ | wan 独有 |
| 1024×1024 (1K方形) | ✅ | ✅ | ✅ | 三者均支持 |
| 1120×1440 (竖版) | ❌ | ❌ | ✅ | z-image-turbo 独有 |
| 1152×2048 (竖版高清) | ❌ | ✅ | ❌ | qwen-image-2.0 独有 |
| 1440×1120 (横版) | ❌ | ❌ | ✅ | z-image-turbo 独有 |
| 1440×1440 (高清方形) | ❌ | ❌ | ✅ | z-image-turbo 独有 |
| 2048×2048 (2K方形) | ✅ | ✅ | ❌ | wan/qwen 支持，qwen 传 `--size 2k` 启用 |
| **4K (3840×2160)** | ❌ | ❌ | ❌ | **三者均不支持 4K 分辨率** |
| 默认分辨率 | `1024*1024`（脚本默认 1k）| `2048*2048`（脚本默认 2k）| `1024*1024`（脚本默认 1k）| wan/z-image 默认 1k；qwen 默认 2k |

> ⚠️ **分辨率限制**：三个模型都采用**总像素限制**而非单边尺寸限制：
> - **qwen-image-2.0**: 总像素在 [512×512, 2048×2048] 之间（约 26 万 ~ 419 万像素）
> - **wan2.7**: 总像素在 [768×768, 2048×2048] 之间，宽高比 [1:8, 8:1]
> - **z-image-turbo**: 总像素在 [512×512, 2048×2048] 之间
> 
> 这意味着可以灵活组合宽高，只要总像素在范围内即可。例如 4096×1024（总像素 4,194,304）也是允许的，虽然宽度超过 2048。如需 4K 标准分辨率输出，需要后期通过 AI 放大工具处理。

---

## 三、质量与效果对比

### 3.1 擅长领域

| 领域 | wan2.7 | qwen-image-2.0 | z-image-turbo | 推荐 | 评分依据 |
|------|:------:|:------:|:------:|:------:|------|
| 📸 写实照片 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (满血版) | ⭐⭐⭐⭐⭐ | qwen-pro/z-image | 满血版质感最细腻 |
| 🎨 艺术插画 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | wan/qwen | 基于实际生成效果 |
| 📊 信息图/图表 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (满血版) | ❌ | qwen-image-2.0-pro | 满血版排版最精确 |
| 📝 文字排版 | ⭐⭐ | ⭐⭐⭐⭐⭐ (满血版最强) | ⭐⭐ | qwen-image-2.0-pro | 满血版文字渲染最佳 |
| 🎬 组图/故事 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ❌ | wan2.7 | 基于实际生成效果 |
| 🖼️ 品牌一致性 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | wan2.7 | 基于实际生成效果 |
| 🔀 多图融合 | ❌ | ⭐⭐⭐⭐⭐ | ❌ | qwen-image-2.0 | 功能支持情况 |
| 🎭 电影感/胶片风 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | z-image-turbo | **基于官方示例提示词风格推断** |
| ⚡ 生成速度 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | z-image-turbo | 基于实际计时测试 |

> 📝 **评分说明**：
> - **基于实际生成效果**：通过测试用例实际生成并对比图片质量得出
> - **功能支持情况**：基于 API 文档和实际测试确认
> - **基于官方示例提示词风格推断**：z-image-turbo 的官方示例使用了大量电影感关键词（film grain, analog film, Kodak Portra 400 等），但实际测试样本较少，结论仅供参考
> - **基于实际计时测试**：通过多次生成计时得出

### 3.2 中文渲染能力

| 能力 | wan2.7 | qwen-image-2.0 | z-image-turbo | 说明 |
|------|:------:|:------:|:------:|------|
| 中文标题 | ⚠️ 可能有错字 | ✅ 基本准确 | ⚠️ 可能有错字 | qwen-image-2.0 明显更好 |
| 中文正文 | ⚠️ 可能有错字 | ✅ 较准确 | ⚠️ 可能有错字 | 复杂文本仍有小概率错误 |
| 英文文字 | ⚠️ 偶尔错误 | ✅ 准确 | ⚠️ 偶尔错误 | qwen-image-2.0 最稳定 |
| 数字渲染 | ⚠️ 偶尔错误 | ✅ 准确 | ⚠️ 偶尔错误 | qwen-image-2.0 更稳定 |
| 混合排版 | ⚠️ | ✅ | ⚠️ | qwen-image-2.0 最适合信息图 |

### 3.3 实测数据

| 测试场景 | wan2.7 耗时 | qwen-image-2.0 耗时 | z-image-turbo 耗时 | 说明 |
|----------|------------|---------------------|--------------------|------|
| 文生图 1张 portrait | ~28s | ~35-45s | **~7s** | z-image-turbo 最快！ |
| 文生图 1张 2K | ~30s | ~30s | — | wan/qwen 接近 |
| 图生图 1张 | ~12s | ~20s | ❌ 不支持 | z-image-turbo 无此功能 |
| 多图 n=4 | ~35s | — | — | wan 支持组图 |
| 多图 n=3 | — | ~40s | — | qwen-image-2.0 多图生成 |
| 多图融合 | ❌ | ~10s | ❌ | qwen-image-2.0 独有 |

---

## 四、API 接口差异

### 4.1 请求方式

**wan2.7 (ImageGeneration API)**:
```python
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message

message = Message(role="user", content=[{"text": "prompt"}])
response = ImageGeneration.call(
    model="wan2.7-image-pro",
    api_key=api_key,
    messages=[message],
    n=1,
    size="1024*1024",
    enable_sequential=False
)

# 响应结构
response.output.choices[0].message.content[0]["image"]
```

**qwen-image-2.0 / z-image-turbo (MultiModalConversation API)**:
```python
from dashscope import MultiModalConversation

messages = [{"role": "user", "content": [{"text": "prompt"}]}]
response = MultiModalConversation.call(
    api_key=api_key,
    model="qwen-image-2.0",  # 或 "z-image-turbo"
    messages=messages,
    result_format='message',
    stream=False,
    n=1,
    watermark=False,  # qwen-image-2.0 支持
    negative_prompt="",  # qwen-image-2.0 支持
    prompt_extend=False  # z-image-turbo 支持
)

# 响应结构
response['output']['choices'][0]['message']['content'][0]['image']
```

### 4.2 响应格式差异

| 维度 | wan2.7 | qwen-image-2.0 / z-image-turbo |
|------|--------|----------------|
| 响应类型 | 对象 (Object) | 字典 (Dict) |
| 状态码 | `response.status_code` | `response['status_code']` |
| 错误码 | `response.code` | `response['code']` |
| 错误信息 | `response.message` | `response['message']` |
| 输出数据 | `response.output` | `response['output']` |
| choices | `response.output.choices` | `response['output']['choices']` |

---



## 五、提示词风格偏好

不同模型对提示词的偏好不同，会影响最终生成效果：

| 模型 | 偏好风格 | 语言 | 示例 |
|------|----------|------|------|
| **wan2.7** | 中文自然语言 | 中文为主 | "一只可爱的橘猫在草地上玩耍，阳光明媚" |
| **qwen-image-2.0** | 结构化中文描述 | 中文为主 | "画面主体：橘猫，场景：草地，光线：明亮，风格：可爱" |
| **z-image-turbo** | 英文电影感关键词 | **英文效果更好** | "film grain, cinematic lighting, shallow depth of field, bokeh background" |

### 提示词建议

- **wan2.7**: 直接用中文描述，简洁自然即可
- **qwen-image-2.0**: 中文描述，可以适当结构化，突出主体、场景、风格
- **z-image-turbo**: 
  - 英文提示词效果明显更好
  - 添加电影感关键词：`film grain`, `cinematic lighting`, `Kodak Portra 400`
  - 可以用中文，但建议 Agent 自动翻译为英文

> 💡 **Skill 设计启示**：当用户输入中文提示词时，Skill 应根据目标模型自动优化：
> - 目标为 z-image-turbo → 翻译为英文 + 添加电影感关键词
> - 目标为 qwen-image-2.0 → 保持中文，适当结构化
> - 目标为 wan2.7 → 保持中文自然语言

## 六、选型建议

### 5.1 选择 wan2.7 的场景

- ✅ 需要生成**组图/故事图**（多图连贯性）
- ✅ 需要**品牌一致性**（同一角色多次出现）
- ✅ 追求**生成速度**（比 qwen-image-2.0 快）
- ✅ 需要**顺序生成**保持风格统一
- ✅ 不需要精确文字排版

### 5.2 选择 qwen-image-2.0 的场景

- ✅ 需要**精确的中英文文字渲染**
- ✅ 生成**信息图、图表、PPT 配图**
- ✅ 需要**多图融合**（2+ 张输入图片）
- ✅ 追求**最高分辨率**（原生 2K）
- ✅ 需要**照片级真实感**
- ✅ 单次需要生成**多张图片**（最多 6 张）

### 5.3 选择 z-image-turbo 的场景

- ✅ 追求**最快速度**（~7s 生成）
- ✅ 需要**电影感、胶片质感**
- ✅ 生成**写实人像摄影**
- ✅ 需要**风景摄影**（航拍、自然风光）
- ✅ 对中文文字渲染要求不高
- ✅ 只需要文生图功能

### 5.4 综合推荐

| 需求场景 | 推荐模型 | 理由 |
|----------|:--------:|------|
| 营销海报设计 | qwen-image-2.0 | 文字渲染优秀，支持多图输入 |
| 社交媒体配图 | z-image-turbo | 速度最快，适合快速迭代 |
| 产品宣传册 | qwen-image-2.0 | 高分辨率，信息图能力强 |
| 绘本/漫画 | wan2.7 | 组图能力，角色一致性 |
| 数据报告配图 | qwen-image-2.0 | 图表和数据可视化能力 |
| 活动邀请卡片 | qwen-image-2.0 | 中文排版能力 |
| 品牌故事系列 | wan2.7 | 顺序生成保证风格统一 |
| 写实产品照片 | qwen-image-2.0 / z-image-turbo | qwen 分辨率高，z-image 速度快 |
| 电影感人像 | z-image-turbo | 胶片质感最强 |
| 风景摄影 | z-image-turbo | 电影感光影效果 |

---

## 七、环境变量与配置

| 配置项 | wan2.7 | qwen-image-2.0 | z-image-turbo |
|--------|--------|----------------|---------------|
| API Key 环境变量 | `Qwen_DASHSCOPE_API_KEY` | `Qwen_DASHSCOPE_API_KEY` | `Qwen_DASHSCOPE_API_KEY` |
| SDK 依赖 | `dashscope` | `dashscope` | `dashscope` |
| 额外依赖 | `requests` | `requests` | `requests` |
| 配置方式 | `~/.zshrc` | `~/.zshrc` | `~/.zshrc` |

> ⚠️ 三个模型共用同一个 API Key（`Qwen_DASHSCOPE_API_KEY`），无需额外配置。

---

## 八、模型列表汇总

| 模型 ID | 别名 | 说明 |
|---------|------|------|
| `wan2.7-image-pro` | `pro` | 通义万相专业版，高质量，组图能力强 |
| `wan2.7-image` | `std` | 通义万相标准版，速度快 |
| `qwen-image-2.0` | `default` | Qwen 加速版，效果与性能平衡，日常首选 |
| `qwen-image-2.0-pro-2026-06-22` | `pro` | Qwen 满血版，系列最强文字渲染 + 真实质感 |
| `z-image-turbo` | `default` | Z-Image Turbo，超快速度，电影感强 |

---

## 九、后续可扩展模型

| 模型 | 状态 | 说明 |
|------|------|------|
| wan2.7-image-pro | ✅ 已完成 | 通义万相专业版 |
| wan2.7-image | ✅ 已完成 | 通义万相标准版 |
| qwen-image-2.0 | ✅ 已完成 | Qwen 加速版，效果与性能平衡 |
| qwen-image-2.0-pro-2026-06-22 | ✅ 已完成 | Qwen 满血版，系列最强效果 |
| z-image-turbo | ✅ 已完成 | Z-Image Turbo 超快速度 |
| 其他模型 | 🔜 待添加 | 根据需求继续扩展 |

---



## 十一、Seed（种子）参数支持

| 模型 | 接受 seed 参数 | 保证复现 | 说明 |
|------|:------:|:------:|------|
| wan2.7 | ✅ | ❌ | 接受参数但不保证相同 seed 产生相同图片 |
| qwen-image-2.0 | ✅ | ❌ | 接受参数但不保证相同 seed 产生相同图片 |
| z-image-turbo | ✅ | ❌ | 接受参数但不保证相同 seed 产生相同图片 |

> ⚠️ **结论**：三个模型都接受 `seed` 参数，但**均不保证复现性**。相同 seed + 相同提示词会产生不同图片。如需复现特定结果，需要保存生成的图片文件本身。

---

## 十二、图生图输入图片限制

| 模型 | 最大文件大小 | 最大像素 | 支持格式 | 备注 |
|------|:------:|:------:|:------:|------|
| wan2.7 | ~20MB | 无明确限制 | JPG/PNG/WEBP | 12MB PNG 通过，26MB PNG 失败 |
| qwen-image-2.0 | **10MB** | 无明确限制 | JPG/PNG/WEBP | 超过 10MB 会报错 "Image size exceeds 10MB limit" |
| z-image-turbo | — | — | — | **不支持图生图功能** |

### 建议处理策略

| 场景 | 处理方式 |
|------|---------|
| 文件 < 10MB | 直接使用 |
| 文件 10-20MB | qwen-image-2.0 需压缩；wan2.7 可直接使用 |
| 文件 > 20MB | 两个模型都需压缩 |
| 压缩后仍超限 | 告知用户，建议手动缩小图片 |

### 压缩策略

1. 优先使用 JPEG 压缩（quality=85），通常能将文件缩小 60-80%
2. 如仍超限，缩小分辨率到 2048×2048 以内
3. 压缩后告知用户原始大小和压缩后大小



## 十三、图生图输入方式

| 模型 | URL 直传 | Base64 编码 | 本地文件 | 备注 |
|------|:------:|:------:|:------:|------|
| wan2.7 | ✅ | ✅ | ✅ | 三种方式均支持 |
| qwen-image-2.0 | ✅ | ✅ | ✅ | 三种方式均支持 |
| z-image-turbo | — | — | — | 不支持图生图 |

### URL 直传的优势

当用户提供图片 URL 时，**优先使用 URL 直传**，无需下载到本地再转 base64：

```python
# URL 直传（推荐）
content = [
    {"image": "https://example.com/photo.jpg"},
    {"text": "将这张图片转为油画风格"}
]

# Base64 编码（本地文件时使用）
content = [
    {"image": "data:image/png;base64,iVBOR..."},
    {"text": "将这张图片转为油画风格"}
]
```

### Skill 处理策略

| 输入类型 | 处理方式 |
|---------|---------|
| HTTP/HTTPS URL | 直接传给 API，不下载 |
| 本地文件路径 | 转 base64 后传给 API |
| URL 无法访问 | 告知用户检查链接 |

> 💡 **注意**：URL 直传时，图片大小限制仍然适用（qwen < 10MB, wan < 20MB），但由 API 服务端校验，Skill 无法提前感知。如果 URL 指向的图片过大，API 会返回错误，此时应提示用户下载后压缩。

## 十、关键差异总结

| 维度 | wan2.7 | qwen-image-2.0 | z-image-turbo |
|------|:------:|:------:|:------:|
| **速度** | ⭐⭐⭐⭐ | ⭐⭐⭐ / ⭐⭐⭐⭐ (满血/加速) | ⭐⭐⭐⭐⭐ |
| **功能丰富度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **文字渲染** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **电影感** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **多图能力** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| **分辨率** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

*本文档随新模型添加持续更新*
