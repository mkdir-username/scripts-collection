#!/usr/bin/env node

/**
 * Удаление объектов по точному совпадению ключ-значение
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');

/**
 * Рекурсивно удаляет объекты, содержащие указанную пару ключ-значение
 * @param {any} data - Данные для обработки
 * @param {string} targetKey - Искомый ключ
 * @param {any} targetValue - Искомое значение
 * @returns {any} Очищенные данные
 */
function removeObjectsByKeyValue(data, targetKey, targetValue) {
  // Обработка массивов
  if (Array.isArray(data)) {
    return data
      .filter(item => {
        // Если элемент - объект, проверяем наличие целевой пары
        if (item && typeof item === 'object') {
          return item[targetKey] !== targetValue;
        }
        return true;
      })
      .map(item => removeObjectsByKeyValue(item, targetKey, targetValue));
  }

  // Обработка объектов
  if (data && typeof data === 'object') {
    // Если текущий объект содержит целевую пару - возвращаем null для удаления
    if (data[targetKey] === targetValue) {
      return null;
    }

    // Рекурсивно обрабатываем все свойства
    const result = {};
    for (const [key, value] of Object.entries(data)) {
      const processed = removeObjectsByKeyValue(value, targetKey, targetValue);
      // Не добавляем null значения (удаленные объекты)
      if (processed !== null) {
        result[key] = processed;
      }
    }
    return result;
  }

  // Примитивные значения возвращаем как есть
  return data;
}

/**
 * Главная функция
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.error('Использование: node remove_objects_v1.0.0.js <input.json> <key> <value> [output.json]');
    console.error('Пример: node remove_objects_v1.0.0.js input.json name "🔩 SwapMe" output.json');
    process.exit(1);
  }

  const inputFile = args[0];
  const targetKey = args[1];
  const targetValue = args[2];
  const outputFile = args[3] || inputFile.replace('.json', '_cleaned.json');

  try {
    // Читаем входной файл
    const rawData = fs.readFileSync(inputFile, 'utf8');
    const data = JSON.parse(rawData);

    console.log(`🔍 Поиск объектов с ${targetKey}="${targetValue}"...`);

    // Удаляем объекты
    const cleaned = removeObjectsByKeyValue(data, targetKey, targetValue);

    // Сохраняем результат
    fs.writeFileSync(outputFile, JSON.stringify(cleaned, null, 2), 'utf8');

    console.log(`✅ Готово! Результат сохранен в: ${outputFile}`);

    // Статистика
    const originalSize = Buffer.byteLength(rawData, 'utf8');
    const cleanedSize = Buffer.byteLength(JSON.stringify(cleaned, null, 2), 'utf8');
    const savedBytes = originalSize - cleanedSize;

    console.log(`📊 Статистика:`);
    console.log(`   Исходный размер: ${(originalSize / 1024).toFixed(2)} KB`);
    console.log(`   Новый размер: ${(cleanedSize / 1024).toFixed(2)} KB`);
    console.log(`   Сокращено: ${(savedBytes / 1024).toFixed(2)} KB (${((savedBytes / originalSize) * 100).toFixed(1)}%)`);

  } catch (error) {
    console.error('❌ Ошибка:', error.message);
    process.exit(1);
  }
}

// Экспорт для использования как модуль
if (require.main === module) {
  main();
} else {
  module.exports = { removeObjectsByKeyValue };
}
