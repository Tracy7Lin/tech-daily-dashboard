# 本地定时生成与自动化说明

## 目标

在不引入额外云依赖的前提下，让科技日报可以在本地 Windows 环境中稳定地每日自动生成。

本轮采用两层结构：

- Python 主链路提供一个稳定的“生成北京时间今天日报”的入口
- PowerShell 脚本负责本地执行、日志落盘和 Windows 计划任务注册

这样可以保持高内聚低耦合：

- 业务层不感知计划任务
- 调度层不复制业务逻辑

## 新增能力

### 1. CLI 自动化入口

新增命令：

```bash
python run_dashboard.py generate-today --output-dir build/site
```

该命令会按 `Asia/Shanghai` 时区解析“今天”，并生成对应日期的日报。

### 2. 本地执行脚本

新增：

- `scripts/run_daily_report.ps1`

职责：

- 切换到项目根目录
- 生成北京时间今天的日报
- 将运行日志写入 `build/logs/<date>.log`
- 在日报生成成功后，追加一次 `health-check`
- 将最近一次运行问题与最近几天重复问题一并写入日志

### 3. Windows 定时任务脚本

新增：

- `scripts/register_daily_task.ps1`
- `scripts/unregister_daily_task.ps1`

职责：

- 注册每日定时任务
- 删除已注册的日报定时任务

## 推荐使用方式

### 手动验证

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_daily_report.ps1
```

### 注册自动任务

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register_daily_task.ps1 -ScheduleTime 08:30
```

### 删除任务

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\unregister_daily_task.ps1
```

## 设计边界

本轮没有做这些事：

- 不引入云端 cron 或外部调度平台
- 不新增守护进程
- 不在业务层内嵌计划任务逻辑
- 不增加告警通道

这些能力可以后续在现有脚本层基础上继续扩展。

## 当前日志内容

当前 `build/logs/<date>.log` 至少会记录：

- 日报生成开始时间
- 日报生成摘要输出
- 生成退出码
- 生成后 `health-check` 开始与结束时间
- 最近一次日报运行中的源问题
- 最近几天重复出现的源问题摘要

这让本地定时任务不再只有“有没有跑成功”，而是能顺带提供最基本的运维可观测性。
