const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function getToken(): string {
  try {
    return localStorage.getItem("pms_token") ?? "";
  } catch {
    return "";
  }
}

export async function apiGet<T>(
  path: string,
  fallback: T,
): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
        "Content-Type": "application/json",
      },
      signal: AbortSignal.timeout(12000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json() as T;
  } catch (e) {
    console.error(`[API GET] ${path}:`, e);
    return fallback;
  }
}

export async function apiPost<T>(
  path: string,
  body: unknown,
  fallback: T,
): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${getToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json() as T;
  } catch (e) {
    console.error(`[API POST] ${path}:`, e);
    return fallback;
  }
}

export async function apiPatch<T>(
  path: string,
  body: unknown,
  fallback: T,
): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${getToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json() as T;
  } catch (e) {
    console.error(`[API PATCH] ${path}:`, e);
    return fallback;
  }
}
