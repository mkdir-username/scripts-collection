# Инструкции по настройке MCP после перемещения alfa-sdui-mcp

## ✅ Выполнено

1. ✅ alfa-sdui-mcp перемещён из `/Users/username/Documents/front-middle-schema/alfa-sdui-mcp` в `/Users/username/Scripts/alfa-sdui-mcp`
2. ✅ Обновлены пути MCP_ROOT во всех vscode-validate скриптах
3. ✅ Создана MCP конфигурация для front-middle-schema проекта

## 📍 Новый путь
```
/Users/username/Scripts/alfa-sdui-mcp
```

## 🔧 MCP конфигурация

Создан файл: `/Users/username/Documents/front-middle-schema/.claude/mcp.json`

```json
{
  "mcpServers": {
    "sdui-schema": {
      "command": "node",
      "args": [
        "/Users/username/Scripts/alfa-sdui-mcp/dist/index.js"
      ],
      "env": {
        "SDUI_SCHEMA_PATH": "/Users/username/Documents/front-middle-schema/SDUI"
      },
      "description": "Alfa SDUI MCP Server - intelligent tools for SDUI contract creation with line-level incremental validation"
    }
  }
}
```

## ✅ Проверка подключения

### 1. Проверить список MCP серверов в Claude Code

В front-middle-schema проекте выполните команду:
```bash
/mcp
```

Должен отобразиться сервер **sdui-schema** со списком инструментов:
- `check_component_availability`
- `validate_contract_incremental`
- `convert_to_web`
- `resolve_schema_ref`
- `apply_state_aware`
- `find_alternative_component`
- `build_contract_step`
- `get_web_components`
- `validate_stateaware`

### 2. Проверить работу MCP сервера

Попробуйте использовать инструмент в Claude Code:
```
Проверь доступность компонента ButtonView для web платформы
```

Claude Code должен использовать `mcp__sdui-schema__check_component_availability` инструмент.

## 🔄 Обновлённые файлы

### Scripts репозиторий
- `vscode-validate-on-save_v1.1.0.js`
- `vscode-validate-on-save_v2.0.0.js`
- `vscode-validate-on-save_v2.0.0.ts`
- `vscode-validate-on-save_v2.1.0.ts`
- `alfa-sdui-mcp/scripts/vscode-validate-on-save_v2.0.0.ts`

### front-middle-schema репозиторий
- `.claude/mcp.json` (новый файл)
- `.claude/settings.local.json` (существующий, не изменён)

## 🛠️ Troubleshooting

### MCP сервер не отображается

1. **Перезапустите Claude Code**
   ```bash
   # Выйдите из текущей сессии и откройте новую
   cd /Users/username/Documents/front-middle-schema
   claude
   ```

2. **Проверьте права доступа**
   ```bash
   chmod +x /Users/username/Scripts/alfa-sdui-mcp/dist/index.js
   ```

3. **Проверьте наличие dist/**
   ```bash
   ls -la /Users/username/Scripts/alfa-sdui-mcp/dist/
   ```

   Если dist/ отсутствует:
   ```bash
   cd /Users/username/Scripts/alfa-sdui-mcp
   npm install
   npm run build
   ```

### MCP сервер подключается, но инструменты не работают

1. **Проверьте SDUI_SCHEMA_PATH**
   ```bash
   ls -la /Users/username/Documents/front-middle-schema/SDUI
   ```
   Должна существовать директория с JSON схемами.

2. **Проверьте логи MCP сервера**
   Логи доступны в Claude Code консоли (обычно в терминале где запущен).

### vscode-validate скрипты не находят MCP сервер

Проверьте путь:
```bash
cat /Users/username/Scripts/vscode-validate-on-save_v2.1.0.ts | grep MCP_ROOT
```

Должно быть:
```typescript
const MCP_ROOT = '/Users/username/Scripts/alfa-sdui-mcp';
```

## 📚 Документация

- **alfa-sdui-mcp README**: `/Users/username/Scripts/alfa-sdui-mcp/README.md`
- **Claude Code MCP docs**: https://docs.claude.com/en/docs/claude-code/mcp
- **MCP SDK docs**: https://github.com/modelcontextprotocol/typescript-sdk

## ✨ Следующие шаги

1. Запустите Claude Code в front-middle-schema проекте
2. Выполните `/mcp` для проверки подключения
3. Протестируйте инструменты SDUI MCP сервера
4. При необходимости настройте дополнительные параметры в `.claude/mcp.json`

---

**Дата создания:** 2025-10-02
**Версия:** 1.0.0
**Автор:** Claude Code CLI
