# ПРИМЕРЫ: computed_data_parser v2.1.0

## Пример 1: Базовая цепочка зависимостей

### Контракт
```json
{
  "state": {
    "firstName": "Alice",
    "lastName": "Smith",
    "age": 28
  },
  "computed": {
    "fullName": "${state.firstName} ${state.lastName}",
    "greeting": "Hello, ${computed.fullName}!",
    "info": "${computed.greeting} You are ${state.age} years old."
  },
  "rootElement": {
    "type": "text",
    "value": "${computed.info}"
  }
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js example1.json empty.json result1.json --debug
```

### Вывод (консоль)
```
📂 Загрузка контракта: example1.json
📂 Загрузка данных: empty.json
✅ Загружено: 3 computed, 0 data, 3 state

⚙️  Вычисление computed...
📊 Построение графа зависимостей...
📊 Граф зависимостей:
  greeting → [fullName]
  info → [greeting]

🔄 Топологическая сортировка...
✅ Порядок вычисления: [fullName → greeting → info]

⚙️  Вычисление: computed.fullName
  🔍 Разрешение пути: ${state.firstName} → [state, firstName]
    ├─ state = {"firstName":"Alice","lastName":"Smith","age":28}
    ├─ firstName = "Alice"
    └─ Результат: "Alice"
  ✅ computed.fullName = "Alice Smith"

⚙️  Вычисление: computed.greeting
  🔍 Разрешение пути: ${computed.fullName} → [computed, fullName]
    ├─ computed = {"fullName":"Alice Smith"}
    ├─ fullName = "Alice Smith"
    └─ Результат: "Alice Smith"
  ✅ computed.greeting = "Hello, Alice Smith!"

⚙️  Вычисление: computed.info
  🔍 Разрешение пути: ${computed.greeting} → [computed, greeting]
    ├─ computed = {"fullName":"Alice Smith","greeting":"Hello, Alice Smith!"}
    ├─ greeting = "Hello, Alice Smith!"
    └─ Результат: "Hello, Alice Smith!"
  ✅ computed.info = "Hello, Alice Smith! You are 28 years old."

✅ Computed вычислено: 3 полей
📋 Значения computed:
  fullName: "Alice Smith"
  greeting: "Hello, Alice Smith!"
  info: "Hello, Alice Smith! You are 28 years old."

🔧 Разрешение rootElement...

✅ Готово! Результат сохранён в /Users/username/Scripts/result1.json
📊 Размер: 81 символов (0.1 KB)
📈 Computed кэшировано: 3
```

### Результат (result1.json)
```json
{
  "rootElement": {
    "type": "text",
    "value": "Hello, Alice Smith! You are 28 years old."
  }
}
```

---

## Пример 2: Conditional с зависимостями

### Контракт
```json
{
  "state": {
    "balance": 1500,
    "currency": "USD",
    "isPremium": true
  },
  "computed": {
    "balanceFormatted": "$${state.balance} ${state.currency}",
    "accountType": {
      "type": "if",
      "$if": "${state.isPremium}",
      "$then": "Premium",
      "$else": "Standard"
    },
    "statusMessage": "${computed.accountType} Account - Balance: ${computed.balanceFormatted}",
    "benefits": {
      "type": "if",
      "$if": "${state.isPremium}",
      "$then": "${computed.statusMessage} (Free transfers included)",
      "$else": "${computed.statusMessage}"
    }
  },
  "rootElement": {
    "type": "container",
    "children": [
      {
        "type": "header",
        "text": "${computed.accountType} Account"
      },
      {
        "type": "text",
        "value": "${computed.benefits}"
      }
    ]
  }
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js example2.json empty.json result2.json --verbose
```

### Вывод (консоль)
```
📂 Загрузка контракта: example2.json
📂 Загрузка данных: empty.json
✅ Загружено: 4 computed, 0 data, 3 state

⚙️  Вычисление computed...
📊 Построение графа зависимостей...
📊 Граф зависимостей:
  statusMessage → [accountType, balanceFormatted]
  benefits → [accountType, statusMessage]

🔄 Топологическая сортировка...
✅ Порядок вычисления: [balanceFormatted → accountType → statusMessage → benefits]

✅ Computed вычислено: 4 полей

🔧 Разрешение rootElement...

✅ Готово! Результат сохранён в /Users/username/Scripts/result2.json
📊 Размер: 289 символов (0.3 KB)
📈 Computed кэшировано: 4
```

### Результат (result2.json)
```json
{
  "rootElement": {
    "type": "container",
    "children": [
      {
        "type": "header",
        "text": "Premium Account"
      },
      {
        "type": "text",
        "value": "Premium Account - Balance: $1500 USD (Free transfers included)"
      }
    ]
  }
}
```

---

## Пример 3: Массивы и $children

### Контракт
```json
{
  "data": {
    "products": [
      {
        "name": "Laptop",
        "price": 999,
        "stock": 5
      },
      {
        "name": "Mouse",
        "price": 25,
        "stock": 50
      },
      {
        "name": "Keyboard",
        "price": 75,
        "stock": 30
      }
    ]
  },
  "computed": {
    "firstProduct": "${data.products[0]}",
    "firstProductName": "${computed.firstProduct.name}",
    "firstProductPrice": "${computed.firstProduct.price}",
    "featuredTitle": "Featured: ${computed.firstProductName}",
    "featuredPrice": "$${computed.firstProductPrice}",
    "featuredDescription": "${computed.featuredTitle} - Only ${computed.featuredPrice}!"
  },
  "rootElement": {
    "type": "container",
    "$children": [
      "${data.products[0]}",
      "${data.products[1]}",
      "${data.products[2]}"
    ],
    "header": "${computed.featuredDescription}"
  }
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js example3.json empty.json result3.json -v
```

### Результат (result3.json)
```json
{
  "rootElement": {
    "type": "container",
    "header": "Featured: Laptop - Only $999!",
    "children": [
      {
        "name": "Laptop",
        "price": 999,
        "stock": 5
      },
      {
        "name": "Mouse",
        "price": 25,
        "stock": 50
      },
      {
        "name": "Keyboard",
        "price": 75,
        "stock": 30
      }
    ]
  }
}
```

---

## Пример 4: Обнаружение циклической зависимости

### Контракт (ОШИБКА)
```json
{
  "computed": {
    "a": "Value A depends on ${computed.b}",
    "b": "Value B depends on ${computed.c}",
    "c": "Value C depends on ${computed.a}"
  },
  "rootElement": {
    "type": "text",
    "value": "${computed.a}"
  }
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js example4_error.json empty.json result4.json --debug
```

### Вывод (консоль)
```
📂 Загрузка контракта: example4_error.json
📂 Загрузка данных: empty.json
✅ Загружено: 3 computed, 0 data, 0 state

⚙️  Вычисление computed...
📊 Построение графа зависимостей...
📊 Граф зависимостей:
  a → [b]
  b → [c]
  c → [a]

🔄 Топологическая сортировка...

❌ Ошибка: Ошибка при сортировке зависимостей: 🔄 Циклическая зависимость в computed: a

Error: Ошибка при сортировке зависимостей: 🔄 Циклическая зависимость в computed: a
    at evaluateComputed (/Users/username/Scripts/computed_data_parser_v2.1.0.js:150)
    at main (/Users/username/Scripts/computed_data_parser_v2.1.0.js:297)
```

---

## Пример 5: Сложный граф зависимостей

### Контракт
```json
{
  "state": {
    "user": {
      "firstName": "Bob",
      "lastName": "Johnson",
      "email": "bob@example.com"
    },
    "session": {
      "loginTime": "2025-10-07T10:30:00Z",
      "isAuthenticated": true
    }
  },
  "computed": {
    "firstName": "${state.user.firstName}",
    "lastName": "${state.user.lastName}",
    "email": "${state.user.email}",
    "fullName": "${computed.firstName} ${computed.lastName}",
    "emailDomain": "${computed.email}",
    "isAuthenticated": "${state.session.isAuthenticated}",
    "welcomeMessage": {
      "type": "if",
      "$if": "${computed.isAuthenticated}",
      "$then": "Welcome back, ${computed.fullName}!",
      "$else": "Please log in"
    },
    "userInfo": "User: ${computed.fullName} (${computed.email})",
    "dashboardHeader": {
      "type": "if",
      "$if": "${computed.isAuthenticated}",
      "$then": "${computed.welcomeMessage} | ${computed.userInfo}",
      "$else": "${computed.welcomeMessage}"
    }
  },
  "rootElement": {
    "type": "dashboard",
    "header": "${computed.dashboardHeader}"
  }
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js example5.json empty.json result5.json --debug
```

### Вывод (граф зависимостей)
```
📊 Граф зависимостей:
  fullName → [firstName, lastName]
  welcomeMessage → [isAuthenticated, fullName]
  userInfo → [fullName, email]
  dashboardHeader → [isAuthenticated, welcomeMessage, userInfo]

✅ Порядок вычисления: [firstName → lastName → email → isAuthenticated → fullName → emailDomain → welcomeMessage → userInfo → dashboardHeader]
```

### Результат (result5.json)
```json
{
  "rootElement": {
    "type": "dashboard",
    "header": "Welcome back, Bob Johnson! | User: Bob Johnson (bob@example.com)"
  }
}
```

---

## Пример 6: Nested objects и массивы

### Контракт
```json
{
  "state": {
    "cart": {
      "items": [
        { "id": 1, "name": "Book", "quantity": 2, "price": 15 },
        { "id": 2, "name": "Pen", "quantity": 5, "price": 2 }
      ]
    }
  },
  "computed": {
    "firstItem": "${state.cart.items[0]}",
    "firstItemName": "${computed.firstItem.name}",
    "firstItemTotal": "${computed.firstItem.quantity}x $${computed.firstItem.price}",
    "secondItem": "${state.cart.items[1]}",
    "secondItemName": "${computed.secondItem.name}",
    "secondItemTotal": "${computed.secondItem.quantity}x $${computed.secondItem.price}",
    "cartSummary": "Cart: ${computed.firstItemName} (${computed.firstItemTotal}), ${computed.secondItemName} (${computed.secondItemTotal})"
  },
  "rootElement": {
    "type": "text",
    "value": "${computed.cartSummary}"
  }
}
```

### Результат
```json
{
  "rootElement": {
    "type": "text",
    "value": "Cart: Book (2x $15), Pen (5x $2)"
  }
}
```

---

## Пример 7: External data merge

### contract.json
```json
{
  "state": {
    "template": "Welcome, ${name}!"
  },
  "computed": {
    "userName": "${state.name}",
    "greeting": "Hello, ${computed.userName}! Your role is: ${state.role}"
  },
  "rootElement": {
    "type": "text",
    "value": "${computed.greeting}"
  }
}
```

### data.json
```json
{
  "name": "Charlie",
  "role": "Admin"
}
```

### Команда
```bash
node computed_data_parser_v2.1.0.js contract.json data.json result7.json
```

### Результат (result7.json)
```json
{
  "rootElement": {
    "type": "text",
    "value": "Hello, Charlie! Your role is: Admin"
  }
}
```

---

## Пример 8: Кэширование при повторном использовании

### Контракт
```json
{
  "state": {
    "expensiveData": [1, 2, 3, 4, 5]
  },
  "computed": {
    "cachedValue": "${state.expensiveData}",
    "usage1": "${computed.cachedValue}",
    "usage2": "${computed.cachedValue}",
    "usage3": "${computed.cachedValue}"
  },
  "rootElement": {
    "type": "container",
    "child1": "${computed.usage1}",
    "child2": "${computed.usage2}",
    "child3": "${computed.usage3}"
  }
}
```

### Вывод (--verbose)
```
📈 Computed кэшировано: 4
```

**Пояснение:** `cachedValue` вычислено 1 раз, затем переиспользовано в `usage1`, `usage2`, `usage3`.

---

## Пример 9: Отсутствующие зависимости

### Контракт
```json
{
  "computed": {
    "a": "${computed.b}",
    "c": "${computed.a}"
  },
  "rootElement": {
    "type": "text",
    "value": "${computed.c}"
  }
}
```

### Вывод (--debug)
```
📊 Граф зависимостей:
  a → [b]
  c → [a]

✅ Порядок вычисления: [b → a → c]

⚙️  Вычисление: computed.b
  ❌ Ошибка при вычислении computed.b: Не удалось разрешить путь: ${computed.b} на части "b"
```

**Пояснение:** `computed.b` отсутствует, но граф строится правильно, ошибка выбрасывается на этапе вычисления.

---

## Пример 10: Performance тест (100 computed)

### Генерация контракта
```javascript
const contract = {
  state: { base: 1 },
  computed: {},
  rootElement: { type: "text", value: "${computed.c99}" }
};

for (let i = 0; i < 100; i++) {
  if (i === 0) {
    contract.computed[`c${i}`] = "${state.base}";
  } else {
    contract.computed[`c${i}`] = "${computed.c" + (i - 1) + "}";
  }
}

// Сохраняем в perf_test.json
```

### Команда
```bash
time node computed_data_parser_v2.1.0.js perf_test.json empty.json perf_result.json -v
```

### Вывод
```
✅ Загружено: 100 computed, 0 data, 1 state

⚙️  Вычисление computed...
✅ Порядок вычисления: [c0 → c1 → c2 → ... → c99]

✅ Computed вычислено: 100 полей

✅ Готово! Результат сохранён в /Users/username/Scripts/perf_result.json
📊 Размер: 51 символов (0.0 KB)
📈 Computed кэшировано: 100

real    0m0.087s
user    0m0.069s
sys     0m0.012s
```

**Результат:** 100 computed за 87ms → ~0.87ms на поле

---

## Полезные команды

### Отладка графа зависимостей
```bash
node computed_data_parser_v2.1.0.js contract.json data.json out.json --debug 2>&1 | grep "Граф зависимостей" -A 20
```

### Проверка порядка вычисления
```bash
node computed_data_parser_v2.1.0.js contract.json data.json out.json --debug 2>&1 | grep "Порядок вычисления"
```

### Проверка на циклы
```bash
node computed_data_parser_v2.1.0.js contract.json data.json out.json 2>&1 | grep "Циклическая зависимость" && echo "ЦИКЛ НАЙДЕН" || echo "Циклов нет"
```

### Benchmark
```bash
for i in {1..10}; do
  time node computed_data_parser_v2.1.0.js contract.json data.json out.json
done | grep real | awk '{print $2}' | sort
```

---

## Типичные ошибки и решения

### Ошибка: "Циклическая зависимость"
**Причина:** A → B → C → A

**Решение:** Разорвать цикл, пересмотреть логику computed

---

### Ошибка: "Не удалось разрешить путь"
**Причина:** Ссылка на несуществующий computed/state/data

**Решение:** Проверить орфографию, добавить недостающее поле

---

### Computed не видит другой computed
**Причина:** Использование старой версии (v2.0.0)

**Решение:** Обновиться на v2.1.0

---

## Совместимость

| Версия | Node.js | Computed→Computed | Топосортировка | Debug |
|--------|---------|-------------------|----------------|-------|
| v2.0.0 | ≥14 | ❌ | ❌ | ❌ |
| v2.1.0 | ≥14 | ✅ | ✅ | ✅ |

---

## См. также

- `CHANGELOG_computed_data_parser_v2.1.0.md` - полное описание изменений
- `/Users/username/Scripts/vscode-validate-on-save_v2.3.0.ts` - валидатор SDUI контрактов
- `/Users/username/Scripts/Python/utils/jinja_hot_reload_v3.7.0.py` - Jinja2 система с зависимостями
