# FreeLLMAPI 全面调研报告

> 调研日期：2026-04-28
> 仓库地址：https://github.com/tashfeenahmed/freellmapi
> 版本：v0.1.0（MIT License）
> Stars：615 | Fork：116 | 创建时间：2026-04-21（仅 7 天前）
> 语言：TypeScript（Node.js 20+）

---

## 一、项目概况

FreeLLMAPI 是一个自托管、OpenAI 兼容的代理服务器，将约 14 个 LLM 提供商的免费层聚合到一个统一的 /v1/chat/completions 端点。旨在将各平台零散的免费额度（每个月总计约 13 亿 token）打包成可用的单一 API。

核心理念：每个免费层单独看是"玩具"，但叠加起来就是可用的推理能力。

---

## 二、支持的 Provider

| 序号 | Provider | 最佳免费模型 | 免费层类型 |
|------|----------|-------------|-----------|
| 1 | Google (Gemini) | Gemini 3.1 Pro Preview, 3 Flash Preview | 永久免费，无需信用卡 |
| 2 | Groq | GPT-OSS 120B, Llama 3.3 70B, Qwen3 32B | 永久免费 |
| 3 | Cerebras | Qwen3-235B, GLM-4.7, GPT-OSS 120B | 永久免费 |
| 4 | SambaNova | DeepSeek V3.2, DeepSeek V3.1, Llama 4 Maverick | 永久免费 |
| 5 | NVIDIA NIM | Nemotron 3 Super 120B, 100+ 模型 | 永久免费（基于积分） |
| 6 | Mistral | Mistral Large 3, Codestral, Devstral | 实验计划（需手机验证） |
| 7 | OpenRouter | MiniMax M2.5, Qwen3 Coder, GPT-OSS 120B (:free) | 永久免费 |
| 8 | GitHub Models | GPT-4.1, GPT-4o | 永久免费 |
| 9 | Hugging Face | Llama 3.3 70B 等 | 推理积分制 |
| 10 | Cohere | Command-A, Command R+ | 1000 次/月试用 |
| 11 | Cloudflare Workers AI | Kimi K2.5, GPT-OSS 120B, Llama 3.3 70B | 10K Neurons/天 |
| 12 | Zhipu (智谱) | GLM-4.5 Flash | 永久免费 |
| 13 | Moonshot（已付费化） | Kimi Latest | 此前免费，现已付费 |
| 14 | MiniMax（已替换） | MiniMax M1 | 已由 OpenRouter 替代 |

---（后续内容继续，完整报告见文件）---


## 三、速率限制详情

### Google Gemini
| 模型 | RPM | RPD | TPM | 月预算 |
|------|-----|-----|-----|-------|
| Gemini 3.1 Pro Preview | 5 | 20 | 250K | ~3M |
| Gemini 3 Flash Preview | 10 | 20 | 250K | ~3M |
| Gemini 2.5 Flash | 10 | 20 | 250K | ~3M |
| Gemini 2.5 Flash-Lite | 15 | 20 | 250K | ~3M |

### Groq（极快速度，276-316 tok/s）
| 模型 | RPM | RPD | TPM | TPD |
|------|-----|-----|-----|-----|
| GPT-OSS 120B | 30 | 1,000 | 8,000 | 200K |
| Llama 3.3 70B | 30 | 1,000 | 12,000 | 500K |
| Qwen3 32B | 60 | 1,000 | 6,000 | 500K |

### Cerebras（最快推理速度，~1,400 tok/s）
| 模型 | RPM | RPD | TPM | TPD |
|------|-----|-----|-----|-----|
| Qwen3-235B | 30 | 14,400 | 60K | 1M |
| GLM-4.7 | 10 | 100 | - | - |

### SambaNova
| 模型 | RPM | RPD | TPD |
|------|-----|-----|-----|
| DeepSeek V3.2 | 20 | 20 | 200K |
| DeepSeek V3.1 | 20 | 20 | 200K |

### OpenRouter (:free 池)
- 20 RPM / 200 RPD（未购买积分）
- 购买 0+ 积分后 1,000 RPD

### 其他
- Mistral: 2 RPM, 500K TPM, 1B token/月
- Cloudflare: 10K Neurons/天
- GitHub Models: 10-15 RPM, 50-150 RPD
- Cohere: 1000 次调用/月
