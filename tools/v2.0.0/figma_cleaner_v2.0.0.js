#!/usr/bin/env node

/**
 * Figma Data Cleaner - убирает лишние метаданные
 * Использование: node figma-cleaner.js <figma-response.json>
 */

function cleanFigmaData(data, options = {}) {
  const {
    includeStyles = false,      // Включать ли globalVars/styles
    includeComponents = false,   // Включать ли components/componentSets
    maxDepth = 2,               // Максимальная глубина
    fieldsToKeep = [            // Какие поля оставить
      'id', 'name', 'type',
      'padding', 'gap', 'spacing',
      'mode', 'sizing', 'borderRadius'
    ]
  } = options;

  // Рекурсивная очистка нод
  function cleanNode(node, depth = 0) {
    if (!node || depth >= maxDepth) return null;

    const cleaned = {};

    // Базовые поля
    if (node.id) cleaned.id = node.id;
    if (node.name) cleaned.name = node.name;
    if (node.type) cleaned.type = node.type;

    // Layout информация (отступы)
    if (node.layout) {
      cleaned.layout = {};
      ['padding', 'gap', 'spacing', 'mode', 'sizing', 'alignItems', 'justifyContent']
        .forEach(field => {
          if (node.layout[field]) {
            cleaned.layout[field] = node.layout[field];
          }
        });

      // Парсим padding в читаемый формат
      if (typeof cleaned.layout.padding === 'string') {
        const paddings = cleaned.layout.padding.split(' ').map(p => p.replace('px', ''));
        cleaned.layout.paddingTop = paddings[0];
        cleaned.layout.paddingRight = paddings[1] || paddings[0];
        cleaned.layout.paddingBottom = paddings[2] || paddings[0];
        cleaned.layout.paddingLeft = paddings[3] || paddings[1] || paddings[0];
      }
    }

    // Размеры
    if (node.dimensions) {
      cleaned.dimensions = node.dimensions;
    }

    // Borders
    if (node.borderRadius) {
      cleaned.borderRadius = node.borderRadius;
    }

    // Рекурсивно чистим детей
    if (node.children && node.children.length > 0) {
      cleaned.children = node.children
        .map(child => cleanNode(child, depth + 1))
        .filter(Boolean);
    }

    return cleaned;
  }

  // Результат
  const result = {
    metadata: {
      name: data.metadata?.name,
      lastModified: data.metadata?.lastModified,
      componentsCount: Object.keys(data.components || {}).length,
      stylesCount: Object.keys(data.globalVars?.styles || {}).length
    },
    structure: []
  };

  // Обрабатываем ноды
  if (data.nodes && Array.isArray(data.nodes)) {
    result.structure = data.nodes.map(node => cleanNode(node));
  }

  // Опционально добавляем компоненты (только названия)
  if (includeComponents && data.components) {
    result.componentNames = Object.values(data.components).map(c => ({
      id: c.id,
      name: c.name
    }));
  }

  // Статистика
  result.stats = {
    originalSize: JSON.stringify(data).length,
    cleanedSize: JSON.stringify(result).length,
    reduction: `${Math.round((1 - JSON.stringify(result).length / JSON.stringify(data).length) * 100)}%`
  };

  return result;
}

// CLI интерфейс
if (require.main === module) {
  const fs = require('fs');
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Использование: node figma-cleaner.js <input.json> [output.json]');
    console.log('Опции можно настроить в коде');
    process.exit(1);
  }

  const inputFile = args[0];
  const outputFile = args[1] || 'cleaned-' + inputFile;

  try {
    const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
    const cleaned = cleanFigmaData(data, {
      includeStyles: false,
      includeComponents: false,
      maxDepth: 2
    });

    fs.writeFileSync(outputFile, JSON.stringify(cleaned, null, 2));

    console.log(`✅ Очищено: ${cleaned.stats.reduction} сокращение`);
    console.log(`📁 Сохранено в: ${outputFile}`);
    console.log(`📊 Структура: ${cleaned.structure.length} top-level нод`);

  } catch (error) {
    console.error('❌ Ошибка:', error.message);
    process.exit(1);
  }
}

module.exports = { cleanFigmaData };