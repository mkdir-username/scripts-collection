# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

SDUI Hybrid Export — Figma-to-SDUI JSON transformer for Alfa-Bank mobile design system. Python server + thin Figma plugin architecture.

## Commands

### Server Management
```bash
./scripts/install.sh           # Install LaunchAgent (auto-start on login)
./scripts/install.sh status    # Check server status
./scripts/install.sh restart   # Restart server
./scripts/install.sh logs      # View logs
./scripts/install.sh uninstall # Remove auto-start

./scripts/start.sh             # Manual start (debugging)
```

### Version Management
```bash
./scripts/set-version.sh              # Show current + available versions
./scripts/set-version.sh latest       # Set to latest version
./scripts/set-version.sh 7.13.0       # Set to specific version
./scripts/set-version.sh auto         # Auto-discovery mode (remove symlink)
```

### Figma Plugin Build
```bash
cd figma-plugin
npm install
npm run build    # Compile TypeScript + copy UI
npm run watch    # Development mode with auto-rebuild
```

### Server Logs
```bash
tail -f ~/.sdui_logs/server.log       # Main server log
tail -f ~/.sdui_logs/requests.log     # Incoming requests
tail -f ~/.sdui_logs/debug.log        # Detailed dumps
curl http://127.0.0.1:8787/health     # Health check
```

## Architecture

```
Figma Plugin (thin)  →  HTTP POST :8787  →  Python Server (server.py)
     ↓                                              ↓
Extracts node data                         Transforms via sdui_export module
Style resolution                           Hot-reload on file change
     ↓                                              ↓
Sends raw Figma JSON                       Returns SDUI-compliant JSON
```

### Module Loading Priority

Server auto-discovers sdui_export in order:
1. `server/sdui_export.py` (symlink — pinned version)
2. `sdui_export_v*.py` in parent dir (latest by version)
3. `sdui_export_v*.py` in server dir

Hot reload: file changes trigger automatic module reload.

### Directory Structure

```
sdui/
├── sdui_export_v7.13.0.py        # Versioned transform modules
├── sdui_export_v7.12.0.py
├── Archive/                      # Deprecated versions
├── server/
│   ├── server.py                 # HTTP server with hot reload
│   └── sdui_export.py → ../...   # Symlink to active version
├── scripts/
│   ├── install.sh                # LaunchAgent installer
│   ├── set-version.sh            # Version manager
│   └── start.sh                  # Manual start
└── figma-plugin/
    ├── src/code.ts               # Plugin logic (style resolution)
    ├── src/ui.html               # Plugin UI
    └── dist/                     # Compiled output
```

## Key Concepts

### SDUI Component Recognition

Layer name prefixes determine component type:
- `LabelView`, `ButtonView`, `ImageView`, `TagView`, `IconView`
- `gap_*`, `spacer_*` → Spacer
- Auto-layout frames → StackView
- Frames with `divider`, `line`, `separator` in name → RectangleView

### Style Resolution Pipeline

**v7.13.0+ Critical Feature: Figma Style Metadata Fetching**

1. **Plugin Side** (`code.ts`):
   - Resolves `textStyleId` → style name via `figma.getStyleById()`
   - Resolves `fillStyleId`, `strokeStyleId` for colors
   - Sends `textStyleName`, `fillStyleName`, `strokeStyleName` to server

2. **Server Side** (`sdui_export.py`):
   - Fetches ALL styles metadata via `GET /v1/files/{file_key}` (cached)
   - Builds global `STYLE_CACHE: {style_id → style_name}`
   - Parses style names → SDUI tokens

### Typography Resolution

Pipeline: `textStyleId` → `figma.getStyleById()` → style name parsing → SDUI token

Style name patterns:
- `"Action/18–24 Primary Large"` → `ActionPrimaryLarge`
- `"Action/16–20 Component Primary"` → `ActionComponent`
- `"Headline/32-40 Medium"` → `HeadlineMedium`
- `"Paragraph/16–24 Primary Medium"` → `ParagraphPrimaryMedium`
- `"Body/Regular"` → `ParagraphPrimaryMedium`

Fallback: if no Text Style applied, server uses `(fontSize, fontWeight)` heuristics (less accurate).

**IMPORTANT:** Designers MUST apply Text Styles, not raw font properties.

### Color Resolution

1. Plugin sends `fillStyleName`/`strokeStyleName` (if style applied)
2. Server tries style name → token mapping
3. Fallback: HEX color → token via `HEX_TO_TOKEN` dict
4. Final fallback: raw HEX value

### Spacing Tokens
```
zero=0, xxxs=2, xxs=4, xs=8, s=12, m=16, l=20, xl=24, xxl=32
```

Schema loaded from `SDUI/Spacing.json` if `--schema-path` provided.

### Endpoints

- `GET /health` — Server status + loaded module info
- `POST /transform` — Transform Figma node data to SDUI JSON

Default port: `8787`. Change via `--port` flag and update `SERVER_URL` in `code.ts`.

## Standalone Usage

Without server (direct Figma API):
```bash
python3 sdui_export_v7.13.0.py <figma_url> --token <FIGMA_TOKEN>
python3 sdui_export_v7.13.0.py <url> --schema-path /path/to/SDUI
python3 sdui_export_v7.13.0.py <url> --infer-wrappers --mode layout
python3 sdui_export_v7.13.0.py <url> --no-cache  # Bypass cache
```

Token auto-loaded from `~/.env` if `FIGMA_TOKEN` defined.

### Export Modes

- `full` (default) — Complete SDUI JSON with all properties
- `layout` — Only structure: type, children, layout properties (no text/colors)
- `skeleton` — Minimal: type + children only
- `names` — Layer names only (for debugging component detection)

### Cache Management

Figma API responses cached in `~/.sdui_export_cache/`:
- Format: `{file_key}_{node_id}.json`
- Use `--no-cache` to bypass
- Speeds up repeated exports

## Troubleshooting

### Plugin Issues

**Typography not resolving correctly:**
- Check that Text Styles are applied in Figma (not raw font properties)
- Verify style names match patterns (e.g., "Action/18–24 Primary Large")
- Check plugin logs in Figma Dev Console

**Server not responding:**
```bash
./scripts/install.sh status     # Check if running
./scripts/install.sh restart    # Restart
tail -f ~/.sdui_logs/server.log # Check errors
```

**Style metadata not loading:**
- v7.13.0+ fetches ALL styles from Figma file on first request
- Check `~/.sdui_logs/debug.log` for API responses
- Verify `FIGMA_TOKEN` is valid

### Standalone Script Issues

**Authentication errors:**
```bash
# Check token is set
echo $FIGMA_TOKEN

# Or specify explicitly
python3 sdui_export_v7.13.0.py <url> --token <YOUR_TOKEN>
```

**Schema validation failures:**
```bash
# Verify schema path
python3 sdui_export_v7.13.0.py <url> --schema-path ~/Documents/front-middle-schema/SDUI
```

## Design Requirements

For accurate SDUI export:

1. **Text Styles REQUIRED** — Apply Text Styles, not raw font properties
2. **Color Styles RECOMMENDED** — Use color styles for consistent token mapping
3. **Component Naming** — Layer names must match: `LabelView`, `ButtonView`, etc.
4. **Auto-layout** — Use Figma auto-layout for StackView generation
5. **Spacing** — Gap/padding values should align with spacing tokens (0, 2, 4, 8, 12, 16, 20, 24, 32)

## ⛔ AI Fingerprints — ЗАПРЕЩЕНО

Никаких `Generated with`, `Co-Authored-By: Claude`, `🤖`, AI/LLM упоминаний.