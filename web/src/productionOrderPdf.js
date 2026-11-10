// Somente conferência; os dados técnicos são encaminhados sem fórmulas locais.
async function post(apiUrl, endpoint, body, { fetchImpl = globalThis.fetch, signal } = {}) {
  let response
  try {
    response = await fetchImpl(`${apiUrl.replace(/\/+$/, '')}/api/v1/production-orders/${endpoint}`, {
      method: 'POST', cache: 'no-store', signal,
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
  } catch (error) {
    if (error.name === 'AbortError' || signal?.aborted) throw error
    throw new Error('API indisponível. Verifique se o servidor está ligado e tente novamente.')
  }
  if (!response.ok) {
    const data = await response.json?.().catch(() => null)
    const details = Array.isArray(data?.detail)
      ? data.detail.map((entry) => `${(entry.loc || []).join(' / ')}: ${entry.msg}`).join('; ')
      : typeof data?.detail === 'string' ? data.detail : ''
    const hint = response.status === 422 ? 'Revise os dados técnicos e o cabeçalho.'
      : response.status === 503 ? 'O serviço de imagens está indisponível; verifique a configuração da API.'
        : 'Não foi possível gerar a conferência.'
    throw new Error(`${hint} HTTP ${response.status}${details ? ': ' + details : ''}`)
  }
  return response
}

export async function fetchProductionOrderReadiness(apiUrl, layoutRequest, options = {}) {
  const response = await post(apiUrl, 'pdf-readiness', layoutRequest, options)
  if (!response.headers.get('Content-Type')?.startsWith('application/json')) throw new Error('A API não retornou as pendências da OP.')
  const readiness = await response.json()
  if (readiness.review_allowed !== true || readiness.fabrication_allowed !== false ||
      !/^[0-9a-f]{64}$/.test(readiness.layout_sha256 || '') ||
      !Array.isArray(readiness.blockers) || !readiness.blockers.length ||
      readiness.blockers.some((blocker) => typeof blocker.code !== 'string' || typeof blocker.message !== 'string')) {
    throw new Error('Resposta de pendências inválida. A fabricação deve permanecer bloqueada.')
  }
  return readiness
}

export async function fetchProductionOrderReview(apiUrl, layoutRequest, {
  fetchImpl = globalThis.fetch, signal,
} = {}) {
  const response = await post(apiUrl, 'pdf', { layout_request: layoutRequest, purpose: 'REVIEW' }, { fetchImpl, signal })
  if (!response.headers.get('Content-Type')?.startsWith('application/pdf') ||
      response.headers.get('X-OP-Mode') !== 'REVIEW' ||
      response.headers.get('X-OP-Fabrication-Allowed') !== 'false') {
    throw new Error('Resposta sem identificação segura de conferência.')
  }
  const blockingCount = Number(response.headers.get('X-OP-Blocking-Count'))
  const pages = Number(response.headers.get('X-OP-Pages'))
  const snapshotSha256 = response.headers.get('X-OP-Snapshot-SHA256')
  if (!Number.isInteger(blockingCount) || blockingCount < 1 || !Number.isInteger(pages) || pages < 1 ||
      !/^[0-9a-f]{64}$/.test(snapshotSha256 || '')) throw new Error('Metadados da conferência inválidos.')
  const blob = await response.blob()
  if (await blob.slice(0, 5).text() !== '%PDF-') throw new Error('Conteúdo recebido não é um PDF.')
  return {
    blob, fabricationAllowed: false, blockingCount, pages, snapshotSha256,
    filename: 'ordem-producao-conferencia.pdf',
  }
}

export async function generateProductionOrderReview(apiUrl, layoutRequest, { onReadiness, ...options } = {}) {
  // Capture once: edits to the caller's object cannot change the second POST.
  const snapshot = structuredClone(layoutRequest)
  const readiness = await fetchProductionOrderReadiness(apiUrl, snapshot, options)
  onReadiness?.(readiness)
  options.signal?.throwIfAborted()
  const pdf = await fetchProductionOrderReview(apiUrl, snapshot, options)
  if (pdf.snapshotSha256 !== readiness.layout_sha256) {
    throw new Error('Os dados ou imagens mudaram durante a geração. Gere novamente para atualizar as pendências.')
  }
  return { ...pdf, readiness }
}
