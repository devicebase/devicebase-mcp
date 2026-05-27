# Devicebase MCP Server

MCP (Model Context Protocol) server for remote mobile device control via Devicebase API.

## Features

- **Device Management**: List devices, get device info
- **Touch Interactions**: Tap, double-tap, long-press, swipe
- **Navigation**: Back, Home buttons
- **App Management**: Launch apps, get current app
- **Text Input**: Input text, clear text
- **UI Inspection**: Dump hierarchy, screenshot

## Requirements

- Python 3.11+
- Devicebase API key

## Installation

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e .
```

## Configuration

Set your Devicebase API key via environment variable:

```bash
export DEVICEBASE_API_KEY="your-api-key"
export DEVICEBASE_BASE_URL="https://api.devicebase.cn"  # Optional, default provided
```

## Usage

### Standalone Server

```bash
DEVICEBASE_API_KEY=your-key uv run python -m devicebase_mcp
```

### Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "devicebase": {
      "command": "uv",
      "args": ["run", "python", "-m", "devicebase_mcp"],
      "env": {
        "DEVICEBASE_API_KEY": "${DEVICEBASE_API_KEY}"
      }
    }
  }
}
```

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "devicebase": {
      "command": "uv",
      "args": ["run", "python", "-m", "devicebase_mcp"],
      "env": {
        "DEVICEBASE_API_KEY": "${DEVICEBASE_API_KEY}"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_devices` | List available devices |
| `get_device_info` | Get device details |
| `tap` | Single tap at coordinates |
| `double_tap` | Double tap |
| `long_press` | Long press |
| `swipe` | Swipe gesture |
| `press_back` | Press back button |
| `press_home` | Press home button |
| `launch_app` | Launch an app |
| `get_current_app` | Get foreground app |
| `input_text` | Input text |
| `clear_text` | Clear text field |
| `dump_hierarchy` | Get UI tree |
| `screenshot` | Get screen capture |

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## License

MIT