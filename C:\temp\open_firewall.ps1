# 需要管理员权限——会弹出 UAC 窗口，请点"是"
New-NetFirewallRule -DisplayName "Hermes SOCKS5 Proxy 1080" -Direction Inbound -Protocol TCP -LocalPort 1080 -Action Allow
Write-Output "防火墙规则已添加，端口 1080 已放行"
