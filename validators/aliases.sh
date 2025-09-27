#!/bin/bash

# Алиасы для быстрого запуска валидаторов SDUI

# Основной валидатор v2.0.0
alias validate-sdui='python /Users/username/Scripts/validators/v2.0.0/sdui_web_validator_v2.0.0_advanced_lines.py'

# Предыдущие версии
alias validate-sdui-v1.0='python /Users/username/Scripts/validators/v1.x.x/sdui_web_validator_v1.0.0.py'
alias validate-sdui-v1.1='python /Users/username/Scripts/validators/v1.x.x/sdui_web_validator_v1.1.0.py'
alias validate-sdui-v1.2='python /Users/username/Scripts/validators/v1.x.x/sdui_web_validator_v1.2.0_with_lines.py'

# Специализированные валидаторы
alias validate-byzantine='python /Users/username/Scripts/validators/specialized/byzantine_validator.py'
alias validate-visual='python /Users/username/Scripts/validators/specialized/sdui_visual_validator.py'
alias validate-cli='python /Users/username/Scripts/validators/specialized/agent_validate_cli.py'
alias validate-terminal='python /Users/username/Scripts/validators/specialized/agent_terminal_validator.py'
alias validate-contract='python /Users/username/Scripts/validators/specialized/sdui_contract_validator.py'
alias validate-pipeline='python /Users/username/Scripts/validators/specialized/validation_pipeline.py'

# Простые валидаторы
alias validate-simple='python /Users/username/Scripts/validators/basic/simple_validator.py'
alias validate-root='python /Users/username/Scripts/validators/basic/validate_root_element.py'
alias validate-compat='python /Users/username/Scripts/validators/basic/check_validator_compatibility.py'

# Тестирование
alias test-validators='python /Users/username/Scripts/validators/test_validators.py'

echo "✅ SDUI валидаторы загружены. Используйте команды:"
echo "  validate-sdui <file>     - Основной валидатор v2.0.0"
echo "  validate-visual <file>   - Визуальный валидатор"
echo "  validate-byzantine <file> - Byzantine валидатор"
echo "  validate-simple <file>   - Простой валидатор"
echo "  test-validators          - Запуск тестов"