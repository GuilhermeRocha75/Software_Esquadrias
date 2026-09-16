# Análise da fonte histórica RAR — Maxim-Ar Fase 3A

Data: 2026-09-11

## Fonte e política de uso

- Arquivo: `1.2 DELL AMANDA.rar`.
- Tamanho: 198.356.570 bytes.
- SHA-256: `E338D099359CEFA226D9ADA56A1F0C6C3B8305FC953088BC3DA0397A5410AD29`.
- Assinatura: RAR5 (`52 61 72 21 1A 07 01 00`).
- O conteúdo foi extraído em diretório temporário fora do repositório.
- Nenhum PDF, imagem, XLSM, `.tmp`, nome de cliente, endereço, contato ou
  valor comercial foi versionado.
- PDFs são referenciados somente por um ID anônimo derivado de seu SHA-256.
- O XLSM oficial de paridade continua exclusivamente o de SHA-256
  `96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160`.

## Inventário

O RAR contém 1.780 arquivos e 232.121.554 bytes descompactados:

| Tipo | Quantidade |
| --- | ---: |
| JPG | 1.454 |
| PDF | 238 |
| PNG | 74 |
| XLSM | 5 |
| TMP | 4 |
| DB | 2 |
| JFIF/WEBP/LNK | 3 |

As pastas principais contêm 1.506 arquivos de croquis, 238 PDFs de orçamentos
e 25 imagens de seções de perfis. Os dois `.db` são caches `Thumbs.db` OLE, não
bases de dados técnicas.

## Auditoria dos orçamentos

Os 238 PDFs somam 653 páginas; 651 possuem texto extraível e nenhum documento
falhou na leitura. A busca sanitizada encontrou:

- 128 PDFs contendo Maxim-Ar;
- 291 ocorrências de itens Maxim-Ar;
- 19 descrições técnicas distintas;
- 230 ocorrências de uma folha, 54 de duas, três de três e quatro de quatro;
- 61 itens de múltiplas folhas;
- 54 itens com tela;
- 40 ocorrências com bandeira inferior e 12 com superior.

Os códigos de grade de bandeira presentes nos PDFs foram:

| Código | Ocorrências | Interpretação confirmada pelo croqui |
| --- | ---: | --- |
| inferior `(00)` | 39 | sem travessas |
| inferior `(10)` | 1 | uma travessa vertical, duas colunas |
| superior `(00)` | 8 | sem travessas |
| superior `(03)` | 4 | três travessas horizontais, quatro linhas |

A pesquisa integral do texto não encontrou `ALUM10238`, `ALUM15338`,
`AC0708`, `AC0002`, `ACB606` ou `AC0312`. Os PDFs são propostas com descrição,
dimensões, vidro e opções; não contêm BOM de perfis, vedações ou acessórios.

### Vínculo ORCS × orçamento × croqui

Dois documentos anônimos contêm os mesmos dois itens técnicos:

| Evidência | Configuração | Vínculo ORCS |
| --- | --- | --- |
| `PDF-39689C6E9678`, item técnico 3; `PDF-2991B48657F8`, item 3 | 1 folha, 1100 × 5750 mm, quantidade 2, bandeira superior `(03)` | ORCS 8696; `AB=4750`, `AK=3` |
| `PDF-39689C6E9678`, item técnico 4; `PDF-2991B48657F8`, item 4 | 1 folha, 1500 × 2025 mm, quantidade 1, bandeira superior `(03)` | ORCS 8701; `AB=1200`, `AK=3` |

O croqui `(03)` mostra quatro painéis de vidro empilhados. O Excel calcula a
altura usando `AK`, mas `MX!G18` usa `AI` e `MX!G61` herda essa quantidade. Nos
dois casos, como `AI=0` e `AK=3`, o legado contabiliza um vidro superior onde a
topologia aprovada mostra quatro. Isso confirma `LEGACY_BUG_CONFIRMED`.

## Auditoria dos croquis

Entre 1.530 imagens, 237 têm Maxim-Ar no nome técnico, representando 161
conteúdos visuais distintos e 234 nomes/configurações. Foram encontrados:

- 132 croquis de múltiplas folhas;
- 100 com bandeira inferior e 44 com superior;
- 39 com tela;
- três com redação de módulo separado;
- três com pinázio externo, que não equivalem a AF/AG estrutural.

Os croquis confirmam visualmente a convenção `(VH)`:

- `(01)` = zero travessa vertical e uma horizontal, formando duas linhas;
- `(10)` = uma vertical e zero horizontal, formando duas colunas;
- `(30)` = três verticais, formando quatro colunas;
- `(03)` = três horizontais, formando quatro linhas;
- `(23)` = duas verticais e três horizontais, formando grade 3 × 4.

O acervo contém códigos inferiores `00`, `01`, `10`, `11`, `20`, `23`, `30`
e `40`, e superiores `00`, `01`, `03`, `10`, `11`, `12`, `20`, `30`, `40` e
`50`. Isso prova que a grade é independente e não pode ser deduzida apenas do
número de folhas.

Um croqui de quatro folhas com bandeiras `(30)` mostra as três travessas
verticais alinhadas aos encontros das quatro folhas. Esse caso explica por que
o Excel parece coerente quando `travessas verticais = folhas - 1`. Em grades
como `(23)`, essa coincidência deixa de existir e a dimensão precisa ser
dividida pela própria grade.

As imagens são elevações comerciais sem cotas internas, seção de encaixe,
lista de corte ou materiais. Elas resolvem a topologia, mas não comprovam
folgas, descontos, perfis, reforços, vedações ou calços.

## XLSM históricos do RAR

Foram encontrados dois workbooks reais e três arquivos owner/lock de 165
bytes. Os nomes originais não foram registrados.

| Snapshot | SHA-256 | Abas | ORCS MX | Resultado |
| --- | --- | ---: | ---: | --- |
| `B41C7DDF16F7` | `B41C7DDF16F7CA9C60077368180BB2BF59D6631D0EC710B93B5BCD936ECF73DF` | 29 | 783 | fórmulas MX iguais às oficiais; AF/AG e reforço preenchido = 0 |
| `6FF0303092BF` | `6FF0303092BF9E7688320DA11B0F4FA508D59C0F6F8F42CF5C1188AACFD2BEE2` | 30 | 3.644 | conteúdo técnico/ORCS equivalente ao oficial, mas hash global diferente; snapshot apenas |

O hash de fórmulas MX dos dois snapshots é
`E6929132D7FA1C1ABC3E3BD56DD3617C7BDC78E2FADB1C8F61CC541F25FA5EB8`,
igual ao XLSM oficial. Nenhum snapshot altera as conclusões sobre AF/AG,
vedações, calços ou reforço estrutural.

## Impacto nos seis bloqueadores

| Bloqueador | Evidência nova | Efeito |
| --- | --- | --- |
| Vedações DESIGN | nenhum código/material nos 238 PDFs; seções DE6058/DE6078 sem indicação de borracha | continua BLOCKED |
| AF/AG da folha | nenhum orçamento/croqui identifica travessa estrutural dentro da folha; pinázio externo é outro componente | continua BLOCKED |
| Bandeiras complexas | croquis e orçamentos confirmam convenção `(VH)`, grades independentes e casos ORCS 8696/8701 | topologia `RESOLVED_HISTORY`; BOM permanece PARTIAL |
| Módulos separados + travessas | três croquis indicam módulos e seis ORCS já conhecidos; nenhum PDF traz lista de corte | continua PARTIAL |
| Calços | nenhum código ou quantidade nos PDFs/croquis | continua BLOCKED |
| Reforço estrutural | nenhum código, descrição ou opção nos PDFs; snapshots têm zero ocorrência | continua BLOCKED e `PENDING_PHYSICAL_HOMOLOGATION` |

## Conclusão

A fonte histórica confirma definitivamente que o Excel não representa
corretamente todas as grades de bandeira. Ela fornece regra topológica segura:
uma bandeira `(V,H)` possui `(V+1) × (H+1)` painéis, com dimensões subdivididas
pela própria grade. Ainda não fornece os descontos de corte, materiais e
encontros necessários para implementar a Fase 3B sem suposição.

O resultado global permanece em 0/6 bloqueadores integralmente resolvidos.
