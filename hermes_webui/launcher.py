#!/usr/bin/env python3
"""Hermes Web UI 启动器 - 修复后台运行问题"""
import os
import sys
import subprocess
import time

def main():
    hermes_dir = os.path.expanduser('~/hermes-agent')
    os.chdir(hermes_dir)
    
    # 激活虚拟环境
    env = os.environ.copy()
    env['PATH'] = f"{hermes_dir}/.venv/bin:" + env.get('PATH', '')
    
    # 启动服务器
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'hermes_webui.server:app',
        '--host', '0.0.0.0',
        '--port', '8080',
        '--log-level', 'info'
    ]
    
    print("=" * 60)
    print("Hermes Web UI 启动中...")
    print("=" * 60)
    print(f"工作目录：{hermes_dir}")
    print(f"访问地址：http://localhost:8080")
    print("=" * 60)
    
    # 启动进程
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # 等待启动
    for _ in range(30):
        line = proc.stdout.readline()
        if line:
            print(line.strip())
            if 'Uvicorn running' in line:
                print("\n✅ 服务器已启动！")
                print("访问：http://localhost:8080")
                break
        time.sleep(0.5)
    else:
        print("⚠️ 服务器启动超时")
    
    # 保持运行
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    
    return proc.returncode

if __name__ == '__main__':
    sys.exit(main())
