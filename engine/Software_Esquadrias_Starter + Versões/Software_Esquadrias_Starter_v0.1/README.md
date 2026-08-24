# Software Esquadrias — Starter v0.1

Primeiro protótipo executável derivado do **Documento de Regras de Engenharia — Módulo CR v0.1**.

## O que já calcula

A `CR Engine 0.1.0` calcula um recorte propositalmente pequeno e testável:

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

Ainda não calcula vidro, tela completa, baguetes, persiana, bandeiras, travessas, reforços, borrachas/escovas e ferragens completas.

## Rodar o exemplo

```bash
python examples/example.py
```

## Rodar testes

```bash
python -m unittest discover -s tests -v
```

## Próxima versão

A v0.2 deve adicionar **vidro + baguetes + tela + vedações + ferragens**, depois que os casos dourados Excel × Engine forem extraídos.

## Banco

`db/schema_v0_1.sql` contém o primeiro desenho PostgreSQL multiempresa.
