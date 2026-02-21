#!/bin/bash
# =============================================================================
# run-infinite.sh - AI 无限自动开发守护进程 (Infinite Daemon)
# =============================================================================

set -e

# 日志目录
LOG_DIR="./automation-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/infinite-$(date +%Y%m%d).log"

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

count_remaining_tasks() {
    if [ -f "task.json" ]; then
        grep -c '"passes": false' task.json 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

log "INFO" "🚀 启动无限运行 AI 开发系统..."

run_count=0

while true; do
    REMAINING=$(count_remaining_tasks)

    # 如果没有任务，休眠 30 秒后再次检查（此时你可以随时修改 task.json 增加任务）
    if [ "$REMAINING" -eq 0 ]; then
        echo -ne "\r[$(date '+%H:%M:%S')] 所有任务已完成，系统待机中，等待新任务写入 task.json... "
        sleep 30
        continue
    fi

    run_count=$((run_count + 1))
    echo ""
    log "INFO" "========================================"
    log "INFO" "⚡ 发现新任务！开始第 $run_count 轮开发，剩余任务: $REMAINING"
    log "INFO" "========================================"

    RUN_START=$(date +%s)
    RUN_LOG="$LOG_DIR/run-${run_count}-$(date +%H%M%S).log"

    # 动态生成 AI 的本轮 Prompt
    PROMPT_FILE=$(mktemp)
    cat > "$PROMPT_FILE" << 'PROMPT_EOF'
请严格按照 CLAUDE.md 的工作流执行：
1. 读取 task.json，找到第一个 passes: false 的任务。
2. 仔细阅读描述，编写并修改代码。
3. 按照 CLAUDE.md 的要求运行测试。
4. 在 progress.txt 记录你的工作内容。
5. 更新 task.json 将该任务的 passes 改为 true。
6. 一次性 Commit 所有更改。

在本轮会话中，请只完成【一个】任务。完成后直接退出。如果遇到无法解决的阻塞（如缺少 API Key），请在 progress.txt 记录阻碍并退出。
PROMPT_EOF

    # 唤醒 Claude Code 执行任务 (静默模式 + 跳过危险操作确认 + 允许全部工具)
    if claude -p \
        --dangerously-skip-permissions \
        --allowed-tools "Bash Edit Read Write Glob Grep Task WebSearch WebFetch mcp__playwright__*" \
        < "$PROMPT_FILE" 2>&1 | tee -a "$RUN_LOG"; then
        
        RUN_END=$(date +%s)
        RUN_DURATION=$((RUN_END - RUN_START))
        log "SUCCESS" "✅ 第 $run_count 轮任务完成！耗时 ${RUN_DURATION} 秒。"
    else
        RUN_END=$(date +%s)
        RUN_DURATION=$((RUN_END - RUN_START))
        log "WARNING" "⚠️ 第 $run_count 轮执行异常结束 (退出码 $?)。可能遇到阻塞或报错。"
        log "WARNING" "休眠 60 秒后重试，请检查日志或手动解除阻塞..."
        sleep 60
    fi

    rm -f "$PROMPT_FILE"
    
    # 两轮任务间短暂休息
    sleep 5
done
