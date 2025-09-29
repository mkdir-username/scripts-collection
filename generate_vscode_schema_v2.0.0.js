#!/usr/bin/env node
/**
 * Генератор правильной JSON Schema для VS Code v2.0.0
 * Загружает реальные схемы компонентов и создает полную схему для валидации
 */

const fs = require('fs').promises;
const path = require('path');

// Список компонентов с путями к их схемам
const COMPONENT_SCHEMAS = {
  // Layouts
  "ConstraintWrapper": "layouts/Constraint/v1/ConstraintWrapper.json",
  "StackView": "components/StackView/v1/StackView.json",
  "StackWrapper": "components/StackWrapper/v1/StackWrapper.json",
  "ScrollWrapper": "components/ScrollWrapper/v1/ScrollWrapper.json",

  // Views
  "TextView": "components/TextView/v1/TextView.json",
  "ImageView": "components/ImageView/v1/ImageView.json",
  "IconView": "components/IconView/v1/IconView.json",
  "ButtonView": "components/ButtonView/v1/ButtonView.json",
  "LabelView": "components/LabelView/v1/LabelView.json",
  "TagView": "components/TagView/v1/TagView.json",
  "BannerWrapper": "components/BannerWrapper/v1/BannerWrapper.json",
  "Spacer": "components/Spacer/v1/Spacer.json",
};

async function loadComponentProperties(componentPath) {
  try {
    const fullPath = path.join(__dirname, componentPath);
    const content = await fs.readFile(fullPath, 'utf8');
    const schema = JSON.parse(content);
    return schema.properties || {};
  } catch (error) {
    console.log(`  ⚠️  Не удалось загрузить ${componentPath}: ${error.message}`);
    return {};
  }
}

async function generateSchema() {
  console.log("🔨 Генерация SDUI схемы v2.3.0 для VS Code...\n");

  // Загружаем LayoutElementContent для получения полного списка компонентов
  const layoutContentPath = path.join(__dirname, "common/LayoutElement/LayoutElementContent.json");
  const layoutContent = JSON.parse(await fs.readFile(layoutContentPath, 'utf8'));

  const allComponentsSet = new Set();
  if (layoutContent.oneOf) {
    layoutContent.oneOf.forEach(item => {
      if (item.value) {
        allComponentsSet.add(item.value);
      }
    });
  }
  const allComponents = Array.from(allComponentsSet).sort();

  console.log(`📦 Найдено ${allComponents.length} уникальных компонентов\n`);

  // Создаем определения для каждого компонента
  const componentDefinitions = [];

  // ConstraintWrapper - особый случай
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "ConstraintWrapper" } }
    },
    "then": {
      "required": ["type", "content"],
      "properties": {
        "type": { "const": "ConstraintWrapper" },
        "content": {
          "type": "object",
          "required": ["children"],
          "properties": {
            "children": {
              "type": "array",
              "items": { "$ref": "#/definitions/LayoutElement" },
              "description": "Вложенные элементы с ограничениями"
            }
          }
        },
        "size": {
          "type": "object",
          "properties": {
            "minWidth": { "type": "number" },
            "minHeight": { "type": "number" },
            "maxWidth": { "type": "number" },
            "maxHeight": { "type": "number" }
          }
        }
      }
    }
  });

  // StackView
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "StackView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "StackView" },
        "content": {
          "type": "object",
          "properties": {
            "axis": { "type": "string", "enum": ["vertical", "horizontal"] },
            "alignment": { "type": "string", "enum": ["center", "leading", "trailing", "fill", "start", "end"] },
            "distribution": { "type": "string", "enum": ["fill", "weighted", "default", "fillEqually", "fillProportionally", "equalSpacing", "equalCentering"] },
            "spacing": { "type": "number" },
            "children": {
              "type": "array",
              "items": { "$ref": "#/definitions/SDUIComponent" }
            },
            "backgroundColor": {
              "$ref": "#/definitions/Color",
              "description": "Цвет фона"
            },
            "corners": {
              "$ref": "#/definitions/Corners",
              "description": "Скругления углов"
            }
          }
        },
        "paddings": { "$ref": "#/definitions/Paddings" },
        "constraints": { "$ref": "#/definitions/Constraints" },
        "tag": { "type": "string" },
        "size": { "$ref": "#/definitions/Size" },
        "hidden": { "type": "boolean" },
        "backgroundColor": { "$ref": "#/definitions/Color" },
        "corners": { "$ref": "#/definitions/Corners" }
      }
    }
  });

  // ImageView - структура согласно примерам
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "ImageView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "ImageView" },
        "content": {
          "type": "object",
          "properties": {
            "url": { "type": "string", "description": "URL изображения" },
            "ratio": { "type": "number", "description": "Соотношение сторон" },
            "shape": {
              "type": "string",
              "enum": ["rect", "circle", "noshape", "superellipse"],
              "description": "Форма изображения"
            }
          }
        },
        "constraints": { "$ref": "#/definitions/Constraints" },
        "tag": { "type": "string" },
        "size": { "$ref": "#/definitions/Size" },
        "paddings": { "$ref": "#/definitions/Paddings" }
      }
    }
  });

  // ButtonView
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "ButtonView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "ButtonView" },
        "title": { "type": "string" },
        "action": { "$ref": "#/definitions/Action" },
        "enabled": { "type": "boolean" },
        "loading": { "type": "boolean" }
      }
    }
  });

  // LabelView
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "LabelView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "LabelView" },
        "content": {
          "type": "object",
          "properties": {
            "text": {
              "type": "object",
              "properties": {
                "value": { "type": "string" },
                "color": { "type": "string" },
                "typography": { "type": "string" },
                "maxLineCount": { "type": "number" }
              }
            },
            "horizontalAlignment": { "type": "string", "enum": ["left", "center", "right"] }
          }
        },
        "paddings": { "$ref": "#/definitions/Paddings" }
      }
    }
  });

  // IconView - структура с дополнительными полями
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "IconView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "IconView" },
        "content": {
          "type": "object",
          "properties": {
            "icon": {
              "type": "object",
              "properties": {
                "name": { "type": "string", "description": "Имя иконки" },
                "url": { "type": "string", "description": "URL иконки" },
                "color": { "type": "string", "description": "Цвет иконки" }
              }
            },
            "size": {
              "type": "string",
              "enum": ["xsmall", "small", "medium", "large", "xlarge"],
              "description": "Размер иконки"
            },
            "shape": {
              "type": "string",
              "enum": ["rect", "circle", "noshape", "superellipse"],
              "description": "Форма иконки"
            }
          }
        },
        "constraints": { "$ref": "#/definitions/Constraints" },
        "tag": { "type": "string" },
        "size": { "$ref": "#/definitions/Size" },
        "paddings": { "$ref": "#/definitions/Paddings" }
      }
    }
  });

  // BannerWrapper - структура согласно реальным примерам
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "BannerWrapper" } }
    },
    "then": {
      "properties": {
        "type": { "const": "BannerWrapper" },
        "content": {
          "type": "object",
          "properties": {
            "backgroundColor": {
              "type": "string",
              "description": "Цвет фона баннера"
            },
            "content": {
              "$ref": "#/definitions/SDUIComponent",
              "description": "Контент баннера"
            }
          }
        },
        "action": { "$ref": "#/definitions/Action" },
        "paddings": { "$ref": "#/definitions/Paddings" },
        "weight": { "type": "number" }
      }
    }
  });

  // TagView - все поля внутри content согласно примерам
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "TagView" } }
    },
    "then": {
      "properties": {
        "type": { "const": "TagView" },
        "content": {
          "type": "object",
          "properties": {
            "title": {
              "type": "object",
              "properties": {
                "text": { "$ref": "#/definitions/Text" }
              }
            },
            "rightAddon": {
              "type": "object",
              "properties": {
                "icon": { "$ref": "#/definitions/Icon" },
                "leftPadding": { "type": "string" },
                "rightPadding": { "type": "string" }
              }
            },
            "action": { "$ref": "#/definitions/Action" }
          }
        },
        "paddings": { "$ref": "#/definitions/Paddings" }
      }
    }
  });

  // Spacer - добавлены недостающие поля из примеров
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "Spacer" } }
    },
    "then": {
      "properties": {
        "type": { "const": "Spacer" },
        "size": {
          "type": "object",
          "properties": {
            "width": { "type": "number" },
            "height": { "type": "number" }
          }
        },
        "content": { "type": "object" },
        "weight": { "type": "number" },
        "padding": { "$ref": "#/definitions/Paddings" },
        "paddings": { "$ref": "#/definitions/Paddings" },
        "hidden": { "type": "boolean" },
        "version": { "type": "number" }
      }
    }
  });

  // ScrollWrapper - поля перемещены внутрь content согласно примерам
  componentDefinitions.push({
    "if": {
      "properties": { "type": { "const": "ScrollWrapper" } }
    },
    "then": {
      "properties": {
        "type": { "const": "ScrollWrapper" },
        "content": {
          "type": "object",
          "properties": {
            "axis": {
              "type": "string",
              "enum": ["vertical", "horizontal"],
              "description": "Направление прокрутки"
            },
            "showAxisScrollIndicator": {
              "type": "boolean",
              "description": "Показывать индикатор прокрутки"
            },
            "isFillViewport": {
              "type": "boolean",
              "description": "Заполнять viewport"
            },
            "shouldScrollToEnd": {
              "type": "boolean",
              "description": "Прокручивать до конца"
            },
            "content": {
              "$ref": "#/definitions/SDUIComponent",
              "description": "Прокручиваемый контент"
            }
          }
        },
        "size": { "$ref": "#/definitions/Size" },
        "paddings": { "$ref": "#/definitions/Paddings" },
        "constraints": { "$ref": "#/definitions/Constraints" }
      }
    }
  });

  // Формируем итоговую схему
  const schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SDUI Contract Schema",
    "description": "Полная схема для валидации SDUI контрактов",
    "oneOf": [
      {
        // Формат с rootElement
        "type": "object",
        "required": ["rootElement"],
        "properties": {
          "version": { "type": "number" },
          "rootElement": { "$ref": "#/definitions/SDUIComponent" },
          "data": { "type": "object" },
          "state": { "type": "object" },
          "computed": { "type": "object" }
        }
      },
      {
        // Прямой компонент
        "$ref": "#/definitions/SDUIComponent"
      }
    ],
    "definitions": {
      "SDUIComponent": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": {
            "type": "string",
            "enum": allComponents,
            "description": "Тип SDUI компонента"
          },
          "NAME": {
            "type": "string",
            "description": "Описательное имя компонента для документирования"
          }
        },
        "additionalProperties": true,
        "allOf": componentDefinitions
      },
      "LayoutElement": {
        "allOf": [
          { "$ref": "#/definitions/SDUIComponent" },
          {
            "type": "object",
            "properties": {
              "tag": { "type": "string", "description": "Тег для ссылок constraint" },
              "constraints": { "$ref": "#/definitions/Constraints" }
            }
          }
        ]
      },
      "Constraints": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": { "type": "string", "enum": ["top", "bottom", "left", "right"] },
            "reference": { "type": "string" },
            "constant": { "type": "number" }
          }
        }
      },
      "Size": {
        "type": "object",
        "properties": {
          "width": { "type": "number" },
          "height": { "type": "number" },
          "minWidth": { "type": "number" },
          "minHeight": { "type": "number" },
          "maxWidth": { "type": "number" },
          "maxHeight": { "type": "number" }
        }
      },
      "Paddings": {
        "type": "object",
        "description": "Отступы от каждого края",
        "properties": {
          "top": { "$ref": "#/definitions/Spacing" },
          "bottom": { "$ref": "#/definitions/Spacing" },
          "left": { "$ref": "#/definitions/Spacing" },
          "right": { "$ref": "#/definitions/Spacing" },
          "horizontalMargin": { "$ref": "#/definitions/Spacing" }
        }
      },
      "EdgeOffsets": {
        "type": "object",
        "description": "Модель для отступов от каждого края",
        "properties": {
          "top": { "$ref": "#/definitions/Spacing" },
          "bottom": { "$ref": "#/definitions/Spacing" },
          "left": { "$ref": "#/definitions/Spacing" },
          "right": { "$ref": "#/definitions/Spacing" }
        },
        "required": ["top", "left", "bottom", "right"]
      },
      "Spacing": {
        "type": "string",
        "description": "Токены отступов из дизайн-системы",
        "enum": [
          "zero", "xxxxs", "xxxs", "xxs", "xs2xs", "xs", "xss", "s", "m", "l",
          "xl", "xxl", "xxxl", "xxxxl", "xxxxxl", "xxxxxxl",
          "horizontalMargin", "extendedHorizontalMargin"
        ]
      },
      "Action": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "url": { "type": "string" },
          "key": { "type": "string" },
          "source": {},
          "version": { "type": "number" }
        }
      },
      "Text": {
        "type": "object",
        "properties": {
          "value": { "type": "string" },
          "color": { "$ref": "#/definitions/Color" },
          "typography": { "$ref": "#/definitions/Typography" },
          "maxLineCount": { "type": "number" }
        }
      },
      "Typography": {
        "type": "string",
        "description": "Токены типографики из дизайн-системы",
        "enum": [
          "HeadlineXLarge", "HeadlineLarge", "HeadlineMedium", "HeadlineSmall", "HeadlineXSmall",
          "PromoXLarge", "PromoLarge", "PromoMedium", "PromoSmall", "PromoXSmall",
          "ParagraphPrimaryLarge", "ParagraphPrimaryMedium", "ParagraphPrimarySmall",
          "ParagraphSecondaryLarge", "ParagraphSecondaryMedium", "ParagraphSecondarySmall",
          "ParagraphComponent", "ParagraphComponentSecondary", "ParagraphTagline", "ParagraphCaps",
          "ActionPrimaryLarge", "ActionPrimaryMedium", "ActionPrimarySmall",
          "ActionSecondaryLarge", "ActionSecondaryMedium", "ActionSecondarySmall",
          "ActionComponent"
        ]
      },
      "Color": {
        "description": "Цвет из палитры или hex значение",
        "oneOf": [
          {
            "type": "string",
            "pattern": "^#[0-9a-fA-F]{6}$",
            "description": "Hex цвет"
          },
          {
            "type": "string",
            "enum": [
              "textColorPrimary", "textColorPrimaryInverted", "textColorSecondary", "textColorSecondaryInverted",
              "textColorTertiary", "textColorTertiaryInverted", "textColorQuaternary", "textColorQuaternaryInverted",
              "textColorAccent", "textColorLink", "textColorLinkInverted", "textColorNegative", "textColorPositive",
              "textColorAttention", "textColorParagraph", "textColorParagraphInverted",
              "backgroundColorPrimary", "backgroundColorPrimaryInverted", "backgroundColorSecondary",
              "backgroundColorSecondaryInverted", "backgroundColorTertiary", "backgroundColorTertiaryInverted",
              "backgroundColorAccent", "backgroundColorComponent", "backgroundColorComponentInverted",
              "backgroundColorNegativeMuted", "backgroundColorPositiveMuted", "backgroundColorAttentionMuted",
              "backgroundColorInfoMuted", "backgroundColorLinkMuted", "backgroundColorNeutral",
              "borderColorPrimary", "borderColorPrimaryInverted", "borderColorSecondary",
              "borderColorSecondaryInverted", "borderColorTertiary", "borderColorTertiaryInverted",
              "borderColorAccent", "borderColorLink", "borderColorKey", "borderColorKeyInverted",
              "graphicColorPrimary", "graphicColorSecondary", "graphicColorTertiary",
              "graphicColorQuaternary", "clear"
            ],
            "description": "Цвет из палитры"
          }
        ]
      },
      "Icon": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "url": { "type": "string" },
          "color": { "$ref": "#/definitions/Color" }
        }
      },
      "Corners": {
        "type": "object",
        "description": "Скругления углов",
        "properties": {
          "topLeft": { "type": "integer", "description": "Скругление верхнего левого угла" },
          "topRight": { "type": "integer", "description": "Скругление верхнего правого угла" },
          "bottomLeft": { "type": "integer", "description": "Скругление нижнего левого угла" },
          "bottomRight": { "type": "integer", "description": "Скругление нижнего правого угла" }
        },
        "required": ["topLeft", "topRight", "bottomLeft", "bottomRight"]
      },
      "Stroke": {
        "type": "object",
        "description": "Модель для обводки",
        "properties": {
          "thickness": {
            "type": "string",
            "enum": ["small", "medium", "large"],
            "description": "Толщина обводки"
          },
          "color": {
            "$ref": "#/definitions/Color",
            "description": "Цвет обводки"
          }
        },
        "required": ["thickness"]
      }
    }
  };

  // Сохраняем схему
  const outputPath = path.join(__dirname, "sdui_vscode_schema_v2.3.0.json");
  await fs.writeFile(outputPath, JSON.stringify(schema, null, 2));

  const stats = await fs.stat(outputPath);
  const sizeInKB = (stats.size / 1024).toFixed(2);

  console.log("✅ Схема создана успешно!");
  console.log(`📄 Файл: ${outputPath}`);
  console.log(`📏 Размер: ${sizeInKB} KB`);
  console.log(`🧩 Компонентов: ${allComponents.length}`);
  console.log("\n🔄 Для применения:");
  console.log("1. Обновите .vscode/settings.json:");
  console.log('   "url": "./SDUI/sdui_vscode_schema_v2.3.0.json"');
  console.log("2. Перезапустите VS Code");
}

// Запуск
generateSchema().catch(console.error);