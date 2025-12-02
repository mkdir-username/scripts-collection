# Figma MCP Rate Limiter

Защита от перелимита Figma API через AI-агенты.

## Что делает

- **Rate Limiting**: max 8 запросов/минуту (безопасно для personal tokens)
- **Кеширование**: 5 минут для идентичных запросов
- **Логирование**: `~/.figma_mcp_wrapper.log`

## Как работает

AI-агенты → wrapper → rate limit check → cache check → Figma API

## Мониторинг

```bash
# Статистика
~/Scripts/figma-mcp-stats.sh

# Live лог
tail -f ~/.figma_mcp_wrapper.log

# Очистка
rm ~/.figma_mcp_wrapper.log
rm -rf ~/.figma_mcp_cache
```

## Активация

**Требуется перезапуск Claude Code** для применения новой конфигурации.

## Настройка

Файл: `/Users/username/Scripts/figma-mcp-wrapper.js`

```js
const MAX_REQUESTS_PER_MINUTE = 8;  // Изменить лимит
const CACHE_TTL_MS = 5 * 60 * 1000; // Изменить время кеша
```

## Отключение

В `.mcp.json` вернуть прямой вызов:
```json
"command": "/path/to/npx",
"args": ["-y", "figma-developer-mcp", "--stdio"]
```
