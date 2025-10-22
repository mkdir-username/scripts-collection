/**
 * Тестовые фикстуры для валидатора v2.3.0
 *
 * Готовые примеры контрактов для быстрого тестирования:
 * - Валидные контракты
 * - Невалидные контракты
 * - Edge cases
 * - Реальные примеры
 *
 * @version 1.0.0
 * @date 2025-10-05
 */

// ============================================================================
// ВАЛИДНЫЕ КОНТРАКТЫ
// ============================================================================

/**
 * Простой валидный контракт с StackView
 */
export const VALID_SIMPLE_STACK = `
{
  "type": "StackView",
  "content": {
    "axis": "vertical",
    "alignment": "fill",
    "children": [
      {
        "type": "TextView",
        "textContent": {
          "defaultValue": "Hello World"
        }
      }
    ]
  }
}`.trim();

/**
 * Контракт с ButtonView (все обязательные поля)
 */
export const VALID_BUTTON = `
{
  "type": "ButtonView",
  "textContent": {
    "defaultValue": "Click Me"
  },
  "actions": [
    {
      "type": "HttpAction",
      "url": "/api/action",
      "method": "POST"
    }
  ]
}`.trim();

/**
 * Контракт с Jinja переменными
 */
export const VALID_WITH_JINJA_VARS = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "{{ userName }}"
  },
  "style": {
    "fontSize": {{ fontSize }},
    "isVisible": {{ isVisible }}
  }
}`.trim();

/**
 * Контракт с импортами
 */
export const VALID_WITH_IMPORTS = `
{
  "type": "StackView",
  "content": {
    "children": [
      // [Header Component](file://./header.json)
      // [Footer Component](file://./footer.json)
    ]
  }
}`.trim();

/**
 * Контракт с state и data bindings
 */
export const VALID_WITH_STATE = `
{
  "version": 1,
  "rootElement": {
    "type": "StackView",
    "content": {
      "children": []
    }
  },
  "state": {
    "isLoading": {{ loadingState.isLoading }},
    "hasData": {{ data != null }}
  },
  "data": {
    "items": {{ items }},
    "totalCount": {{ count }}
  }
}`.trim();

// ============================================================================
// НЕВАЛИДНЫЕ КОНТРАКТЫ
// ============================================================================

/**
 * ButtonView без обязательных полей
 */
export const INVALID_MISSING_REQUIRED_FIELDS = `
{
  "type": "ButtonView"
}`.trim();

/**
 * Неизвестный тип компонента
 */
export const INVALID_UNKNOWN_COMPONENT = `
{
  "type": "UnknownComponentView",
  "content": {}
}`.trim();

/**
 * Некорректный JSON синтаксис
 */
export const INVALID_JSON_SYNTAX = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "TextView"
        missing_comma: true
      }
    ]
  }
}`.trim();

/**
 * Циклические импорты
 */
export const INVALID_CIRCULAR_IMPORT_A = `
{
  "type": "StackView",
  // [Import B](file://./b.j2.java)
}`.trim();

export const INVALID_CIRCULAR_IMPORT_B = `
{
  "type": "StackView",
  // [Import A](file://./a.j2.java)
}`.trim();

/**
 * Отсутствующий импорт
 */
export const INVALID_MISSING_IMPORT = `
{
  "type": "StackView",
  // [Missing File](file://./nonexistent.json)
}`.trim();

// ============================================================================
// EDGE CASES
// ============================================================================

/**
 * Пустой объект
 */
export const EDGE_EMPTY_OBJECT = `{}`;

/**
 * Только комментарии
 */
export const EDGE_ONLY_COMMENTS = `
// Comment 1
// Comment 2
// [Not an import](note)
`.trim();

/**
 * Вложенные структуры (глубина 10)
 */
export const EDGE_DEEP_NESTING = JSON.stringify({
  type: 'StackView',
  content: {
    children: [
      {
        type: 'StackView',
        content: {
          children: [
            {
              type: 'StackView',
              content: {
                children: [
                  {
                    type: 'StackView',
                    content: {
                      children: [
                        {
                          type: 'StackView',
                          content: {
                            children: [
                              {
                                type: 'TextView',
                                textContent: { defaultValue: 'Deep!' },
                              },
                            ],
                          },
                        },
                      ],
                    },
                  },
                ],
              },
            },
          ],
        },
      },
    ],
  },
});

/**
 * Очень длинная строка
 */
export const EDGE_LONG_STRING = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "${'A'.repeat(10000)}"
  }
}`.trim();

/**
 * Unicode символы
 */
export const EDGE_UNICODE = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "Привет, мир! 👋 🌍 你好世界"
  }
}`.trim();

/**
 * Экранированные символы
 */
export const EDGE_ESCAPED_CHARS = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "Line 1\\nLine 2\\tTabbed"
  }
}`.trim();

/**
 * Большой массив (1000 элементов)
 */
export const EDGE_LARGE_ARRAY = JSON.stringify({
  type: 'StackView',
  content: {
    children: Array.from({ length: 1000 }, (_, i) => ({
      type: 'TextView',
      id: `text_${i}`,
      textContent: { defaultValue: `Item ${i}` },
    })),
  },
});

// ============================================================================
// РЕАЛЬНЫЕ ПРИМЕРЫ
// ============================================================================

/**
 * Реальный пример: Main Screen с импортами
 */
export const REAL_MAIN_SCREEN = `
{
  "version": 1,
  "rootElement": {
    "type": "StackView",
    "content": {
      "axis": "vertical",
      "alignment": "fill",
      "distribution": "weighted",
      "children": [{
        "type": "ConstraintWrapper",
        "size": {
          "minWidth": 320,
          "minHeight": 568,
          "maxWidth": 9999,
          "maxHeight": 9999
        },
        "content": {
          "children": [
            // [Стопка монет](file:///path/to/Coins.json)
            // [Фон градиент](file:///path/to/Gradient.json)
            {
              "type": "StackView",
              "content": {
                "alignment": "fill",
                "axis": "vertical",
                "children": [
                  {
                    "type": "Spacer",
                    "size": { "height": 30 }
                  },
                  // [Блок "Моя зарплата"](file:///path/to/Salary-block.json)
                  {
                    "type": "Spacer",
                    "size": { "height": 24 }
                  }
                ]
              }
            }
          ]
        }
      }]
    }
  },
  "state": {
    "isAverageSalaryShow": {{ averageSalaryState.isAverageSalaryShow }},
    "isVideoBannerShow": {{ videoBanner != null }}
  },
  "data": {}
}`.trim();

/**
 * Реальный пример: Java класс с Jinja
 */
export const REAL_JAVA_CLASS = `
package ru.alfabank.mobile.salary;

import {{ package.imports }};

public class SalaryScreen {
    private String userName = "{{ user.name }}";
    private int balance = {{ user.balance }};
    private boolean isVisible = {{ state.visible }};

    {% if enableFeature %}
    public void showFeature() {
        System.out.println("Feature enabled for {{ user.name }}");
    }
    {% endif %}

    public Map<String, Object> getData() {
        Map<String, Object> data = new HashMap<>();
        data.put("balance", {{ account.balance }});
        data.put("currency", "{{ account.currency }}");
        return data;
    }
}`.trim();

/**
 * Реальный пример: Модуль Button
 */
export const REAL_BUTTON_MODULE = `
{
  "type": "ButtonView",
  "textContent": {
    "defaultValue": "{{ buttonTitle }}",
    "focusedValue": "{{ buttonTitle }} (focused)"
  },
  "backgroundColor": {
    "defaultValue": "{{ colors.primary }}",
    "highlightedValue": "{{ colors.primaryDark }}",
    "disabledValue": "{{ colors.disabled }}"
  },
  "actions": [
    {
      "type": "HttpAction",
      "url": "{{ apiEndpoint }}/submit",
      "method": "POST",
      "body": {
        "userId": "{{ userId }}",
        "action": "submit"
      }
    }
  ]
}`.trim();

// ============================================================================
// ВСПОМОГАТЕЛЬНЫЕ МОДУЛИ ДЛЯ ИМПОРТОВ
// ============================================================================

/**
 * Модуль: Header
 */
export const MODULE_HEADER = `
{
  "type": "StackView",
  "content": {
    "axis": "horizontal",
    "children": [
      {
        "type": "TextView",
        "textContent": { "defaultValue": "Header" }
      }
    ]
  }
}`.trim();

/**
 * Модуль: Footer
 */
export const MODULE_FOOTER = `
{
  "type": "StackView",
  "content": {
    "axis": "horizontal",
    "children": [
      {
        "type": "TextView",
        "textContent": { "defaultValue": "Footer" }
      }
    ]
  }
}`.trim();

/**
 * Модуль: Spacer
 */
export const MODULE_SPACER = `
{
  "type": "Spacer",
  "size": {
    "height": 16
  }
}`.trim();

/**
 * Модуль: Icon Button
 */
export const MODULE_ICON_BUTTON = `
{
  "type": "ButtonView",
  "icon": {
    "defaultValue": "icon_close"
  },
  "textContent": {
    "defaultValue": ""
  },
  "actions": [
    {
      "type": "CloseAction"
    }
  ]
}`.trim();

// ============================================================================
// DEFAULT VALUES ДЛЯ JINJA ПЕРЕМЕННЫХ
// ============================================================================

/**
 * Дефолтные значения для common переменных
 */
export const DEFAULT_VALUES_COMMON = {
  userName: 'John Doe',
  userId: '12345',
  itemCount: 10,
  isVisible: true,
  isEnabled: false,
  fontSize: 16,
  title: 'Default Title',
  description: 'Default Description',
};

/**
 * Дефолтные значения для state
 */
export const DEFAULT_VALUES_STATE = {
  loadingState: {
    isLoading: false,
  },
  averageSalaryState: {
    isAverageSalaryShow: true,
  },
  state: {
    visible: true,
  },
};

/**
 * Дефолтные значения для data
 */
export const DEFAULT_VALUES_DATA = {
  data: {
    items: [1, 2, 3],
    totalCount: 3,
  },
  items: ['item1', 'item2', 'item3'],
  count: 42,
  videoBanner: {
    url: 'https://example.com/video.mp4',
  },
};

/**
 * Дефолтные значения для user
 */
export const DEFAULT_VALUES_USER = {
  user: {
    name: 'Alice Smith',
    age: 30,
    balance: 1000,
  },
  account: {
    balance: 500.5,
    currency: 'USD',
  },
};

/**
 * Дефолтные значения для UI
 */
export const DEFAULT_VALUES_UI = {
  colors: {
    primary: '#007AFF',
    primaryDark: '#0051A8',
    disabled: '#C7C7CC',
  },
  buttonTitle: 'Submit',
  apiEndpoint: 'https://api.example.com',
};

/**
 * Дефолтные значения для Java
 */
export const DEFAULT_VALUES_JAVA = {
  package: {
    imports: 'java.util.*',
  },
  enableFeature: true,
};

/**
 * Все дефолтные значения (объединенные)
 */
export const DEFAULT_VALUES_ALL = {
  ...DEFAULT_VALUES_COMMON,
  ...DEFAULT_VALUES_STATE,
  ...DEFAULT_VALUES_DATA,
  ...DEFAULT_VALUES_USER,
  ...DEFAULT_VALUES_UI,
  ...DEFAULT_VALUES_JAVA,
};

// ============================================================================
// ЭКСПОРТ
// ============================================================================

export const FIXTURES = {
  // Валидные
  VALID_SIMPLE_STACK,
  VALID_BUTTON,
  VALID_WITH_JINJA_VARS,
  VALID_WITH_IMPORTS,
  VALID_WITH_STATE,

  // Невалидные
  INVALID_MISSING_REQUIRED_FIELDS,
  INVALID_UNKNOWN_COMPONENT,
  INVALID_JSON_SYNTAX,
  INVALID_CIRCULAR_IMPORT_A,
  INVALID_CIRCULAR_IMPORT_B,
  INVALID_MISSING_IMPORT,

  // Edge cases
  EDGE_EMPTY_OBJECT,
  EDGE_ONLY_COMMENTS,
  EDGE_DEEP_NESTING,
  EDGE_LONG_STRING,
  EDGE_UNICODE,
  EDGE_ESCAPED_CHARS,
  EDGE_LARGE_ARRAY,

  // Реальные примеры
  REAL_MAIN_SCREEN,
  REAL_JAVA_CLASS,
  REAL_BUTTON_MODULE,

  // Модули
  MODULE_HEADER,
  MODULE_FOOTER,
  MODULE_SPACER,
  MODULE_ICON_BUTTON,
};

export const DEFAULT_VALUES = {
  COMMON: DEFAULT_VALUES_COMMON,
  STATE: DEFAULT_VALUES_STATE,
  DATA: DEFAULT_VALUES_DATA,
  USER: DEFAULT_VALUES_USER,
  UI: DEFAULT_VALUES_UI,
  JAVA: DEFAULT_VALUES_JAVA,
  ALL: DEFAULT_VALUES_ALL,
};
