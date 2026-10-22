let accessKey = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public cacheStatus: string | null = null,
  ) {
    super(message);
  }
}
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
  let response: Response;
  try {
    response = await fetch(path, {
    ...options,
    headers,
    signal: options.signal ?? AbortSignal.timeout(270000),
  });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error("Não foi possível conectar à API. Na demonstração local, abra iniciar-demo.cmd na pasta do projeto, mantenha a janela aberta e atualize esta página.");
  }
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
    throw new ApiError(message, response.status, response.headers.get("X-Cache-Status"));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
