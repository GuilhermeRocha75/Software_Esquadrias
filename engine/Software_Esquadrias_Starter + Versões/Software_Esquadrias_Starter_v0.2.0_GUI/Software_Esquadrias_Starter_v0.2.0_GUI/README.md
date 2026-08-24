# Software Esquadrias — CR Engine + Tester v0.2.0

Esta versão foi criada a partir do primeiro teste real Excel × Engine.

## O que mudou

A v0.1 calculava principalmente PVC/perfis estruturais.

A v0.2 acrescenta ao módulo **CR — Correr**, para o recorte sem travessas/bandeiras:

- perfis principais;
- baguetes conforme a espessura do vidro;
- acabamentos interno e externo (guarnição/barra chata);
- reforços de marco e folha;
- vidro por m²;
- tela mosquiteira simples;
- borracha da folha;
- borracha da tela;
- escova da folha;
- corta-vento;
- calços de vidro;
- tapa-deságue;
- limitadores;
- cremona;
- maçaneta;
- maçaneta oculta;
- fecho oculto;
- roldanas;
- contra-fecho;
- parafusos de reforço;
- parafusos de ferragem.

A interface agora também permite escolher os parâmetros que antes estavam faltando:
**vidro, fechamento, cremona, roldana, acabamento interno e acabamento externo**.

## Executar a interface

Na pasta do projeto:

```powershell
python tester_gui.py
```

## Executar o exemplo

```powershell
python examples\example.py
```

## Rodar os testes

```powershell
python -m unittest discover -s tests -v
```

## Primeiro caso real

O arquivo enviado `golden_cases.csv` registrou:

- Porta PRIME 42x88
- 2 folhas
- 2000 × 2000 mm
- Engine v0.1: R$ 873,35656
- Excel: R$ 1.645,55
- diferença: -46,93%

Ao reconstruir os blocos que faltavam e usar a configuração:

- 04mm FLOAT INCOLOR
- MAÇANETA COM CREMONA + FECHO OCULTO
- CREMONA 1 PONTO
- ROLDANA 30KG
- GUARNIÇÃO DE 70MM interna
- BARRA CHATA DE 30MM externa

a CR Engine v0.2 calcula aproximadamente:

**R$ 1.645,63**

A diferença para os R$ 1.645,55 informados é de aproximadamente R$ 0,08 e deve ser investigada com os parâmetros exatos usados no Excel.

## Limites atuais

Ainda não estão completos:

- travessas internas das folhas;
- cotas manuais;
- bandeira inferior;
- bandeira superior;
- reforço estrutural de bandeiras;
- composição completa da persiana;
- casos especiais de mais de um vão de vidro por folha.

Essas regras já existem no Excel e serão migradas em versões seguintes.

## Dataset Dourado v0.2

A nova interface salva os próximos testes em:

```text
test_cases/golden_cases_v0_2.csv
```

O arquivo antigo enviado foi preservado como:

```text
test_cases/golden_cases_v0_1_original.csv
```
