# Active Scripts

> Текущие версии активно используемых скриптов

## Скрипты

### jinja_hot_reload.py
**Symlink на**: `../Python/utils/jinja_hot_reload_v3.6.0.py`  
**Версия**: 3.6.0  
**Назначение**: Парсинг Jinja2-JSON контрактов

**Использование**:
```bash
python ~/Scripts/active/jinja_hot_reload.py
# Или
cd /Users/username/Documents/FMS_GIT/_JSON/WEB/feature/desktop/
python ~/Scripts/active/jinja_hot_reload.py
```

---

### validate_sdui.py
**Symlink на**: `../validators/v3.0.0/sdui_web_validator_v3.0.0.py`  
**Версия**: 3.0.0  
**Назначение**: Валидация SDUI контрактов

**Использование**:
```bash
python ~/Scripts/active/validate_sdui.py <contract.json>
```

---

## Зачем symlinks?

1. **Простота использования** - короткий путь
2. **Стабильность** - всегда актуальная версия
3. **Обратная совместимость** - не ломает старый код

## Обновление

Чтобы обновить на новую версию:

```bash
cd ~/Scripts/active
rm jinja_hot_reload.py
ln -sf ../Python/utils/jinja_hot_reload_v3.7.0.py jinja_hot_reload.py
```

