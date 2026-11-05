# Ordem de Produção V1 — Especificação inicial

## Estado e fonte
Base da Fase A aprovada com ressalvas segundo autorização do proprietário. Fase B1 implementada para nova auditoria; **NÃO homologada automaticamente**. Renderização PDF e Web não implementadas nesta entrega. Branch isolada da main.
Infraestrutura, recursos privados e pendências B1: [OP_FASE_B1.md](OP_FASE_B1.md).
Contratos, limitações e evidências: [OP_FASE_A.md](OP_FASE_A.md).
Fonte: planilha `SOFTBETA_ PERFIL PRE DELL AMANDA.xlsm`, SHA-256
`96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160`.
VBA `OP1.OP_1`: itens `ORC IMP!AK:BU`, família em `BH`, planilhas `CR/MX/GR/PV/FX/GD`,
intermediária `POP`, destino `OP`, croquis `Croquis` e perfis `Croquis_perfis`.

## Referências reais fornecidas pelo proprietário
* `op.pdf` — 3 itens/páginas (2 CR com tela, 1 GR porta giro com painel); metadados da impressão indicam workbook **SOFTBETA_ SERVIDOR.xlsm** (versão diferente a conferir).
* `OP 2.pdf` — 8 itens/páginas (5 CR, 3 Maxim-Ar): janela básica, persiana, porta correr em quantidade 2, acabamento preto, 3 MX.
* `OP 3.pdf` — 1 item/página (CR janela com persiana).
* Total: 12 páginas A4 retrato; **8 CR, 3 MX, 1 GR, nenhum FX**.
* PDFs/RAR NÃO devem ser commitados no repositório público, porque incluem dados de clientes. Fixtures devem ser anonimizadas.

## Formato obrigatório
Um item por página para casos de referência:
1. croqui do modelo, imagens da seção de marco e folha;
2. cabeçalho `Cód. Cliente | Nome | Item | Largura | Altura | Quant.`;
3. descrição do modelo, folhas, cor, persiana/tela;
4. tabela `Utilização | [imagem perfil] | Descrição | Código | Med. Final | Med. Corte | Quant.`;
5. grupos de perfis/cortes, vidros/telas (colunas `Largura | Altura | Quant.`), consumíveis, ferragens, acessórios e parafusos;
6. impressão A4 retrato, visual próximo ao Excel, sem truncamento para grande número de itens, com prévia e download de PDF.

Não imprimir paths `C:\\Users\\...\\Croquis...` nem caracteres sentinelas `A`. Ambos são defeitos visuais existentes nas amostras. Não inventar ativos ausentes nem códigos de peças.

## Arquitetura
- Engine é a ÚNICA fonte de regras/fórmulas técnicas; **NÃO** duplicar fórmula de medida, quantidade ou corte no frontend, API ou PDF.
- Adaptador `ProductionOrder` recebe dados técnicos por item, preservando posição, uso, código, descrição, unidade, medida final, medida de corte e quantidade. Inspecionar se a Engine expõe medidas finais: caso contrário, acrescentar representação tipada na Engine com testes, sem alterar resultados homologados.
- Separar totalmente OP de orçamento comercial e de plano otimizado de compra de barras (não são equivalentes).
- API versionada JSON preview + endpoint PDF, validação explícita; frontend botão `Gerar Ordem de Produção`.
- Croquis e perfis indexados por descritor/código/cor com caminhos relativos; incluir substituição/configuração futura, jamais caminho absoluto do Excel.
- Snapshot de inputs + versão Engine para reimprimir de maneira determinística.
- PV/GD aguardam seus cálculos homologados. FX: incluir implementação, porém **validar com caso próprio**, pois nenhuma OP de FX foi fornecida.
- Cortes maiores que a barra: representar peça inteira e sinalizar emenda planejada conforme regra já validada, sem cortar automaticamente na OP.

## Casos golden pontuais (PDF, página; dados de cliente removidos)
| Caso | Entrada (mm; qtd) | Referências obrigatórias |
| --- | --- | --- |
| op p1 CR tela | 1930×1490; 1 | PR13852 largura 1930/1935 ×2, PR4266 largura 954/959 ×4, vidro 846×1294 ×2, tela 846×1294 ×1 |
| op p2 CR tela | 1630×1490; 1 | PR13852 1630/1635 ×2; PR4266 804/809 ×4; vidro 696×1294 ×2 |
| op p3 GR painel | 1160×2110; 1 | DE6058 1160/1165 ×1; DE60104 1096/1101 ×2; painel DE20150 quantidade 12,8357143 |
| OP2 p1 CR | 2800×1400; 1 | PR8852 2800/2805 ×2; PR4266 1389/1394 ×4; vidro 1281×1204 ×2 |
| OP2 p2 CR persiana | 1420×1610; 1 | PR8852 1420/1425 ×2; marco altura 1410/1415 ×2; tala comprimento 1346 e quantidade 40,25 |
| OP2 p3 CR porta | 1160×2100; 2 | PR8852 1160/1165 ×4; PR4288 580/585 ×8; vidro 428×1860 ×4 |
| OP2 p4 CR preto | 2480×1080; 1 | PR8852 2480/2485 ×2; PR4266 1229/1234 ×4; vidro 1121×884 ×2 |
| OP2 p5 MX | 530×1030; 1 | DE6058 530/535 ×2; DE6078 466/471 ×2; vidro 338×838 ×1 |
| OP2 p6 CR | 1100×1040; 1 | PR8852 1100/1105 ×2; PR4266 539/544 ×4; vidro 431×844 ×2 |
| OP2 p7 MX | 500×1030; 1 | DE6058 500/505 ×2; DE6078 436/441 ×2; vidro 308×838 ×1 |
| OP2 p8 MX | 510×1040; 2 | DE6058 510/515 ×4; DE6078 446/451 ×4; vidro 318×848 ×2 |
| OP3 p1 CR persiana | 1980×1180; 1 | PR8852 1980/1985 ×2; marco altura 980/985 ×2; tala 933 ×59; vidro 871×784 ×2 |

**Atenção:** Golden acima é PARCIAL, não transcrição de todas as linhas; toda divergência Engine × PDF deve ser auditada antes de mudar fórmulas.

## Anomalias legadas documentadas
- OP3 p1: `Divisor central (Eixo único)` com descrição vazia, código `0` e quantidade `1`.
- OP2 p2: `TALA DE PVC 40MM` quantidade `40,25`, potencial incompatibilidade com unidade física; não arredondar sem validação.
- op p3: `PAINEL FECHAMENTO` quantidade fracionária `12,8357143`. Verificar unidade física antes de aplicar correção.
- Parafusos e consumíveis com frações; unidade é indispensável.
- Paths Windows aparecem impressos no cabeçalho; todos os arquivos referenciados nesta amostra existem no RAR.
- A fonte `op.pdf` tem metadados de workbook diferente das outras duas.

## Execução por gates
1. Inspecionar a API/Engine atuais e criar contrato de OP testável (sem PDF). Testar casos anonimizados; reportar paridade e divergências.
2. Gerar PDF e mapear assets com hashes; testar desenho e diagramação A4 (12 páginas de referência).
3. Integrar API/UI (preview, download, impressão), testes de regressão Engine/API/frontend.
4. Auditoria independente antes de fazer merge na main.

**Não fazer merge, force push ou alterar famílias homologadas sem evidência.**
