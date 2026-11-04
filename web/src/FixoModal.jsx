import { useState } from 'react'

export const fixoDefaults = {
  family: 'FX', width_mm: 1200, height_mm: 1000, quantity: 1,
  vertical_transoms: 0, horizontal_transoms: 0,
  glass_description: '04mm FLOAT INCOLOR',
  internal_finish: 'GUARNIÇÃO DE 70MM', external_finish: 'BARRA CHATA DE 30MM',
}

export const fallbackFixoOptions = {
  glasses: [{ description: '04mm FLOAT INCOLOR' }, { description: '06mm TEMPERADO INCOLOR' }, { description: '08mm TEMPERADO INCOLOR' }],
  internal_finishes: ['GUARNIÇÃO DE 70MM', 'BARRA CHATA DE 30MM'],
  external_finishes: ['GUARNIÇÃO DE 70MM', 'BARRA CHATA DE 30MM'],
}

export default function FixoModal({ onClose, onSave, options, item }) {
  const [form, setForm] = useState(() => ({ ...fixoDefaults, ...(item || {}) }))
  const [validation, setValidation] = useState('')
  const set = (field) => (event) => {
    const numeric = ['width_mm', 'height_mm', 'quantity', 'vertical_transoms', 'horizontal_transoms'].includes(field)
    setForm((current) => ({ ...current, [field]: numeric ? (event.target.value === '' ? '' : Number(event.target.value)) : event.target.value }))
    setValidation('')
  }
  const save = (event) => {
    event.preventDefault()
    if (![form.width_mm, form.height_mm].every((value) => Number.isFinite(value) && value > 0)) return setValidation('Informe largura e altura positivas.')
    if (!Number.isInteger(form.quantity) || form.quantity < 1) return setValidation('Informe uma quantidade inteira positiva.')
    if (![form.vertical_transoms, form.horizontal_transoms].every((value) => Number.isInteger(value) && value >= 0)) return setValidation('Informe quantidades inteiras de travessas.')
    onSave({ ...form, family: 'FX', id: item?.id || crypto.randomUUID() })
  }
  return <div className="modal-backdrop" onClick={onClose}>
    <form className="modal modal-large" onSubmit={save} onClick={(event) => event.stopPropagation()}>
      <div className="modal-head"><div><strong>{item ? 'Editar Modelo Fixo' : 'Inserir Modelo Fixo'}</strong><span>Painel com vidro e divisões iguais</span></div><button type="button" className="icon-button" onClick={onClose}>×</button></div>
      <div className="modal-scroll">
        {validation && <div className="error-banner">{validation}</div>}
        <section className="field-section"><h3 className="field-section-title">Dimensões</h3><div className="modal-grid">
          <label>Largura (mm)<input type="number" required min="1" step="any" value={form.width_mm} onChange={set('width_mm')} /></label>
          <label>Altura (mm)<input type="number" required min="1" step="any" value={form.height_mm} onChange={set('height_mm')} /></label>
          <label>Quantidade<input type="number" required min="1" step="1" value={form.quantity} onChange={set('quantity')} /></label>
        </div></section>
        <section className="field-section"><h3 className="field-section-title">Divisões do painel</h3><div className="modal-grid">
          <label>Travessas verticais<input type="number" required min="0" step="1" value={form.vertical_transoms} onChange={set('vertical_transoms')} /></label>
          <label>Travessas horizontais<input type="number" required min="0" step="1" value={form.horizontal_transoms} onChange={set('horizontal_transoms')} /></label>
        </div></section>
        <section className="field-section"><h3 className="field-section-title">Vidro e acabamentos</h3><div className="modal-grid">
          <label className="span-2">Vidro<select value={form.glass_description} onChange={set('glass_description')}>{options.glasses.map((glass) => <option key={glass.description} value={glass.description}>{glass.description}</option>)}</select></label>
          <label>Acabamento interno<select value={form.internal_finish} onChange={set('internal_finish')}>{options.internal_finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Acabamento externo<select value={form.external_finish} onChange={set('external_finish')}>{options.external_finishes.map((value) => <option key={value}>{value}</option>)}</select></label>
        </div></section>
      </div>
      <div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button type="submit" className="primary">{item ? 'Salvar alterações' : 'Adicionar ao pedido'}</button></div>
    </form>
  </div>
}
