export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public cacheStatus: string | null = null,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  const csrfToken = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith("copylab_csrf="))
    ?.slice("copylab_csrf=".length);
  if (
    csrfToken &&
    ["POST", "PUT", "PATCH", "DELETE"].includes(
      (options.method ?? "GET").toUpperCase(),
    )
  ) {
    headers.set("X-CSRF-Token", decodeURIComponent(csrfToken));
  }
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      headers,
      credentials: "include",
      signal: options.signal ?? AbortSignal.timeout(270000),
    });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error(
      "Não foi possível conectar ao serviço. Verifique sua conexão e tente novamente.",
    );
  }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/api/v1/auth/")) {
      window.dispatchEvent(new Event("copylab:unauthorized"));
    }
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
    throw new ApiError(message, response.status, response.headers.get("X-Cache-Status"));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
