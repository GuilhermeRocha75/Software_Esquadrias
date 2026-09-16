# Iniciador local (Windows)

Clique duas vezes em `INICIAR_SOFTWARE.bat` na raiz do projeto. Ele inicia a API
em `127.0.0.1:8000`, o Vite em `127.0.0.1:5173`, aguarda ambos responderem e
abre a interface no navegador. Um novo clique reutiliza os serviços já prontos
sem iniciar cópias. `PARAR_SOFTWARE.bat` encerra somente os processos
registrados por este iniciador, conferindo PID, horário e linha de comando.

Pré-requisitos: Windows com PowerShell, Node.js/npm no `PATH` e uma `.venv` na
raiz com `api/requirements.txt` instalado. Se `web/node_modules` estiver
ausente, o iniciador executa `npm ci` com o lockfile. Os logs e o registro de
processos ficam em `.run/`, ignorado pelo Git. Se uma porta estiver ocupada por
outro serviço, o iniciador informa o conflito e não tenta encerrá-lo.

Para teste sem abrir navegador:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/iniciar_software.ps1 -NoBrowser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/parar_software.ps1
```

O iniciador é para desenvolvimento local (`uvicorn --reload`). O deploy de
produção usa configuração separada em `deploy/hostinger/`, sem reload.
