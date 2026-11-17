import { useEffect, useRef } from 'react'
import ProductionOrderPanel from './ProductionOrderPanel.jsx'

export default function ProductionOrderDialog({ open, close, ...panelProps }) {
  const dialog = useRef(null)
  useEffect(() => {
    const node = dialog.current
    if (open) node.showModal()
    else node.close()
    return () => node.close()
  }, [open])

  return <dialog ref={dialog} className="production-order-dialog" aria-labelledby="production-dialog-title" onCancel={close}>
    <div className="modal-head">
      <strong id="production-dialog-title">Ordem de Produção de Conferência</strong>
      <button autoFocus onClick={close} aria-label="Fechar ordem de produção">×</button>
    </div>
    <ProductionOrderPanel {...panelProps} />
  </dialog>
}
