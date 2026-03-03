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

Login padrão:
- usuário: `admin`
- senha: `admin123`

## Integrações
Configure variáveis de ambiente para integração real:
- `AGENDOR_TOKEN`
- `AUTENTIQUE_TOKEN`
- `SESSION_SECRET`
- `ROOT_PATH` (ex: `/microsaas` para servir em `nexuscoreautomacao.com/microsaas`)

Fluxo implementado:
1. Cadastro de indicação.
2. Ao clicar **Fechar venda**:
   - calcula bônus e pontos;
   - ativa assinatura do cliente por 12 meses;
   - envia cliente para Agendor;
   - dispara payload para Autentique.

## Deploy no GitHub + domínio
1. Suba este projeto no GitHub.
2. Faça deploy em um serviço compatível com FastAPI (Railway, Render, Fly.io, VPS).
3. Configure proxy reverso para mapear `nexuscoreautomacao.com/microsaas` para a app.
4. Defina `ROOT_PATH=/microsaas` para corrigir rotas.

Exemplo `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
