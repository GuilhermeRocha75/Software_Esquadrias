# Deploy de produção (Hostinger VPS Linux com Docker Compose)

O repositório não revela o plano contratado, o domínio nem credenciais de
servidor. A publicação atual do frontend pelo GitHub/Hostinger não comprova
que exista um processo Python persistente. Esta configuração requer **VPS com
Docker Compose e acesso para instalar o proxy HTTPS**. Ela não ativa sozinha a
API em uma hospedagem que publique apenas arquivos estáticos.

Arquitetura: navegador → HTTPS no nginx do host → `127.0.0.1:8080` → nginx
do container → `/api/v1/*` e `/health` no FastAPI interno. O frontend usa
URLs relativas no build de produção. A API não é exposta diretamente na rede
do VPS; ambas as containers usam `restart: unless-stopped`. Healthchecks
validam a API e a página inicial. Uvicorn registra acessos, não usa reload e
confia nos cabeçalhos de proxy apenas porque a API está isolada na rede Compose.

## Implantação no VPS

1. Instale Docker Engine, o plugin Compose, nginx e TLS no VPS. Garanta que o
   domínio aponte para o VPS. Confirme antes qual plano Hostinger está ativo.
2. Clone a branch revisada em um diretório do VPS. Copie `.env.example` para
   `.env` nesta pasta e ajuste `WEB_PORT` se 8080 estiver ocupado. `PORT` da API
   é 8000 dentro da rede Compose. `CORS_ALLOWED_ORIGINS` pode ficar vazio para
   mesmo domínio; para outro frontend, forneça lista explícita separada por
   vírgulas, por exemplo `https://app.exemplo.com`.
3. Na raiz do repositório, execute:

   ```sh
   docker compose --env-file deploy/hostinger/.env -f deploy/hostinger/compose.yaml up -d --build
   docker compose --env-file deploy/hostinger/.env -f deploy/hostinger/compose.yaml ps
   curl --fail http://127.0.0.1:8080/health
   curl --fail http://127.0.0.1:8080/api/v1/engine/maxim-ar/options
   ```

4. Adapte `host-nginx.example.conf` para o domínio e certificados reais e
   instale no nginx do host. Faça `nginx -t` e recarregue o serviço. Teste
   `https://DOMINIO/health`, `/api/v1/engine/maxim-ar/options` e a página
   inicial a partir de outra rede. A URL do frontend e da API é a mesma
   origem; o proxy preserva `/api/v1`, sem duplicar prefixos.
5. Para atualizar, faça pull da branch aprovada e repita `docker compose ... up
   -d --build`. Para logs, use `docker compose ... logs -f api web`.

O único requisito para colocar este pacote online é acesso efetivo a um VPS
compatível e ao DNS/proxy do domínio. Não foi fornecido acesso à conta
Hostinger; a implantação externa e o teste do domínio devem ocorrer nela.
