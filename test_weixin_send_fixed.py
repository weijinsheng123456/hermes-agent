#!/usr/bin/env python3
"""
使用正确的 API 测试微信消息发送
"""

import json
import asyncio
import aiohttp
from pathlib import Path

async def test_weixin_send():
    """测试发送微信消息"""
    print("="*60)
    print("微信消息发送测试（使用正确API）")
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
        user_id = account_data.get('user_id', 'o9cq800pQnzVkBIL4za6iBRT5MNw@im.wechat')
        
        if not bot_token:
            print("❌ 没有 bot_token")
            return False
        
        print(f"✅ 账户文件: {main_file.name}")
        print(f"user_id: {user_id}")
        print(f"bot_token 前30位: {bot_token[:30]}...")
        
        # 使用正确的 API 端点
        send_url = f"{base_url}/ilink/bot/sendmessage"
        headers = {
            'Authorization': f'Bearer {bot_token}',
            'Content-Type': 'application/json'
        }
        
        # 构建消息数据（根据微信 API 格式）
        message_data = {
            'to_user_id': user_id,
            'msg_type': 'text',
            'content': '测试消息：Hermes Gateway 微信机器人测试成功！🎉'
        }
        
        print(f"\n发送消息到: {send_url}")
        print(f"接收者: {user_id}")
        print(f"消息内容: {message_data['content']}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(send_url, headers=headers, json=message_data, timeout=15) as resp:
                    print(f"\n响应状态码: {resp.status}")
                    
                    if resp.status == 200:
                        content = await resp.read()
                        try:
                            data = json.loads(content)
                            print(f"✅ 消息发送成功！")
                            print(f"响应数据: {data}")
                            
                            if data.get('ret') == 0:
                                print(f"🎉 微信消息发送成功！ret=0 表示成功")
                                return True
                            else:
                                print(f"⚠️  API返回非零ret: {data.get('ret')}")
                                print(f"错误信息: {data.get('errmsg', '未知错误')}")
                                return False
                        except Exception:
                            text = content.decode('utf-8', errors='ignore')
                            print(f"响应内容: {text[:200]}")
                            return True
                    else:
                        text = await resp.text()
                        print(f"❌ 消息发送失败，状态码: {resp.status}")
                        print(f"错误信息: {text[:200]}")
                        return False
            except asyncio.TimeoutError:
                print("❌ 请求超时")
                return False
            except Exception as e:
                print(f"❌ 请求失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n准备测试微信消息发送...")
    print("这将向你的微信发送一条测试消息")
    
    # 等待用户确认
    input("\n按 Enter 键开始测试（将向你的微信发送消息）...")
    
    success = await test_weixin_send()
    
    print("\n" + "="*60)
    if success:
        print("✅ 测试完成！请检查微信是否收到消息")
    else:
        print("❌ 测试失败，需要进一步调试")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())