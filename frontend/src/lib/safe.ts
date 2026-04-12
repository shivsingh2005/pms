export function n(val: unknown, fallback = 0): number {
  if (typeof val === "number" && !Number.isNaN(val)) return val;
  if (typeof val === "string") {
    const parsed = Number.parseFloat(val);
    if (!Number.isNaN(parsed)) return parsed;
  }
  return fallback;
}

export function arr<T>(val: unknown): T[] {
  return Array.isArray(val) ? (val as T[]) : [];
}

export function str(val: unknown, fallback = ""): string {
  if (typeof val === "string") return val;
  if (val == null) return fallback;
  return String(val);
}

export function pct(val: unknown, decimals = 0): string {
  return `${n(val, 0).toFixed(decimals)}%`;
}

export function fixed(val: unknown, decimals = 1): string {
  return n(val, 0).toFixed(decimals);
}

export function obj<T extends object>(val: unknown, fallback: T): T {
  if (val && typeof val === "object" && !Array.isArray(val)) {
    return val as T;
  }
  return fallback;
}
