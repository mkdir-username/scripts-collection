/**
 * Main Validation Entry Point
 * SDUI JSON Validator v2.3.1
 *
 * ;02=0O DC=:F8O 20;840F88 D09;>2 A ?>445@6:>9 Jinja2 H01;>=>2
 *
 * @module main
 * @version 2.3.1
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  ValidationResult,
  ValidationError,
  ValidatorConfig,
  FileType,
  ValidationSeverity,
  ErrorCategory,
  PerformanceMetrics
} from './types';

// ============================================================================
// Interfaces
// ============================================================================

interface ValidateFileOptions {
  strict?: boolean;
  jinjaAware?: boolean;
  maxFileSize?: number;
  trackPerformance?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const SUPPORTED_EXTENSIONS = ['.json', '.jinja.json', '.j2.java'];

// ============================================================================
// File Type Detection
// ============================================================================

/**
 * ?@545;O5B B8? D09;0 ?> @0AH8@5=8N
 */
function detectFileType(filePath: string): FileType {
  const fileName = path.basename(filePath).toLowerCase();

  if (fileName.endsWith('.jinja.json')) {
    return FileType.JINJA_JSON;
  }
  if (fileName.endsWith('.j2.java')) {
    return FileType.J2_JAVA;
  }
  if (fileName.endsWith('.json')) {
    return FileType.JSON;
  }

  return FileType.UNKNOWN;
}

/**
 * @>25@O5B =0;8G85 Jinja A8=B0:A8A0 2 A>45@68<><
 */
function hasJinjaSyntax(content: string): boolean {
  const jinjaPatterns = [
    /\{\{.*?\}\}/s,      // {{ variables }}
    /\{%.*?%\}/s,        // {% blocks %}
    /\{#.*?#\}/s         // {# comments #}
  ];

  return jinjaPatterns.some(pattern => pattern.test(content));
}

// ============================================================================
// Content Validation
// ============================================================================

/**
 * 0;848@C5B JSON A8=B0:A8A
 */
function validateJsonSyntax(content: string, filePath: string): ValidationError[] {
  const errors: ValidationError[] = [];

  try {
    JSON.parse(content);
  } catch (error) {
    if (error instanceof SyntaxError) {
      // 72;5G5=85 ?>78F88 87 A>>1I5=8O >1 >H81:5
      const match = error.message.match(/at position (\d+)/);
      const position = match ? parseInt(match[1], 10) : 0;

      const lines = content.substring(0, position).split('\n');
      const line = lines.length;
      const column = lines[lines.length - 1].length + 1;

      errors.push({
        severity: ValidationSeverity.ERROR,
        category: ErrorCategory.SYNTAX,
        message: 'JSON syntax error',
        description: error.message,
        line,
        column,
        code: 'JSON_PARSE_ERROR',
        file: filePath
      });
    }
  }

  return errors;
}

/**
 * 0;848@C5B Jinja A8=B0:A8A
 */
function validateJinjaSyntax(content: string, filePath: string): ValidationError[] {
  const errors: ValidationError[] = [];
  const lines = content.split('\n');

  // @>25@:0 ?0@=>AB8 Jinja B53>2
  let blockStack: Array<{ type: string; line: number; column: number }> = [];

  lines.forEach((line, lineIndex) => {
    const lineNum = lineIndex + 1;

    // >8A: >B:@K20NI8E 1;>:>2
    const blockStartRegex = /\{%\s*(if|for|block|macro|call|filter|set|with)\s/g;
    let match;

    while ((match = blockStartRegex.exec(line)) !== null) {
      blockStack.push({
        type: match[1],
        line: lineNum,
        column: match.index + 1
      });
    }

    // >8A: 70:@K20NI8E 1;>:>2
    const blockEndRegex = /\{%\s*end(if|for|block|macro|call|filter|set|with)\s*%\}/g;

    while ((match = blockEndRegex.exec(line)) !== null) {
      const endType = match[1];
      const lastBlock = blockStack.pop();

      if (!lastBlock) {
        errors.push({
          severity: ValidationSeverity.ERROR,
          category: ErrorCategory.JINJA,
          message: `Unexpected closing tag: {% end${endType} %}`,
          description: 'No matching opening tag found',
          line: lineNum,
          column: match.index + 1,
          code: 'JINJA_UNMATCHED_CLOSE',
          file: filePath
        });
      } else if (lastBlock.type !== endType) {
        errors.push({
          severity: ValidationSeverity.ERROR,
          category: ErrorCategory.JINJA,
          message: `Mismatched Jinja block: expected {% end${lastBlock.type} %}, got {% end${endType} %}`,
          line: lineNum,
          column: match.index + 1,
          code: 'JINJA_BLOCK_MISMATCH',
          file: filePath
        });
      }
    }
  });

  // @>25@:0 =570:@KBKE 1;>:>2
  blockStack.forEach(block => {
    errors.push({
      severity: ValidationSeverity.ERROR,
      category: ErrorCategory.JINJA,
      message: `Unclosed Jinja block: {% ${block.type} %}`,
      description: 'Block was opened but never closed',
      line: block.line,
      column: block.column,
      code: 'JINJA_UNCLOSED_BLOCK',
      file: filePath
    });
  });

  return errors;
}

/**
 * 1@01>B:0 Jinja H01;>=0 4;O JSON 20;840F88
 */
function preprocessJinjaTemplate(content: string): string {
  let processed = content;

  // 0<5=0 ?5@5<5==KE Jinja =0 703;CH:8
  processed = processed.replace(/\{\{[^}]*\}\}/g, (match) => {
    // !>E@0=O5< B8? 7=0G5=8O 5A;8 2>7<>6=>
    if (match.includes('|') || match.includes('default')) {
      return '""'; // !B@>:>2>5 7=0G5=85 ?> C<>;G0=8N
    }
    return 'null';
  });

  // #40;5=85 :><<5=B0@852 Jinja
  processed = processed.replace(/\{#[^#]*#\}/g, '');

  // 1@01>B:0 CA;>2=KE 1;>:>2 - 15@5< B>;L:> A>45@68<>5 ?5@2>3> 1;>:0
  processed = processed.replace(/\{%\s*if\s+[^%]*%\}([\s\S]*?)\{%\s*endif\s*%\}/g, '$1');
  processed = processed.replace(/\{%\s*if\s+[^%]*%\}([\s\S]*?)\{%\s*else\s*%\}[\s\S]*?\{%\s*endif\s*%\}/g, '$1');

  // 1@01>B:0 F8:;>2 - 15@5< >4=C 8B5@0F8N
  processed = processed.replace(/\{%\s*for\s+[^%]*%\}([\s\S]*?)\{%\s*endfor\s*%\}/g, '$1');

  // #40;5=85 4@C38E 1;>:>2
  processed = processed.replace(/\{%[^%]*%\}/g, '');

  return processed;
}

// ============================================================================
// Main Validation Function
// ============================================================================

/**
 * 0;848@C5B D09; A JSON/Jinja :>=B5=B><
 *
 * @param filePath - CBL : D09;C 4;O 20;840F88
 * @param options - ?F88 20;840F88
 * @returns  57C;LB0B 20;840F88
 */
export async function validateFile(
  filePath: string,
  options: ValidateFileOptions = {}
): Promise<ValidationResult> {
  const startTime = Date.now();
  const errors: ValidationError[] = [];

  // 0AB@>9:8 ?> C<>;G0=8N
  const config = {
    strict: options.strict ?? true,
    jinjaAware: options.jinjaAware ?? true,
    maxFileSize: options.maxFileSize ?? DEFAULT_MAX_FILE_SIZE,
    trackPerformance: options.trackPerformance ?? true
  };

  // @>25@:0 ACI5AB2>20=8O D09;0
  if (!fs.existsSync(filePath)) {
    errors.push({
      severity: ValidationSeverity.ERROR,
      category: ErrorCategory.SYNTAX,
      message: 'File not found',
      description: `Cannot find file: ${filePath}`,
      line: 0,
      column: 0,
      code: 'FILE_NOT_FOUND',
      file: filePath
    });

    return createValidationResult(filePath, errors, startTime);
  }

  // @>25@:0 @0AH8@5=8O D09;0
  const fileType = detectFileType(filePath);
  if (fileType === FileType.UNKNOWN) {
    errors.push({
      severity: ValidationSeverity.WARNING,
      category: ErrorCategory.SYNTAX,
      message: 'Unsupported file type',
      description: `Supported extensions: ${SUPPORTED_EXTENSIONS.join(', ')}`,
      line: 0,
      column: 0,
      code: 'UNSUPPORTED_FILE_TYPE',
      file: filePath
    });
  }

  // @>25@:0 @07<5@0 D09;0
  const stats = fs.statSync(filePath);
  if (stats.size > config.maxFileSize) {
    errors.push({
      severity: ValidationSeverity.ERROR,
      category: ErrorCategory.PERFORMANCE,
      message: 'File too large',
      description: `File size ${stats.size} exceeds maximum ${config.maxFileSize}`,
      line: 0,
      column: 0,
      code: 'FILE_TOO_LARGE',
      file: filePath
    });

    return createValidationResult(filePath, errors, startTime, stats.size, fileType);
  }

  // 'B5=85 A>45@68<>3> D09;0
  const readStartTime = Date.now();
  const content = fs.readFileSync(filePath, 'utf-8');
  const readTime = Date.now() - readStartTime;

  // ?@545;5=85 =0;8G8O Jinja A8=B0:A8A0
  const hasJinja = hasJinjaSyntax(content);

  // 0;840F8O Jinja A8=B0:A8A0 (5A;8 2:;NG5=>)
  if (config.jinjaAware && hasJinja) {
    const jinjaStartTime = Date.now();
    const jinjaErrors = validateJinjaSyntax(content, filePath);
    errors.push(...jinjaErrors);

    // @54>1@01>B:0 Jinja 4;O JSON 20;840F88
    const processedContent = preprocessJinjaTemplate(content);
    const jsonErrors = validateJsonSyntax(processedContent, filePath);
    errors.push(...jsonErrors);

    const jinjaTime = Date.now() - jinjaStartTime;
  } else {
    // @O<0O 20;840F8O JSON
    const jsonErrors = validateJsonSyntax(content, filePath);
    errors.push(...jsonErrors);
  }

  // !>740=85 @57C;LB0B0 20;840F88
  return createValidationResult(
    filePath,
    errors,
    startTime,
    stats.size,
    fileType,
    content.split('\n').length,
    readTime
  );
}

/**
 * !>7405B >1J5:B @57C;LB0B0 20;840F88
 */
function createValidationResult(
  filePath: string,
  errors: ValidationError[],
  startTime: number,
  fileSize: number = 0,
  fileType: FileType = FileType.UNKNOWN,
  totalLines: number = 0,
  readTime: number = 0
): ValidationResult {
  const duration = Date.now() - startTime;
  const errorCount = errors.filter(e => e.severity === ValidationSeverity.ERROR).length;
  const warningCount = errors.filter(e => e.severity === ValidationSeverity.WARNING).length;

  const metrics: PerformanceMetrics = {
    totalTime: duration,
    readTime,
    parseTime: duration - readTime,
    validationTime: duration,
    jinjaTime: 0,
    cacheHit: false,
    linesPerSecond: totalLines > 0 ? (totalLines / duration) * 1000 : 0,
    totalLines
  };

  return {
    isValid: errorCount === 0,
    errors,
    filePath,
    timestamp: startTime,
    duration,
    fileSize,
    fileType,
    metrics,
    warningCount,
    errorCount
  };
}

// ============================================================================
// Batch Validation
// ============================================================================

/**
 * 0;848@C5B =5A:>;L:> D09;>2
 */
export async function validateFiles(
  filePaths: string[],
  options: ValidateFileOptions = {}
): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];

  for (const filePath of filePaths) {
    const result = await validateFile(filePath, options);
    results.push(result);
  }

  return results;
}

/**
 * 0;848@C5B 2A5 D09;K 2 48@5:B>@88
 */
export async function validateDirectory(
  dirPath: string,
  options: ValidateFileOptions & { recursive?: boolean } = {}
): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];

  if (!fs.existsSync(dirPath)) {
    throw new Error(`Directory not found: ${dirPath}`);
  }

  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);

    if (entry.isDirectory() && options.recursive) {
      const subResults = await validateDirectory(fullPath, options);
      results.push(...subResults);
    } else if (entry.isFile() && SUPPORTED_EXTENSIONS.some(ext => entry.name.endsWith(ext))) {
      const result = await validateFile(fullPath, options);
      results.push(result);
    }
  }

  return results;
}

// ============================================================================
// Exports
// ============================================================================

export default validateFile;
