import assert from 'node:assert/strict'
import test from 'node:test'
import { apiBaseUrl, checkApiHealth, monitorApiHealth } from '../src/apiHealth.js'

const healthy = () => ({ ok: true, json: async () => ({ status: 'ok', engines: ['CR_ENGINE_0.5.0'] }) })

test('a URL padrão é a mesma origem no domínio e no desenvolvimento com proxy', () => {
  assert.equal(apiBaseUrl(undefined), '')
  assert.equal(apiBaseUrl('/'), '')
  assert.equal(apiBaseUrl(' https://api.exemplo.com/ '), 'https://api.exemplo.com')
})

test('saúde consulta /health sem cache, sem depender do conteúdo do orçamento', async () => {
  let requested
  const online = await checkApiHealth('', { fetchImpl: async (url, options) => {
    requested = { url, options }; return healthy()
  } })
  assert.equal(online, true)
  assert.equal(requested.url, '/health')
  assert.equal(requested.options.cache, 'no-store')
})

test('404, erro de rede, HTML da hospedagem estática e saúde de outro produto não viram online', async () => {
  for (const response of [
    { ok: false, status: 404 },
    { ok: true, json: async () => { throw new SyntaxError('HTML') } },
    { ok: true, json: async () => ({ status: 'ok' }) },
    { ok: true, json: async () => ({ status: 'ok', engines: [] }) },
    { ok: true, json: async () => ({ status: 'error', engines: ['CR'] }) },
  ]) assert.equal(await checkApiHealth('', { fetchImpl: async () => response }), false)
  assert.equal(await checkApiHealth('', { fetchImpl: async () => { throw new TypeError('Network') } }), false)
})

test('monitoramento recupera de offline para online e para ao desmontar', async () => {
  const timers = new Map()
  const statuses = []
  let nextId = 0
  let calls = 0
  const stop = monitorApiHealth('', (online) => statuses.push(online), {
    fetchImpl: async () => (++calls === 1 ? { ok: false } : healthy()),
    setTimer: (callback, delay) => { const id = ++nextId; timers.set(id, { callback, delay }); return id },
    clearTimer: (id) => timers.delete(id),
  })
  await new Promise(setImmediate)
  assert.deepEqual(statuses, [false])
  const [id, next] = [...timers][0]
  assert.equal(next.delay, 15000)
  timers.delete(id)
  await next.callback()
  assert.deepEqual(statuses, [false, true])
  stop()
  assert.equal(timers.size, 0)
})

test('timeout aborta requisição e desmontagem não publica estado tardio', async () => {
  const timers = new Map()
  const statuses = []
  let signal
  let nextId = 0
  const stop = monitorApiHealth('', (online) => statuses.push(online), {
    fetchImpl: async (_url, options) => {
      signal = options.signal
      return new Promise((_resolve, reject) => signal.addEventListener('abort', () => reject(new Error('Aborted'))))
    },
    setTimer: (callback, delay) => { const id = ++nextId; timers.set(id, { callback, delay }); return id },
    clearTimer: (id) => timers.delete(id),
  })
  const timeout = [...timers.values()][0]
  assert.equal(timeout.delay, 5000)
  timeout.callback()
  stop()
  await new Promise(setImmediate)
  assert.equal(signal.aborted, true)
  assert.deepEqual(statuses, [])
  assert.equal(timers.size, 0)
})
