# 万象Ai API 能力文档
> 自动生成于 2026-05-16 15:07:34

## 平台接口

```json
{
  "auth": {
    "format": "Bearer {api_key}",
    "header": "Authorization",
    "method": "bearer"
  },
  "base_url": "https://api.lk888.ai/api",
  "categories": [
    {
      "endpoints": [
        {
          "description": "按类型查询平台所有可用模型。返回每个模型的名称、展示名称、类型、功能标签和简介。\n- 不传 type 参数返回所有类型的模型\n- type=chat 时只返回 gpt/o1/o3/chatgpt/claude/gemini 前缀的语言模型，并额外返回 api_format（调用格式：openai/anthropic/gemini）和 api_endpoint（对应的请求路径）\n- type=image/video/audio/tts/music 返回对应类型的媒体模型\n\n响应字段说明：\n- name: 模型标识名，调用接口时传此值\n- display_name: 展示用的中文名称\n- type: 模型类型（chat/image/video/audio/tts/music）\n- tags: 功能标签数组，如[\"文生视频\",\"图生视频\"]\n- description: 模型简介\n- input_hint: 输入提示文案\n- api_format: [仅chat] 调用格式，openai/anthropic/gemini\n- api_endpoint: [仅chat] 对应请求路径，如 /v1/chat/completions",
          "id": "list_models",
          "method": "GET",
          "name": "获取模型列表",
          "params": [
            {
              "enum": [
                "chat",
                "image",
                "video",
                "audio"
              ],
              "name": "type",
              "type": "string",
              "required": false,
              "description": "按模型类型筛选，不传则返回全部"
            }
          ],
          "path": "/v1/skills/models",
          "response_example": {
            "type": "video",
            "total": 3,
            "models": [
              {
                "name": "gpt-4o",
                "tags": [
                  "对话",
                  "多模态"
                ],
                "type": "chat",
                "api_format": "openai",
                "input_hint": "",
                "description": "OpenAI旗舰模型",
                "api_endpoint": "/v1/chat/completions",
                "display_name": "GPT-4o"
              },
              {
                "name": "grok-video-3",
                "tags": [
                  "文生视频"
                ],
                "type": "video",
                "input_hint": "描述视频内容",
                "description": "高质量AI视频生成",
                "display_name": "Grok Video 3"
              },
              {
                "name": "kwvideo-v2",
                "tags": [
                  "文生视频",
                  "首尾帧"
                ],
                "type": "video",
                "aliases": [
                  "Seedance",
                  "即梦"
                ],
                "input_hint": "不传图=文生视频，1张图=首帧，2张图=首尾帧",
                "description": "字节跳动即梦团队推出的旗舰级视频生成模型 Seedance 2.0...",
                "display_name": "SD 2.0 首尾帧"
              }
            ]
          },
          "tips": "1. chat 类型只返回主流语言模型（gpt/o1/o3/chatgpt/claude/gemini 前缀），其他特殊模型不在此列表中。\n2. 媒体模型（image/video/audio）返回全部可用模型。TTS 语音合成和 music 音乐模型统一归类为 audio 类型，使用 type=audio 可查询到。\n3. 每个 chat 模型的 api_format 告诉你该用哪种格式调用：openai 用 /v1/chat/completions，anthropic 用 /v1/messages，gemini 用 /v1beta/models/{model}:{action}。\n4. 要获取模型详细参数用 /v1/skills/models/{name}，要获取价格用 /v1/skills/models/{name}/pricing。\n5. aliases 字段：可选。当模型 display_name 是缩写但 des
```

## 调用指南

```json
{
  "call_modes": [
    {
      "applicable_models": "模型名称以 gpt、o1、o3、chatgpt 开头的语言模型",
      "auth": "Authorization: Bearer {api_key}",
      "description": "100% 兼容 OpenAI Chat Completions API，支持流式输出。",
      "endpoints": [
        {
          "method": "POST",
          "name": "Chat Completions",
          "path": "/v1/chat/completions"
        },
        {
          "method": "POST",
          "name": "Responses",
          "path": "/v1/responses"
        }
      ],
      "mode": "realtime_openai",
      "name": "OpenAI 格式（GPT 系列）",
      "request_example": {
        "messages": [
          {
            "content": "你好",
            "role": "user"
          }
        ],
        "model": "gpt-4o",
        "stream": false
      },
      "tips": [
        "设置 stream: true 开启流式输出",
        "兼容 OpenAI SDK，修改 base_url 即可",
        "流式响应以 data: [DONE] 结尾"
      ]
    },
    {
      "applicable_models": "模型名称以 claude 开头的语言模型",
      "auth": "Authorization: Bearer {api_key}",
      "description": "兼容 Anthropic Messages API。",
      "endpoints": [
        {
          "method": "POST",
          "name": "Messages",
          "path": "/v1/messages"
        }
      ],
      "mode": "realtime_anthropic",
      "name": "Anthropic 格式（Claude 系列）",
      "request_example": {
        "max_tokens": 1024,
        "messages": [
          {
            "content": "你好",
            "role": "user"
          }
        ],
        "model": "claude-4-sonnet"
      },
      "tips": [
        "必须传 max_tokens 参数",
        "兼容 Anthropic SDK，修改 base_url 即可",
        "支持 stream: true 流式输出"
      ]
    },
    {
      "applicable_models": "模型名称以 gemini 开头的语言模型",
      "auth": "Authorization: Bearer {api_key}",
      "description": "兼容 Google Gemini API，路径中包含模型名和操作。",
      "endpoints": [
        {
          "method": "POST",
          "name": "Generate Content",
          "path": "/v1beta/models/{model}:generateContent"
        },
        {
          "method": "POST",
          "name": "Stream Generate Content",
          "path": "/v1beta/models/{model}:streamGenerateContent"
        }
      ],
      "mode": "realtime_gemini",
      "name": "Gemini 格式（Gemini 系列）",
      "request_example": {
        "contents": [
          {
            "parts": [
              {
                "text": "你好"
              }
            ],
            "role": "user"
          }
        ]
      },
      "tips": [
        "模型名称在 URL 路径中，不在请求体里",
        "streamGenerateContent 自动添加 ?alt=sse",
        "兼容 Google AI SDK"
      ]
    },
    {
      "applicable_types": [
        "image",
        "video",
        "audio"
      ],
      "applicable_types_note": "audio 涵盖 TTS 语音合成、语音克隆、音乐生成等全部音频类模型；不存在独立的 tts/music 取值。",
      "description": "用于媒体生成，提交任务后轮询获取结果。",
      "file_upload_note": "平台不提供文件上传/托管服务。模型参数中 type=upload 的字段需要传入可公开访问的文件URL，请自行将文件上传至COS、CDN或其他对象存储服务后，将URL作为参数值传入。",
      "generate_endpoint": {
        "method": "POST",
        "path": "/v1/media/generate"
      },
      "max_wait_seconds"
```

## 模型列表

```json
{
  "models": [
    {
      "name": "vidu-mv",
      "display_name": "VIDU-音乐MV",
      "type": "video",
      "description": "Vidu 音乐MV：上传 1～7 张人物/风格参考图 + 1 个音频（首尾合成1～180秒）即可生成一条有叙事、有画面的 MV，支持 540p/720p/1080p 多画幅 + 可选对口型 + 自动字幕，按实际成片秒数计费。",
      "input_hint": "选择了音频后，可填写提示词指定分镜/风格（最多3000字）。为获得更好效果，建议不要照歌词写分镜，可以参考“玩法说明”提供的示例。",
      "tags": [
        "音乐MV",
        "图生视频",
        "音频驱动",
        "对口型",
        "自动字幕",
        "540P/720P/1080P",
        "多画幅",
        "按秒计费"
      ]
    },
    {
      "name": "sora-2",
      "display_name": "Sora-2 官转版",
      "type": "video",
      "description": "OpenAI Sora-2 稳定版，高质量视频生成，直接接入的官方接口，价格会比基础版稍贵，但是基本上保证100%成功率，且生成后的质量更高。",
      "input_hint": "由于该模型渠道火爆，选择智能调度分组时，大概率会调度到高价格分组，请适度使用\r\n\r\n最好的效果是横版传横图，竖版传竖图，尽量不要乱传",
      "tags": [
        "文生视频",
        "图生视频",
        "稳定"
      ]
    },
    {
      "name": "gemini-3-pro-image-preview",
      "display_name": "Nano Banana Pro",
      "type": "image",
      "description": "谷歌2025年最新超高清图像模型，拥有目前最强的文字渲染能力，擅长生成8K分辨率的微距摄影、皮肤质感与复杂排版设计。",
      "input_hint": "描述你想要生成的图片内容，支持上传参考图片进行图生图，最多14张",
      "tags": [
        "文生图",
        "图生图",
        "4k",
        "高清",
        "香蕉"
      ]
    },
    {
      "name": "gpt-5.4",
      "display_name": "GPT-5.4",
      "type": "chat",
      "description": "GPT-5.4是OpenAI用于复杂专业工作的前沿模型，具备强大的深度推理、多模态理解和工具调用能力，适用于高难度分析、代码开发与创意写作。",
      "input_hint": "描述你的需求或粘贴代码，GPT-5.4擅长复杂专业工作、深度推理与多模态理解。",
      "tags": [
        "多轮对话",
        "多模态",
        "深度思考",
        "长上下文",
        "联网搜索"
      ],
      "api_format": "openai",
      "api_endpoint": "/v1/chat/completions",
      "api_endpoints": [
        {
          "format": "openai",
          "endpoint": "/v1/chat/completions",
          "note": "OpenAI Chat Completions 透传，推荐使用（生态最广，所有 SDK/教程都能直接用）"
        },
        {
          "format": "openai_responses",
          "endpoint": "/v1/responses",
          "note": "OpenAI Responses API 透传，请求体用 input 字段（支持字符串或结构化消息数组），适合 reasoning / 内建工具场景"
        }
      ]
    },
    {
      "name": "grok-video-3",
      "display_name": "grok-video-3",
      "type": "video",
      "description": "Grok 推出的首帧参考图视频模型，专注于高效的图生视频体验。支持生成 6 秒及 10 秒时长的 720P 分辨率视频，具备极快的响应速度。它能将静态图像瞬间转化为流畅的动态影像，是短视频创作者快速验证灵感与获取素材的便捷工具。",
      "input_hint": "描述视频动作、场景及氛围，上传首帧参考图效果更佳（上传后视频比例将跟图片一致）",
      "tags": [
        "文生视频",
        "图生视频",
        "首帧参考图",
        "1080p",
        "高清"
      ]
    },
    {
      "name": "gemini-3.1-flash-image-preview",
      "display_name": "Nano Banana 2",
      "type": "image",
      "description": "谷歌最新高效图像模型，Nano Banana Pro的高速版本，针对速度和高用量场景优化。支持联网搜索生图、Google图片搜索接地、512px快速预览，新增1:4/4:1/1:8/8:1超宽比例。",
      "input_hint": "描述你想要生成的图片内容，支持上传参考图片进行图生图，最多14张",
      "tags": [
        "文生图",
        "图生图",
        "4k",
        "高清",
        "香蕉"
      ]
    },
    {
      "name": "gemini-3.1-pro-preview",
      "display_name": "Gemini 3.1 Pro",
      "type": "chat",
      "description": "Gemini 3.1是谷歌迄今为止最智能的模型系列，以先进的推理能力为基础，最适合需要广泛世界知识和跨模态的高级推理的复杂任务。",
      "input_hint": "输入复杂的多模态分析、深度推理或长文档处理任务，逻辑能力极强。",
      "tags": [
        "多轮对话",
        "多模态",
        "深度思考",
        "长上下文",
        "联网搜索",
        "哈基米"
      ],
      "api_format": "gemini",
      "api_endpoint": "/v1beta/models/{model}:{action}",
      "api_endpoints": [
        {
          "format": "gemini",
          "endpoint": "/v1beta/models/{model}:{action}",
          "note": "Google Gemini generateContent / streamGenerateContent 透传"
        }
      ]
    },
    {
      "name": "doubao-seedance-1-5-pro-251215",
      "display_name": "即梦 3.5 Pro",
      "type": "video",
      "description": "字节跳动即梦团队推出的高质量视频生成模型，支持音画同生，可生成带有环境音、动作音、背景音乐的有声视频，画质细腻流畅。",
      "input_hint": "描述视频内容、动作和场景，可上传首帧或首尾帧图片控制视频生成。支持4-12秒有声视频。",
      "tags": [
        "文生视频",
        "图生视频",
        "首帧参考图",
        "首尾帧",
        "有声视频",
        "1080p",
        "高清"
      ]
    },
    {
      "name": "gpt-image-2",
      "display_name": "GPT Image 2",
      "type": "image",
      "description": "OpenAI 最新一代图像生成模型，语义理解与细节表现更强，支持文生图与图生图。",
      "input_hint": "描述画面中的物体、风格及文字排版，注重指令精准与细节还原。",
      "tags": [
        "文生图",
        "图生图"
      ]
    },
    {
      "name": "speech-2.8",
      "display_name": "海螺 语音克隆 2.8",
      "type": "audio",
      "description": "MiniMax 海螺语音克隆模型，支持上传音频复刻你的专属音色，首次激活后永久有效。提供 HD 高清和 Turbo 极速两种合成质量，支持语速、语调、情绪、音效等精细调节，适用于有声读物、配音、播客等场景。",
      "input_hint": "输入想要朗读的文本内容，选择你的专属克隆音色，一键生成语音",
      "tags": [
        "语音克隆",
        "文字转语音",
        "音色复刻",
        "多语言"
      ]
    },
    {
      "name": "kwvideo-v2-ref",
      "display_name": "SD 2.0 参考生",
      "aliases": [
        "Seedance",
        "即梦"
      ],
      "type": "video",
      "description": "字节跳动即梦团队推出的旗舰级视频生成模型 Seedance 2.0，支持多图参考生视频，上传 1~9 张参考图，模型智能融合风格、元素和构图生成新视频。自动生成有声视频，4~15秒灵活时长，标准/快速双版本可选。按官方 Token 计费。",
      "input_hint": "上传 1~9 张参考图 + 描述词，生成风格一致的视频\nPrompt 必填，参考图至少 1 张，最多 9 张\n图片：JPEG/PNG/WebP/BMP/TIFF/GIF，单张 ≤ 30MB，300~6000px"
```

