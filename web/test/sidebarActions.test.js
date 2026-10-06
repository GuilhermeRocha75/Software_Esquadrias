import assert from 'node:assert/strict'
import test from 'node:test'

import { sidebarModelAction } from '../src/sidebarActions.js'

test('o botão lateral Giro GR abre somente o configurador GR', () => {
  const opened = []
  const handlers = {
    onAddCR: () => opened.push('CR'),
    onAddMaximAr: () => opened.push('MAXIM_AR'),
    onAddGr: () => opened.push('GR'),
  }

  const action = sidebarModelAction('Inserir Modelo Giro', handlers)

  assert.equal(action, handlers.onAddGr)
  action()
  assert.deepEqual(opened, ['GR'])
})

test('os três modelos da lateral mantêm ações independentes', () => {
  const handlers = {
    onAddCR: () => 'CR',
    onAddMaximAr: () => 'MAXIM_AR',
    onAddGr: () => 'GR',
  }

  assert.equal(sidebarModelAction('Inserir Modelo Correr', handlers)(), 'CR')
  assert.equal(sidebarModelAction('Inserir Modelo Maxim-Ar', handlers)(), 'MAXIM_AR')
  assert.equal(sidebarModelAction('Inserir Modelo Giro', handlers)(), 'GR')
  assert.equal(sidebarModelAction('Dashboard', handlers), undefined)
})
