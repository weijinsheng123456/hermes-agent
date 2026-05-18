#!/usr/bin/env python3
"""
Browser AI Validate Tool - 页面状态验证

受 skyvern 的 page.validate() 启发，使用自然语言验证页面状态。
返回布尔值，表示页面是否符合预期状态。

功能：
- 登录状态验证："检查用户是否已登录"
- 元素存在验证："检查购物车是否有商品"
- 内容验证："检查页面是否包含'成功'字样"
- 错误检测："检查页面是否有错误提示"

工作原理：
1. 获取当前页面快照（accessibility tree）
2. 使用 LLM 分析页面内容
3. 根据验证条件返回 true/false
4. 提供详细的验证说明
"""

import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 导入现有 browser 工具
try:
    from tools.browser_tool import browser_snapshot
except ImportError as e:
    logger.error(f"Failed to import browser tools: {e}")
    browser_snapshot = None

# 导入 LLM 客户端
try:
    from agent.auxiliary_client import call_llm
except ImportError:
    call_llm = None


def browser_ai_validate(
    prompt: str,
    task_id: Optional[str] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """
    使用自然语言验证页面状态
    
    Args:
        prompt: 自然语言描述验证条件，如"检查用户是否已登录"、"检查购物车是否有商品"
        task_id: 任务 ID（可选）
        timeout: 超时时间（秒，默认 10）
    
    Returns:
        JSON 字符串，包含验证结果：
        {
            "success": true/false,  # 验证是否成功执行
            "valid": true/false,    # 页面状态是否符合预期
            "confidence": 0.0-1.0,  # 置信度
            "evidence": "...",      # 支持结论的证据
            "message": "验证结果描述"
        }
    
    Examples:
        >>> browser_ai_validate("检查用户是否已登录", task_id="task_123")
        >>> browser_ai_validate("检查购物车是否有商品", task_id="task_123")
        >>> browser_ai_validate("检查页面是否包含'支付成功'字样", task_id="task_123")
        >>> browser_ai_validate("检查是否有错误提示", task_id="task_123")
    """
    if browser_snapshot is None:
        return json.dumps({
            "success": False,
            "error": "Browser tools not available",
            "valid": False
        })
    
    if call_llm is None:
        return json.dumps({
            "success": False,
            "error": "LLM client not available",
            "valid": False
        })
    
    try:
        # 第 1 步：获取页面快照
        logger.info(f"[AI Validate] Getting page snapshot for task {task_id}")
        snapshot_result = browser_snapshot(full=True, task_id=task_id)
        
        if isinstance(snapshot_result, str):
            snapshot_data = json.loads(snapshot_result)
        else:
            snapshot_data = snapshot_result
        
        if not snapshot_data.get("success", False):
            return json.dumps({
                "success": False,
                "error": f"Failed to get snapshot: {snapshot_data.get('error', 'Unknown error')}",
                "valid": False
            })
        
        snapshot_text = snapshot_data.get("snapshot", "")
        url = snapshot_data.get("url", "unknown")
        
        # 第 2 步：使用 LLM 验证页面状态
        logger.info(f"[AI Validate] Validating page. Prompt: {prompt}")
        
        validation_prompt = f"""你是一个页面状态验证专家。分析当前页面内容，判断是否符合用户的验证条件。

当前页面 URL: {url}

验证条件：{prompt}

页面内容（accessibility tree）:
{snapshot_text[:12000]}

任务：
1. 理解用户要验证什么条件
2. 在页面内容中查找相关证据
3. 判断条件是否成立
4. 提供支持结论的具体证据

请以 JSON 格式返回：
{{
    "success": true/false,  # 验证是否成功执行
    "valid": true/false,    # 页面状态是否符合预期
    "confidence": 0.0-1.0,  # 置信度
    "evidence": "支持结论的具体证据，如找到的文本、元素等",
    "reasoning": "判断过程简述",
    "suggestion": "如果验证失败，建议下一步操作"
}}
"""
        
        llm_response = call_llm(
            messages=[{"role": "user", "content": validation_prompt}],
            model="qwen3.5-plus",
            temperature=0.1,
        )
        
        # 解析 LLM 响应
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(llm_response)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"[AI Validate] Failed to parse LLM response: {e}")
            return json.dumps({
                "success": False,
                "error": f"Failed to parse LLM response: {str(e)}",
                "valid": False,
                "raw_response": llm_response[:500] if llm_response else None
            })
        
        # 确保结果格式正确
        if not isinstance(result, dict):
            result = {
                "success": False,
                "valid": False,
                "error": "Invalid response format"
            }
        
        # 添加默认值
        result.setdefault("success", True)
        result.setdefault("valid", False)
        result.setdefault("confidence", 0.5)
        result.setdefault("evidence", "")
        result.setdefault("reasoning", "")
        result.setdefault("url", url)
        
        logger.info(f"[AI Validate] Result: valid={result.get('valid')}, confidence={result.get('confidence')}")
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"[AI Validate] Error: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "valid": False
        })


def browser_ai_wait_for(
    prompt: str,
    timeout: int = 30,
    task_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    等待页面达到指定状态（AI 增强版）
    
    Args:
        prompt: 自然语言描述等待条件，如"等待登录按钮出现"、"等待加载完成"
        timeout: 超时时间（秒，默认 30）
        task_id: 任务 ID（可选）
    
    Returns:
        JSON 字符串，包含等待结果
    """
    import time
    
    start_time = time.time()
    interval = 2  # 每 2 秒检查一次
    
    while time.time() - start_time < timeout:
        result = browser_ai_validate(prompt=prompt, task_id=task_id)
        
        if isinstance(result, str):
            result_data = json.loads(result)
        else:
            result_data = result
        
        if result_data.get("success") and result_data.get("valid"):
            return json.dumps({
                "success": True,
                "waited_seconds": round(time.time() - start_time, 2),
                "message": f"条件已满足：{prompt}",
                "evidence": result_data.get("evidence", "")
            })
        
        time.sleep(interval)
    
    return json.dumps({
        "success": False,
        "error": "Timeout",
        "message": f"等待超时 ({timeout}秒)：{prompt}",
        "waited_seconds": timeout
    })


# 注册工具
def register_ai_validate_tools():
    """注册 AI Validate 工具到 registry"""
    from tools.registry import registry
    
    # browser_ai_validate
    schema_validate = {
        "name": "browser_ai_validate",
        "description": "使用自然语言验证页面状态。直接描述要验证的条件，如'检查用户是否已登录'、'检查购物车是否有商品'。返回布尔值和详细证据。",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "自然语言描述验证条件"
                },
                "task_id": {
                    "type": "string",
                    "description": "任务 ID（可选）"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒，默认 10）",
                    "default": 10
                }
            },
            "required": ["prompt"]
        }
    }
    
    # browser_ai_wait_for
    schema_wait = {
        "name": "browser_ai_wait_for",
        "description": "等待页面达到指定状态。AI 轮询检查直到条件满足或超时。如'等待登录按钮出现'、'等待加载完成'。",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "自然语言描述等待条件"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒，默认 30）",
                    "default": 30
                },
                "task_id": {
                    "type": "string",
                    "description": "任务 ID（可选）"
                }
            },
            "required": ["prompt"]
        }
    }
    
    registry.register(
        name="browser_ai_validate",
        toolset="browser",
        schema=schema_validate,
        handler=lambda args, **kw: browser_ai_validate(
            prompt=args.get("prompt", ""),
            task_id=kw.get("task_id"),
            timeout=args.get("timeout", 10)
        ),
        emoji="✅",
    )
    
    registry.register(
        name="browser_ai_wait_for",
        toolset="browser",
        schema=schema_wait,
        handler=lambda args, **kw: browser_ai_wait_for(
            prompt=args.get("prompt", ""),
            timeout=args.get("timeout", 30),
            task_id=kw.get("task_id")
        ),
        emoji="⏳",
    )


# 自动注册
register_ai_validate_tools()
