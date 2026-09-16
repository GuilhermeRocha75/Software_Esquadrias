# Análise dos arquivos temporários — Maxim-Ar Fase 3A

Data: 2026-09-10

Os arquivos foram examinados sem alteração. Nenhum `.tmp`, workbook ou dado de
cliente foi copiado para o repositório. A recuperação descrita abaixo ocorreu
somente em memória e o relatório registra apenas metadados técnicos.

## Inventário

| Arquivo | Bytes | SHA-256 | Assinatura e integridade | Resultado técnico |
| --- | ---: | --- | --- | --- |
| `3831B623.tmp` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | vazio | nenhum dado recuperável |
| `732F897F.tmp` | 3.146.853 | `88B31621FFA653815A31803EB35FE0287A4D5047FACCF2F24D09B0EBA59A3567` | ZIP/OpenXML íntegro, 149 entradas | cópia/snapshot completo de workbook, com 29 abas e 773 ORCS MX |
| `8246B22E.tmp` | 5.459.021 | `AAE91A5A8DE5278DB5DDD187B68BCFC7D582458D47A940B815D56C93386D79` | começa como ZIP/OpenXML, sem diretório central; 61,94% bytes zero | fragmento temporário incompleto; 74 entradas descompactadas em memória, incluindo XML de MX, LISTAPERFIS e PFAB, mas não ORCS |
| `FD44DAFB.tmp` | 3.220.272 | `CB00F3C1A58A86A1AF56DBA96A84228AAEF57DDF7F714A397E5A5B6170796A4C` | começa como ZIP/OpenXML, sem diretório central; 68,23% bytes zero e último byte não nulo em 1.048.575 | fragmento truncado/preenchido com zeros; nenhuma das abas técnicas MX/ORCS/catálogos ficou recuperável |

Também existem três arquivos Excel do tipo owner/lock, com 165 bytes e mesmo
hash `983042C7C872564CEF5830E596BF0361BF476DDC8E732610C3D7FE1D5D2C899C`.
Eles não são workbooks nem evidência técnica; nomes/conteúdo de usuário não
foram extraídos.

## Snapshot íntegro `732F897F.tmp`

- As 29 abas coincidem com as abas comuns do XLSM oficial; o oficial possui
  ainda a aba `Macro1`.
- O hash de fórmulas de cada uma das 29 abas comuns é idêntico ao oficial,
  inclusive MX.
- Contém 773 registros MX, contra 3.644 no oficial atual.
- Não contém AF/AG não nulos nem reforço estrutural preenchido.
- Contém 98 registros com bandeira, 15 casos complexos, seis módulos separados
  e quatro módulos separados com travessas. Todos esses IDs estão no histórico
  oficial, que é um superconjunto mais recente.
- Portanto, confirma que as fórmulas ambíguas já existiam no snapshot, mas não
  acrescenta configuração física ou BOM capaz de resolver os bloqueadores.

## Fragmentos incompletos

`8246B22E.tmp` conserva 76 cabeçalhos locais plausíveis; 74 entradas puderam
ser descompactadas em memória e 49 XMLs são analisáveis. O manifesto enumera as
29 abas, mas a ausência de diretório central e de partes essenciais impede
tratá-lo como workbook confiável. As fórmulas-chave recuperadas de MX repetem
os comportamentos atuais: DESIGN sem vedação, AF/AG apenas alterando contagens,
painel superior usando campos inferiores, calços por `G10*2` e subtotal
`I56=SUM(I42:I47)`. O hash total da aba difere do oficial, logo não é fonte
primária e não deve substituir o XLSM de hash obrigatório.

`FD44DAFB.tmp` conserva cabeçalhos e um manifesto parcial, mas as partes
técnicas relevantes não puderam ser recuperadas. Abrir os dois fragmentos no
Excel produz apenas uma planilha genérica, não a estrutura original.

Classificação: prováveis arquivos temporários/autorecovery de gravações Office,
não caches técnicos autônomos. Nenhum deles resolve os seis bloqueadores.

## Reprodução

```powershell
python tools/audit_maxim_ar_phase3a.py '<XLSM-oficial>' --compare '<732F897F.tmp>' --pretty
python tools/audit_maxim_ar_phase3a.py '<8246B22E.tmp>' --pretty
python tools/audit_maxim_ar_phase3a.py '<FD44DAFB.tmp>' --pretty
```
