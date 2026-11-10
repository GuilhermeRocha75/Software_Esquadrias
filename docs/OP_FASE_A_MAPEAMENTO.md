# Inspeção anterior à implementação — OP Fase A

Branch: `feature/ordem-producao-v1`. Base: 365 testes Engine e 75 API passam.
O caminho ativo é o `src/esquadrias_engine` do diretório histórico v0.3.1,
carregado por `api/app/engine_bridge.py`. Nenhuma migração desse caminho faz
parte desta entrega.

| Família / versão | Identificação e grupos | Medidas e quantidades existentes | Lacunas identificadas |
| --- | --- | --- | --- |
| CR / 0.5.0 | `unit_bom`: category, role, material_code, description, unit, source opcional | geometry contém finais/cortes de marco e folha; BOM.length_mm geralmente é corte; width/height para vidro/tela; quantity_per_unit/order | final não ligado à linha; source ausente nas linhas antigas; fator de área da tela não equivale à quantidade física; parafusos fracionários |
| MAXIM_AR / MX 0.3.0 | Mesma BOM; referências MX e códigos de regra | geometry contém finais/cortes; bandeiras e transoms estruturados; vidro e tela recolhível na BOM | final não ligado à linha; vedação possui ID configurável, não código legado de perfil |
| GR / 0.25.0 | Mesma BOM; source referencia GR; preenchimento DE20150 | geometry contém finais/cortes; porta tem tolerância vertical de marco diferente da horizontal; bandeiras/vidros/tela estruturados | painel fracionário é saída existente; ordem da BOM pode refletir anexação por fases, não posição impressa |
| FX / 0.1.0 | Mesma BOM; role em português e source FX!linha | geometry contém width/height e cortes de marco, vãos, vidro, travessas; quantidades unitárias e totais | faltam aliases de final de marco; nenhum PDF golden de FX; validar com caso sintético próprio e regressões existentes |

Grupos existentes: PERFIS PRINCIPAIS, BAGUETES, ACABAMENTOS, REFORÇOS,
VIDROS, TELA, VEDAÇÕES, ACESSÓRIOS, FERRAGENS e PERSIANA, conforme família.
Vidros/telas têm largura/altura; perfis têm comprimento e quantidade de
peças, embora a unidade comercial seja `m`. Vedações podem representar
consumo agregado. Não interpretar `m` como unidade de contagem de peças.

API atual converte requests nos quatro tipos da Engine e serializa BOM,
geometria, custos e compra. A Web chama calculate-all para os quatro modelos.
OP terá contrato próprio, sem preços, compra ou alterações na Web.

Os 12 golden não contêm configuração completa (fechamentos, acabamentos,
acionamento de persiana, cor técnica/catálogo de ativos). Comparações devem
registrar explicitamente a reconstrução utilizada e limitar a conclusão aos
campos transcritos. A fixture omite tela, talas e painel mencionados na
especificação; essas referências adicionais precisam ser testadas separadamente.

Ordem exata de POP/OP e assets não podem ser comprovados somente pela fixture.
Preservar todas as posições e grupos da Engine, inclusive grupos intercalados,
e referências legadas disponíveis, sem ordenar por código ou consolidar linhas.
Validar diagramação/ordem impressa com os documentos privados na auditoria.
Não introduzir ativos, códigos ou medidas finais por aproximação.
