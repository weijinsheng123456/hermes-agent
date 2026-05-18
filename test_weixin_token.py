#!/usr/bin/env python3
"""
测试微信 token 有效性
"""

import json
import asyncio
import aiohttp
from pathlib import Path

async def test_weixin_token():
    """测试微信 token 是否有效"""
    print("测试微信 token 有效性...")
    
    # 读取主账户文件
    accounts_dir = Path.home() / ".hermes" / "weixin" / "accounts"
    main_file = accounts_dir / "96083731d96b@im.bot.json"
    
    if not main_file.exists():
        print(f"❌ 主账户文件不存在: {main_file}")
        return False
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
        
        bot_token = account_data.get('bot_token', '')
        base_url = account_data.get('base_url', 'https://ilinkai.weixin.qq.com')
        
        if not bot_token:
            print("❌ 账户文件中没有 bot_token")
            return False
        
        print(f"✅ 找到账户文件: {main_file.name}")
        print(f"bot_token: {bot_token[:30]}...")
        print(f"base_url: {base_url}")
        
        # 测试 token 有效性
        print("\n测试 token 有效性...")
        
        # 使用 token 调用一个简单的 API
        test_url = f"{base_url}/ilink/bot/get_bot_info"
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(test_url, headers=headers, timeout=10) as resp:
                    print(f"API 状态码: {resp.status}")
                    
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ Token 有效！响应: {data}")
                        return True
                    elif resp.status == 401:
                        print("❌ Token 无效或已过期")
                        return False
                    else:
                        print(f"⚠️  未知状态码: {resp.status}")
                        text = await resp.text()
                        print(f"响应内容: {text[:200]}")
                        return False
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 读取账户文件失败: {e}")
        return False

async def test_send_message():
    """测试发送微信消息"""
    print("\n" + "="*60)
    print("测试发送微信消息...")
    print("="*60)
    
    # 读取账户文件
    accounts_dir = Path.home() / ".hermes" / "weixin" / "accounts"
    main_file = accounts_dir / "96083731d96b@im.bot.json"
    
    if not main_file.exists():
        print("❌ 账户文件不存在")
        return False
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            account_data = json.load(f)
        
        bot_token = account_data.get('bot_token', '')
        base_url = account_data.get('base_url', 'https://ilinkai.weixin.qq.com')
        user_id = account_data.get('user_id', '')
        
        if not user_id:
            print("❌ 没有 user_id，无法发送消息")
            return False
        
        # 发送测试消息
        send_url = f"{base_url}/ilink/bot/send_message"
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        message_data = {
            'to_user_id': user_id,
            'msg_type': 'text',
            'content': {
                'text': '测试消息：Hermes Gateway 微信机器人测试'
            }
        }
        
        print(f"发送消息给: {user_id}")
        print(f"消息内容: {message_data['content']['text']}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(send_url, headers=headers, json=message_data, timeout=15) as resp:
                    print(f"发送状态码: {resp.status}")
                    
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ 消息发送成功！响应: {data}")
                        return True
                    else:
                        text = await resp.text()
                        print(f"❌ 消息发送失败: {resp.status}")
                        print(f"错误信息: {text[:200]}")
                        return False
            except Exception as e:
                print(f"❌ 发送请求失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    print("="*60)
    print("微信 token 和消息发送测试")
    print("="*60)
    
    # 测试 token 有效性
    token_valid = await test_weixin_token()
    
    if token_valid:
        print("\n" + "="*60)
        print("✅ Token 有效，准备测试消息发送...")
        print("="*60)
        
        # 等待用户确认
        input("\n按 Enter 键开始测试消息发送...")
        
        # 测试发送消息
        await test_send_message()
    else:
        print("\n" + "="*60)
        print("❌ Token 无效，需要重新认证")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())