# Disponibilidade da API

## Diagnóstico em 16/10/2026

`https://meisterperfis.com/` responde 200, mas `/health` e
`/api/v1/engine/cr/options` respondem 404. O frontend publicado usa a mesma
origem. As rotas de backend não estão atendidas nesse domínio. Isso não permite
concluir qual plano foi contratado ou se há outra API em outro endereço.

Há também um erro no indicador: anteriormente só um cálculo bem-sucedido
marcava a API como online. Um orçamento vazio permanecia offline e uma resposta
422 de validação era tratada como API indisponível.

## Correção no código

- O indicador consulta `/health` imediatamente e repete a checagem 15 segundos
  após cada resposta, com timeout de 5 segundos e cancelamento ao sair da tela.
- Mostra “verificando” durante a primeira consulta. A saúde independe de itens
  no orçamento ou de erros de validação do cálculo.
- Recarrega as opções quando a API volta a responder.
- O desenvolvimento usa o proxy do Vite: navegador → `127.0.0.1:5173/health`
  e `/api/*` → FastAPI em `127.0.0.1:8000`. Isso mantém a mesma origem e evita
  depender de configurações CORS de produção no desenvolvimento.
- O iniciador Windows define essa mesma origem explicitamente e protege o
  caminho do Vite com aspas quando houver espaços. O script é salvo com BOM
  UTF-8 para as mensagens funcionarem também no Windows PowerShell 5.1.
- A interface limpa o resultado anterior quando o cálculo falha, sem exibir
  totais antigos como se fossem o cálculo novo.

Após atualizar a branch local, execute `PARAR_SOFTWARE.bat` e depois
`INICIAR_SOFTWARE.bat`, para o Vite reiniciar com a configuração nova. A API
local continua precisando da `.venv` com `api/requirements.txt` instalado.

## Produção permanente

Publicar os arquivos do frontend a partir da main não mantém um processo
Python em execução. Para funcionar sem o computador do desenvolvedor, o
backend precisa estar em um serviço de servidor ativo e acessível ao frontend.

O pacote já existente em `deploy/hostinger/` prepara um VPS com Docker Compose:
FastAPI e nginx, ambos com `restart: unless-stopped`, healthchecks e proxy de
`/health` e `/api`. O nginx do host termina HTTPS e encaminha ao container web.
Docker deve iniciar com o sistema. Essa configuração depende de VPS compatível,
acesso para implantação e apontamento/proxy do domínio.

Se o plano atual publicar somente o frontend, será necessário disponibilizar
um backend persistente e configurar o proxy, ou informar a URL pública HTTPS
do backend em `VITE_API_URL`, reconstruir o frontend e autorizar sua origem na
API. `VITE_API_URL` é configuração de build, não muda um site já compilado.

Antes de escolher ou implantar a opção de hospedagem, identificar provedor,
produto contratado e método atual de publicação. Não foi efetuada mudança no
servidor nem no DNS nesta correção. Não há promessa de ausência absoluta de
interrupções; o objetivo é executar a API continuamente e reiniciar o processo
após falhas/reinício do servidor.

Critérios de aceite para o domínio: `/health` responder JSON do Software
Esquadrias com status `ok`; `/api/v1/engine/cr/options` responder JSON; cálculo
válido funcionar no navegador; API continuar acessível com o computador local
desligado. O 404 observado ainda requer implantação/configuração externa.
