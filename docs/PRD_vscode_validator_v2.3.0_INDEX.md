# VSCode Validator v2.3.0 - Requirements Documentation Index

**Проект:** VSCode On-Save SDUI Validator
**Версия:** v2.3.0
**Дата создания:** 2025-10-05
**Статус:** Draft для утверждения stakeholders

---

## Обзор документации

Полный набор требований для разработки VSCode Validator v2.3.0, организованный по уровням детализации:

```
Level 1: Executive Summary (5 минут чтения)
    ↓
Level 2: Full PRD (30 минут чтения)
    ↓
Level 3: Architecture Diagrams (15 минут)
    ↓
Level 4: User Stories (45 минут, for developers)
```

---

## Документы

### 1. Executive Summary (НАЧНИТЕ ОТСЮДА)

**Файл:** [PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md](./PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md)

**Аудитория:** Tech Lead, Product Owner, Stakeholders

**Содержание:**
- Краткое описание проблемы и решения (2 страницы)
- Ключевые требования (checklist)
- Success Metrics (KPIs)
- Timeline и Milestones
- Top 5 рисков
- Scope boundaries (In/Out)
- Open Questions (требуют решения к M1)
- Stakeholder Actions Required
- Next Steps

**Время чтения:** 5-10 минут

**Когда использовать:**
- Для быстрого понимания проекта
- Перед stakeholder review meeting
- Для получения sign-off на scope

---

### 2. Full Product Requirements Document

**Файл:** [PRD_vscode_validator_v2.3.0.md](./PRD_vscode_validator_v2.3.0.md)

**Аудитория:** Tech Lead, Developers, QA, Product Team

**Содержание:**
- Executive Summary
- Problem Statement (текущая ситуация, воздействие, желаемый результат)
- Stakeholders (primary/secondary, коммуникация)
- **Functional Requirements** (FR-1 to FR-5)
  - Jinja2 Template Processing
  - Comment-Import Processing
  - Position Tracking для Mixed Format
  - Backward Compatibility
  - Smart Context Generation
- **Non-Functional Requirements** (NFR-1 to NFR-5)
  - Performance
  - Reliability
  - Maintainability
  - Compatibility
  - Security
- **Architecture Requirements** (AR-1 to AR-5)
  - Modular Pipeline Architecture
  - Source Map Architecture
  - Cache Strategy
  - Integration с Jinja Hot Reload
  - Error Reporting Architecture
- **Testing Requirements** (TR-1 to TR-5)
  - Unit Testing
  - Integration Testing
  - Regression Testing
  - Error Scenario Testing
  - Test Fixtures
- Success Metrics
- Scope & Timeline
- Risks & Mitigation
- Assumptions
- Open Questions
- Appendices (Technical Diagrams, Workflows, Migration Guide, FAQ)

**Время чтения:** 30-45 минут

**Когда использовать:**
- Для детального планирования разработки
- Как reference во время implementation
- Для onboarding новых разработчиков
- Для создания technical design document

---

### 3. Architecture Diagrams

**Файл:** [PRD_vscode_validator_v2.3.0_ARCHITECTURE.md](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md)

**Аудитория:** Developers, Architects, Tech Lead

**Содержание:**
1. High-Level System Architecture (Mermaid)
2. Validation Pipeline Flow (Flowchart)
3. Source Map Layers Architecture
4. Import Resolution & Dependency Graph
5. Jinja2 Processing Architecture (Sequence)
6. Cache Architecture
7. Error Reporting Flow
8. Class Diagram (Core Components)
9. Data Flow Diagram
10. Deployment Architecture
11. Performance Optimization Strategy
12. Error Handling Strategy

**Время чтения:** 15-20 минут (визуальное изучение)

**Когда использовать:**
- Для понимания системной архитектуры
- При проектировании компонентов
- Для code review и architectural decisions
- Для документации technical design

**Формат:** Все диаграммы в Mermaid (рендерятся в GitHub, VSCode, etc.)

---

### 4. User Stories & Acceptance Criteria

**Файл:** [PRD_vscode_validator_v2.3.0_USER_STORIES.md](./PRD_vscode_validator_v2.3.0_USER_STORIES.md)

**Аудитория:** Developers, QA, Scrum Master

**Содержание:**
- **Epic 1: Jinja2 Template Support** (3 stories, 14 scenarios)
  - US-1.1: Automatic Jinja2 Detection
  - US-1.2: Jinja2 Template Rendering
  - US-1.3: Smart Context Generation
- **Epic 2: Comment-Import System** (4 stories, 16 scenarios)
  - US-2.1: Parse Comment-Import Declarations
  - US-2.2: Resolve Import Dependencies
  - US-2.3: Detect Circular Dependencies
  - US-2.4: Inline Import Expansion
- **Epic 3: Enhanced Position Tracking** (3 stories, 10 scenarios)
  - US-3.1: Build Jinja2 Source Map
  - US-3.2: Build Import Source Map
  - US-3.3: Layer Source Maps
- **Epic 4: Backward Compatibility** (2 stories, 7 scenarios)
  - US-4.1: Pure JSON Fast Path
  - US-4.2: CLI Compatibility
- **Epic 5: Developer Experience** (3 stories, 10 scenarios)
  - US-5.1: Helpful Error Messages
  - US-5.2: Clickable Error Links
  - US-5.3: Performance Feedback
- **Epic 6: Testing & Quality** (2 stories, 6 scenarios)
  - US-6.1: Comprehensive Test Suite
  - US-6.2: Real-World Test Data

**Итого:** 6 Epics, 17 User Stories, 60 Scenarios

**Story Points:** 73 SP (~7 weeks @ 10 SP/week)

**Время чтения:** 45-60 минут (детальное изучение)

**Когда использовать:**
- Для sprint planning и task breakdown
- Для написания unit/integration тестов
- Для QA test case creation
- Для tracking development progress

---

## Навигация по требованиям

### По роли

**Если вы Tech Lead:**
1. Прочитайте [Executive Summary](./PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md)
2. Изучите [Architecture Diagrams](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md)
3. Просмотрите [Full PRD](./PRD_vscode_validator_v2.3.0.md) (секции Risks, Timeline, Success Metrics)
4. Review Open Questions и примите решения

**Если вы Developer:**
1. Прочитайте [Executive Summary](./PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md) для контекста
2. Детально изучите [User Stories](./PRD_vscode_validator_v2.3.0_USER_STORIES.md) для вашего Epic
3. Используйте [Architecture Diagrams](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md) для дизайна компонентов
4. Обращайтесь к [Full PRD](./PRD_vscode_validator_v2.3.0.md) для уточнения NFR и constraints

**Если вы QA Engineer:**
1. Прочитайте [Executive Summary](./PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md)
2. Изучите [User Stories](./PRD_vscode_validator_v2.3.0_USER_STORIES.md) - каждый scenario = test case
3. Обратите внимание на Testing Requirements в [Full PRD](./PRD_vscode_validator_v2.3.0.md)
4. Используйте Epic 6 (Testing & Quality) для планирования test strategy

**Если вы Product Owner:**
1. Прочитайте [Executive Summary](./PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md)
2. Валидируйте Success Metrics и Scope в [Full PRD](./PRD_vscode_validator_v2.3.0.md)
3. Приоритизируйте User Stories в [User Stories](./PRD_vscode_validator_v2.3.0_USER_STORIES.md)
4. Approve timeline и milestones

---

## Быстрые ссылки на ключевые секции

### Требования

| Тип | Локация | Критичность |
|-----|---------|-------------|
| **Jinja2 Processing** | [Full PRD § FR-1](./PRD_vscode_validator_v2.3.0.md#fr-1-jinja2-template-processing) | CRITICAL |
| **Comment-Import System** | [Full PRD § FR-2](./PRD_vscode_validator_v2.3.0.md#fr-2-comment-import-processing) | CRITICAL |
| **Position Tracking** | [Full PRD § FR-3](./PRD_vscode_validator_v2.3.0.md#fr-3-position-tracking-для-mixed-format) | HIGH |
| **Backward Compatibility** | [Full PRD § FR-4](./PRD_vscode_validator_v2.3.0.md#fr-4-backward-compatibility-с-pure-json) | CRITICAL |
| **Performance** | [Full PRD § NFR-1](./PRD_vscode_validator_v2.3.0.md#nfr-1-performance) | HIGH |
| **Architecture** | [Architecture § AR-1](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#ar-1-modular-pipeline-architecture) | HIGH |

### Диаграммы

| Диаграмма | Локация | Назначение |
|-----------|---------|------------|
| **System Overview** | [Architecture § 1](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#1-high-level-system-architecture) | Понимание общей архитектуры |
| **Pipeline Flow** | [Architecture § 2](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#2-validation-pipeline-flow) | Понимание процесса валидации |
| **Source Maps** | [Architecture § 3](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#3-source-map-layers-architecture) | Понимание position tracking |
| **Dependency Graph** | [Architecture § 4](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#4-import-resolution--dependency-graph) | Понимание import resolution |
| **Class Diagram** | [Architecture § 8](./PRD_vscode_validator_v2.3.0_ARCHITECTURE.md#8-class-diagram-core-components) | Дизайн компонентов |

### User Stories

| Epic | Локация | Story Points |
|------|---------|--------------|
| **Epic 1: Jinja2** | [User Stories § Epic 1](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-1-jinja2-template-support) | 13 SP |
| **Epic 2: Imports** | [User Stories § Epic 2](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-2-comment-import-system) | 21 SP |
| **Epic 3: Position** | [User Stories § Epic 3](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-3-enhanced-position-tracking) | 13 SP |
| **Epic 4: Compat** | [User Stories § Epic 4](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-4-backward-compatibility) | 5 SP |
| **Epic 5: UX** | [User Stories § Epic 5](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-5-developer-experience) | 8 SP |
| **Epic 6: Testing** | [User Stories § Epic 6](./PRD_vscode_validator_v2.3.0_USER_STORIES.md#epic-6-testing--quality) | 13 SP |

---

## Ключевые решения

### Уже принятые решения

| ID | Вопрос | Решение | Ратionale |
|----|--------|---------|-----------|
| D0 | Создавать v2.3.0 или v3.0.0? | v2.3.0 (minor) | Backward compatible, не breaking changes |
| D1 | Поддерживать .j2.json формат? | Да | Требование от SDUI team, 70% контрактов используют |
| D2 | Интегрировать с jinja_hot_reload? | Да (feature parity) | Переиспользование логики, консистентность |

### Решения, требующие утверждения (к M1: 2025-10-12)

| ID | Вопрос | Опции | Рекомендация | Impact |
|----|--------|-------|--------------|--------|
| **Q1** | Jinja2 Engine | Nunjucks vs Python bridge | **Nunjucks** | Architecture, maintainability |
| **Q2** | Import Syntax | Только markdown vs расширенный | **Только markdown** | Scope, simplicity |
| **Q3** | Context Format | JSON only vs JSON+YAML | **JSON only v2.3.0** | Scope, timeline |
| **Q4** | Error Severity | Undefined=ERROR vs WARNING | **Undefined=WARNING** | Developer UX |
| **Q5** | Cache Strategy | In-memory vs disk | **In-memory v2.3.0** | Simplicity, performance |
| **Q6** | Distribution | CLI tool vs VSCode ext | **CLI tool v2.3.0** | Time to market |

**Action Required:** Tech Lead approve recommendations к 2025-10-12

---

## Success Criteria для Sign-Off

### Requirements Sign-Off (M1: 2025-10-12)

- [ ] All stakeholders прочитали Executive Summary
- [ ] All Open Questions (Q1-Q6) resolved
- [ ] Success Metrics agreed upon
- [ ] Timeline и milestones утверждены
- [ ] Risks assessed и mitigation plans defined
- [ ] Resource allocation (1 dev, 7 weeks) confirmed

### Prototype Demo (M2: 2025-10-19)

- [ ] Working Jinja2 rendering demo
- [ ] Import resolution demo (single-level)
- [ ] Position tracking demo (basic)
- [ ] Performance baseline established

### Alpha Release (M3: 2025-10-26)

- [ ] All Epics 1-4 implemented
- [ ] Unit tests > 70% coverage
- [ ] Integration tests pass
- [ ] Internal testing (Tech Lead + 2 developers)

### Beta Release (M4: 2025-11-02)

- [ ] All Epics 1-6 implemented
- [ ] Unit tests > 80% coverage
- [ ] Real-world contracts tested (50+)
- [ ] Performance targets met
- [ ] Limited rollout (10 developers)

### GA Release (M5: 2025-11-09)

- [ ] All User Stories completed
- [ ] All acceptance criteria met
- [ ] Documentation complete
- [ ] Beta feedback incorporated
- [ ] Stakeholder sign-off
- [ ] Public release

---

## Работа с документацией

### Обновление требований

**Процесс изменения требований:**

1. **Предложение изменения**
   - Создать issue в трекере с тегом `requirements-change`
   - Описать: что меняется, зачем, impact

2. **Review**
   - Tech Lead reviews impact на timeline и scope
   - Stakeholders review business value
   - Decision: approve/reject/defer

3. **Обновление документов**
   - Обновить соответствующие секции в PRD
   - Обновить User Stories если нужно
   - Обновить Architecture если нужно
   - Increment version в Changelog

4. **Notification**
   - Notify все affected stakeholders
   - Update project timeline если нужно

### Версионирование документов

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 0.1 | 2025-10-05 | Requirements Analysis | Initial draft всех документов |
| 1.0 | TBD | - | Approved version после stakeholder review |

**Location:** `/Users/username/Scripts/docs/`

---

## Контакты и коммуникация

### Stakeholder Matrix

| Stakeholder | Role | Contact | Availability |
|-------------|------|---------|--------------|
| Tech Lead | Approver | TBD | Weekly reviews |
| SDUI Team Lead | Reviewer | TBD | Bi-weekly demos |
| QA Lead | Reviewer | TBD | Test planning |
| Product Owner | Approver | TBD | Milestone reviews |

### Communication Channels

- **Slack:** #sdui-validators (day-to-day)
- **Weekly Sync:** Fridays 10:00 (status updates)
- **Demo Sessions:** Bi-weekly Wednesdays 14:00
- **Document Reviews:** Google Docs comments

### Escalation Path

1. **Blocker:** Developer → Tech Lead (same day)
2. **Scope Change:** Tech Lead → Product Owner (2 days)
3. **Timeline Risk:** Tech Lead → All Stakeholders (weekly)

---

## Полезные ссылки

### Внутренние ресурсы

- **Current Version:** [vscode-validate-on-save_v2.2.0.ts](../vscode-validate-on-save_v2.2.0.ts)
- **Integration:** [alfa-sdui-mcp](/Users/username/Scripts/alfa-sdui-mcp)
- **Jinja Processor:** [jinja_hot_reload_v3.7.0.py](../Python/utils/jinja_hot_reload_v3.7.0.py)
- **Test Contracts:** [/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/](/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/)

### Внешние ресурсы

- **Nunjucks:** https://mozilla.github.io/nunjucks/
- **Jinja2 Docs:** https://jinja.palletsprojects.com/
- **VSCode Tasks:** https://code.visualstudio.com/docs/editor/tasks
- **Source Maps Spec:** https://sourcemaps.info/spec.html

---

## Следующие шаги

### Immediate Actions (Week 1)

**2025-10-07 (Monday):**
- [ ] Circulate Executive Summary для stakeholder review
- [ ] Schedule review meeting (2025-10-10 Wednesday)

**2025-10-08 (Tuesday):**
- [ ] Tech Lead: Assign developer resource
- [ ] Developer: Start technical spike (Nunjucks PoC)

**2025-10-09 (Wednesday):**
- [ ] Collect feedback на PRD documents
- [ ] Resolve Open Questions (Q1-Q6)

**2025-10-10 (Thursday):**
- [ ] Stakeholder review meeting
- [ ] Finalize requirements based on feedback

**2025-10-12 (Friday):**
- [ ] **M1: Requirements Sign-Off**
- [ ] Kick-off development
- [ ] Setup project repository

---

## FAQ

**Q: Где хранятся эти документы?**
A: `/Users/username/Scripts/docs/PRD_vscode_validator_v2.3.0_*.md`

**Q: Как часто обновляются требования?**
A: По мере необходимости, с версионированием в Changelog

**Q: Что делать при конфликте требований?**
A: Escalate на Tech Lead, который resolves с stakeholders

**Q: Как track progress против User Stories?**
A: Используйте issue tracker (GitHub, Jira) для linking stories → tasks

**Q: Где найти примеры .j2.json файлов?**
A: `/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/`

---

**Document Owner:** Requirements Analysis Agent
**Last Updated:** 2025-10-05
**Status:** Draft → Awaiting Stakeholder Review
**Next Review:** 2025-10-10

---

## Appendix: Document Tree

```
docs/
├── PRD_vscode_validator_v2.3.0_INDEX.md (ВЫ ЗДЕСЬ)
├── PRD_vscode_validator_v2.3.0_EXECUTIVE_SUMMARY.md
├── PRD_vscode_validator_v2.3.0.md
├── PRD_vscode_validator_v2.3.0_ARCHITECTURE.md
└── PRD_vscode_validator_v2.3.0_USER_STORIES.md

Total: 5 documents, ~15,000 words, 60 scenarios, 73 story points
```

**Estimated Reading Time (Full Set):** 2-3 hours

**Recommended Reading Order:**
1. INDEX (you are here) - 5 min
2. EXECUTIVE_SUMMARY - 10 min
3. ARCHITECTURE (visual scan) - 15 min
4. Full PRD (sections relevant to your role) - 30-60 min
5. USER_STORIES (your Epic) - 20-30 min

---

**Happy Requirements Reading! 🚀**
