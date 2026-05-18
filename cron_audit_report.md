# Cron 任务审计报告

**审计时间**: 2026-04-29 12:23 CST
**任务总数**: 41
**审计者**: Hermes Agent

---

## 一、失败任务检查

| 状态 | 数量 |
|------|------|
| ✅ 运行正常 (last_status=ok) | 35 |
| ✅ 新任务尚未运行 (last_status=null) | 6 |
| ❌ 失败任务 (last_status=error) | **0** |

**结论**: 所有已运行的任务均成功完成，无交付错误。无失败任务。

---

## 二、孤儿任务（引用了不存在的脚本）

| 任务名称 | Job ID | 引用脚本 | 状态 |
|---------|--------|---------|------|
| 每日系统健康检查 | `2f61ebf9-3ae` | `~/.hermes/scripts/auto_repair.sh` | ❌ **文件不存在** |
| 自动化系统修复 | `d4366728-3dd` | `~/.hermes/scripts/auto_repair_final.sh` | ❌ **文件不存在** |

**建议**: 这两个任务引用的 shell 脚本已丢失，任务实际运行时可能失败或产生错误。建议清理或修复脚本。

---

## 三、冗余/重叠任务分析

### 3.1 健康检查 (5个任务重叠)

| # | 任务名 | 调度 | 描述 | 建议 |
|---|-------|------|------|------|
| 1 | `daily-system-analysis` | 每天 05:00 | 系统分析器 | ✅ 保留 |
| 2 | `每日系统健康检查` | 每天 07:00 | auto_repair.sh（已丢失） | ❌ **建议删除**（脚本丢失+冗余） |
| 3 | `每日健康报告` | 每天 09:15 | 健康报告生成 | ⚠️ 与 daily-system-analysis 重叠 |
| 4 | `Monthly Health Check` | 每月1日 03:00 | 健康检查技能 | ✅ 保留（月度） |
| 5 | `weekly-health-check` | 每周一 08:00 | weekly_health_check.py | ⚠️ 与 Monthly Health Check 重叠 |

### 3.2 检查点/Checkpoint 清理 (3个任务重叠)

| # | 任务名 | 调度 | 脚本 | 建议 |
|---|-------|------|------|------|
| 1 | `weekly-maintenance` | 每周日 04:00 | cleanup_checkpoints.py | ✅ 保留（只有它同时做日志轮转） |
| 2 | `checkpoint-limit` | 每天 03:15 | limit_checkpoints.py | ⚠️ 与 weekly-maintenance 重叠 |
| 3 | `checkpoint-auto-cleanup` | 每天 04:00 | checkpoint_cleanup.py | ⚠️ 与 weekly-maintenance 重叠 |

**建议**: 合并为每周一次的清理，`checkpoint-limit` 和 `checkpoint-auto-cleanup` 可删除。

### 3.3 数据库 VACUUM (2个任务重叠)

| # | 任务名 | 调度 | 建议 |
|---|-------|------|------|
| 1 | `state-db-vacuum` | 每周日 02:30 | ✅ 保留（周级足够） |
| 2 | `Database VACUUM` | **每天** 03:00 | ❌ **建议删除**（每天 VACUUM 过于频繁且冗余） |

### 3.4 内存管理 (3个任务重叠)

| # | 任务名 | 调度 | 技能/脚本 | 建议 |
|---|-------|------|-----------|------|
| 1 | `memory-auto-maintenance` | 每周日 03:00 | proactive-memory + health-check | ✅ 保留 |
| 2 | `memory-auto-optimize` | 每天 03:00 | memory_optimizer.py | ❌ **建议删除**（memory-auto-maintenance 已涵盖） |
| 3 | `memory-slimming` | 每月1日 03:00 | proactive-memory | ⚠️ 月度瘦身可保留，但检查是否与 maintenance 重复 |

### 3.5 费用/Token 报告 (3个任务重叠)

| # | 任务名 | 调度 | 脚本 | 建议 |
|---|-------|------|------|------|
| 1 | `Daily Cost Report` | 每天 08:30 | cost_monitor.py | ⚠️ 与每日费用报告重复 |
| 2 | `daily-token-report` | 每天 01:00 | token_monitor.py | ✅ 保留（凌晨运行，时间分散） |
| 3 | `每日费用报告` | 每天 08:00 | 读 state.db | ⚠️ 与 Daily Cost Report 高度重叠 |

**建议**: `Daily Cost Report` 和 `每日费用报告` 功能相似，建议合并为一个。

### 3.6 自动化修复 (2个任务，均脚本丢失)

| # | 任务名 | 调度 | 脚本状态 | 建议 |
|---|-------|------|---------|------|
| 1 | `每日系统健康检查` | 每天 07:00 | auto_repair.sh ❌ 丢失 | ❌ **建议删除** |
| 2 | `自动化系统修复` | 每周日 03:00 | auto_repair_final.sh ❌ 丢失 | ❌ **建议删除** |

---

## 四、资源争用热点

### 4.1 早晨 08:00 拥堵（4个任务同时运行）

| 任务 | 时间 |
|------|------|
| Daily Topic Generation | 08:00 |
| 每日总结 | 08:00 |
| 中小企业主每日热点推送 | 08:00 |
| 每日费用报告 | 08:00 |
| ✅ 稳定性综合报告 | 08:45（错峰） |
| ✅ 每日健康报告 | 09:15（错峰） |

**建议**: 将这些任务的执行时间分散开（如 08:00, 08:10, 08:20, 08:30），减少并发压力。

### 4.2 凌晨 03:00 拥堵（3个任务 + 2个月度）

| 任务 | 时间 |
|------|------|
| memory-auto-optimize | 03:00 |
| system-baseline | 03:00 |
| Database VACUUM | 03:00 |
| checkpoint-limit | 03:15 |
| Monthly Health Check | 03:00（每月1日） |
| memory-slimming | 03:00（每月1日） |

**建议**: 分散到 02:30, 03:00, 03:30, 04:00。

---

## 五、高频执行任务评估

| 任务 | 频率 | 建议 |
|------|------|------|
| `看门狗监控` | **每1分钟** | ⚠️ 每1分钟用 LLM 检查系统？成本较高，建议考虑降低频率 |
| `Gateway 进程健康守护` | **每3分钟** | ⚠️ 高频守护，可考虑调至5分钟 |
| `Gateway 熔断器监控` | **每5分钟** | ⚠️ 与上方Gateway任务重叠 |
| `定时任务错误恢复` | **每10分钟** | ⚠️ 与 Auto-Scale Delegation Workers 功能重叠 |
| `config-change-watcher` | **每10分钟** | ✅ 合理 |

**注意**: `看门狗监控` 每1分钟执行一次 LLM 调用（deepseek-v4-flash），每日约 1440 次请求，成本较高。建议评估必要性。

---

## 六、总结建议

### 优先清理（脚本丢失，任务无法正常运行）
1. ❌ `每日系统健康检查` — 删除（auto_repair.sh 丢失）
2. ❌ `自动化系统修复` — 删除（auto_repair_final.sh 丢失）

### 建议删除（冗余）
3. ❌ `checkpoint-limit` — 被 weekly-maintenance 覆盖
4. ❌ `checkpoint-auto-cleanup` — 被 weekly-maintenance 覆盖
5. ❌ `Database VACUUM`（每天）— 被 state-db-vacuum（每周）覆盖，每天VACUUM太频繁
6. ❌ `memory-auto-optimize` — 被 memory-auto-maintenance 覆盖

### 建议合并
7. ⚠️ `Daily Cost Report` + `每日费用报告` → 合并为一个

### 建议错峰
8. ⚠️ 早晨 08:00 的 4 个任务和凌晨 03:00 的 3 个任务需要分散排期

### 建议评估
9. ⚠️ `看门狗监控` 每1分钟运行，每日成本很高

---

**总计可优化任务**: 建议删除6个冗余/孤儿任务，合并2个，错峰调整约7个。
