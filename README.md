# Devicebase MCP Server

MCP (Model Context Protocol) server for the [Devicebase](https://devicebase.cn) device automation API — remote control across three device platforms:

| Platform | Covers | Tools |
|----------|--------|-------|
| **mobile** | Android, HarmonyOS, iOS | `mobile_*` (17) |
| **browser** | Chrome / Chromium / Edge over CDP | `browser_*` (21) |
| **computer** | macOS / Windows / Linux desktops | `computer_*` (15) |

Plus two platform-agnostic tools: `list_devices` (discovery) and `screenshot` (cross-family).

## Features

- **Device management** — list and filter devices across all three platforms
- **Mobile** — tap, swipe, text input, app launch/stop, shell, UI hierarchy, install
- **Browser** — navigation, DOM operations, JavaScript evaluation, tabs, keyboard
- **Computer** — mouse, keyboard, app launch, screen size, host shell
- **Screenshots** — for any platform, via one route the server dispatches by device type

## Requirements

- Python 3.11+

## Installation

```bash
git clone https://github.com/devicebase/devicebase-mcp
cd devicebase-mcp
./install.sh
```

Or by hand:

```bash
uv sync --extra dev
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `DEVICEBASE_API_KEY` | yes | API key. Get one from https://www.devicebase.cn/ |
| `DEVICEBASE_BASE_URL` | no | API base URL (default: `https://api.devicebase.cn`) |
| `MCP_TRANSPORT` | no | `stdio` (default) or `streamable-http` |
| `MCP_HOST` | no | Bind host for HTTP (default: `localhost`) |
| `MCP_PORT` | no | Bind port for HTTP (default: `8080`) |

## Transports

### stdio (default)

For MCP clients that launch the server as a subprocess. There is no incoming HTTP request, so the API key always comes from `DEVICEBASE_API_KEY`.

**Claude Code:**

```bash
claude mcp add devicebase \
  -e DEVICEBASE_API_KEY=your-api-key \
  -- uv run --directory /path/to/devicebase-mcp python -m devicebase_mcp
```

Or in `.mcp.json` / `~/.claude.json`:

```json
{
  "mcpServers": {
    "devicebase": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/devicebase-mcp", "python", "-m", "devicebase_mcp"],
      "env": { "DEVICEBASE_API_KEY": "your-api-key" }
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):

```json
{
  "servers": {
    "devicebase": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/devicebase-mcp", "python", "-m", "devicebase_mcp"],
      "env": { "DEVICEBASE_API_KEY": "your-api-key" }
    }
  }
}
```

### streamable-http

For clients that connect over HTTP. Start the server, then point the client at it:

```bash
uv run python -m devicebase_mcp --transport streamable-http --port 8080
```

```json
{
  "type": "http",
  "url": "http://localhost:8080/mcp",
  "headers": { "Authorization": "Bearer your-api-key" }
}
```

Over HTTP a per-request `Authorization: Bearer <key>` header takes precedence over `DEVICEBASE_API_KEY`, so one server can serve several accounts. Over stdio there is no request to read a header from, so the environment variable is the only source.

## Tools

### Discovery

| Tool | Description |
|------|-------------|
| `list_devices` | List devices. Filter by `keyword`, `state`, `type`, `limit`. **Start here** — this is how you find the `serialno` every other tool needs. |
| `screenshot` | Capture any device as base64 JPEG. Works for all three platforms. |

`type` accepts a category (`mobile` / `browser` / `computer`) or a system type (`android` / `harmonyos` / `ios` / `macos` / `windows` / `linux` / `chrome` / `chromium` / `edge` / `other`). System types match the device's `os_type`, because a device row only carries the coarse type — a Chrome browser is `type=browser` with `os_type=Chrome`.

### Mobile (`mobile_*`)

Serial: from `list_devices(type="mobile")`.

| Area | Tools |
|------|-------|
| Touch | `mobile_tap`, `mobile_double_tap`, `mobile_long_press`, `mobile_swipe` |
| Navigation | `mobile_back`, `mobile_home` |
| Apps | `mobile_launch_app`, `mobile_stop_app`, `mobile_stop_current_app`, `mobile_current_app` |
| Text | `mobile_input_text`, `mobile_clear_text` |
| State | `mobile_device_info`, `mobile_dump_hierarchy` |
| Shell | `mobile_bash` (adb/hdc only) |
| Install | `mobile_install_app`, `mobile_install_status` |

### Browser (`browser_*`)

Serial: from `list_devices(type="browser")`. Selectors are CSS selectors.

| Area | Tools |
|------|-------|
| Navigation | `browser_navigate`, `browser_refresh`, `browser_go_back`, `browser_go_forward` |
| DOM | `browser_click`, `browser_fill`, `browser_select`, `browser_text`, `browser_attribute`, `browser_exists`, `browser_execute` |
| Text | `browser_input` (CDP `Input.insertText`, reliable for CJK) |
| Keyboard | `browser_hotkey` |
| Tabs | `browser_state`, `browser_tabs`, `browser_tab_open`, `browser_tab_close`, `browser_tab_close_all`, `browser_tab_switch` |
| Lifecycle | `browser_launch`, `browser_close` |

`browser_execute` is **danger tier** — the script runs with the page's own privileges. Editing shortcuts (`Meta a`) act on the page; browser-chrome shortcuts such as `Control+t` are not reachable, because CDP drives the page rather than the browser UI.

### Computer (`computer_*`)

Serial: from `list_devices(type="computer")`. Coordinates are absolute screen pixels.

| Area | Tools |
|------|-------|
| Mouse | `computer_click`, `computer_double_click`, `computer_long_click`, `computer_move`, `computer_drag`, `computer_scroll` |
| Keyboard | `computer_type_text`, `computer_press`, `computer_hotkey` |
| System | `computer_position`, `computer_screen_size`, `computer_permissions`, `computer_launch_app` |
| Blocking | `computer_wait` (milliseconds), `computer_bash` (timeout in seconds) |

`computer_bash` is **danger tier** — it runs on the host machine as the desktop user, unsandboxed. A non-zero command exit is reported in `data.exitCode`, not as a tool error, because the API call itself succeeded.

## Errors

Two failure layers are surfaced, and the second is easy to miss:

- **HTTP layer** — a non-2xx status becomes `AuthenticationError` (401), `DeviceNotFoundError` (404), `ValidationError` (400/422), or `DevicebaseError`.
- **Envelope layer** — an HTTP 200 whose body carries a non-2xx `code` becomes `BusinessError`. The control API reports action failures this way (a selector that matches nothing returns `{"code":502,...}`), so a tool that only checked the status would report failure as success.

## Development

```bash
make test        # pytest
make test-cov    # pytest with coverage
make lint        # ruff check
make format      # ruff format + fix
make typecheck   # mypy --strict
```

## Troubleshooting

**Every device call fails with `HTTP 503: 请求失败: fetch failed`, while `list_devices` works.**

If the machine has a system-wide HTTP proxy configured, `httpx` picks it up automatically (its `trust_env` default) and routes through it — including for `127.0.0.1`. Some proxies cause `httpx` to emit a duplicated `Connection` header, which the gateway rejects with a 503 that masks the real cause. Bypass the proxy for the Devicebase host:

```bash
export NO_PROXY=127.0.0.1,localhost
```

This is a client/proxy interaction rather than a Devicebase fault: `curl` and the Go client do not read the macOS system proxy settings, so they are unaffected on the same machine.

## License

MIT
