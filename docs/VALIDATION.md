## Revisão geral mais recente — 20/10/2026

41 testes backend e 5 frontend aprovados; build, E2E desktop/móvel, Ruff e auditoria npm aprovados. Benchmark local: 20/20 requisições bem-sucedidas. Consulte [PROJECT_REVIEW.md](PROJECT_REVIEW.md) para correções, evidências e pendências. As seções abaixo preservam o registro das verificações anteriores.

# Registro de validação

## Revisão de 20/10/2026

29 testes backend aprovados, 5 testes frontend aprovados e build TypeScript/Vite concluído.
O teste Chromium passou por CRUD, geração, HIT, clipboard, previews, dashboard, layout móvel,
demonstração guiada de quatro verificações e download do relatório JSON.
A demonstração guiada observou 422/BYPASS, 200/MISS, 200/HIT e 200/MISS após mudança de tom.
Artefatos adicionais: `artifacts/guide-report.json` e `artifacts/screenshots/guide-desktop.png`.
As evidências são locais, com SQLite, cache simulado e IA simulada; não validam Gemini ou infraestrutura reais.
Docker está instalado, mas o engine não respondeu e a virtualização de firmware permaneceu desativada.
O servidor de demonstração agora habilita foreign keys no SQLite e informa os componentes ativos em `/health`.

## Validação anterior

Verificações locais realizadas em 22/09/2026, Windows, Python 3.14.7 e Node 24.19.0. O runtime declarado para Docker/CI é Python 3.12 e Node 22.

| Verificação | Resultado e escopo |
|---|---|
| Pytest | 28 testes aprovados; SQLite com FK habilitada, FakeRedis e provedor controlado |
| Ruff | Sem violações nas camadas backend, scripts, migrações e testes |
| Vitest | 5 testes aprovados; normalização, campos extras, coerção, duplicatas e parsing de atributos |
| TypeScript | Compilação estrita sem erros |
| Vite | Build de produção gerado com divisão do bundle de gráficos |
| npm audit | Nenhuma vulnerabilidade reportada na árvore instalada no momento da validação |
| Navegador Chromium | Fluxo completo: cadastro, geração, HIT, clipboard, previews, métricas, pesquisa, edição, exclusão e viewport móvel 390 px |
| Benchmark HTTP | 10 produtos, 30 gerações; 10 MISS e 20 HIT, nenhuma falha; **modo mock sobre SQLite/FakeRedis** |
| Alembic | Migração inicial compilada para SQL PostgreSQL em modo offline |
| Compose | YAML analisado e quatro serviços conferidos; sem execução Docker local |
| Dependências Linux | Wheels das versões fixadas resolvidos para Python 3.12/Linux x86-64, incluindo asyncpg e uvloop |

Os testes backend incluem validação 422 sem chamada ao LLM, CRUD, conflito de SKU, pesquisa escapada, exclusão em cascata, autenticação, HIT/MISS, TTL, edição/tom, snapshot histórico, métricas, cinco pedidos concorrentes com uma única inferência, cache corrompido, falhas de leitura/escrita Redis, timeout, liberação de lock, retentativas 429/503, ausência de retry para 400/401 e rejeição de saída inválida.

Artefatos locais gerados (há arquivos desta pasta atualmente rastreados pelo Git):

- `artifacts/screenshots/studio-empty.png`
- `artifacts/screenshots/studio-generated.png`
- `artifacts/screenshots/studio-mobile.png`
- `artifacts/screenshots/metrics-desktop.png`
- `artifacts/benchmarks/952d3efcd47b/requests.csv`
- `artifacts/benchmarks/952d3efcd47b/results.json`
- `artifacts/benchmarks/952d3efcd47b/report.md`
- `artifacts/validation/migration.sql`

As capturas do dashboard também contêm requisições de QA posteriores ao benchmark. Não se deve comparar seu total diretamente com uma execução isolada do CSV.

## Validações ainda necessárias no ambiente alvo

Docker está instalado, mas o engine está indisponível neste computador. Não foram executados aqui: build/inicialização dos contêineres, migração em PostgreSQL real, comandos em Redis real nem inferência contra a API Gemini. Não se afirma homologação de produção, garantia de disponibilidade ou desempenho real do provedor.

O workflow `.github/workflows/ci.yml` está preparado para PostgreSQL 17, Redis 7.4, migrações com `alembic check`, testes da API, build frontend, Compose e navegador. Sua execução em um runner não foi observada nesta entrega. Após habilitar a virtualização e iniciar o Docker, executar `docker compose up --build` e o benchmark real para produzir as evidências do TCC.

O SDK Google emite um aviso de depreciação interna de typing sob Python 3.14. O aviso não causou falha e não foi ocultado; o contêiner usa Python 3.12.
