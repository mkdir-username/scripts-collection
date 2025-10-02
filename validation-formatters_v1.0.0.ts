/**
 * Generates a clickable file link with optional line number
 * @param filePath - Absolute path to the file
 * @param line - Optional line number
 * @returns File URI with optional line anchor
 */
export function generateFileLink(filePath: string, line?: number): string {
  const fileUri = `file://${filePath}`;
  return line !== undefined ? `${fileUri}#${line}` : fileUri;
}

/**
 * Finds the line number in a JSON file for a given JSON pointer
 * @param filePath - Absolute path to the JSON file
 * @param jsonPointer - JSON pointer (e.g., "/elements/0/type")
 * @returns Line number or undefined if not found
 * @remarks This is a stub implementation - to be implemented later
 */
export function findJsonLine(filePath: string, jsonPointer: string): number | undefined {
  // TODO: Implement JSON pointer to line number resolution
  return undefined;
}

/**
 * Renders a progress bar with percentage and ratio
 * @param current - Current progress value
 * @param total - Total value
 * @param width - Width of the bar in characters (default: 20)
 * @returns Formatted progress bar string
 *
 * @example
 * renderProgressBar(448, 448, 20)
 * // => "[████████████████████] 100% (448/448 components)"
 *
 * renderProgressBar(250, 500, 20)
 * // => "[██████████          ] 50% (250/500 components)"
 *
 * renderProgressBar(1, 100, 20)
 * // => "[█                   ] 1% (1/100 components)"
 */
export function renderProgressBar(current: number, total: number, width: number = 20): string {
  // Calculate percentage
  const percentage = total === 0 ? 0 : Math.floor((current / total) * 100);

  // Calculate filled blocks
  const filledBlocks = total === 0 ? 0 : Math.floor((current / total) * width);

  // Build progress bar
  const filled = '█'.repeat(filledBlocks);
  const empty = ' '.repeat(width - filledBlocks);

  // Format output
  return `[${filled}${empty}] ${percentage}% (${current}/${total} components)`;
}

/**
 * Converts a JavaScript-style property path to RFC 6901 JSON Pointer format
 *
 * @param path - Property path like "rootElement.content.children[2]"
 * @returns JSON Pointer like "/rootElement/content/children/2"
 *
 * @example
 * pathToJsonPointer("rootElement.content.children[2]")
 * // => "/rootElement/content/children/2"
 *
 * pathToJsonPointer("rootElement.content['$children'][15]")
 * // => "/rootElement/content/$children/15"
 *
 * pathToJsonPointer("data.banner.content")
 * // => "/data/banner/content"
 */
export function pathToJsonPointer(path: string): string {
  if (!path || path === '') {
    return '';
  }

  // Escape special characters in property keys according to RFC 6901
  const escapeJsonPointerToken = (token: string): string => {
    return token.replace(/~/g, '~0').replace(/\//g, '~1');
  };

  // Split path into tokens
  const tokens: string[] = [];

  // Regular expression to match:
  // - Dot notation: .property
  // - Bracket notation with quotes: ['property'] or ["property"]
  // - Bracket notation with index: [123]
  const pathRegex = /\.?([^.[\]]+)|\['([^']+)'\]|\["([^"]+)"\]|\[(\d+)\]/g;

  let match: RegExpExecArray | null;

  while ((match = pathRegex.exec(path)) !== null) {
    // match[1] - dot notation property
    // match[2] - single-quoted bracket notation
    // match[3] - double-quoted bracket notation
    // match[4] - numeric index

    const token = match[1] || match[2] || match[3] || match[4];

    if (token !== undefined && token !== '') {
      tokens.push(escapeJsonPointerToken(token));
    }
  }

  // Join tokens with '/' prefix
  return '/' + tokens.join('/');
}
