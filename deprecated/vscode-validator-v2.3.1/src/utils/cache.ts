/**
 * LRU Cache Implementation
 *
 * Least Recently Used cache with:
 * - TTL support
 * - Size limits
 * - Statistics tracking
 * - Automatic eviction
 *
 * @version 2.3.1
 * @module utils/cache
 */

import { CacheEntry, CacheStats } from '../types';

// ============================================================================
// Cache Node
// ============================================================================

/**
 * Doubly linked list node for LRU implementation
 */
class CacheNode<T> {
  key: string;
  entry: CacheEntry<T>;
  prev: CacheNode<T> | null = null;
  next: CacheNode<T> | null = null;

  constructor(key: string, entry: CacheEntry<T>) {
    this.key = key;
    this.entry = entry;
  }
}

// ============================================================================
// LRU Cache Class
// ============================================================================

/**
 * LRU Cache with TTL support
 */
export class LRUCache<T> {
  private maxSize: number;
  private defaultTTL: number;
  private cache: Map<string, CacheNode<T>>;
  private head: CacheNode<T> | null = null;
  private tail: CacheNode<T> | null = null;

  // Statistics
  private stats: {
    hits: number;
    misses: number;
    evictions: number;
    sets: number;
    deletes: number;
  };

  constructor(maxSize = 1000, defaultTTL = 3600000) {
    // defaultTTL in milliseconds (default: 1 hour)
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
    this.cache = new Map();
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      sets: 0,
      deletes: 0
    };
  }

  // ========================================================================
  // Core Operations
  // ========================================================================

  /**
   * Get value from cache
   */
  get(key: string): T | undefined {
    const node = this.cache.get(key);

    if (!node) {
      this.stats.misses++;
      return undefined;
    }

    // Check if expired
    if (this.isExpired(node.entry)) {
      this.delete(key);
      this.stats.misses++;
      return undefined;
    }

    // Move to front (most recently used)
    this.moveToFront(node);

    // Update stats
    this.stats.hits++;
    node.entry.hits++;

    return node.entry.value;
  }

  /**
   * Set value in cache
   */
  set(key: string, value: T, ttl?: number): void {
    const existingNode = this.cache.get(key);

    // Create cache entry
    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
      hits: 0,
      size: this.estimateSize(value),
      ttl: ttl || this.defaultTTL
    };

    if (existingNode) {
      // Update existing entry
      existingNode.entry = entry;
      this.moveToFront(existingNode);
    } else {
      // Create new node
      const newNode = new CacheNode(key, entry);
      this.cache.set(key, newNode);
      this.addToFront(newNode);

      // Evict if over capacity
      if (this.cache.size > this.maxSize) {
        this.evictLRU();
      }
    }

    this.stats.sets++;
  }

  /**
   * Delete value from cache
   */
  delete(key: string): boolean {
    const node = this.cache.get(key);

    if (!node) {
      return false;
    }

    this.removeNode(node);
    this.cache.delete(key);
    this.stats.deletes++;

    return true;
  }

  /**
   * Check if key exists (without updating LRU order)
   */
  has(key: string): boolean {
    const node = this.cache.get(key);

    if (!node) {
      return false;
    }

    // Check if expired
    if (this.isExpired(node.entry)) {
      this.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.head = null;
    this.tail = null;
  }

  // ========================================================================
  // Batch Operations
  // ========================================================================

  /**
   * Get multiple values
   */
  getMany(keys: string[]): Map<string, T> {
    const results = new Map<string, T>();

    for (const key of keys) {
      const value = this.get(key);
      if (value !== undefined) {
        results.set(key, value);
      }
    }

    return results;
  }

  /**
   * Set multiple values
   */
  setMany(entries: Map<string, T>, ttl?: number): void {
    for (const [key, value] of entries) {
      this.set(key, value, ttl);
    }
  }

  /**
   * Delete multiple keys
   */
  deleteMany(keys: string[]): number {
    let deleted = 0;

    for (const key of keys) {
      if (this.delete(key)) {
        deleted++;
      }
    }

    return deleted;
  }

  // ========================================================================
  // Maintenance Operations
  // ========================================================================

  /**
   * Remove expired entries
   */
  purgeExpired(): number {
    let purged = 0;
    const now = Date.now();

    for (const [key, node] of this.cache) {
      if (this.isExpired(node.entry, now)) {
        this.delete(key);
        purged++;
      }
    }

    return purged;
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    if (!this.tail) {
      return;
    }

    const key = this.tail.key;
    this.delete(key);
    this.stats.evictions++;
  }

  /**
   * Check if entry is expired
   */
  private isExpired(entry: CacheEntry<T>, now = Date.now()): boolean {
    return now - entry.timestamp > entry.ttl;
  }

  // ========================================================================
  // Linked List Operations
  // ========================================================================

  /**
   * Add node to front of list
   */
  private addToFront(node: CacheNode<T>): void {
    node.next = this.head;
    node.prev = null;

    if (this.head) {
      this.head.prev = node;
    }

    this.head = node;

    if (!this.tail) {
      this.tail = node;
    }
  }

  /**
   * Move existing node to front
   */
  private moveToFront(node: CacheNode<T>): void {
    if (node === this.head) {
      return;
    }

    this.removeNode(node);
    this.addToFront(node);
  }

  /**
   * Remove node from list
   */
  private removeNode(node: CacheNode<T>): void {
    if (node.prev) {
      node.prev.next = node.next;
    } else {
      this.head = node.next;
    }

    if (node.next) {
      node.next.prev = node.prev;
    } else {
      this.tail = node.prev;
    }
  }

  // ========================================================================
  // Statistics and Info
  // ========================================================================

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? this.stats.hits / total : 0;

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate,
      evictions: this.stats.evictions
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0,
      sets: 0,
      deletes: 0
    };
  }

  /**
   * Get all keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Get entry info
   */
  getEntry(key: string): CacheEntry<T> | undefined {
    const node = this.cache.get(key);
    return node?.entry;
  }

  /**
   * Get total memory usage estimate
   */
  getTotalSize(): number {
    let total = 0;

    for (const node of this.cache.values()) {
      total += node.entry.size;
    }

    return total;
  }

  // ========================================================================
  // Utility Methods
  // ========================================================================

  /**
   * Estimate size of value
   */
  private estimateSize(value: T): number {
    if (value === null || value === undefined) {
      return 0;
    }

    if (typeof value === 'string') {
      return value.length * 2; // UTF-16
    }

    if (typeof value === 'number' || typeof value === 'boolean') {
      return 8;
    }

    if (typeof value === 'object') {
      // Rough estimate based on JSON stringification
      try {
        return JSON.stringify(value).length * 2;
      } catch {
        return 0;
      }
    }

    return 0;
  }

  /**
   * Set max size
   */
  setMaxSize(maxSize: number): void {
    this.maxSize = maxSize;

    // Evict excess entries
    while (this.cache.size > this.maxSize) {
      this.evictLRU();
    }
  }

  /**
   * Set default TTL
   */
  setDefaultTTL(ttl: number): void {
    this.defaultTTL = ttl;
  }

  /**
   * Get configuration
   */
  getConfig(): { maxSize: number; defaultTTL: number } {
    return {
      maxSize: this.maxSize,
      defaultTTL: this.defaultTTL
    };
  }

  /**
   * Export cache as JSON
   */
  toJSON(): Record<string, unknown> {
    const entries: Record<string, unknown> = {};

    for (const [key, node] of this.cache) {
      entries[key] = {
        value: node.entry.value,
        timestamp: node.entry.timestamp,
        hits: node.entry.hits,
        ttl: node.entry.ttl
      };
    }

    return {
      entries,
      stats: this.getStats(),
      config: this.getConfig()
    };
  }

  /**
   * Import cache from JSON
   */
  fromJSON(data: { entries: Record<string, { value: T; timestamp: number; hits: number; ttl: number }> }): void {
    this.clear();

    for (const [key, entry] of Object.entries(data.entries)) {
      this.set(key, entry.value, entry.ttl);
    }
  }
}

// ============================================================================
// Default Instance
// ============================================================================

/**
 * Default cache instance for validation results
 */
export const validationCache = new LRUCache<unknown>(1000, 3600000);

// ============================================================================
// Exports
// ============================================================================

export default LRUCache;
