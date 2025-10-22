/**
 * Console Output Formatter
 *
 * Formats validation results for console output:
 * - Error tables
 * - Summary reports
 * - Progress bars
 * - Statistics
 *
 * @version 2.3.1
 * @module formatters/console-formatter
 */

import { ValidationResult, ValidationError, ValidationSeverity, PerformanceMetrics } from '../types';
import { ColorFormatter } from './color-formatter';
import { LinkGenerator } from './link-generator';

// ============================================================================
// Console Formatter Class
// ============================================================================

/**
 * Console output formatter with rich formatting
 */
export class ConsoleFormatter {
  private colorFormatter: ColorFormatter;
  private linkGenerator: LinkGenerator;
  private indentLevel = 0;
  private readonly INDENT = '  ';

  constructor(enableColor = true, enableLinks = true) {
    this.colorFormatter = new ColorFormatter(enableColor);
    this.linkGenerator = new LinkGenerator(process.cwd(), enableLinks);
  }

  // ========================================================================
  // Main Formatting Methods
  // ========================================================================

  /**
   * Format complete validation result
   */
  formatResult(result: ValidationResult): string {
    const sections: string[] = [];

    // Header
    sections.push(this.formatHeader(result));
    sections.push('');

    // Errors
    if (result.errors.length > 0) {
      sections.push(this.formatErrors(result.errors));
      sections.push('');
    }

    // Summary
    sections.push(this.formatSummary(result));

    // Performance
    if (result.metrics) {
      sections.push('');
      sections.push(this.formatMetrics(result.metrics));
    }

    return sections.join('\n');
  }

  /**
   * Format header
   */
  private formatHeader(result: ValidationResult): string {
    const title = result.isValid ? 'VALIDATION PASSED' : 'VALIDATION FAILED';
    const icon = result.isValid ? '✓' : '✗';
    const color = result.isValid ? this.colorFormatter.green : this.colorFormatter.red;

    const header = color(`${icon} ${title}`);
    const file = this.linkGenerator.generateClickableLink(result.filePath);

    return `${this.colorFormatter.bold(header)}\n${this.colorFormatter.dim('File:')} ${file}`;
  }

  /**
   * Format errors as table
   */
  private formatErrors(errors: ValidationError[]): string {
    const lines: string[] = [];

    lines.push(this.colorFormatter.bold('Errors:'));
    lines.push(this.createSeparator());

    // Group by severity
    const grouped = this.groupBySeverity(errors);

    for (const [severity, severityErrors] of Object.entries(grouped)) {
      if (severityErrors.length === 0) continue;

      lines.push('');
      lines.push(this.formatSeverityHeader(severity as ValidationSeverity, severityErrors.length));

      for (const error of severityErrors) {
        lines.push(this.formatError(error));
      }
    }

    lines.push(this.createSeparator());

    return lines.join('\n');
  }

  /**
   * Format single error
   */
  private formatError(error: ValidationError): string {
    const lines: string[] = [];

    // Location
    const location = this.colorFormatter.dim(`${error.line}:${error.column}`);
    const severityBadge = this.formatSeverityBadge(error.severity);
    const categoryBadge = this.formatCategoryBadge(error.category);

    lines.push(`${this.INDENT}${location} ${severityBadge} ${categoryBadge}`);

    // Message
    const message = this.colorFormatter.colorBySeverity(error.message, error.severity);
    lines.push(`${this.INDENT}${this.INDENT}${message}`);

    // Description
    if (error.description) {
      lines.push(`${this.INDENT}${this.INDENT}${this.colorFormatter.dim(error.description)}`);
    }

    // Context
    if (error.context) {
      lines.push(`${this.INDENT}${this.INDENT}${this.formatContext(error.context, error.column)}`);
    }

    // Fix suggestion
    if (error.fix) {
      const fixLabel = this.colorFormatter.green('Fix:');
      lines.push(`${this.INDENT}${this.INDENT}${fixLabel} ${error.fix}`);
    }

    // Documentation link
    if (error.docUrl) {
      const docLabel = this.colorFormatter.blue('Docs:');
      lines.push(`${this.INDENT}${this.INDENT}${docLabel} ${error.docUrl}`);
    }

    return lines.join('\n');
  }

  /**
   * Format error context with pointer
   */
  private formatContext(context: string, column: number): string {
    const lines = context.split('\n');
    if (lines.length === 0) return '';

    const contextLines: string[] = [];

    // Show context lines
    for (const line of lines) {
      contextLines.push(this.colorFormatter.dim('│ ') + this.colorFormatter.code(line));
    }

    // Add pointer to error location
    const pointer = ' '.repeat(column - 1) + this.colorFormatter.red('^');
    contextLines.push(this.colorFormatter.dim('│ ') + pointer);

    return contextLines.join('\n' + this.INDENT.repeat(2));
  }

  /**
   * Format summary
   */
  private formatSummary(result: ValidationResult): string {
    const lines: string[] = [];

    lines.push(this.colorFormatter.bold('Summary:'));

    // File stats
    lines.push(`${this.INDENT}File size: ${this.formatBytes(result.fileSize)}`);
    lines.push(`${this.INDENT}File type: ${this.colorFormatter.cyan(result.fileType)}`);

    // Error stats
    const errorText =
      result.errorCount === 0
        ? this.colorFormatter.green('0 errors')
        : this.colorFormatter.red(`${result.errorCount} errors`);

    const warningText =
      result.warningCount === 0
        ? this.colorFormatter.dim('0 warnings')
        : this.colorFormatter.yellow(`${result.warningCount} warnings`);

    lines.push(`${this.INDENT}${errorText}, ${warningText}`);

    // Duration
    lines.push(`${this.INDENT}Duration: ${this.formatDuration(result.duration)}`);

    return lines.join('\n');
  }

  /**
   * Format performance metrics
   */
  private formatMetrics(metrics: PerformanceMetrics): string {
    const lines: string[] = [];

    lines.push(this.colorFormatter.bold('Performance:'));

    // Timing breakdown
    lines.push(`${this.INDENT}Parse time: ${this.formatDuration(metrics.parseTime)}`);
    lines.push(`${this.INDENT}Validation time: ${this.formatDuration(metrics.validationTime)}`);
    if (metrics.jinjaTime > 0) {
      lines.push(`${this.INDENT}Jinja time: ${this.formatDuration(metrics.jinjaTime)}`);
    }
    lines.push(`${this.INDENT}Total time: ${this.formatDuration(metrics.totalTime)}`);

    // Throughput
    lines.push(`${this.INDENT}Throughput: ${this.colorFormatter.cyan(metrics.linesPerSecond.toFixed(0))} lines/sec`);

    // Cache
    const cacheStatus = metrics.cacheHit ? this.colorFormatter.green('HIT') : this.colorFormatter.yellow('MISS');
    lines.push(`${this.INDENT}Cache: ${cacheStatus}`);

    // Memory
    if (metrics.memoryUsage) {
      lines.push(`${this.INDENT}Memory: ${this.formatBytes(metrics.memoryUsage)}`);
    }

    return lines.join('\n');
  }

  // ========================================================================
  // Helper Methods
  // ========================================================================

  /**
   * Format severity badge
   */
  private formatSeverityBadge(severity: ValidationSeverity): string {
    const badges = {
      [ValidationSeverity.ERROR]: this.colorFormatter.boldRed('[ERROR]'),
      [ValidationSeverity.WARNING]: this.colorFormatter.boldYellow('[WARN]'),
      [ValidationSeverity.INFO]: this.colorFormatter.blue('[INFO]'),
      [ValidationSeverity.HINT]: this.colorFormatter.gray('[HINT]')
    };

    return badges[severity];
  }

  /**
   * Format category badge
   */
  private formatCategoryBadge(category: string): string {
    return this.colorFormatter.dim(`[${category.toUpperCase()}]`);
  }

  /**
   * Format severity header
   */
  private formatSeverityHeader(severity: ValidationSeverity, count: number): string {
    const text = `${severity.toUpperCase()} (${count})`;
    return this.colorFormatter.colorBySeverity(text, severity);
  }

  /**
   * Group errors by severity
   */
  private groupBySeverity(errors: ValidationError[]): Record<ValidationSeverity, ValidationError[]> {
    const grouped: Record<ValidationSeverity, ValidationError[]> = {
      [ValidationSeverity.ERROR]: [],
      [ValidationSeverity.WARNING]: [],
      [ValidationSeverity.INFO]: [],
      [ValidationSeverity.HINT]: []
    };

    for (const error of errors) {
      grouped[error.severity].push(error);
    }

    return grouped;
  }

  /**
   * Format bytes
   */
  private formatBytes(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = bytes;
    let unitIndex = 0;

    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024;
      unitIndex++;
    }

    return this.colorFormatter.cyan(`${value.toFixed(2)} ${units[unitIndex]}`);
  }

  /**
   * Format duration
   */
  private formatDuration(ms: number): string {
    if (ms < 1) {
      return this.colorFormatter.cyan(`${(ms * 1000).toFixed(0)}μs`);
    } else if (ms < 1000) {
      return this.colorFormatter.cyan(`${ms.toFixed(2)}ms`);
    } else {
      return this.colorFormatter.cyan(`${(ms / 1000).toFixed(2)}s`);
    }
  }

  /**
   * Create separator line
   */
  private createSeparator(width = 80): string {
    return this.colorFormatter.dim('─'.repeat(width));
  }

  /**
   * Format progress bar
   */
  formatProgress(current: number, total: number, label?: string): string {
    const percentage = (current / total) * 100;
    const barWidth = 40;
    const filled = Math.floor((barWidth * current) / total);
    const empty = barWidth - filled;

    const bar = this.colorFormatter.green('█'.repeat(filled)) + this.colorFormatter.dim('░'.repeat(empty));

    const percent = this.colorFormatter.cyan(`${percentage.toFixed(1)}%`);
    const counter = this.colorFormatter.dim(`${current}/${total}`);

    return `${label ? label + ' ' : ''}[${bar}] ${percent} ${counter}`;
  }

  /**
   * Format table
   */
  formatTable(headers: string[], rows: string[][]): string {
    const columnWidths = headers.map((header, i) => {
      const maxRowWidth = Math.max(...rows.map((row) => (row[i] || '').length));
      return Math.max(header.length, maxRowWidth);
    });

    const lines: string[] = [];

    // Header
    const headerRow = headers.map((header, i) => header.padEnd(columnWidths[i])).join(' │ ');
    lines.push(this.colorFormatter.bold(headerRow));

    // Separator
    lines.push(columnWidths.map((width) => '─'.repeat(width)).join('─┼─'));

    // Rows
    for (const row of rows) {
      const rowStr = row.map((cell, i) => (cell || '').padEnd(columnWidths[i])).join(' │ ');
      lines.push(rowStr);
    }

    return lines.join('\n');
  }

  /**
   * Format list
   */
  formatList(items: string[], bullet = '•'): string {
    return items.map((item) => `${this.colorFormatter.dim(bullet)} ${item}`).join('\n');
  }

  /**
   * Set indent level
   */
  setIndent(level: number): void {
    this.indentLevel = level;
  }

  /**
   * Get current indent
   */
  getIndent(): string {
    return this.INDENT.repeat(this.indentLevel);
  }
}

// ============================================================================
// Default Instance
// ============================================================================

/**
 * Default console formatter instance
 */
export const consoleFormatter = new ConsoleFormatter();

// ============================================================================
// Exports
// ============================================================================

export default ConsoleFormatter;
