const paths = {
  client: <><circle cx="9" cy="8" r="4"/><path d="M2 21v-3a7 7 0 0 1 14 0v3M19 7v6m-3-3h6"/></>,
  items: <><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 3v18M3 12h18"/></>,
  quote: <><path d="M14 2H5v20h14V7zM14 2v5h5M8 11h8M8 15h8M8 19h5"/></>,
  production: <><rect x="5" y="4" width="14" height="18" rx="2"/><path d="M9 4V2h6v2M8 11l2 2 5-5M8 18h8"/></>,
}
export default function HomeNavigation({ onClient, onItems, onQuote, onProduction }) {
  return <nav className="home-navigation" aria-label="Áreas do software">
    {[
      ['client', 'Cadastro de Cliente', 'Dados do cliente e da obra', onClient],
      ['items', 'Itens do orçamento', 'Modelos, custos e materiais', onItems],
      ['quote', 'Orçamentos', 'Valores, condições e PDF', onQuote],
      ['production', 'Ordem de produção', 'Conferência e geração da OP', onProduction],
    ].map(([key, title, description, action]) => <button key={key} className="home-tile" onClick={action}>
      <span className="home-tile-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[key]}</svg></span>
      <strong>{title}</strong><span>{description}</span><span className="home-tile-arrow" aria-hidden="true">↗</span>
    </button>)}
  </nav>
}
