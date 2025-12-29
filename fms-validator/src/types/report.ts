/**
 * FMS Contract Validator - AI-Friendly Report Types
 * Optimized for Claude AI agent consumption
 */

// ═══════════════════════════════════════════════════════════════
// CORE ENUMS
// ═══════════════════════════════════════════════════════════════

export type Severity = 'critical' | 'error' | 'warning' | 'info';

export type ErrorCategory =
  | 'UNKNOWN_COMPONENT'      // type не существует в SDUI
  | 'MISSING_REQUIRED'       // обязательное поле отсутствует
  | 'INVALID_ENUM'           // значение не из enum
  | 'TYPE_MISMATCH'          // неправильный тип данных
  | 'EL_SYNTAX'              // синтаксис Expression Language
  | 'EL_UNDEFINED_REF'       // ${data.x} где x не существует
  | 'EL_BOOLEAN_REQUIRED'    // if требует boolean
  | 'RELEASE_VERSION'        // компонент не released
  | 'SCHEMA_REF'             // невалидный $ref
  | 'RENDER_ERROR'           // ошибка рендеринга в браузере
  | 'CONSOLE_ERROR';         // console.error из браузера

// ═══════════════════════════════════════════════════════════════
// LOCATION & CONTEXT
// ═══════════════════════════════════════════════════════════════

export interface SourceLocation {
  /** JSON Path: $.rootElement.content.children[2].type */
  jsonPath: string;
  /** JSON Pointer: /rootElement/content/children/2/type */
  jsonPointer: string;
  /** Snippet of surrounding JSON (3-5 lines) */
  snippet: string;
  /** Line number hint (approximate, for compiled JSON) */
  lineHint?: number;
}

export interface ComponentContext {
  /** Component type: StackView, LabelView, etc. */
  type: string;
  /** Schema version: v1, v2 */
  version: string;
  /** Path to SDUI schema */
  schemaPath: string;
  /** Path to samples */
  samplesPath: string;
}

// ═══════════════════════════════════════════════════════════════
// VALIDATION ERROR
// ═══════════════════════════════════════════════════════════════

export interface ValidationError {
  /** Unique ID: E001, E002, W001 */
  id: string;

  /** Severity level */
  severity: Severity;

  /** Error category for grouping */
  category: ErrorCategory;

  /** Is this error blocking render? */
  blocking: boolean;

  /** Where the error occurred */
  location: SourceLocation;

  /** Human-readable error message */
  message: string;

  /** Raw console/runtime message (if applicable) */
  rawMessage?: string;

  /** Component context (if error is component-related) */
  component?: ComponentContext;

  /** What was expected vs what was found */
  expected?: {
    type?: string;
    values?: string[];
    schema?: string;
  };

  /** What was actually found */
  actual?: {
    type?: string;
    value?: unknown;
  };

  /** How to fix this error */
  fix: {
    /** Action to take */
    action: string;
    /** Suggested replacement */
    suggestion?: string;
    /** Reference docs */
    refs: string[];
  };

  /** AI-optimized hint for fixing */
  aiHint: string;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT TREE VALIDATION
// ═══════════════════════════════════════════════════════════════

export interface ComponentNode {
  /** JSON path to this component */
  path: string;
  /** Component type */
  type: string;
  /** Validation status */
  status: 'OK' | 'WARN' | 'FAIL';
  /** Error ID if failed */
  errorId?: string;
  /** Nested children */
  children: ComponentNode[];
}

// ═══════════════════════════════════════════════════════════════
// EXPRESSION LANGUAGE VALIDATION
// ═══════════════════════════════════════════════════════════════

export interface ExpressionValidation {
  /** The expression: ${data.userName} */
  expression: string;
  /** Where used */
  path: string;
  /** Expression type */
  type: 'data' | 'state' | 'computed' | 'mixed';
  /** Status */
  status: 'OK' | 'WARN' | 'FAIL';
  /** Issues found */
  issues: string[];
}

// ═══════════════════════════════════════════════════════════════
// RUNTIME VALIDATION (Playwright)
// ═══════════════════════════════════════════════════════════════

export interface RuntimeValidation {
  /** Did the page render? */
  rendered: boolean;
  /** Render status */
  renderStatus: 'FULL' | 'PARTIAL' | 'FAILED';
  /** Console errors */
  consoleErrors: Array<{
    level: 'error' | 'warn';
    message: string;
    source: string;
  }>;
  /** Network errors */
  networkErrors: string[];
  /** Screenshot info */
  screenshot?: {
    path: string;
    viewport: { width: number; height: number };
    timestamp: string;
  };
}

// ═══════════════════════════════════════════════════════════════
// AI ACTION ITEMS
// ═══════════════════════════════════════════════════════════════

export interface ActionItem {
  /** Priority: 1=must fix, 2=should fix, 3=consider */
  priority: 1 | 2 | 3;
  /** What to do (imperative) */
  action: string;
  /** Affected JSON paths */
  paths: string[];
  /** Related error IDs */
  errorIds: string[];
  /** Effort estimate */
  effort: 'trivial' | 'small' | 'medium' | 'large';
}

// ═══════════════════════════════════════════════════════════════
// MAIN REPORT
// ═══════════════════════════════════════════════════════════════

export interface ValidationReport {
  /** Report format version */
  version: '1.0';

  /** Metadata */
  meta: {
    validator: string;
    timestamp: string;
    contractPath: string;
    contractHash: string;
    platform: 'web' | 'ios' | 'android';
    newclickUrl?: string;
  };

  /** Overall verdict */
  verdict: {
    status: 'VALID' | 'INVALID' | 'WARNINGS';
    blocking: number;
    nonBlocking: number;
    renderResult: 'FULL' | 'PARTIAL' | 'FAILED' | 'NOT_TESTED';
  };

  /** AI-optimized summary */
  forAI: {
    /** One-line summary */
    oneLine: string;
    /** Prioritized actions (imperative) */
    priorityActions: string[];
    /** Key reference docs */
    references: string[];
  };

  /** All errors (sorted by severity) */
  errors: ValidationError[];

  /** Component tree */
  componentTree: ComponentNode;

  /** Expression validations */
  expressions: ExpressionValidation[];

  /** Runtime validation (if performed) */
  runtime?: RuntimeValidation;

  /** Structured action items */
  actionItems: ActionItem[];
}

// ═══════════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════════

export interface ValidatorConfig {
  /** Path to FMS_GIT */
  fmsGitPath: string;
  /** Path to newclick */
  newclickPath: string;
  /** Target platform */
  platform: 'web' | 'ios' | 'android';
  /** Perform runtime validation */
  runtime: boolean;
  /** Take screenshot */
  screenshot: boolean;
  /** Newclick endpoint path */
  endpoint: string;
  /** Output format */
  format: 'json' | 'text';
  /** Output path (stdout if not set) */
  output?: string;
}
