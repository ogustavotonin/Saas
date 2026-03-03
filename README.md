# Micro SaaS NexusCore (Assinaturas + Indicações)

Aplicação web para gerenciar:
- clientes em comodato de automação residencial/predial;
- assinaturas ativas e período da assinatura;
- indicações com bônus (% quando a venda fecha);
- benefícios em pontos quando a venda não fecha;
- histórico de manutenções;
- integração com Agendor e Autentique após fechamento.

## Stack
- FastAPI + Jinja2
- SQLite + SQLAlchemy
- Sessão com autenticação em cookie

## Executar localmente
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Acesse: `http://localhost:8000`

Login inicial:
- usuário: `admin`
- senha: valor de `ADMIN_INITIAL_PASSWORD` (se não definir, uma senha temporária é gerada no startup e exibida no log)

## Integrações
Configure variáveis de ambiente para integração real:
- `AGENDOR_TOKEN`
- `AUTENTIQUE_TOKEN`
- `SESSION_SECRET`
- `ADMIN_INITIAL_PASSWORD`
- `ROOT_PATH` (ex: `/microsaas` para servir em `nexuscoreautomacao.com/microsaas`)

Fluxo implementado:
1. Cadastro de indicação.
2. Ao clicar **Fechar venda**:
   - calcula bônus e pontos;
   - ativa assinatura do cliente por 12 meses;
   - envia cliente para Agendor;
   - dispara payload para Autentique.

## Deploy na VPS (Git clone + domínio)
1. Faça `git clone` deste repositório na VPS.
2. Crie o arquivo `.env` com as variáveis (`SESSION_SECRET`, `AGENDOR_TOKEN`, `AUTENTIQUE_TOKEN`, etc.).
3. Suba a aplicação com Docker Compose:
   ```bash
   docker compose up -d --build
   ```
4. Configure o Nginx (ou Traefik/Caddy) para redirecionar `sistema.nexuscoreautomacao.com` para `127.0.0.1:8000`.
5. Como o acesso será por subdomínio, mantenha `ROOT_PATH` vazio (ou remova a variável).

Arquivos de infraestrutura incluídos no repositório:
- `Dockerfile`
- `docker-compose.yml`
