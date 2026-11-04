export const sidebarModelAction = (item, handlers) => ({
  'Inserir Modelo Correr': handlers.onAddCR,
  'Inserir Modelo Maxim-Ar': handlers.onAddMaximAr,
  'Inserir Modelo Giro': handlers.onAddGr,
  'Inserir Modelo Fixo': handlers.onAddFixo,
}[item])
