#!/usr/bin/env node
/**
 * Генератор полной и валидной JSON Schema для SDUI (v2.3.0+)
 * На основе реальных схем компонентов из репозитория
 */

const fs = require('fs').promises;
const path = require('path');

// Путь к корню схем SDUI: из аргумента или по умолчанию
const SDUI_ROOT = process.argv[2]
  ? path.dirname(process.argv[2]).replace(/\/SDUI.*$/, '')
  : '/Users/username/Documents/front-middle-schema';

async function loadJson(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (err) {
    console.warn(`⚠️  Не удалось загрузить: ${filePath} — ${err.message}`);
    return null;
  }
}

// Рекурсивно нормализует схему: убирает лишние поля, оставляет только нужное для JSON Schema
function extractSchemaFragment(schema, depth = 0) {
  if (!schema || typeof schema !== 'object') return schema;

  // Защита от слишком глубокой рекурсии
  if (depth > 10) return schema;

  // Убираем поля, не относящиеся к JSON Schema
  const {
    name,
    description,
    releaseVersion,
    required,
    properties,
    type,
    enum: enumVal,
    $ref,
    items,
    format,
    default: def,
    oneOf,
    anyOf,
    allOf,
    additionalProperties,
    ...rest
  } = schema;

  const result = {};
  if (type !== undefined) result.type = type;
  if (enumVal !== undefined) result.enum = enumVal;

  // Обработка $ref
  if ($ref !== undefined) {
    // Если это file:// ссылка, заменяем на AnyComponent (предотвращает зависание IntelliSense)
    if ($ref.startsWith('file://')) {
      result.$ref = '#/definitions/AnyComponent';
    }
    // Если это внутренняя ссылка #/definitions/..., сохраняем как есть
    else if ($ref.startsWith('#/definitions/')) {
      result.$ref = $ref;
    }
    // Для остальных случаев тоже сохраняем
    else {
      result.$ref = $ref;
    }
  }

  if (items !== undefined) {
    // Для массивов компонентов используем AnyComponent
    const extractedItems = extractSchemaFragment(items, depth + 1);
    if (extractedItems.$ref && extractedItems.$ref.includes('/')) {
      result.items = { $ref: '#/definitions/AnyComponent' };
    } else {
      result.items = extractedItems;
    }
  }

  if (format !== undefined) result.format = format;
  if (def !== undefined) result.default = def;
  if (description !== undefined) result.description = description;
  if (oneOf !== undefined) result.oneOf = oneOf.map((s) => extractSchemaFragment(s, depth + 1));
  if (anyOf !== undefined) result.anyOf = anyOf.map((s) => extractSchemaFragment(s, depth + 1));
  if (allOf !== undefined) result.allOf = allOf.map((s) => extractSchemaFragment(s, depth + 1));
  if (additionalProperties !== undefined) result.additionalProperties = additionalProperties;

  if (properties) {
    result.properties = {};
    for (const [key, value] of Object.entries(properties)) {
      // Специальная обработка для свойств, содержащих компоненты
      if (key === 'children' || key === 'content' || key === 'rootElement' ||
          key === 'leftAddon' || key === 'rightAddon' || key === 'header' || key === 'footer') {
        const extracted = extractSchemaFragment(value, depth + 1);
        // Если это ссылка на компонент, заменяем на AnyComponent
        if (extracted.$ref && extracted.$ref.includes('/')) {
          result.properties[key] = { $ref: '#/definitions/AnyComponent' };
        } else {
          result.properties[key] = extracted;
        }
      } else {
        result.properties[key] = extractSchemaFragment(value, depth + 1);
      }
    }
  }

  // required — особый случай: он должен быть на том же уровне, что и properties
  if (required !== undefined && Array.isArray(required)) {
    result.required = required;
  }

  return result;
}

// Основная функция генерации
async function generateSchema() {
  console.log('🔨 Генерация полной SDUI JSON Schema v2.3.0...\n');

  // 1. Загружаем LayoutElementContent, чтобы получить список всех компонентов
  const layoutContentPath = path.join(
    SDUI_ROOT,
    'SDUI',
    'common',
    'LayoutElement',
    'LayoutElementContent.json'
  );
  const layoutContent = await loadJson(layoutContentPath);
  if (!layoutContent?.oneOf) {
    throw new Error(`Не найден LayoutElementContent.json или отсутствует oneOf`);
  }

  const componentMap = new Map(); // имя компонента → путь к файлу
  for (const item of layoutContent.oneOf) {
    if (item.value && item.$ref) {
      // Пример: "$ref": "file:///.../ButtonView.json"
      const url = new URL(item.$ref);
      const fullPath = url.pathname; // Unix-путь
      // Преобразуем абсолютный путь в относительный от SDUI_ROOT
      const relativePath = path.relative(SDUI_ROOT, fullPath);
      componentMap.set(item.value, relativePath);
    }
  }

  const allComponents = Array.from(componentMap.keys()).sort();
  console.log(`📦 Найдено ${allComponents.length} компонентов`);

  // 2. Генерируем отдельные определения для каждого компонента (для oneOf)
  const componentDefinitions = {};
  const sharedDefinitions = {}; // Для enum'ов и вспомогательных типов

  for (const componentName of allComponents) {
    const schemaPath = componentMap.get(componentName);
    const schema = await loadJson(path.join(SDUI_ROOT, schemaPath));

    if (!schema) {
      console.warn(`  ⚠️  Пропущен: ${componentName}`);
      continue;
    }

    // Извлекаем definitions из схемы компонента (enum'ы, вспомогательные типы)
    if (schema.definitions) {
      for (const [defName, defValue] of Object.entries(schema.definitions)) {
        // Пропускаем определения компонентов (они уже будут добавлены)
        if (!allComponents.includes(defName) && !sharedDefinitions[defName]) {
          sharedDefinitions[defName] = extractSchemaFragment(defValue);
        }
      }
    }

    // Извлекаем корневые properties и required из схемы компонента
    const fragment = extractSchemaFragment(schema);

    // Создаём определение компонента с const для type
    const componentDef = {
      type: 'object',
      properties: {
        type: {
          const: componentName,
          description: `Компонент ${componentName}`
        }
      },
      required: ['type'],
      additionalProperties: true
    };

    // Переносим properties и required из схемы компонента
    if (fragment.properties) {
      componentDef.properties = { ...componentDef.properties, ...fragment.properties };
    }
    if (fragment.required && Array.isArray(fragment.required)) {
      componentDef.required = [
        ...new Set([...(componentDef.required || []), ...fragment.required])
      ];
    }

    componentDefinitions[componentName] = componentDef;
    console.log(`  ✅ ${componentName}`);
  }

  console.log(`\n📚 Извлечено ${Object.keys(sharedDefinitions).length} общих определений`);

  // 3. Формируем базовые определения (цвета, отступы и т.д.)
  const baseDefinitions = {
    Spacing: {
      type: 'string',
      enum: [
        'zero',
        'xxxxs',
        'xxxs',
        'xxs',
        'xs2xs',
        'xs',
        'xss',
        's',
        'm',
        'l',
        'xl',
        'xxl',
        'xxxl',
        'xxxxl',
        'xxxxxl',
        'xxxxxxl',
        'horizontalMargin',
        'extendedHorizontalMargin'
      ],
      description: 'Токены отступов из дизайн-системы'
    },
    Color: {
      oneOf: [
        { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
        {
          type: 'string',
          enum: [
            'textColorPrimary',
            'textColorPrimaryInverted',
            'textColorSecondary',
            'textColorSecondaryInverted',
            'textColorTertiary',
            'textColorTertiaryInverted',
            'textColorQuaternary',
            'textColorQuaternaryInverted',
            'textColorAccent',
            'textColorLink',
            'textColorLinkInverted',
            'textColorNegative',
            'textColorPositive',
            'textColorAttention',
            'textColorParagraph',
            'textColorParagraphInverted',
            'backgroundColorPrimary',
            'backgroundColorPrimaryInverted',
            'backgroundColorSecondary',
            'backgroundColorSecondaryInverted',
            'backgroundColorTertiary',
            'backgroundColorTertiaryInverted',
            'backgroundColorAccent',
            'backgroundColorComponent',
            'backgroundColorComponentInverted',
            'backgroundColorNegativeMuted',
            'backgroundColorPositiveMuted',
            'backgroundColorAttentionMuted',
            'backgroundColorInfoMuted',
            'backgroundColorLinkMuted',
            'backgroundColorNeutral',
            'borderColorPrimary',
            'borderColorPrimaryInverted',
            'borderColorSecondary',
            'borderColorSecondaryInverted',
            'borderColorTertiary',
            'borderColorTertiaryInverted',
            'borderColorAccent',
            'borderColorLink',
            'borderColorKey',
            'borderColorKeyInverted',
            'graphicColorPrimary',
            'graphicColorSecondary',
            'graphicColorTertiary',
            'graphicColorQuaternary',
            'clear',
            'staticGraphicColorBlueMaya',
            'staticGraphicColorRed',
            'staticGraphicColorGreen',
            'staticGraphicColorOrange',
            'staticGraphicColorPurple',
            'staticGraphicColorYellow'
          ]
        }
      ],
      description: 'Цвет из палитры или hex'
    },
    Typography: {
      type: 'string',
      enum: [
        'HeadlineXLarge',
        'HeadlineLarge',
        'HeadlineMedium',
        'HeadlineSmall',
        'HeadlineXSmall',
        'PromoXLarge',
        'PromoLarge',
        'PromoMedium',
        'PromoSmall',
        'PromoXSmall',
        'ParagraphPrimaryLarge',
        'ParagraphPrimaryMedium',
        'ParagraphPrimarySmall',
        'ParagraphSecondaryLarge',
        'ParagraphSecondaryMedium',
        'ParagraphSecondarySmall',
        'ParagraphComponent',
        'ParagraphComponentSecondary',
        'ParagraphTagline',
        'ParagraphCaps',
        'ActionPrimaryLarge',
        'ActionPrimaryMedium',
        'ActionPrimarySmall',
        'ActionSecondaryLarge',
        'ActionSecondaryMedium',
        'ActionSecondarySmall',
        'ActionComponent'
      ]
    },
    Action: {
      type: 'object',
      properties: {
        type: { type: 'string' },
        url: { type: 'string' },
        key: { type: 'string' },
        source: {},
        version: { type: 'number' }
      }
    }
    // Добавьте другие общие определения по мере необходимости
  };

  // 4. Собираем ЕДИНУЮ универсальную схему для контрактов И компонентов
  const universalSchema = {
    $schema: 'http://json-schema.org/draft-07/schema#',
    title: 'SDUI Universal Schema with VS Code IntelliSense',
    description: 'Единая схема для всех SDUI JSON: контрактов, экранов и компонентов',
    oneOf: [
      // Вариант 1: Полный контракт (с rootElement)
      { $ref: '#/definitions/SDUIContract' },
      // Вариант 2: Отдельный компонент
      { $ref: '#/definitions/AnyComponent' }
    ],
    definitions: {
      SDUIContract: {
        type: 'object',
        required: ['rootElement'],
        properties: {
          $schema: {
            type: 'string',
            description: 'Ссылка на JSON Schema'
          },
          version: {
            type: 'integer',
            description: 'Версия контракта'
          },
          rootElement: {
            $ref: '#/definitions/AnyComponent',
            description: 'Корневой элемент UI (должен содержать type)'
          },
          data: {
            type: 'object',
            description: 'Статические данные контракта',
            additionalProperties: true
          },
          state: {
            type: 'object',
            description: 'Состояние контракта (runtime переменные)',
            additionalProperties: true
          },
          computed: {
            type: 'object',
            description: 'Вычисляемые свойства',
            additionalProperties: true
          },
          metadata: {
            type: 'object',
            description: 'Метаданные контракта',
            additionalProperties: true
          }
        },
        additionalProperties: false
      },
      AnyComponent: {
        oneOf: allComponents.map((name) => ({
          $ref: `#/definitions/${name}`
        }))
      },
      ...componentDefinitions,
      ...sharedDefinitions,
      ...baseDefinitions
    }
  };

  // 5. Сохраняем единую схему
  const schemaPath = path.join(SDUI_ROOT, 'SDUI', 'sdui_vscode_schema_v2.3.0.json');
  await fs.writeFile(schemaPath, JSON.stringify(universalSchema, null, 2), 'utf8');

  const schemaStats = await fs.stat(schemaPath);
  console.log(`\n✅ Единая схема сохранена: ${schemaPath}`);
  console.log(`📏 Размер: ${(schemaStats.size / 1024).toFixed(2)} KB`);
  console.log(`🧩 Компонентов: ${allComponents.length}`);

  // Также сохраняем копию в Scripts для обратной совместимости
  const legacyPath = path.join(__dirname, 'sdui_vscode_schema_v2.3.0.json');
  await fs.writeFile(legacyPath, JSON.stringify(universalSchema, null, 2), 'utf8');
  console.log(`✅ Копия сохранена в Scripts: ${legacyPath}`);
}

generateSchema().catch((err) => {
  console.error('❌ Ошибка:', err);
  process.exit(1);
});
