export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    }
  })

  if (!resp.ok) {
    let message = `Request failed: ${resp.status}`
    try {
      const payload = await resp.json()
      if (typeof payload?.detail === 'string') {
        message = payload.detail
      }
    } catch {
      // keep default message
    }
    throw new ApiError(message, resp.status)
  }

  return resp.json() as Promise<T>
}

