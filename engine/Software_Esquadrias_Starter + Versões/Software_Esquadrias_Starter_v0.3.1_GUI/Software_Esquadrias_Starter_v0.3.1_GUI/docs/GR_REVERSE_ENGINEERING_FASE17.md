# GR — Reverse engineering Fase 17

Status: **GR_ENGINE_0.17.0 — APROVADO NO ESCOPO DA FASE 17**

## Escopo novo

A Fase 17 adiciona bandeira inferior simples para:

- janela GR Design 60x78;
- 1 folha;
- VIDRO INTEIRO;
- módulo único;
- sem tela;
- sem persiana;
- sem subdivisões internas;
- sem reforço estrutural opcional;
- dobradiça 90 mm ou Sistema OB, desde que a ferragem já esteja homologada pela Engine base;
- no Sistema OB, cremona escolhida explicitamente.

A bandeira superior já homologada nas Fases 15/16 permanece preservada.

## Evidência ORCS

Há **23 registros GR** com bandeira inferior preenchida.

O recorte histórico é mais heterogêneo que o de bandeira superior, com mistura de:

- janelas;
- portas;
- persiana;
- tela;
- Sistema OB;
- 1 e 2 folhas;
- subdivisões internas.

A Fase 17 usa como principal evidência geométrica:

### ORCS 10588

- 800x2100 mm;
- janela 1 folha;
- Design 60x78 abertura externa;
- bandeira inferior 600 mm;
- vidro 6 mm temperado incolor;
- sem persiana;
- sem tela;
- Sistema OB;
- fechamento com cremona.

O campo Q da cremona está vazio no histórico. Por isso o custo AO de R$ 1.134,00 não é usado como golden financeiro atual.

O golden técnico escolhe explicitamente:

`CREMONA OSCILO/GIRO COMP. 1100mm E:15mm`

apenas para tornar o custo presente determinístico. A regra física já confirmada anteriormente permanece: Sistema OB usa a família CREMONA OSCILO/GIRO e o comprimento deve ser selecionado explicitamente.

## Bug legado 1 — dupla subtração da bandeira inferior

A aba GR contém:

`D9 = E2 - V3 - AA2 - AB2`

e depois, no caminho de janela com bandeira inferior, `GR!J11` volta a subtrair `AA2`.

Assim, a altura da bandeira inferior é subtraída duas vezes no caminho legado.

Classificação:

**LEGACY_BUG_CONFIRMED_BY_TOPOLOGY**

A Fase 17 reconstrói a geometria pela topologia física dos perfis Design já homologada.

Para janela sem bandeira:

`H_folha = H - 64`

Com bandeira inferior simples:

- uma face de marco = 40 mm;
- uma travessa DE6072 = 18 mm;
- overlaps da folha = 2x 8 mm.

Logo:

`H_folha = H_total - H_bandeira - 42`

## Bug legado 2 — LISTAPERFIS!E40 vazio

`GR!D26` usa `LISTAPERFIS!E40` para a altura da abertura inferior.

Essa referência não fornece a dimensão necessária no workbook oficial.

A mesma topologia física DE6058 + DE6072 já foi recuperada e homologada nas Fases 15/16.

Para bandeira simples sem subdivisões:

`largura_vão = W - 80`

`altura_vão = H_bandeira - 58`

Vidro:

`largura_vidro = W - 88`

`altura_vidro = H_bandeira - 66`

Classificação:

**LEGACY_BUG_CONFIRMED_BY_SHARED_TOPOLOGY**

## Travessa da bandeira

A separação entre bandeira inferior e folha móvel usa:

- perfil `DE6072`;
- reforço `RAG - DE6072`;
- comprimento = `W - 68`.

No recorte de janela 1 folha:

- `G8 = 2` horizontais externos do marco;
- `G10 = 2` peças de folha por eixo;
- `G19 = 1` travessa da bandeira.

## Parafusos de reforço

A Fase 17 preserva a fórmula estrutural de `GR!G118` com as quantidades reais do conjunto.

Golden ORCS 10588 reconstruído:

**PAR2 = 43,84**

## Vedações

As regras físicas já confirmadas continuam válidas:

- borracha de vidro/lambri ACB606 no vidro da folha móvel;
- borracha redonda AC0002 na folha por fora;
- borracha redonda AC0002 no marco por dentro;
- ACB606 adicional no perímetro do vidro da bandeira inferior.

No golden:

**custo de vedações = R$ 25,619200**

## Geometria golden — ORCS 10588

Entrada:

- 800x2100 mm;
- bandeira inferior = 600 mm.

Resultado:

- marco externo = 800x2100 mm;
- folha móvel = 736x1458 mm;
- vidro principal = 608x1330 mm;
- travessa da bandeira = 732 mm;
- vão fixo inferior = 720x542 mm;
- vidro da bandeira = 712x534 mm.

## Custo técnico atual

Com cremona OB 1100 mm explicitamente escolhida:

**R$ 1.034,836600**

Esse valor não deve ser comparado diretamente ao AO histórico de R$ 1.134,00 porque o histórico não gravou o comprimento da cremona e usa a lógica legada de bandeira.

## API

A Fase 17 expõe:

`bottom_flag_height_mm`

O endpoint de opções agora separa:

- `top_flag`;
- `bottom_flag`.

Restrições da bandeira inferior nesta fase:

- aplicação JANELA;
- 1 folha;
- Design 60x78;
- vidro inteiro;
- sem tela/persiana/divisões.

## Compra/corte

Continua bloqueado para GR.

## Gate técnico

Aprovar somente com:

- Engine completa verde;
- API completa verde;
- Web build verde;
- regressão Fases 1–16;
- CR e Maxim-Ar sem alteração interna;
- branch linear sobre a main homologada.
