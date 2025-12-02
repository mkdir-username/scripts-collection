#!/usr/bin/env node
/**
 * Figma MCP Rate-Limiting Wrapper
 * Prevents API quota exhaustion with caching + rate limiting
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// === CONFIG ===
const MAX_REQUESTS_PER_MINUTE = 8; // Safe limit for personal tokens
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 min
const LOG_PATH = path.join(process.env.HOME, '.figma_mcp_wrapper.log');
const CACHE_DIR = path.join(process.env.HOME, '.figma_mcp_cache');

// === STATE ===
const requestTimestamps = [];
const cache = new Map(); // key -> {data, expires}

// === HELPERS ===
function log(msg) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] ${msg}\n`;
  fs.appendFileSync(LOG_PATH, line, 'utf8');
}

function ensureCacheDir() {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
  }
}

function getCacheKey(request) {
  // Cache based on method + params
  const method = request.method || '';
  const params = JSON.stringify(request.params || {});
  return `${method}:${params}`;
}

function checkRateLimit() {
  const now = Date.now();
  const oneMinuteAgo = now - 60 * 1000;

  // Remove old timestamps
  while (requestTimestamps.length > 0 && requestTimestamps[0] < oneMinuteAgo) {
    requestTimestamps.shift();
  }

  if (requestTimestamps.length >= MAX_REQUESTS_PER_MINUTE) {
    const oldestRequest = requestTimestamps[0];
    const waitMs = oldestRequest + 60 * 1000 - now;
    return { limited: true, waitMs };
  }

  requestTimestamps.push(now);
  return { limited: false };
}

function getFromCache(key) {
  const cached = cache.get(key);
  if (!cached) return null;

  if (Date.now() > cached.expires) {
    cache.delete(key);
    return null;
  }

  log(`CACHE HIT: ${key}`);
  return cached.data;
}

function setCache(key, data) {
  cache.set(key, {
    data,
    expires: Date.now() + CACHE_TTL_MS
  });
}

// === MAIN ===
async function main() {
  ensureCacheDir();
  log('=== Wrapper started ===');

  // Spawn real MCP server
  const mcp = spawn('npx', ['-y', 'figma-developer-mcp', '--stdio'], {
    env: { ...process.env, FIGMA_API_KEY: process.env.FIGMA_API_KEY },
    stdio: ['pipe', 'pipe', 'inherit']
  });

  let buffer = '';

  // Process stdin -> wrapper logic -> mcp stdin
  process.stdin.on('data', async (chunk) => {
    buffer += chunk.toString();

    const lines = buffer.split('\n');
    buffer = lines.pop(); // Keep incomplete line

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const request = JSON.parse(line);
        const cacheKey = getCacheKey(request);

        // Check cache first
        const cached = getFromCache(cacheKey);
        if (cached) {
          process.stdout.write(JSON.stringify(cached) + '\n');
          continue;
        }

        // Check rate limit
        const rateLimitCheck = checkRateLimit();
        if (rateLimitCheck.limited) {
          const waitSec = Math.ceil(rateLimitCheck.waitMs / 1000);
          log(`RATE LIMITED: waiting ${waitSec}s`);

          // Return error to client
          const error = {
            jsonrpc: '2.0',
            id: request.id,
            error: {
              code: -32000,
              message: `Rate limit: wait ${waitSec}s (${MAX_REQUESTS_PER_MINUTE}/min)`
            }
          };
          process.stdout.write(JSON.stringify(error) + '\n');
          continue;
        }

        log(`REQUEST: ${request.method} (${requestTimestamps.length}/${MAX_REQUESTS_PER_MINUTE})`);

        // Forward to real MCP (cache response separately)
        mcp.stdin.write(line + '\n');
      } catch (e) {
        // Not JSON, pass through
        mcp.stdin.write(line + '\n');
      }
    }
  });

  // Process mcp stdout -> wrapper cache -> stdout
  let mcpBuffer = '';
  mcp.stdout.on('data', (chunk) => {
    mcpBuffer += chunk.toString();

    const lines = mcpBuffer.split('\n');
    mcpBuffer = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;

      try {
        const response = JSON.parse(line);

        // Cache successful responses
        if (response.result && !response.error) {
          // Find matching request key (simplified)
          const key = `method:${JSON.stringify(response.result).substring(0, 50)}`;
          setCache(key, response);
        }

        process.stdout.write(line + '\n');
      } catch (e) {
        // Not JSON, pass through
        process.stdout.write(line + '\n');
      }
    }
  });

  mcp.on('exit', (code) => {
    log(`=== MCP exited: ${code} ===`);
    process.exit(code);
  });

  process.on('SIGTERM', () => {
    mcp.kill();
    process.exit(0);
  });
}

main().catch((err) => {
  log(`ERROR: ${err.message}`);
  process.exit(1);
});
