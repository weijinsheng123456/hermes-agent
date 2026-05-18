#!/usr/bin/env python3
"""
直接调用微信 QR 登录函数
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/xiaobai/hermes-agent')

async def weixin_qr_login():
    """调用微信 QR 登录"""
    try:
        # 导入 qr_login 函数
        from gateway.platforms.weixin import qr_login
        
        print("=" * 60)
        print("微信 QR 登录")
        print("=" * 60)
        
        # 检查账户目录
        accounts_dir = Path.home() / ".hermes" / "weixin" / "accounts"
        print(f"\n账户目录: {accounts_dir}")
        print(f"目录存在: {accounts_dir.exists()}")
        
        if accounts_dir.exists():
            files = list(accounts_dir.glob("*.json"))
            print(f"现有文件: {len(files)} 个")
            for f in files:
                print(f"  - {f.name}")
        
        print("\n" + "=" * 60)
        print("开始微信 QR 登录...")
        print("=" * 60)
        
        # 调用 QR 登录函数
        print("\n⚠️  注意：")
        print("1. 即将显示微信二维码")
        print("2. 请使用微信扫码")
        print("3. 扫码后在微信中点击'确认登录'")
        print("4. 二维码有效期约5分钟")
        print("\n准备扫码...")
        
        result = await qr_login(
            hermes_home=str(Path.home() / ".hermes"),
            bot_type="3",
            timeout_seconds=300  # 5分钟
        )
        
        if result:
            print("\n✅ 认证成功！")
            print(f"账户ID: {result.get('account_id')}")
            print(f"昵称: {result.get('nickname')}")
            print(f"头像: {result.get('headimgurl')}")
            
            # 检查文件是否创建
            files = list(accounts_dir.glob("*.json"))
            print(f"\n创建的token文件: {len(files)} 个")
            for f in files:
                print(f"  - {f.name}")
                # 显示文件大小
                print(f"    大小: {f.stat().st_size} 字节")
        else:
            print("\n❌ 认证失败或超时")
            print("可能原因：")
            print("1. 网络连接问题")
            print("2. 二维码过期（超过5分钟）")
            print("3. 扫码后未在微信中确认")
            print("4. 微信账号权限问题")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在 hermes-agent 目录中运行")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行认证
    asyncio.run(weixin_qr_login())