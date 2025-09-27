# 🛠️ Scripts Collection

A comprehensive collection of Python and Bash scripts for SDUI validation, schema management, and development automation.

## 📁 Repository Structure

```
Scripts/
├── Python/                 # Python scripts and utilities
│   ├── sdui/              # SDUI resolvers and API tools
│   ├── refs/              # Reference ($ref) management utilities
│   ├── utils/             # General utilities
│   ├── mcp/               # MCP integrations
│   ├── tests/             # Test scripts
│   └── diff_watcher/      # Diff watching module
├── bash/                   # Bash scripts
│   ├── validators/        # Validation scripts
│   ├── git/              # Git utilities
│   ├── json/             # JSON processing
│   └── utils/            # General bash utilities
└── validators/             # SDUI Web validators
    ├── v1.0.0/           # Version 1.0.0
    ├── v1.1.0/           # Version 1.1.0
    ├── v1.2.0/           # Version 1.2.0 with line detection
    ├── v2.0.0/           # Version 2.0.0 advanced
    └── current/          # Symlinks to latest versions
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Bash 4.0+
- Git
- jq (for JSON processing)

### Installation

```bash
git clone https://github.com/username/scripts.git
cd scripts
pip install -r Python/requirements.txt
```

## 📦 Main Components

### 🔍 SDUI Web Validators

Advanced validators for checking SDUI JSON contracts compatibility with web platform.

**Latest version:** `v2.0.0`

```bash
python validators/current/sdui_web_validator.py contract.json
```

### 🔗 Reference Management Tools

Tools for managing and fixing `$ref` references in JSON schemas.

```bash
python Python/refs/universal_refs_converter_v1.0.0.py --help
```

### 🎯 SDUI Resolvers

Advanced SDUI schema resolvers with caching and optimization.

```bash
python Python/sdui/sdui_resolver_v2.0.0_enhanced.py
```

## 📋 Versioning

All scripts follow semantic versioning:
```
{name}_v{major}.{minor}.{patch}_{optional_desc}.{ext}
```

## 🔗 Backward Compatibility

All scripts maintain backward compatibility through symbolic links.

## 📊 Statistics

- **Python Scripts:** 25 scripts
- **Bash Scripts:** 15 scripts
- **Validators:** 4 versions
- **Total Tools:** 40+ utilities

## 📝 License

MIT License

## 👤 Author

**Your Name**
- GitHub: [@username](https://github.com/username)

---

⭐️ If you find this collection useful, please consider giving it a star!
