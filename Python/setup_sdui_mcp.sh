#!/bin/bash

# MCP SDUI Resolver Setup Script
# This script sets up the MCP SDUI Resolver for Claude Code integration

set -e

echo "==================================="
echo "MCP SDUI Resolver Setup"
echo "==================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create virtual environment if it doesn't exist
VENV_DIR="/Users/username/Scripts/Python/.venv_sdui"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r /Users/username/Scripts/Python/sdui_requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Make the script executable
chmod +x /Users/username/Scripts/Python/mcp_sdui_resolver.py
echo -e "${GREEN}✓ Script made executable${NC}"

# Test the MCP server
echo "Testing MCP server..."
timeout 2 python3 /Users/username/Scripts/Python/mcp_sdui_resolver.py --version 2>/dev/null || true

# Setup Claude Code configuration
CLAUDE_CONFIG_DIR="$HOME/.config/claude-code"
MCP_CONFIG_DIR="$CLAUDE_CONFIG_DIR/mcp-servers"

if [ ! -d "$MCP_CONFIG_DIR" ]; then
    mkdir -p "$MCP_CONFIG_DIR"
    echo -e "${GREEN}✓ Created MCP configuration directory${NC}"
fi

# Copy configuration
cp /Users/username/Scripts/Python/mcp_sdui_config.json "$MCP_CONFIG_DIR/sdui-resolver.json"
echo -e "${GREEN}✓ Configuration copied to Claude Code${NC}"

# Create launcher script
LAUNCHER_SCRIPT="$MCP_CONFIG_DIR/launch_sdui_resolver.sh"
cat > "$LAUNCHER_SCRIPT" << 'EOF'
#!/bin/bash
source /Users/username/Scripts/Python/.venv_sdui/bin/activate
exec python3 /Users/username/Scripts/Python/mcp_sdui_resolver.py
EOF

chmod +x "$LAUNCHER_SCRIPT"
echo -e "${GREEN}✓ Launcher script created${NC}"

echo
echo "==================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "==================================="
echo
echo "The MCP SDUI Resolver has been successfully installed."
echo
echo "To use in Claude Code:"
echo "1. Restart Claude Code application"
echo "2. The following tools will be available:"
echo "   - mcp__sdui_resolver__resolve_schema"
echo "   - mcp__sdui_resolver__validate_contract"
echo "   - mcp__sdui_resolver__get_navigation"
echo
echo "Configuration file: $MCP_CONFIG_DIR/sdui-resolver.json"
echo "Log file: $HOME/.claude-code/logs/mcp-sdui-resolver.log"
echo
echo "For manual testing, run:"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 /Users/username/Scripts/Python/mcp_sdui_resolver.py"