/**
 * VSCode Link Generator
 *
 * Generates clickable links for:
 * - File paths with line numbers
 * - Error locations
 * - Documentation URLs
 * - Source references
 *
 * @version 2.3.1
 * @module formatters/link-generator
 */

import * as path from 'path';
import { ValidationError, VscodeLink } from '../types';

// ============================================================================
// Link Generation
// ============================================================================

/**
 * VSCode link generator
 */
export class LinkGenerator {
  private workspaceRoot: string;
  private enableLinks: boolean;

  constructor(workspaceRoot?: string, enableLinks = true) {
    this.workspaceRoot = workspaceRoot || process.cwd();
    this.enableLinks = enableLinks;
  }

  /**
   * Generate VSCode file link
   *
   * Format: file:///path/to/file.ts:line:column
   */
  generateFileLink(filePath: string, line?: number, column?: number): string {
    if (!this.enableLinks) {
      return this.formatSimplePath(filePath, line, column);
    }

    const absolutePath = path.isAbsolute(filePath)
      ? filePath
      : path.join(this.workspaceRoot, filePath);

    let link = `file://${absolutePath}`;

    if (line !== undefined) {
      link += `:${line}`;
      if (column !== undefined) {
        link += `:${column}`;
      }
    }

    return link;
  }

  /**
   * Generate clickable terminal link
   *
   * Format: \x1b]8;;file:///path\x1b\\text\x1b]8;;\x1b\\
   */
  generateClickableLink(filePath: string, text?: string, line?: number, column?: number): string {
    if (!this.enableLinks) {
      return text || this.formatSimplePath(filePath, line, column);
    }

    const link = this.generateFileLink(filePath, line, column);
    const displayText = text || this.formatSimplePath(filePath, line, column);

    // OSC 8 hyperlink format
    return `\x1b]8;;${link}\x1b\\${displayText}\x1b]8;;\x1b\\`;
  }

  /**
   * Generate link from validation error
   */
  generateErrorLink(error: ValidationError): string {
    if (!error.file) {
      return this.formatLocation(error.line, error.column);
    }

    return this.generateClickableLink(
      error.file,
      this.formatSimplePath(error.file, error.line, error.column),
      error.line,
      error.column
    );
  }

  /**
   * Generate VSCode link object
   */
  generateVscodeLink(filePath: string, line: number, column: number, text?: string): VscodeLink {
    return {
      file: path.isAbsolute(filePath) ? filePath : path.join(this.workspaceRoot, filePath),
      line,
      column,
      text: text || this.formatSimplePath(filePath, line, column)
    };
  }

  /**
   * Format simple path without links
   */
  private formatSimplePath(filePath: string, line?: number, column?: number): string {
    const relativePath = this.getRelativePath(filePath);
    let result = relativePath;

    if (line !== undefined) {
      result += `:${line}`;
      if (column !== undefined) {
        result += `:${column}`;
      }
    }

    return result;
  }

  /**
   * Format location (line:column)
   */
  private formatLocation(line: number, column: number): string {
    return `${line}:${column}`;
  }

  /**
   * Get relative path from workspace root
   */
  private getRelativePath(filePath: string): string {
    if (!path.isAbsolute(filePath)) {
      return filePath;
    }

    const relative = path.relative(this.workspaceRoot, filePath);
    return relative.startsWith('..') ? filePath : relative;
  }

  /**
   * Convert file path to URI
   */
  filePathToUri(filePath: string): string {
    const absolutePath = path.isAbsolute(filePath)
      ? filePath
      : path.join(this.workspaceRoot, filePath);

    // Convert Windows paths to URI format
    const normalized = absolutePath.replace(/\\/g, '/');
    return `file://${normalized.startsWith('/') ? '' : '/'}${normalized}`;
  }

  /**
   * Convert URI to file path
   */
  uriToFilePath(uri: string): string {
    if (!uri.startsWith('file://')) {
      return uri;
    }

    const filePath = uri.substring(7);
    // Convert URI format back to Windows paths if needed
    return process.platform === 'win32' ? filePath.replace(/\//g, '\\') : filePath;
  }

  /**
   * Generate documentation link
   */
  generateDocLink(section: string): string {
    const baseUrl = 'https://confluence.moscow.alfaintra.net/display/FMS';
    return `${baseUrl}/${encodeURIComponent(section)}`;
  }

  /**
   * Generate GitHub link
   */
  generateGitHubLink(repo: string, filePath: string, line?: number): string {
    let link = `https://github.com/${repo}/blob/master/${filePath}`;
    if (line !== undefined) {
      link += `#L${line}`;
    }
    return link;
  }

  /**
   * Format multiple links
   */
  formatMultipleLinks(links: Array<{ file: string; line?: number; column?: number }>): string {
    return links.map((link) => this.generateClickableLink(link.file, undefined, link.line, link.column)).join('\n');
  }

  /**
   * Check if terminal supports hyperlinks
   */
  static supportsHyperlinks(): boolean {
    // Check for known terminals that support OSC 8
    const term = process.env.TERM_PROGRAM || process.env.TERM || '';

    const supportedTerminals = ['iTerm.app', 'vscode', 'hyper', 'gnome-terminal', 'konsole'];

    return supportedTerminals.some((supported) => term.toLowerCase().includes(supported.toLowerCase()));
  }

  /**
   * Enable or disable links
   */
  setEnabled(enabled: boolean): void {
    this.enableLinks = enabled;
  }

  /**
   * Set workspace root
   */
  setWorkspaceRoot(root: string): void {
    this.workspaceRoot = root;
  }

  /**
   * Get workspace root
   */
  getWorkspaceRoot(): string {
    return this.workspaceRoot;
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create a link with optional styling
 */
export function createStyledLink(
  filePath: string,
  line: number,
  column: number,
  style: (text: string) => string = (t) => t
): string {
  const generator = new LinkGenerator();
  const link = generator.generateClickableLink(filePath, undefined, line, column);
  return style(link);
}

/**
 * Batch generate links
 */
export function generateBatchLinks(errors: ValidationError[]): VscodeLink[] {
  const generator = new LinkGenerator();
  return errors
    .filter((error) => error.file)
    .map((error) => generator.generateVscodeLink(error.file!, error.line, error.column, error.message));
}

/**
 * Extract file path from error message
 */
export function extractFilePathFromMessage(message: string): { file: string; line?: number; column?: number } | null {
  // Match patterns like: file.ts:10:5 or file.ts(10,5)
  const patterns = [
    /([^\s:]+):(\d+):(\d+)/, // file.ts:10:5
    /([^\s(]+)\((\d+),(\d+)\)/, // file.ts(10,5)
    /at ([^\s:]+):(\d+):(\d+)/ // at file.ts:10:5
  ];

  for (const pattern of patterns) {
    const match = message.match(pattern);
    if (match) {
      return {
        file: match[1],
        line: parseInt(match[2], 10),
        column: parseInt(match[3], 10)
      };
    }
  }

  return null;
}

// ============================================================================
// Default Instance
// ============================================================================

/**
 * Default link generator instance
 */
export const linkGenerator = new LinkGenerator();

// ============================================================================
// Exports
// ============================================================================

export default LinkGenerator;
