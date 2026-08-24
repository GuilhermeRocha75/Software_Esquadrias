# Software Esquadrias — Starter v0.1.1 GUI

Esta versão mantém a **CR Engine 0.1.0** e adiciona uma interface gráfica local para acelerar a validação dos cálculos.

## Novidade principal: Tester CR

Execute, na pasta do projeto:

```powershell
python tester_gui.py
```

A interface permite informar:

- largura e altura;
- quantidade;
- 2, 3, 4 ou 6 folhas;
- Janela PRIME 42x66;
- Porta PRIME 42x88;
- Porta DESIGN 60x111;
- tela mosquiteira;
- persiana;
- custo esperado calculado pelo Excel;
- observação do teste.

Ela apresenta:

- geometria calculada;
- BOM / lista de materiais implementada;
- custo parcial por unidade;
- custo parcial total do pedido;
- alertas de engenharia;
- diferença entre Engine e custo informado do Excel.

## Dataset Dourado

Depois de calcular um caso e conferir o mesmo item no Excel, informe o **Custo esperado no Excel** e clique em:

**Salvar caso de teste**

O programa cria automaticamente a pasta:

```text
test_cases
```

e grava:

```text
test_cases/golden_cases.csv
```

Além do CSV consolidado, cada caso também recebe um arquivo JSON individual. Isso será utilizado futuramente para transformar casos reais em testes automatizados Excel × Engine.

## Rodar o exemplo de terminal

```powershell
python examples\example.py
```

## Rodar os testes automatizados

```powershell
python -m unittest discover -s tests -v
```

## Escopo atual da CR Engine 0.1.0

Implementado:

- seleção do marco principal;
- largura/altura e medidas de corte do marco;
- seleção do perfil de folha;
- largura/altura e medidas de corte das folhas;
- interlock;
- fechamento central em 4/6 folhas;
- trilho de alumínio;
- tapa-folha DESIGN;
- BOM unitária e quantidade total do pedido;
- custo linear dos componentes implementados;
- warnings para regras legadas suspeitas.

Ainda não implementado integralmente:

- vidro;
- tela completa;
- baguetes;
- persiana;
- bandeiras;
- travessas;
- reforços;
- borrachas/escovas;
- ferragens completas.

**Importante:** portanto, o valor mostrado na interface é identificado como **custo parcial implementado**, e não deve ser comparado com o custo total do Excel como se toda a composição já estivesse migrada.

## Banco de dados

`db/schema_v0_1.sql` continua sendo o primeiro desenho PostgreSQL multiempresa.

## Dependências

A interface utiliza `tkinter`, que normalmente já acompanha a instalação padrão do Python no Windows. Não foram adicionadas bibliotecas externas.
