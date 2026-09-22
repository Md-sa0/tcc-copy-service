# CopyLab · Conteúdo publicitário multicanal

Aplicação full-stack para automação de conteúdo no varejo eletrônico: catálogo em PostgreSQL, geração assíncrona com Google Gemini e Pydantic v2, cache Redis com SHA-256, SPA React/Tailwind e métricas experimentais persistidas.

**Instituição:** Instituto de Ensino Superior (iCEV)

**Curso:** Bacharelado em Engenharia de Software

**Aluno:** Marcus David Nascimento de Sá

**Orientador:** Prof. Me. Ítalo César Carvalho Lima

**Tema:** Automação da geração de conteúdo publicitário para o varejo eletrônico utilizando microsserviços e modelos de linguagem de larga escala (LLMs) com garantia de saídas estruturadas e cache determinístico.

## Iniciar com um comando

Pré-requisito: Docker Engine/Desktop em execução, com Docker Compose v2 e suporte a contêineres Linux. No diretório do projeto:

```sh
docker compose up --build
```

Abra [a aplicação](http://localhost:8080), [a documentação OpenAPI](http://localhost:8080/docs) ou [a prontidão da API](http://localhost:8080/health/ready). O primeiro build baixa dependências. As migrações Alembic são aplicadas automaticamente antes de iniciar a API; o frontend aguarda sua prontidão.

Sem configuração adicional, a aplicação usa **modo demonstrativo (`LLM_PROVIDER=mock`)**. Todo o fluxo de catálogo, banco, Redis, histórico e métricas funciona, mas os textos são produzidos por um simulador determinístico, sem consumo de tokens e sem resultados experimentais atribuíveis ao Gemini. O banner da SPA e os relatórios identificam esse modo. O catálogo começa vazio; cadastre um produto ou execute a carga abaixo.

### Usar Gemini real

Se ainda não existir `.env`, copie `.env.example` para `.env`. Se já existir, preserve-o e acrescente/ajuste:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_google
GEMINI_MODEL=gemini-2.5-flash
```

Depois execute novamente `docker compose up --build`. O modelo é configurável; disponibilidade e cota dependem da sua conta. A aplicação não troca silenciosamente de modelo nem usa mock quando o provedor falha. A chave Gemini fica exclusivamente na API. Seu `.env` é ignorado pelo Git e excluído do contexto de build.

### Popular 10 produtos e gerar o benchmark

Em outro terminal, com os contêineres já saudáveis:

```sh
docker compose exec api python seed_and_benchmark.py --url http://localhost:8000 --output /tmp/benchmarks --concurrency 2 --repeats 3
docker compose cp api:/tmp/benchmarks ./artifacts-benchmarks
```

O script cria 10 produtos em categorias distintas, incluindo eletrônicos, cosméticos e vestuário. Executa 10 chamadas iniciais e 30 chamadas de repetição, com barreira entre fases. Gera `requests.csv`, `results.json` e `report.md` em uma pasta identificada por execução. Os arquivos ficam em `/tmp` até serem copiados; não são um volume de dados permanente.

Somente carga, reutilizando os SKUs conhecidos:

```sh
docker compose exec api python seed_and_benchmark.py --url http://localhost:8000 --output /tmp/benchmarks --seed-only --reuse-catalog
```

O padrão usa novos IDs/SKUs para obter um cenário inicial sem cache sem apagar dados anteriores. `--reuse-catalog` permite que a primeira rodada seja HIT; os relatórios sempre usam o status efetivamente observado. Em modo Gemini as chamadas consomem sua cota. Para experimentos, use uma base dedicada e registre configuração e data; veja [o protocolo experimental](docs/BENCHMARK.md).

## O que foi implementado

- **Catálogo:** criação, consulta, pesquisa por nome/SKU, paginação, edição por substituição completa e exclusão com remoção das copies dependentes.
- **Contratos:** campos extras proibidos, tipos de texto sem coerção numérica, normalização Unicode NFC, limites de tamanho, atributos obrigatórios, benefícios sem duplicatas e quatro tons de voz.
- **Geração:** SDK `google-genai` assíncrono, JSON Schema derivado de Pydantic, revalidação local da resposta, limites SEO, timeout e retentativas limitadas com backoff exponencial e jitter para 429/503.
- **Cache:** Redis assíncrono, `GET`/`SETEX`, TTL configurável, chaves `copy:sha256:{hash}`, lock distribuído `SET NX EX` e liberação Lua condicionada ao proprietário.
- **Persistência:** SQLAlchemy 2.0/asyncpg, PostgreSQL JSONB, FK, índices, snapshot da entrada de cada geração e migração Alembic versionada. Nenhuma criação automática de tabelas em produção.
- **SPA:** React/TypeScript/Tailwind, validação Zod, editor de produtos, histórico de copies, prévias Instagram/WhatsApp/SEO, botão de cópia com toast, estados de carregamento e erros, layout responsivo.
- **Métricas:** tempo interno, status HTTP/cache, ID da requisição, hash, modelo e tokens. Gráficos HIT × MISS e tabela paginada. Dados de mock e modelo real não se misturam no resumo.
- **Operação:** quatro contêineres, volumes persistentes, redes separadas, serviços de dados sem portas públicas, usuários não root na API e Nginx, healthchecks, API key opcional em desenvolvimento e obrigatória em produção, limite de requisições no Nginx e pipeline de CI.

## Arquitetura e código

```text
Navegador React + Tailwind
         │ HTTP (mesma origem)
         ▼
Nginx :8080 ──► FastAPI /api/v1
                  ├── routers ─► schemas Pydantic
                  ├── services ─► Gemini async / Structured Outputs
                  ├── SQLAlchemy asyncpg ─► PostgreSQL (catálogo, copies, auditoria)
                  └── redis-py async ─────► Redis (TTL e lock por hash)
```

O sistema é uma aplicação distribuída em processos e infraestrutura, com um serviço de negócio modular. A organização interna é **Layered Architecture**, com injeção de dependências e separação entre roteamento, contratos, serviços e persistência. Não é uma coleção de microsserviços independentes por domínio nem uma implementação completa de Clean Architecture hexagonal. A geração usa I/O assíncrono na própria requisição HTTP, sem fila de jobs ou garantia de execução após desconexão.

- [Diagrama detalhado, sequência de dados e decisões](docs/ARCHITECTURE.md)
- [Árvore completa de arquivos](docs/FILE_TREE.md)
- [Contratos HTTP e exemplos](docs/API.md)
- [Metodologia, fórmulas e limitações do benchmark](docs/BENCHMARK.md)
- [Operação, configuração, produção e troubleshooting](docs/OPERATIONS.md)
- [Registro das verificações executadas](docs/VALIDATION.md)

O código está completo no repositório, sem blocos omitidos. Entradas principais: `src/main.py`, `src/services/generation.py`, `src/services/llm.py`, `frontend/src/App.tsx`, `docker-compose.yml` e `seed_and_benchmark.py`. O antigo `main.py` monolítico foi removido; `benchmark.py` delega ao novo benchmark e `test_falhas.py` exercita os contratos atuais. Os PDFs acadêmicos existentes foram preservados.

## Testes e desenvolvimento local

### Demonstração sem Docker neste computador

Com a `.venv` e o build em `frontend/dist` já preparados, abra o terminal do VS Code na raiz do projeto e execute:

```powershell
.\.venv\Scripts\python.exe -m tests.ui_server --port 8082 --serve-frontend
```

Abra http://localhost:8082 e mantenha o terminal aberto. Para encerrar, pressione Ctrl+C.
O comando serve frontend e API no mesmo processo, usando SQLite, FakeRedis e IA simulada.
Não precisa ativar a virtualenv nem executar Node para visualizar o build existente.
Após alterar o código frontend, gere novamente o build para que as mudanças apareçam.
Essa demonstração não valida PostgreSQL, Redis ou Gemini reais.

### Instalação e verificações

Python 3.12+ e Node.js 22.12+:

```sh
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.lock -r requirements-dev.txt
pytest -q
ruff check src tests scripts migrations seed_and_benchmark.py
```

Os testes locais isolados usam SQLite e FakeRedis, sem Gemini. No CI, as mesmas rotas são exercitadas com PostgreSQL e Redis reais em bancos de teste dedicados; há também migrações e smoke test do Compose. `TEST_DATABASE_URL` e `TEST_REDIS_URL` são exclusivamente para bases descartáveis: os fixtures recriam tabelas e limpam o banco Redis indicado.

```sh
cd frontend
npm ci
npm test
npm run build
```

Para desenvolvimento da API com infraestrutura real, configure `DATABASE_URL` e `REDIS_URL` acessíveis, execute `alembic upgrade head` e `uvicorn src.main:app --reload`. A configuração padrão do Compose não publica as portas de PostgreSQL/Redis; use serviços locais de desenvolvimento ou um override explícito.

Teste visual funcional isolado, em terminais separados, sem Docker:

```sh
python -m tests.ui_server
# outro terminal:
cd frontend
npm run dev
# outro terminal, dentro de frontend:
npx playwright install chromium
npm run test:e2e
```

Esse servidor é apenas um auxiliar de QA com SQLite/FakeRedis, jamais o runtime de produção. O teste de navegador cria, gera, verifica cache, copia texto, muda de canal, consulta métricas, pesquisa, edita/seleciona, exclui e verifica o layout móvel. Capturas ficam em `artifacts/screenshots/`.

## Limite da garantia

Structured Outputs e Pydantic garantem a **estrutura aceita pela aplicação**, não a veracidade comercial do texto. Saídas inválidas não são persistidas nem armazenadas em cache, mas alegações e adequação publicitária ainda exigem revisão humana. A chave SHA-256 é determinística; uma nova inferência após expiração do cache não é necessariamente idêntica.

O projeto fornece uma base operacional para implantação. A liberação de produção depende da validação no ambiente alvo, configuração de TLS e segredos, política de backups/restauração, observabilidade e controles de acesso compatíveis com o uso. O Compose entregue publica apenas em `127.0.0.1`; não é uma implantação pública já homologada.

## Referências técnicas

- [Google: Structured Outputs e Pydantic](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [SQLAlchemy: extensão asyncio](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
