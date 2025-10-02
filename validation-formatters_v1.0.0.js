/**
 * Validation Formatters v1.0.0
 *
 * Утилиты для форматирования результатов валидации SDUI контрактов
 */

import { basename, relative } from 'path';

// Константы
const SEPARATOR_FULL = '━'.repeat(80);
const SEPARATOR_SECTION = '─'.repeat(60);

/**
 * Создает прогресс-бар
 */
export function createProgressBar(current, total, width = 40) {
  const percentage = total > 0 ? current / total : 0;
  const filled = Math.floor(percentage * width);
  const empty = width - filled;

  const bar = '█'.repeat(filled) + '░'.repeat(empty);
  const percent = (percentage * 100).toFixed(0);

  return `[${bar}] ${percent}%`;
}

/**
 * Форматирует заголовок секции
 */
export function formatSectionHeader(title) {
  const padding = Math.floor((80 - title.length - 8) / 2);
  const left = '━'.repeat(padding);
  const right = '━'.repeat(80 - padding - title.length - 8);
  return `${left} ${title} ${right}`;
}

/**
 * Форматирует информацию о файле
 */
export function formatFileInfo(filePath, projectRoot, fileSize) {
  const fileName = basename(filePath);
  const relativePath = relative(projectRoot, filePath);

  let output = formatSectionHeader('FILE INFO') + '\n';
  output += `📄 Name: ${fileName}\n`;
  output += `📁 Path: ${relativePath}\n`;
  if (fileSize) {
    output += `📊 Size: ${fileSize} KB\n`;
  }

  return output;
}

/**
 * Форматирует статус валидации
 */
export function formatValidationStatus(valid) {
  let output = formatSectionHeader(valid ? 'STATUS ✅' : 'STATUS ❌') + '\n';

  if (valid) {
    output += '✅ CONTRACT VALID\n';
    output += '   Контракт готов к использованию\n';
  } else {
    output += '❌ CONTRACT INVALID\n';
    output += '   Исправьте ошибки для использования контракта\n';
  }

  return output;
}

/**
 * Форматирует summary валидации
 */
export function formatSummary(report) {
  let output = formatSectionHeader('SUMMARY') + '\n';

  output += `📊 Web Compatibility: ${report.webCompatibility.toFixed(1)}%\n`;
  output += `🔴 Errors: ${report.errors.length}\n`;
  output += `🟡 Warnings: ${report.warnings.length}\n`;

  if (report.dataBindings?.hasBindings) {
    output += `🔗 Data Bindings: ${report.dataBindings.totalBindings} found\n`;
    output += `   Types: state(${report.dataBindings.byType.state}), `;
    output += `data(${report.dataBindings.byType.data}), `;
    output += `computed(${report.dataBindings.byType.computed})\n`;
  }

  if (report.versions) {
    const versionsList = Object.entries(report.versions.byVersion)
      .map(([v, count]) => `${v}(${count})`)
      .join(', ');
    output += `📦 Components: ${report.versions.totalComponents}\n`;
    output += `   Versions: ${versionsList}\n`;
  }

  return output;
}

/**
 * Конвертирует path в JSON Pointer
 */
export function pathToJsonPointer(path) {
  if (!path) return '';

  // Преобразуем path вида "components[0].id" в "/components/0/id"
  return '/' + path
    .replace(/\[(\d+)\]/g, '/$1')
    .replace(/\./g, '/');
}

/**
 * Создает file:// ссылку с line number
 */
export function createFileLink(filePath, line) {
  const fileUrl = `file://${filePath}`;
  return line ? `${fileUrl}:${line}` : fileUrl;
}

/**
 * Группирует issues по компонентам
 */
export function groupIssuesByComponent(issues) {
  const grouped = new Map();

  issues.forEach(issue => {
    // Пытаемся извлечь компонент из сообщения
    const componentMatch = issue.match(/Component ['"]([^'"]+)['"]/i) ||
                          issue.match(/at path ['"]?([^'":\s]+)/i) ||
                          issue.match(/^([^:]+):/);

    const component = componentMatch ? componentMatch[1] : 'General';

    if (!grouped.has(component)) {
      grouped.set(component, []);
    }
    grouped.get(component).push(issue);
  });

  return grouped;
}

/**
 * Форматирует component box
 */
export function formatComponentBox(componentName, issueCount) {
  const titleLine = ` ${componentName} `;
  const countLine = ` ${issueCount} issue${issueCount !== 1 ? 's' : ''} `;
  const maxWidth = Math.max(titleLine.length, countLine.length);

  const topBorder = '┌─' + '─'.repeat(maxWidth) + '─┐';
  const bottomBorder = '└─' + '─'.repeat(maxWidth) + '─┘';

  const paddedTitle = titleLine.padEnd(maxWidth);
  const paddedCount = countLine.padEnd(maxWidth);

  return [
    topBorder,
    `│ ${paddedTitle} │`,
    `│ ${paddedCount} │`,
    bottomBorder
  ].join('\n');
}

/**
 * Форматирует issue с деталями
 */
export function formatIssue(index, message, filePath, path, jsonPointer) {
  let output = `\n❌ [${index}] ${message}\n`;

  if (path) {
    output += `    Path: ${path}\n`;
  }

  if (jsonPointer) {
    output += `    JSON Pointer: ${jsonPointer}\n`;
  }

  if (filePath) {
    output += `    Link: ${createFileLink(filePath)}\n`;
  }

  return output;
}

/**
 * Форматирует warning с деталями
 */
export function formatWarning(index, message, filePath, path, jsonPointer) {
  let output = `\n⚠️  [${index}] ${message}\n`;

  if (path) {
    output += `    Path: ${path}\n`;
  }

  if (jsonPointer) {
    output += `    JSON Pointer: ${jsonPointer}\n`;
  }

  if (filePath) {
    output += `    Link: ${createFileLink(filePath)}\n`;
  }

  return output;
}

/**
 * Форматирует секцию ошибок с группировкой по компонентам
 */
export function formatErrorsSection(errors, filePath) {
  if (errors.length === 0) return '';

  let output = '\n' + formatSectionHeader(`ERRORS (${errors.length})`) + '\n';

  const grouped = groupIssuesByComponent(errors);

  grouped.forEach((componentErrors, component) => {
    output += '\n' + formatComponentBox(component, componentErrors.length) + '\n';

    componentErrors.forEach((error, index) => {
      // Извлекаем path если есть
      const pathMatch = error.match(/at path ['"]?([^'":\s]+)/i);
      const path = pathMatch ? pathMatch[1] : undefined;
      const jsonPointer = path ? pathToJsonPointer(path) : undefined;

      output += formatIssue(
        index + 1,
        error,
        filePath,
        path,
        jsonPointer
      );
    });
  });

  return output;
}

/**
 * Форматирует секцию warnings с группировкой по компонентам
 */
export function formatWarningsSection(warnings, filePath) {
  if (warnings.length === 0) return '';

  let output = '\n' + formatSectionHeader(`WARNINGS (${warnings.length})`) + '\n';

  const grouped = groupIssuesByComponent(warnings);

  grouped.forEach((componentWarnings, component) => {
    output += '\n' + formatComponentBox(component, componentWarnings.length) + '\n';

    componentWarnings.forEach((warning, index) => {
      // Извлекаем path если есть
      const pathMatch = warning.match(/at path ['"]?([^'":\s]+)/i);
      const path = pathMatch ? pathMatch[1] : undefined;
      const jsonPointer = path ? pathToJsonPointer(path) : undefined;

      output += formatWarning(
        index + 1,
        warning,
        filePath,
        path,
        jsonPointer
      );
    });
  });

  return output;
}

/**
 * Форматирует footer
 */
export function formatFooter(duration) {
  let output = SEPARATOR_FULL + '\n';
  if (duration) {
    output += `⏱️  Completed in ${duration}s\n`;
  }
  return output;
}

/**
 * Форматирует ошибку парсинга
 */
export function formatParseError(filePath, projectRoot, errorMessage) {
  let output = SEPARATOR_FULL + '\n';
  output += formatFileInfo(filePath, projectRoot);
  output += '\n' + formatSectionHeader('PARSE ERROR ❌') + '\n';
  output += errorMessage + '\n';
  output += '\n💡 Исправьте синтаксические ошибки JSON\n';
  output += formatFooter();

  return output;
}
