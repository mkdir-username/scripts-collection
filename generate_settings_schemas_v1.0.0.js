#!/usr/bin/env node
/**
 * Генератор json.schemas правил для settings.json
 * Создает отдельное правило для каждого компонента SDUI
 */

const fs = require('fs').promises;
const path = require('path');

const SDUI_ROOT = '/Users/username/Documents/front-middle-schema';

async function loadJson(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.warn(`⚠️  Пропущен: ${path.basename(filePath)}`);
    return null;
  }
}

async function findComponentSchemas(dir, componentList = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      await findComponentSchemas(fullPath, componentList);
    } else if (entry.isFile() && entry.name.endsWith('.json')) {
      const schema = await loadJson(fullPath);

      // Проверяем, что это схема компонента (имеет $schema и properties с type)
      if (schema?.$schema && schema?.properties?.type) {
        const relativePath = fullPath.replace(SDUI_ROOT + '/', './');
        const componentName = path.basename(entry.name, '.json');

        componentList.push({
          name: componentName,
          path: relativePath,
          fullPath: fullPath
        });
      }
    }
  }

  return componentList;
}

async function main() {
  console.log('🔍 Поиск всех схем компонентов...\n');

  const componentsDir = path.join(SDUI_ROOT, 'SDUI');
  const components = await findComponentSchemas(componentsDir);

  console.log(`✅ Найдено ${components.length} схем компонентов\n`);

  // Генерируем правила для settings.json
  const schemaRules = components.map(comp => ({
    fileMatch: [
      `**/${comp.name}/**/*.json`,
      `**/${comp.name}.json`,
      `**/*${comp.name}*.json`
    ],
    url: comp.path
  }));

  // Добавляем правило для контрактов (файлы с rootElement)
  schemaRules.unshift({
    fileMatch: [
      ".JSON/**/*.json"
    ],
    url: "./SDUI/contract/SDUIContract.json"
  });

  const output = {
    "json.schemas": schemaRules
  };

  const outputPath = path.join(SDUI_ROOT, 'Scripts/settings_schemas_rules.json');
  await fs.writeFile(outputPath, JSON.stringify(output, null, 2) + '\n', 'utf8');

  console.log(`📝 Создано ${schemaRules.length} правил`);
  console.log(`💾 Сохранено: ${outputPath}`);
  console.log('\n📋 Скопируйте содержимое в .vscode/settings.json');
}

main().catch(err => {
  console.error('❌ Ошибка:', err.message);
  process.exit(1);
});