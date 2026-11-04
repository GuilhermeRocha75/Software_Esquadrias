// Disponibilidade do serviço é independente da validação de um orçamento.
export const apiBaseUrl = (configuredUrl) => (configuredUrl || '').trim().replace(/\/+$/, '')

export async function checkApiHealth(apiUrl, { fetchImpl = globalThis.fetch, signal } = {}) {
  try {
    const response = await fetchImpl(`${apiUrl}/health`, { cache: 'no-store', signal })
    if (!response.ok) return false
    const body = await response.json()
    return body?.status === 'ok' && Array.isArray(body.engines) && body.engines.length > 0 &&
      body.engines.every((engine) => typeof engine === 'string')
  } catch {
    return false
  }
}

export function monitorApiHealth(apiUrl, onStatus, {
  fetchImpl = globalThis.fetch, intervalMs = 15000, timeoutMs = 5000,
  setTimer = setTimeout, clearTimer = clearTimeout,
} = {}) {
  let stopped = false
  let nextCheck
  let timeout
  let request
  const check = async () => {
    request = new AbortController()
    timeout = setTimer(() => request.abort(), timeoutMs)
    const online = await checkApiHealth(apiUrl, { fetchImpl, signal: request.signal })
    clearTimer(timeout)
    if (stopped) return
    onStatus(online)
    // Agenda após a resposta para nunca sobrepor requisições de saúde.
    nextCheck = setTimer(check, intervalMs)
  }
  void check()
  return () => {
    stopped = true
    clearTimer(nextCheck)
    clearTimer(timeout)
    request?.abort()
  }
}
