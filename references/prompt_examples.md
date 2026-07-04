# 各模型提示词示例

## wan2.7 提示词风格（自然中文）

### 文生图示例

**示例1: 人物肖像**
```
画一个东亚年轻女性，长发，站在樱花树下，春日阳光柔和，面带微笑，穿着白色连衣裙，发丝随风飘动，背景是模糊的粉色樱花，整体色调温暖柔和，清新自然风格
```

**示例2: 风景**
```
一片金黄色的麦田，夕阳西下，天空呈现橙红色渐变，远处有一座小山，田野中有一条蜿蜒的小路，光线温暖，充满田园气息，高清细节
```

**示例3: 产品**
```
一瓶果酒放在木质桌面上，旁边有新鲜水果和绿叶，背景是模糊的厨房环境，光线柔和自然，产品标签清晰可见，商业摄影风格
```

---

## qwen-image-2.0 提示词风格（结构化中文）

### 文生图示例

**示例1: 人物肖像**
```
画面主体：东亚年轻女性，长发；姿态：站立，面带微笑；场景：樱花树下，春日环境；光线：柔和的春日阳光；风格：清新自然，温暖治愈；细节：发丝随风飘动，背景虚化，高清摄影质感
```

**示例2: 信息图**
```
画面类型：信息图卡片；主题：基金投资指南；布局：竖版9:16，分为4个小节；内容：分散风险、费用低廉、市场追踪、适合长投；风格：简约科研风，白色背景，蓝色数据图表；文字：中文无衬线字体，清晰可读
```

**示例3: 产品海报**
```
画面类型：品牌活动海报；产品：果酒瓶；主题：春日微醺野餐季；场景：户外草坪，鲜花、野餐垫、藤编篮；光线：明亮的自然光；风格：优雅浪漫，春天气息；文字：标题"春日微醺野餐季"，副标题"和悦野果酒一起，把春天喝进风里"
```



---

## qwen-image-2.0-pro 提示词风格（精细结构化中文，满血版专属）

> 满血版支持更精细的细节描述和更复杂的指令（1k token），适合高质量输出场景。
> 提示词风格与加速版相同（结构化中文），但应包含更多细节。

### 文生图示例

**示例1: 人物肖像（满血版精细描述）**
```
画面主体：东亚年轻女性，25岁左右，长发及肩，皮肤白皙细腻；姿态：站立，微微侧身，面带温柔微笑；场景：樱花树下，花瓣飘落，春日庭院；光线：柔和的春日午后阳光，金色光斑透过树叶；风格：超写实摄影，浅景深；细节：发丝清晰可见，睫毛根根分明，皮肤毛孔可见，背景虚化呈奶油散景，8K 高清质感
```

**示例2: 海报设计（满血版排版指令）**
```
画面类型：品牌活动海报；产品：果酒瓶，玻璃质感，标签设计精美；主题：春日微醺野餐季；场景：户外草坪，鲜花环绕，复古藤编篮，亚麻野餐垫；光线：明亮的自然光，侧面打光突出产品立体感；风格：优雅浪漫，日系杂志感；文字：标题"春日微醺野餐季"使用中文书法体，居中大字，金色；副标题"和悦野果酒一起，把春天喝进风里"使用中文无衬线体，白色小字，居标题下方；底部：品牌 logo 和二维码，右下角
```

**示例3: 信息图（满血版复杂排版）**
```
画面类型：信息图卡片；主题：基金投资四大优势；布局：竖版 9:16，顶部标题区，中间四宫格内容区，底部总结区；标题："为什么选择指数基金？"，中文黑体，24pt，深蓝色；四宫格：左上"分散风险"配饼图图标，右上"费用低廉"配硬币图标，左下"市场追踪"配折线图图标，右下"适合长投"配时间轴图标；每个格子：图标 + 中文标题 + 一行说明文字；底部：一行总结"懒人理财首选"，橙色高亮；风格：简约商务风，白色背景，蓝色主色调
```

---
## z-image-turbo 提示词风格（英文 + 电影感）

### 文生图示例

**示例1: 人物肖像**
```
film grain, analog film texture, soft film lighting, Kodak Portra 400 style, cinematic grainy texture, photorealistic details, subtle noise, a young East Asian woman with long hair standing under cherry blossom trees, soft spring sunlight, gentle smile, white dress, hair flowing in the wind, blurred pink cherry blossoms in background, warm and natural color palette, fresh and natural style
```

**示例2: 城市夜景**
```
cyberpunk city at night, neon lights reflecting on wet pavement after rain, tall buildings with holographic advertisements, cinematic lighting, volumetric fog, film grain, anamorphic lens flare, Blade Runner aesthetic, moody atmosphere, ultra detailed, 8k quality
```

**示例3: 产品摄影**
```
product photography, a bottle of fruit wine on wooden table, fresh fruits and green leaves beside it, blurred kitchen background, soft natural lighting, commercial photography style, shallow depth of field, bokeh background, cinematic color grading, high detail
```

---

## 提示词优化对比

### 简单提示词 → 优化后

| 原始提示词 | 目标模型 | 优化后 |
|-----------|---------|--------|
| "一只猫" | wan2.7 | "画一只毛茸茸的橘猫趴在阳光洒满的窗台上慵懒地晒太阳，温暖的午后光线，治愈系风格，高清细节" |
| "一只猫" | qwen-image-2.0 (加速版) | "画面主体：橘猫；姿态：慵懒地趴着；场景：阳光洒满的窗台；光线：温暖的午后阳光；风格：治愈系，高清细节" |
| "一只猫" | qwen-image-2.0-pro (满血版) | "画面主体：橘猫，毛发细腻蓬松；姿态：慵懒趴着，前爪交叠；场景：阳光洒满的木质窗台，窗外绿树；光线：温暖午后金色光，光影斑驳；风格：超写实摄影，浅景深；细节：毛发根根可见，瞳孔反光，背景奶油散景，8K 高清质感" |
| "一只猫" | z-image-turbo | "A fluffy orange tabby cat resting lazily on a sunlit windowsill, warm afternoon golden hour lighting, film grain, cinematic shallow depth of field, bokeh background, Kodak Portra 400 style" |

---

## 场景关键词 → 推荐模型

| 用户提到的关键词 | 推荐模型 | 理由 |
|------------------|---------|------|
| "文字"/"排版"/"信息图" | qwen-image-2.0-pro (满血版) | 文字渲染最准确，排版最精细 |
| "组图"/"连环画"/"故事" | wan2.7 | 支持顺序生成，风格一致 |
| "快速"/"电影感"/"胶片" | z-image-turbo | 速度最快，电影感强 |
| "图生图"/"编辑图片" | wan2.7 或 qwen-image-2.0 | z-image-turbo 不支持 |
| "多图融合" | qwen-image-2.0 | 唯一支持 |
| "写实"/"真实感"/"高清" | qwen-image-2.0-pro (满血版) | 真实质感最细腻 |
| 无特殊要求 | qwen-image-2.0 (加速版) | 日常使用，速度效果平衡 |

