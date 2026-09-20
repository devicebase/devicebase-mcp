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
echo "1. Set your API key (read by the server at request time):"
echo "   export DEVICEBASE_API_KEY='your-api-key'"
echo ""
echo "2. Run the server directly. It speaks stdio by default, so it is normally"
echo "   launched by an MCP client rather than by hand. To serve HTTP instead:"
echo "   uv run python -m devicebase_mcp --transport streamable-http"
echo ""
echo "3. Register it with an MCP client."
echo ""
echo "   Claude Code, from the command line:"
echo "     claude mcp add devicebase -e DEVICEBASE_API_KEY=your-api-key -- \\"
echo "       uv run --directory \"\$(pwd)\" python -m devicebase_mcp"
echo ""
echo "   Or by hand (~/.claude.json / .mcp.json), which is a stdio server:"
echo '     "mcpServers": {"devicebase": {"command": "uv",'
echo '       "args": ["run", "--directory", "/path/to/devicebase-mcp", "python", "-m", "devicebase_mcp"],'
echo '       "env": {"DEVICEBASE_API_KEY": "your-api-key"}}}'
echo ""
echo "   VS Code (.vscode/mcp.json):"
echo '     {"servers": {"devicebase": {"type": "stdio", "command": "uv",'
echo '       "args": ["run", "--directory", "/path/to/devicebase-mcp", "python", "-m", "devicebase_mcp"],'
echo '       "env": {"DEVICEBASE_API_KEY": "your-api-key"}}}}'
echo ""
echo "   For the HTTP transport the client config differs — the server must be"
echo "   running, and the key travels as a request header:"
echo '     {"type": "http", "url": "http://localhost:8080/mcp",'
echo '      "headers": {"Authorization": "Bearer your-api-key"}}'
