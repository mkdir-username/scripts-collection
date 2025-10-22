/**
 * ANSI Color Formatter for Terminal Output
 *
 * Provides color and style utilities for console output:
 * - ANSI escape codes
 * - Color detection
 * - Style chaining
 * - Cross-platform support
 *
 * @version 2.3.1
 * @module formatters/color-formatter
 */

import { ValidationSeverity, ErrorCategory } from '../types';

// ============================================================================
// ANSI Escape Codes
// ============================================================================

/**
 * ANSI color codes
 */
export const ANSI = {
  // Reset
  reset: '\x1b[0m',

  // Text colors
  black: '\x1b[30m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  gray: '\x1b[90m',

  // Bright colors
  brightRed: '\x1b[91m',
  brightGreen: '\x1b[92m',
  brightYellow: '\x1b[93m',
  brightBlue: '\x1b[94m',
  brightMagenta: '\x1b[95m',
  brightCyan: '\x1b[96m',
  brightWhite: '\x1b[97m',

  // Background colors
  bgBlack: '\x1b[40m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m',
  bgBlue: '\x1b[44m',
  bgMagenta: '\x1b[45m',
  bgCyan: '\x1b[46m',
  bgWhite: '\x1b[47m',

  // Styles
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  italic: '\x1b[3m',
  underline: '\x1b[4m',
  blink: '\x1b[5m',
  reverse: '\x1b[7m',
  hidden: '\x1b[8m',
  strikethrough: '\x1b[9m'
} as const;

// ============================================================================
// Color Detection
// ============================================================================

/**
 * Check if terminal supports colors
 */
export function supportsColor(): boolean {
  // Check environment variables
  if (process.env.NO_COLOR || process.env.NODE_DISABLE_COLORS) {
    return false;
  }

  if (process.env.FORCE_COLOR) {
    return true;
  }

  // Check if stdout is a TTY
  if (!process.stdout.isTTY) {
    return false;
  }

  // Check TERM environment variable
  const term = process.env.TERM || '';
  if (term === 'dumb') {
    return false;
  }

  // Check for color support
  if (term.includes('color') || term.includes('256') || term.includes('ansi')) {
    return true;
  }

  // Default to true for modern terminals
  return true;
}

/**
 * Strip ANSI codes from string
 */
export function stripAnsi(text: string): string {
  return text.replace(/\x1b\[[0-9;]*m/g, '');
}

/**
 * Get text length without ANSI codes
 */
export function getTextLength(text: string): number {
  return stripAnsi(text).length;
}

// ============================================================================
// Color Formatter Class
// ============================================================================

/**
 * Color formatter with chaining support
 */
export class ColorFormatter {
  private colorEnabled: boolean;

  constructor(enabled?: boolean) {
    this.colorEnabled = enabled ?? supportsColor();
  }

  /**
   * Enable or disable colors
   */
  setEnabled(enabled: boolean): void {
    this.colorEnabled = enabled;
  }

  /**
   * Apply color to text
   */
  private apply(text: string, codes: string[]): string {
    if (!this.colorEnabled) {
      return text;
    }
    return codes.join('') + text + ANSI.reset;
  }

  // Basic colors
  red(text: string): string {
    return this.apply(text, [ANSI.red]);
  }

  green(text: string): string {
    return this.apply(text, [ANSI.green]);
  }

  yellow(text: string): string {
    return this.apply(text, [ANSI.yellow]);
  }

  blue(text: string): string {
    return this.apply(text, [ANSI.blue]);
  }

  magenta(text: string): string {
    return this.apply(text, [ANSI.magenta]);
  }

  cyan(text: string): string {
    return this.apply(text, [ANSI.cyan]);
  }

  white(text: string): string {
    return this.apply(text, [ANSI.white]);
  }

  gray(text: string): string {
    return this.apply(text, [ANSI.gray]);
  }

  // Bright colors
  brightRed(text: string): string {
    return this.apply(text, [ANSI.brightRed]);
  }

  brightGreen(text: string): string {
    return this.apply(text, [ANSI.brightGreen]);
  }

  brightYellow(text: string): string {
    return this.apply(text, [ANSI.brightYellow]);
  }

  brightBlue(text: string): string {
    return this.apply(text, [ANSI.brightBlue]);
  }

  // Styles
  bold(text: string): string {
    return this.apply(text, [ANSI.bold]);
  }

  dim(text: string): string {
    return this.apply(text, [ANSI.dim]);
  }

  italic(text: string): string {
    return this.apply(text, [ANSI.italic]);
  }

  underline(text: string): string {
    return this.apply(text, [ANSI.underline]);
  }

  strikethrough(text: string): string {
    return this.apply(text, [ANSI.strikethrough]);
  }

  // Combined styles
  boldRed(text: string): string {
    return this.apply(text, [ANSI.bold, ANSI.red]);
  }

  boldGreen(text: string): string {
    return this.apply(text, [ANSI.bold, ANSI.green]);
  }

  boldYellow(text: string): string {
    return this.apply(text, [ANSI.bold, ANSI.yellow]);
  }

  boldBlue(text: string): string {
    return this.apply(text, [ANSI.bold, ANSI.blue]);
  }

  // Severity-based coloring
  colorBySeverity(text: string, severity: ValidationSeverity): string {
    switch (severity) {
      case ValidationSeverity.ERROR:
        return this.boldRed(text);
      case ValidationSeverity.WARNING:
        return this.boldYellow(text);
      case ValidationSeverity.INFO:
        return this.blue(text);
      case ValidationSeverity.HINT:
        return this.gray(text);
      default:
        return text;
    }
  }

  // Category-based coloring
  colorByCategory(text: string, category: ErrorCategory): string {
    switch (category) {
      case ErrorCategory.SYNTAX:
        return this.red(text);
      case ErrorCategory.STRUCTURE:
        return this.yellow(text);
      case ErrorCategory.SCHEMA:
        return this.blue(text);
      case ErrorCategory.JINJA:
        return this.magenta(text);
      case ErrorCategory.COMPATIBILITY:
        return this.cyan(text);
      case ErrorCategory.PERFORMANCE:
        return this.brightYellow(text);
      case ErrorCategory.SECURITY:
        return this.brightRed(text);
      default:
        return text;
    }
  }

  // Success/failure indicators
  success(text: string): string {
    return this.green('✓ ') + this.green(text);
  }

  failure(text: string): string {
    return this.red('✗ ') + this.red(text);
  }

  warning(text: string): string {
    return this.yellow('⚠ ') + this.yellow(text);
  }

  info(text: string): string {
    return this.blue('ℹ ') + this.blue(text);
  }

  // Progress indicators
  spinner(text: string, frame: number): string {
    const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    const spinner = frames[frame % frames.length];
    return this.cyan(spinner) + ' ' + text;
  }

  // Highlighting
  highlight(text: string, pattern: string | RegExp): string {
    if (!this.colorEnabled) {
      return text;
    }

    const regex = typeof pattern === 'string' ? new RegExp(pattern, 'g') : pattern;
    return text.replace(regex, (match) => this.boldYellow(match));
  }

  // Code formatting
  code(text: string): string {
    return this.apply(text, [ANSI.dim, ANSI.cyan]);
  }

  // Path formatting
  path(text: string): string {
    return this.underline(this.blue(text));
  }

  // Number formatting
  number(value: number): string {
    return this.cyan(value.toString());
  }

  // Timestamp formatting
  timestamp(date: Date): string {
    return this.gray(date.toISOString());
  }
}

// ============================================================================
// Default Instance
// ============================================================================

/**
 * Default color formatter instance
 */
export const colorFormatter = new ColorFormatter();

// Convenience exports
export const {
  red,
  green,
  yellow,
  blue,
  magenta,
  cyan,
  white,
  gray,
  bold,
  dim,
  italic,
  underline,
  success,
  failure,
  warning,
  info
} = colorFormatter;

// ============================================================================
// Exports
// ============================================================================

export default ColorFormatter;
