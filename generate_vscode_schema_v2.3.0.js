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
function extractSchemaFragment(schema) {
  if (!schema || typeof schema !== 'object') return schema;

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
    ...rest
  } = schema;

  const result = {};
  if (type !== undefined) result.type = type;
  if (enumVal !== undefined) result.enum = enumVal;
  if ($ref !== undefined) result.$ref = $ref;
  if (items !== undefined) result.items = extractSchemaFragment(items);
  if (format !== undefined) result.format = format;
  if (def !== undefined) result.default = def;
  if (description !== undefined) result.description = description;

  if (properties) {
    result.properties = {};
    for (const [key, value] of Object.entries(properties)) {
      result.properties[key] = extractSchemaFragment(value);
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

  // 2. Генерируем определения для каждого компонента
  const componentConditions = [];

  for (const componentName of allComponents) {
    const schemaPath = componentMap.get(componentName);
    const schema = await loadJson(path.join(SDUI_ROOT, schemaPath));

    if (!schema) {
      console.warn(`  ⚠️  Пропущен: ${componentName}`);
      continue;
    }

    // Извлекаем корневые properties и required из схемы компонента
    const fragment = extractSchemaFragment(schema);

    // Убедимся, что type — это объект с полем "type"
    const thenBlock = {
      type: 'object',
      properties: {
        type: { const: componentName }
      },
      required: ['type']
    };

    // Переносим properties и required из схемы компонента в thenBlock
    if (fragment.properties) {
      thenBlock.properties = { ...thenBlock.properties, ...fragment.properties };
    }
    if (fragment.required && Array.isArray(fragment.required)) {
      thenBlock.required = [
        ...new Set([...(thenBlock.required || []), ...fragment.required])
      ];
    }

    componentConditions.push({
      if: {
        properties: { type: { const: componentName } },
        required: ['type']
      },
      then: thenBlock
    });

    console.log(`  ✅ ${componentName}`);
  }

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

  // 4. Собираем финальную схему
  const fullSchema = {
    $schema: 'http://json-schema.org/draft-07/schema#',
    title: 'SDUI Contract Schema',
    description: 'Полная схема для валидации SDUI контрактов',
    oneOf: [
      {
        type: 'object',
        required: ['rootElement'],
        properties: {
          version: { type: 'number' },
          rootElement: { $ref: '#/definitions/SDUIComponent' },
          data: { type: 'object' },
          state: { type: 'object' },
          computed: { type: 'object' }
        }
      },
      { $ref: '#/definitions/SDUIComponent' }
    ],
    definitions: {
      SDUIComponent: {
        type: 'object',
        required: ['type'],
        properties: {
          type: {
            type: 'string',
            enum: allComponents,
            description: 'Тип SDUI компонента'
          },
          NAME: {
            type: 'string',
            description: 'Описательное имя компонента для документирования'
          }
        },
        additionalProperties: true,
        allOf: componentConditions
      },
      LayoutElement: { $ref: '#/definitions/SDUIComponent' },
      ...baseDefinitions
    }
  };

  // 5. Сохраняем
  const outputPath = path.join(__dirname, 'sdui_vscode_schema_v2.3.0.json');
  await fs.writeFile(outputPath, JSON.stringify(fullSchema, null, 2), 'utf8');

  const stats = await fs.stat(outputPath);
  console.log(`\n✅ Схема сохранена: ${outputPath}`);
  console.log(`📏 Размер: ${(stats.size / 1024).toFixed(2)} KB`);
  console.log(`🧩 Компонентов: ${allComponents.length}`);
}

generateSchema().catch((err) => {
  console.error('❌ Ошибка:', err);
  process.exit(1);
});
