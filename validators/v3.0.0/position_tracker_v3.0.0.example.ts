/**
 * Примеры использования Position Tracker v3.0.0
 *
 * @version 3.0.0
 * @author Claude Code
 * @date 2025-10-05
 */

import { PositionTracker } from './position_tracker_v3.0.0';

// ============================================================================
// ПРИМЕР 1: БАЗОВОЕ ИСПОЛЬЗОВАНИЕ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 1: Базовое использование');
console.log('='.repeat(60));
console.log('');

const simpleJson = `{
  "name": "Position Tracker v3.0.0",
  "version": "3.0.0",
  "features": {
    "json5": true,
    "caching": true,
    "patternMatching": true
  }
}`;

const tracker1 = new PositionTracker();
const map1 = tracker1.buildPositionMap(simpleJson);

console.log('Position Map построена:');
console.log(`  Всего строк: ${map1.totalLines}`);
console.log(`  Токенов: ${map1.stats.tokenCount}`);
console.log(`  Время парсинга: ${map1.stats.parseTimeMs.toFixed(2)}ms`);
console.log('');

// Поиск позиций
const nameLine = tracker1.findLineNumber('name');
const featureLine = tracker1.findLineNumber('features.json5');

console.log('Найденные позиции:');
console.log(`  "name": строка ${nameLine}`);
console.log(`  "features.json5": строка ${featureLine}`);
console.log('');

// Полная информация о позиции
const namePosition = tracker1.findPosition('name');
console.log('Полная информация о "name":');
console.log(`  Строка: ${namePosition?.line}`);
console.log(`  Колонка: ${namePosition?.column}`);
console.log(`  Смещение: ${namePosition?.offset}`);
console.log(`  Тип токена: ${namePosition?.tokenType}`);
console.log('');

// ============================================================================
// ПРИМЕР 2: JSON5 ПОДДЕРЖКА
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 2: JSON5 поддержка');
console.log('='.repeat(60));
console.log('');

const json5Sample = `{
  // Конфигурация приложения
  "appName": "My App",

  /*
   * Настройки сервера
   */
  "server": {
    "host": "localhost",
    "port": 3000, // Можно изменить
  },

  // Функции
  "features": [
    "auth",
    "api",
    "logging", // Последняя запятая разрешена
  ]
}`;

const tracker2 = new PositionTracker({
  json5Support: true
});

const map2 = tracker2.buildPositionMap(json5Sample);

console.log('JSON5 файл обработан:');
console.log(`  Комментариев найдено: ${map2.stats.commentCount}`);
console.log(`  Всего токенов: ${map2.stats.tokenCount}`);
console.log('');

const serverHostLine = tracker2.findLineNumber('server.host');
console.log(`Позиция "server.host": строка ${serverHostLine}`);
console.log('(Комментарии корректно проигнорированы)');
console.log('');

// ============================================================================
// ПРИМЕР 3: РАБОТА С МАССИВАМИ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 3: Работа с массивами');
console.log('='.repeat(60));
console.log('');

const arrayJson = `{
  "users": [
    {
      "id": 1,
      "name": "Alice",
      "roles": ["admin", "user"]
    },
    {
      "id": 2,
      "name": "Bob",
      "roles": ["user"]
    },
    {
      "id": 3,
      "name": "Charlie",
      "roles": ["moderator", "user"]
    }
  ]
}`;

const tracker3 = new PositionTracker({
  buildPatternIndex: true
});

tracker3.buildPositionMap(arrayJson);

// Точные пути
console.log('Точные пути:');
console.log(`  users[0].name: строка ${tracker3.findLineNumber('users[0].name')}`);
console.log(`  users[1].name: строка ${tracker3.findLineNumber('users[1].name')}`);
console.log(`  users[2].name: строка ${tracker3.findLineNumber('users[2].name')}`);
console.log('');

// Pattern matching
console.log('Pattern matching:');
const allNames = tracker3.findAllByPattern('users[*].name');
console.log(`  Найдено имен пользователей: ${allNames.length}`);
allNames.forEach((pos, index) => {
  console.log(`    ${index + 1}. Строка ${pos.line}`);
});
console.log('');

// Wildcard паттерны
const allIds = tracker3.findAllByPattern('*.id');
console.log(`  Все поля "id": ${allIds.length} шт.`);
console.log('');

// ============================================================================
// ПРИМЕР 4: КЭШИРОВАНИЕ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 4: Кэширование');
console.log('='.repeat(60));
console.log('');

PositionTracker.clearCache();

const largeJson = JSON.stringify(
  {
    items: Array.from({ length: 100 }, (_, i) => ({
      id: i,
      name: `Item ${i}`,
      value: i * 2
    }))
  },
  null,
  2
);

console.log('Первый запуск (без кэша):');
const tracker4a = new PositionTracker({
  enableCaching: true,
  filePath: '/test/large.json'
});

const start1 = performance.now();
const map4a = tracker4a.buildPositionMap(largeJson);
const time1 = performance.now() - start1;

console.log(`  Время: ${time1.toFixed(2)}ms`);
console.log(`  Размер файла: ${map4a.stats.fileSizeBytes} байт`);
console.log('');

console.log('Второй запуск (с кэшем):');
const tracker4b = new PositionTracker({
  enableCaching: true,
  filePath: '/test/large.json'
});

const start2 = performance.now();
const map4b = tracker4b.buildPositionMap(largeJson);
const time2 = performance.now() - start2;

console.log(`  Время: ${time2.toFixed(2)}ms`);
console.log(`  Ускорение: ${(time1 / time2).toFixed(0)}x`);
console.log('');

const cacheStats = PositionTracker.getCacheStats();
console.log('Статистика кэша:');
console.log(`  Размер: ${cacheStats.size} / ${cacheStats.maxSize}`);
console.log('');

// ============================================================================
// ПРИМЕР 5: FALLBACK К РОДИТЕЛЬСКОМУ ПУТИ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 5: Fallback к родительскому пути');
console.log('='.repeat(60));
console.log('');

const nestedJson = `{
  "component": {
    "type": "ButtonView",
    "content": {
      "textContent": {
        "text": "Click me"
      }
    }
  }
}`;

const tracker5 = new PositionTracker();
tracker5.buildPositionMap(nestedJson);

// Существующий путь
const existingPath = 'component.content.textContent.text';
const existingLine = tracker5.findLineNumber(existingPath);
console.log(`Существующий путь "${existingPath}":`);
console.log(`  Строка: ${existingLine}`);
console.log('');

// Несуществующий путь без fallback
const nonExistentPath = 'component.content.textContent.nonexistent.deep.path';
const noFallbackLine = tracker5.findLineNumber(nonExistentPath, '', {
  fallbackToParent: false
});
console.log(`Несуществующий путь без fallback:`);
console.log(`  Строка: ${noFallbackLine} (fallback на начало файла)`);
console.log('');

// Несуществующий путь с fallback
const withFallbackLine = tracker5.findLineNumber(nonExistentPath, '', {
  fallbackToParent: true
});
console.log(`Несуществующий путь с fallback:`);
console.log(`  Строка: ${withFallbackLine} (найден родительский путь "component.content.textContent")`);
console.log('');

// ============================================================================
// ПРИМЕР 6: ИНТЕГРАЦИЯ С ВАЛИДАТОРОМ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 6: Интеграция с валидатором');
console.log('='.repeat(60));
console.log('');

interface ValidationError {
  path: string;
  message: string;
  severity: 'error' | 'warning';
}

const contractJson = `{
  "type": "StackView",
  "id": "mainStack",
  "children": [
    {
      "type": "ButtonView",
      "content": {
        "textContent": {
          "text": "Submit"
        }
      },
      "actions": []
    }
  ]
}`;

const tracker6 = new PositionTracker({
  enableCaching: true,
  filePath: '/path/to/contract.json'
});

tracker6.buildPositionMap(contractJson);

// Имитация ошибок валидации
const errors: ValidationError[] = [
  {
    path: 'children[0].type',
    message: 'Неизвестный тип компонента',
    severity: 'error'
  },
  {
    path: 'children[0].actions',
    message: 'Массив actions пустой',
    severity: 'warning'
  },
  {
    path: 'children[0].content.textContent.text',
    message: 'Текст слишком короткий',
    severity: 'warning'
  }
];

console.log('Результаты валидации:');
console.log('');

for (const error of errors) {
  const position = tracker6.findPosition(error.path);

  if (position) {
    const icon = error.severity === 'error' ? '❌' : '⚠️';
    console.log(
      `${icon} ${error.severity.toUpperCase()} на строке ${position.line}:${position.column}`
    );
    console.log(`   Путь: ${error.path}`);
    console.log(`   Сообщение: ${error.message}`);
    console.log('');
  }
}

// ============================================================================
// ПРИМЕР 7: СЛОЖНЫЕ SDUI КОНТРАКТЫ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 7: Сложные SDUI контракты');
console.log('='.repeat(60));
console.log('');

const sduiContract = `{
  "type": "StackView",
  "children": [
    {
      "type": "TextContentView",
      "content": {
        "textContent": {
          "kind": "composite",
          "items": [
            {
              "text": "Hello",
              "style": {
                "fontSize": 16,
                "color": "#000000"
              }
            }
          ]
        }
      }
    },
    {
      "type": "ButtonView",
      "content": {
        "textContent": {
          "text": "Click"
        }
      },
      "actions": [
        {
          "type": "HttpAction",
          "url": "/api/submit",
          "method": "POST"
        },
        {
          "type": "NavigationAction",
          "destination": "/success"
        }
      ]
    }
  ]
}`;

const tracker7 = new PositionTracker({
  buildPatternIndex: true,
  includeTokenTypes: true
});

tracker7.buildPositionMap(sduiContract);

console.log('Анализ SDUI контракта:');
console.log('');

// Найти все типы компонентов
const allTypes = tracker7.findAllByPattern('*.type');
console.log(`Типы компонентов найдены: ${allTypes.length}`);
allTypes.forEach((pos, index) => {
  console.log(`  ${index + 1}. Строка ${pos.line} (тип токена: ${pos.tokenType})`);
});
console.log('');

// Найти все действия
const allActions = tracker7.findAllByPattern('*.actions[*].type');
console.log(`Действия найдены: ${allActions.length}`);
allActions.forEach((pos, index) => {
  console.log(`  ${index + 1}. Строка ${pos.line}`);
});
console.log('');

// Конкретные пути
const paths = [
  'children[0].content.textContent.items[0].style.fontSize',
  'children[1].actions[0].url',
  'children[1].actions[1].destination'
];

console.log('Конкретные поля:');
paths.forEach(path => {
  const line = tracker7.findLineNumber(path);
  console.log(`  ${path}: строка ${line}`);
});
console.log('');

// ============================================================================
// ПРИМЕР 8: ПРОИЗВОДИТЕЛЬНОСТЬ
// ============================================================================

console.log('='.repeat(60));
console.log('ПРИМЕР 8: Производительность');
console.log('='.repeat(60));
console.log('');

const sizes = [10, 100, 1000];

console.log('Тестирование производительности на разных размерах:');
console.log('');

for (const size of sizes) {
  const testJson = JSON.stringify(
    {
      items: Array.from({ length: size }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        data: { value: i * 2 }
      }))
    },
    null,
    2
  );

  const tracker = new PositionTracker({ enableCaching: false });

  const start = performance.now();
  const map = tracker.buildPositionMap(testJson);
  const buildTime = performance.now() - start;

  // Тест поиска
  const searchStart = performance.now();
  for (let i = 0; i < Math.min(100, size); i++) {
    tracker.findLineNumber(`items[${i}].name`);
  }
  const searchTime = performance.now() - searchStart;
  const avgSearchTime = searchTime / Math.min(100, size);

  console.log(`${size} элементов:`);
  console.log(`  Построение: ${buildTime.toFixed(2)}ms`);
  console.log(`  Размер: ${map.stats.fileSizeBytes} байт`);
  console.log(`  Токенов: ${map.stats.tokenCount}`);
  console.log(`  Средний поиск: ${avgSearchTime.toFixed(4)}ms`);
  console.log('');
}

// ============================================================================
// ЗАКЛЮЧЕНИЕ
// ============================================================================

console.log('='.repeat(60));
console.log('ЗАКЛЮЧЕНИЕ');
console.log('='.repeat(60));
console.log('');

console.log('Position Tracker v3.0.0 предоставляет:');
console.log('  ✓ Поддержка JSON5 (комментарии, trailing commas)');
console.log('  ✓ Кэширование для быстрого повторного доступа');
console.log('  ✓ Pattern matching с wildcards');
console.log('  ✓ Fallback к родительским путям');
console.log('  ✓ Расширенная информация о токенах');
console.log('  ✓ O(n) сложность построения, O(1) поиска');
console.log('  ✓ Поддержка файлов любого размера');
console.log('');

console.log('Рекомендации по использованию:');
console.log('  • Включайте кэширование для повторного использования');
console.log('  • Используйте pattern matching для массовых операций');
console.log('  • Включайте JSON5 поддержку только если нужна');
console.log('  • Используйте fallback для обработки ошибок');
console.log('');
