# Operação e configuração

## Configurações

| Variável | Padrão | Uso |
|---|---|---|
| APP_ENV | development | development, test ou production |
| SETTINGS_ENCRYPTION_KEY | vazio | Chave mestra Fernet estável para cifrar credenciais cadastradas na interface |
| PROMPT_VERSION | retail-v2 | Invalidar semanticamente o cache após mudar prompt |
| API_KEY | vazio | Proteção X-API-Key da própria API; produção exige >=32 caracteres |
| CACHE_TTL_SECONDS | 86400 | 1–2592000 segundos |
| GENERATION_TIMEOUT_SECONDS | 90 | 5–240; limite da seção crítica |
| DATABASE_URL | localhost | SQLAlchemy URL; Compose define host postgres |
| REDIS_URL | localhost | Redis URL; Compose define host redis e senha |
| POSTGRES_USER / DB / PASSWORD | copy / copy / copy_local | Credenciais locais do Compose |
| REDIS_PASSWORD | redis_local | Senha local do Compose |
| CORS_ORIGINS | localhost:8080 e :5173 | Lista JSON; produção proíbe wildcard |

Ao personalizar senhas com caracteres reservados de URL (`@`, `:`, `/`, `#`, `%`), use URL percent-encoded nas URLs e um override apropriado do Compose; para uso direto da interpolação entregue, prefira segredos aleatórios alfanuméricos longos. Trocar `POSTGRES_PASSWORD` em um volume já inicializado não altera a senha da role existente: faça rotação no banco e ajuste a aplicação em conjunto. `SETTINGS_ENCRYPTION_KEY` protege credenciais cadastradas na interface e deve permanecer estável; ela não é a chave do provedor.

`APP_ENV=production` exige API_KEY forte. Isso é uma validação básica de configuração, não um sistema de identidade empresarial. O controle implementado usa chave compartilhada, sem usuários, papéis, tenants ou revogação individual. Para acesso por equipes, substitua/estenda por OIDC/OAuth2 e RBAC antes da exposição pública. A chave de um provedor de IA é sempre informada pelo usuário na interface; não a configure em `.env`.

## Comandos comuns

```sh
docker compose up --build
docker compose ps
docker compose logs -f api
docker compose logs -f frontend
docker compose exec api alembic current
docker compose exec api alembic check
docker compose down
```

`down` preserva os volumes nomeados. `down -v` remove permanentemente os dados e só deve ser usado quando a perda for intencional. O script de benchmark não usa esse comando.

## Backups e restauração

Exemplo que mantém saída binária fora do redirecionamento do PowerShell:

```sh
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/copy.dump'
docker compose cp postgres:/tmp/copy.dump ./copy.dump
```

Teste periodicamente restauração em outra instância/banco, com `pg_restore`, e confira contagens, FK e migrações. Defina RPO/RTO e retenção conforme o ambiente. O volume Redis tem AOF, mas cache não substitui backup do PostgreSQL. Não trate presença de volume persistente como garantia de recuperação.

## Implantação

A porta da SPA é publicada apenas em `127.0.0.1:8080`. Para acesso externo, configure um proxy/ingress com TLS, domínio e limites, restrinja a rede e ajuste as origens CORS. Não exponha PostgreSQL/Redis. Os defaults de senha são exclusivamente locais. Use secret manager/segredos do orquestrador e rotação no ambiente alvo. Credenciais de provedores são armazenadas cifradas no banco; nunca as compile em variáveis `VITE_*`.

Nginx limita `/api/` a 10 r/s por IP com burst de 30 e rejeição 429. Atrás de outro proxy, a identidade de cliente precisa de configuração explícita de proxies confiáveis. O limite por IP não substitui quotas por usuário. O cliente HTTP do provedor tem timeout de 90 s; a API tem limite total e Nginx aguarda 270 s.

Migrações são executadas no entrypoint da API para permitir o comando único. Para múltiplas réplicas, execute migrações como job único antes do rollout; não inicie migradores concorrentes. Redis compartilha cache entre réplicas, mas não oferece garantia exactly-once diante de perda de estado ou expiração de lease.

`requirements.lock` e `package-lock.json` fixam dependências de aplicação. Imagens base usam tags versionadas, não digests; um processo de release mais rigoroso deve fixar digests, escanear imagens e executar testes no ambiente alvo. O CI foi entregue, mas sua inclusão no repositório não comprova que já executou no GitHub.

## Observabilidade e retenção

Logs da API são estruturados como JSON por requisição auditada, sem payloads nem credenciais. Correlacione por `X-Request-ID`. A auditoria é gravada antes de devolver a resposta, com prazo de 3 segundos; se o banco de métricas falhar, o erro é registrado no log e a resposta de negócio não é descartada. Portanto, falhas de observabilidade podem causar lacunas: os logs devem ser coletados externamente.

Monitorar: 5xx, latência/p95, taxa de 429 do proxy/provedor, disponibilidade de Redis, memória/TTL, volume de conexões PostgreSQL, tempo de inferência e falhas de gravação de métricas. `/health` é liveness; `/health/ready` verifica catálogo e Redis. Nenhum deles faz uma inferência paga.

Não há retenção automática de métricas ou histórico: estabeleça política de retenção e expurgo administrativo com backup/auditoria. Para grande volume, considere particionamento e agregações temporais. As consultas são paginadas; índices atendem o estágio inicial, não substituem análise de plano com carga real.

## Solução de problemas

- **docker não encontrado:** instalar Docker Desktop/Engine e habilitar Compose v2; no Windows, usar o backend Linux/WSL2 conforme o ambiente.
- **Porta 8080 ocupada:** alterar apenas o mapeamento do frontend e ajustar URLs/CORS.
- **API não fica pronta:** examinar logs e estado de PostgreSQL/Redis; confirmar senha e migração Alembic.
- **401 na SPA:** informar a `API_KEY` do servidor no ícone de chave. Recarregar a página apaga a chave da memória.
- **422:** conferir nomes, campos obrigatórios, limites, UUID e tom de voz.
- **409 no cadastro:** SKU é único; editar o produto existente ou usar outro SKU.
- **503 após quota:** reduzir concorrência, verificar quota e aguardar; o serviço não muda de modelo para ocultar a falha.
- **Falha no provedor de IA:** confira modelo, endpoint, chave/permissão e compatibilidade com OpenAI Chat Completions. O erro público é sanitizado para não expor dados do provedor.
- **Cache indisponível:** consultas históricas seguem possíveis; novas gerações falham cedo para evitar duplicação de inferências.
- **Número de tokens zero:** modo mock ou ausência de usage_metadata. “—” na economia significa base insuficiente, não 100% de economia.
