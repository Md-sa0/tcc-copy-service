let accessKey = "";
export function setAccessKey(value: string) {
  accessKey = value;
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (accessKey) headers.set("X-API-Key", accessKey);
  const response = await fetch(path, {
    ...options,
    headers,
    signal: options.signal ?? AbortSignal.timeout(270000),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail
          .map(
            (item: { loc: string[]; msg: string }) =>
              `${item.loc.slice(1).join(".")}: ${item.msg}`,
          )
          .join("; ")
      : typeof detail === "string"
        ? detail
        : `Falha na requisição (${response.status})`;
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
