#!/usr/bin/env node
/**
 * Упрощенный генератор JSON Schema для SDUI v2.4.0
 * Решает проблему зависания IntelliSense из-за глубокой рекурсии oneOf
 * Стратегия: базовая валидация + enum для type без полной проверки всех компонентов
 */

const fs = require('fs').promises;
const path = require('path');

const SDUI_ROOT = process.argv[2]
  ? path.dirname(process.argv[2]).replace(/\/SDUI.*$/, '')
  : '/Users/username/Documents/front-middle-schema';

async function loadJson(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.warn(`⚠️  Не удалось загрузить: ${filePath}`);
    return null;
  }
}

async function extractComponentNames() {
  const layoutContentPath = path.join(SDUI_ROOT, 'SDUI/common/LayoutElement/LayoutElementContent.json');
  const schema = await loadJson(layoutContentPath);

  if (!schema?.oneOf) {
    throw new Error('Не найден oneOf в LayoutElementContent.json');
  }

  const componentNames = schema.oneOf
    .map(item => item.$ref?.split('/').pop().replace('.json', ''))
    .filter(Boolean)
    .sort();

  console.log(`✅ Найдено ${componentNames.length} компонентов`);
  return componentNames;
}

async function main() {
  console.log('🔨 Генерация упрощенной SDUI Schema v2.4.0...\n');

  const componentNames = await extractComponentNames();

  // Упрощенная схема: базовая структура + enum для type
  const simplifiedSchema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SDUI Simplified Schema v2.4.0",
    "description": "Упрощенная схема без глубокой рекурсии для быстрого IntelliSense",
    "type": "object",
    "properties": {
      "$schema": {
        "type": "string",
        "description": "Ссылка на JSON Schema"
      },
      "version": {
        "type": "integer",
        "description": "Версия контракта",
        "default": 1
      },
      "rootElement": {
        "type": "object",
        "description": "Корневой UI элемент",
        "properties": {
          "type": {
            "type": "string",
            "enum": componentNames,
            "description": "Тип компонента"
          }
        },
        "required": ["type"],
        "additionalProperties": true
      },
      "type": {
        "type": "string",
        "enum": componentNames,
        "description": "Тип компонента (для отдельных компонентов без контракта)"
      },
      "data": {
        "type": "object",
        "description": "Статические данные контракта",
        "additionalProperties": true
      },
      "state": {
        "type": "object",
        "description": "Состояние контракта (runtime переменные)",
        "additionalProperties": true
      },
      "computed": {
        "type": "object",
        "description": "Вычисляемые свойства",
        "additionalProperties": true
      },
      "metadata": {
        "type": "object",
        "description": "Метаданные контракта",
        "additionalProperties": true
      }
    },
    "additionalProperties": true,
    "definitions": {
      "Component": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": componentNames,
            "description": "Тип компонента"
          }
        },
        "required": ["type"],
        "additionalProperties": true
      }
    }
  };

  const outputPath = path.join(SDUI_ROOT, 'Scripts/sdui_vscode_schema_v2.4.0_simplified.json');
  await fs.writeFile(outputPath, JSON.stringify(simplifiedSchema, null, 2) + '\n', 'utf8');

  console.log(`\n✅ Схема сохранена: ${outputPath}`);
  console.log(`📊 Компонентов в enum: ${componentNames.length}`);
  console.log(`📦 Размер: ${(JSON.stringify(simplifiedSchema).length / 1024).toFixed(1)} KB`);
  console.log('\n💡 Эта схема предоставляет:');
  console.log('   ✓ Быстрый IntelliSense без зависания');
  console.log('   ✓ Автодополнение для type (55 компонентов)');
  console.log('   ✓ Базовую валидацию структуры контракта');
  console.log('   ✗ НЕ проверяет специфичные свойства каждого компонента');
}

main().catch(err => {
  console.error('❌ Ошибка:', err.message);
  process.exit(1);
});