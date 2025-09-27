# Python Scripts Organization
Version: 1.0.0
Date: 2025-01-27

## 📁 Directory Structure

```
/Users/username/Scripts/Python/
├── sdui/           # SDUI резолверы и API
├── refs/           # Утилиты для работы с $ref
├── utils/          # Общие утилиты
├── mcp/            # MCP интеграции
├── tests/          # Тестовые скрипты
├── archive/        # Архив старых версий
└── diff_watcher/   # Модуль diff_watcher (legacy)
```

## 📋 File Versioning Pattern

All files follow semantic versioning:
```
{base_name}_v{major}.{minor}.{patch}_{optional_desc}.py
```

## 🔗 Backward Compatibility

All original filenames are preserved as symbolic links pointing to versioned files.

## 📦 Categories

### SDUI Scripts (`sdui/`)
- `sdui_resolver_v2.0.0_enhanced.py` - Enhanced SDUI resolver
- `sdui_resolver_v1.2.0_final.py` - Final version of resolver
- `sdui_resolver_v1.1.0.py` - Stable resolver version
- `sdui_resolver_v1.0.0_fixed.py` - Initial fixed version
- `sdui_resolver_examples_v1.0.0.py` - Usage examples
- `sdui_api_demo_v1.0.0.py` - API demonstration
- `sdui_api_examples_v1.0.0.py` - API examples
- `sdui_agents_integration_v1.0.0.py` - Agents integration
- `sdui_validator_v1.0.0.py` - SDUI validator

### Refs Utilities (`refs/`)
- `fix_schema_refs_v1.0.0.py` - Fix schema references
- `fix_broken_refs_v1.0.0.py` - Fix broken $ref links
- `fix_extra_slash_v1.0.0.py` - Fix extra slashes in paths
- `fix_refs_missing_slash_v1.0.0.py` - Fix missing slashes
- `convert_to_absolute_refs_v1.0.0.py` - Convert to absolute refs
- `sdui_refs_manager_v1.0.0.py` - Refs management tool
- `sdui_refs_to_absolute_v1.0.0.py` - Convert SDUI refs to absolute
- `universal_refs_converter_v1.0.0.py` - Universal refs converter
- `validate_all_refs_v1.0.0.py` - Validate all references

### General Utilities (`utils/`)
- `generate_vscode_schemas_v1.0.0.py` - Generate VSCode schemas
- `jinja_hot_reload_v1.0.0.py` - Jinja template hot reload
- `performance_analyzer_v1.0.0.py` - Performance analysis tool
- `update_links_runner_v1.0.0.py` - Update links runner

### MCP Integration (`mcp/`)
- `mcp_sdui_extensions_v1.0.0.py` - MCP SDUI extensions

### Tests (`tests/`)
- `test_mcp_sdui_v1.0.0.py` - MCP SDUI tests
- `test_data_sdui_v1.0.0.py` - SDUI test data

## 🔧 Migration Notes

All scripts maintain backward compatibility through symbolic links.
No code changes required for existing imports.

## 📝 Version History

- **v1.0.0** (2025-01-27): Initial organization and versioning