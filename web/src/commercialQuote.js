// VBA reads currency-formatted cells through Range.Value at four decimal places.
function currencyValue(value) {
  const [whole, fraction = ''] = Math.abs(value).toFixed(12).split('.')
  let scaled = Number(whole) * 10000 + Number(fraction.slice(0, 4))
  const tail = Number(fraction.slice(4))
  if (tail > 50000000 || (tail === 50000000 && scaled % 2)) scaled++
  return Math.sign(value) * scaled / 10000
}

export function calculateQuote(items, calculated, settings = {}) {
  if (!items.length || items.length > 51 || calculated?.length !== items.length) return null
  const rows = items.map((item, i) => {
    const override = settings.lines?.[item.id] || {}
    const base = calculated[i].unit_technical_cost
    if (!Number.isFinite(base)) return null
    const cost = override.cost === '' || override.cost == null ? base : Number(override.cost)
    const factor = Number(override.factor || settings.factor || 1)
    const unit = currencyValue(cost) * factor
    const total = currencyValue(unit) * item.quantity
    const area = item.width_mm * item.height_mm * item.quantity / 1000000
    return { cost, unit, total, area, quantity: item.quantity }
  })
  if (rows.some(row => !row)) return null
  const subtotal = rows.reduce((sum, row) => sum + row.total, 0)
  const area = rows.reduce((sum, row) => sum + row.area, 0)
  const quantity = rows.reduce((sum, row) => sum + row.quantity, 0)
  const installation = area * Number(settings.perArea ?? 120)
    + quantity * Number(settings.perUnit ?? 0) + Number(settings.fixed ?? 300)
  return { rows, subtotal, area, quantity, installation, total: subtotal + installation }
}
