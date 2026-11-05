# Conferência visual B2 — implementação, sem homologação

Foram inspecionadas lado a lado as primeiras páginas dos 12 casos, com os três
PDFs originais disponíveis localmente e verificados por SHA-256. Os pares estão
em `.private/op-b2/review/visual/OP-GOLDEN-NN.png`; a esquerda é o original,
com identificação do cliente e paths ocultados na cópia em memória; a direita
é o candidato. Os originais não foram alterados. Nenhuma imagem desta
conferência foi adicionada ao Git.

Observações comuns: croquis reais e seções compatíveis com o modelo; barras
pretas de cabeçalho e sequência B1 preservadas; medidas finais/corte em colunas
distintas; vidros/telas com largura e altura; unidades explícitas. A geometria
das caixas dos croquis e dos perfis deriva das referências. As imagens JPEG
incorporadas também foram verificadas por bytes e pixels, sem redesenho.

O candidato acrescenta seções de marco/folha no topo, obra, títulos de grupos,
marca de conferência e anexo de pendências. Fontes e espaçamento diferem do
Excel. As caixas principais seguem a impressão legada, que estica os croquis;
as seções adicionais no topo preservam a proporção. O visual não é idêntico
pixel a pixel. A revisão visual não resolve divergências de engenharia.

| Caso | Fonte / família | Observações da conferência |
| --- | --- | --- |
| 01 | op p1 / CR | Croqui de tela e perfis presentes. Quatro arremates ausentes na BOM reconstruída; vidro e ferragem divergem. PAR2 83,424 × 84,224. Consumíveis usam mm/esquadria e conjuntos, em vez do total em metros da fonte. |
| 02 | op p2 / CR | Mesma estrutura do 01, dimensões menores preservadas. Quatro arremates ausentes. PAR2 77,424 × 78,224; código do vidro/ferragens pendente. |
| 03 | op p3 / GR | Painel, folha de giro e perfis presentes. Quantidade do painel aparece sem arredondamento, com unidade pendente. Utilização originalmente vazia da contra-testa continua vazia. Três borrachas adicionais; um acabamento ausente; ferragem e PAR1 diferentes. |
| 04 | OP2 p1 / CR | Croqui, perfis e vidros presentes. Quatro arremates ausentes e código de vidro/ferragens pendente. PAR2 76,256 × 77,056. |
| 05 | OP2 p2 / CR | Croqui com persiana e linhas do kit presentes. Tala 40,25 na fonte × 41 na Engine exposta no anexo. Arremates/vidro/ferragens e PAR2 continuam diferentes. |
| 06 | OP2 p3 / CR | Porta e quantidade 2 preservadas. Tabela traz quantidades totais e anexo repete valores por esquadria. Inspecionada também a terceira página do anexo: últimas quantidades e rodapé presentes, sem corte. PAR2 133,984 × 135,584. |
| 07 | OP2 p4 / CR | Croqui preto correto; tabela e medidas presentes. Ausências de acabamento da reconstrução não são supridas pelo croqui preto. PAR2 63,456 × 64,256. |
| 08 | OP2 p5 / MAXIM_AR | Croqui, seções, vidro e cortes presentes. Três linhas de vedação adicionais ficam explícitas, incluindo código longo com identificação completa no anexo. |
| 09 | OP2 p6 / CR | Geometria e vidro presentes; acabamento e opções incompletos. PAR2 40,416 × 41,215999999999994; o artefato numérico da Engine é mantido, sem arredondamento silencioso. |
| 10 | OP2 p7 / MAXIM_AR | Croqui e medidas de 500 × 1030 presentes. Três vedações adicionais. Não declarar equivalência só porque os 51 campos numéricos comuns coincidem. |
| 11 | OP2 p8 / MAXIM_AR | Quantidade 2 e medidas de 510 × 1040 presentes; anexo distingue por esquadria/total. Três vedações adicionais permanecem. |
| 12 | OP3 p1 / CR | Croqui de persiana presente; tala 59 × 60, eixo 950 × 1940 e seis quantidades do kit diferentes. Linha legada código 0/descrição vazia não é inventada na BOM. Inspecionada a segunda página: PAR2 e PAR1 finais presentes, identificação e colunas repetidas. |

O caso próprio `FX-PROPRIO` também foi inspecionado: croqui real, seção do
marco, perfis, vidro e acessórios presentes; não há seção de folha fictícia.
Tem 13 linhas e duas páginas com anexo. Não existe PDF original FX para
comparação. O rótulo herdado B1 `Vidros (Band. Sup.)` no FX simples merece
revisão do mapeamento de apresentação, sem alterar a geometria do vidro.

Todos os casos continuam pendentes de auditoria técnica independente e de
conferência visual pelo proprietário. A inspeção aqui registrada é a revisão
da implementação, não aprovação de ordens para fábrica.
