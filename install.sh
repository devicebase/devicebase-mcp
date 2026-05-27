#!/bin/bash
set -e

# Devicebase MCP Server Installer

echo "Installing devicebase-mcp..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "Installing Python dependencies..."
uv sync --extra dev

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set your API key:"
echo "   export DEVICEBASE_API_KEY='your-api-key'"
echo ""
echo "2. Run the MCP server:"
echo "   uv run python -m devicebase_mcp"
echo ""
echo "3. Or add to Claude Code config (~/.claude/settings.json):"
echo '   "mcpServers": {"devicebase": {"command": "uv", "args": ["run", "python", "-m", "devicebase_mcp"]}}'