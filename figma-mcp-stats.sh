#!/bin/bash
# Figma MCP Wrapper Statistics

LOG_FILE="$HOME/.figma_mcp_wrapper.log"

if [[ ! -f "$LOG_FILE" ]]; then
    echo "No log file found. Wrapper not used yet."
    exit 0
fi

echo "=== Figma MCP Wrapper Stats ==="
echo ""
echo "Total requests: $(grep -c 'REQUEST:' "$LOG_FILE")"
echo "Cache hits: $(grep -c 'CACHE HIT:' "$LOG_FILE")"
echo "Rate limited: $(grep -c 'RATE LIMITED:' "$LOG_FILE")"
echo ""
echo "Last 10 events:"
tail -10 "$LOG_FILE"
echo ""
echo "Full log: $LOG_FILE"
