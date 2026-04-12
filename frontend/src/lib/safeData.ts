/**
 * Safe data handling utilities
 * Prevents "not iterable" and null reference errors
 */

/**
 * Safely convert any value to an array
 * Prevents "not iterable" errors
 */
export function safeArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[]
  if (value === null || value === undefined) return []
  return []
}

/**
 * Safely get a number value with fallback
 */
export function safeNumber(
  value: unknown,
  fallback = 0
): number {
  if (typeof value === 'number' && !isNaN(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = parseFloat(value)
    if (!isNaN(parsed)) return parsed
  }
  return fallback
}

/**
 * Safely get a string value with fallback
 */
export function safeString(
  value: unknown,
  fallback = ''
): string {
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return fallback
  return String(value)
}

/**
 * Safely get nested object property
 */
export function safeGet<T>(
  obj: unknown,
  path: string,
  fallback: T
): T {
  try {
    const keys = path.split('.')
    let current: any = obj
    for (const key of keys) {
      if (current === null || current === undefined) {
        return fallback
      }
      current = current[key]
    }
    return current ?? fallback
  } catch {
    return fallback
  }
}

/**
 * Safely convert to boolean
 */
export function safeBoolean(value: unknown, fallback = false): boolean {
  if (typeof value === 'boolean') return value
  if (value === 'true' || value === '1' || value === 1) return true
  if (value === 'false' || value === '0' || value === 0) return false
  return fallback
}
