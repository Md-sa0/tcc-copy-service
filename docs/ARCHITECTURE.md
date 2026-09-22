# Arquitetura e fluxo de dados

## Visão de implantação

```mermaid
flowchart LR
    U[Operador no navegador] -->|HTTP localhost:8080| N[Nginx / SPA React]
    subgraph edge[Rede edge]
        N -->|/api/v1 e /health| A[FastAPI · serviço de conteúdo]
    end
    subgraph data[Rede data · interna]
        A -->|SQLAlchemy asyncpg| P[(PostgreSQL 17)]
        A -->|redis-py async| R[(Redis 7.4)]
    end
    A -->|HTTPS · SDK async| G[Google Gemini]
    P --- VP[Volume postgres_data]
    R --- VR[Volume redis_data / AOF]
```

O Redis é cache compartilhado e coordenador de concorrência, não a fonte definitiva do histórico. PostgreSQL é a fonte de verdade. Ambos ficam inacessíveis externamente por portas no Compose. A API participa também da rede edge, que permite saída HTTPS ao Gemini. O bundle frontend nunca contém a chave Gemini.

## Camadas

| Camada | Responsabilidade | Implementação |
|---|---|---|
| Interface web | Formulários, catálogo, previews, métricas | React + TypeScript + Tailwind, Zod, Recharts |
| Entrega HTTP | Rotas, autenticação, paginação | `src/routers`, `src/core/dependencies.py` |
| Contratos | Validação na borda e validação do LLM | `src/schemas` |
| Aplicação | Cache, coordenação, geração e persistência | `src/services/generation.py` |
| Integração IA | Prompt, schema, SDK async, retries | `src/services/llm.py` |
| Domínio persistido | Produtos, versões de copies, auditoria | `src/models` |
| Infraestrutura | Settings, engine, Redis, middleware | `src/core` |
| Evolução do banco | Migrações explícitas | `migrations/versions` |

É arquitetura em camadas. Os serviços dependem de contratos Pydantic e entidades SQLAlchemy; não se afirma independência total do framework. A fábrica `create_app` aceita provedor, sessão e cache injetados, permitindo testar o comportamento de integração.

## Sequência de geração

```mermaid
sequenceDiagram
    participant UI as React
    participant API as FastAPI
    participant SQL as PostgreSQL
    participant R as Redis
    participant LLM as Gemini
    UI->>API: POST /products ou PUT /products/{id}
    API->>API: Autenticação + ProductCreate
    API->>SQL: Persistir cadastro / verificar SKU único
    SQL-->>UI: Produto com UUID
    UI->>API: POST /copies/generate {product_id, tone_of_voice}
    API->>API: GenerateRequest + UUID + enum
    API->>SQL: Ler snapshot do produto
    API->>API: Canonizar JSON e calcular SHA-256
    API->>R: GET copy:sha256:{hash}
    alt HIT
        R-->>API: CopyRead serializado
    else MISS
        API->>R: SET lock:{key} owner NX EX
        Note over API,R: Contendentes aguardam cache ou retomam lock
        API->>R: GET novamente sob lock
        API->>LLM: generate_content assíncrono + JSON Schema
        Note over API,LLM: 429/503: backoff exponencial limitado + jitter
        LLM-->>API: JSON + usage_metadata
        API->>API: Revalidar MarketingOutput
        API->>SQL: COMMIT generated_copies + snapshot
        API->>R: SETEX key TTL CopyRead
        API->>R: Lua: liberar somente se owner coincidir
    end
    API->>SQL: Gravar api_metrics
    API-->>UI: Copy + cache_status + X-Process-Time + X-Request-ID
```

Uma entrada inválida retorna 422 antes de consultar o catálogo, Redis ou LLM para geração. O middleware ainda grava a falha na auditoria; portanto, validação na borda não significa ausência absoluta de I/O de observabilidade. O tempo informado no header e em `api_metrics.latency_ms` é medido antes dessa gravação.

## Canonização e identidade

1. Pydantic remove espaços externos, normaliza Unicode NFC e rejeita tipos/limites inválidos.
2. A canonização inclui UUID e todos os atributos cadastrais, inclusive SKU; benefícios são ordenados por terem semântica de conjunto.
3. Acrescenta tom, modelo/provedor efetivo, versão do prompt, versão do schema e temperatura.
4. Serializa com `sort_keys=True`, `ensure_ascii=False`, separadores compactos e codificação UTF-8.
5. Aplica SHA-256. O mesmo snapshot canônico também é enviado ao LLM.

Datas de cadastro não participam do hash. Reordenar chaves de JSON ou benefícios não gera um novo hash. Editar um atributo estável, tom, modelo ou versão do prompt gera outra chave. Alterações no prompt exigem incremento de `PROMPT_VERSION`; mudanças no contrato de saída exigem atualização da versão do schema em `hashing.py`.

O identificador do produto evita que um HIT de outro produto retorne uma FK incorreta. Excluir um produto remove as copies por FK `ON DELETE CASCADE`; chaves antigas expiram pelo TTL, mas não são acessíveis pela geração porque o produto é consultado antes do cache. Recriar o mesmo SKU produz outro UUID.

## Concorrência e consistência

- Lock Redis por hash com token aleatório; liberação atômica com Lua compara o proprietário.
- O trecho de geração/persistência/cache tem timeout total menor que o lease. O segundo GET após adquirir o lock evita corrida com outro worker.
- Redis usa `noeviction` para não expulsar locks antes do prazo. Capacidade deve ser monitorada; falta de memória pode causar 503 em vez de chamadas duplicadas descontroladas.
- A transação de leitura é encerrada antes da espera pelo LLM. Se o produto for editado durante a inferência, a versão gerada preserva o snapshot original. Se for excluído antes do commit, a FK rejeita a gravação e a API responde 409.
- Primeiro grava no PostgreSQL, depois no cache. Se `SETEX` falhar, entrega o registro salvo e registra aviso; a próxima chamada pode gerar novamente. Redis e PostgreSQL não compartilham uma transação distribuída.
- Expiração do TTL causa nova inferência, mantendo as versões anteriores no banco. `input_hash` tem índice, não restrição UNIQUE.
- Um crash após commit e antes do cache, pausa de processo superior ao lease ou perda do estado do Redis pode gerar versões repetidas. Não há promessa de exactly-once entre serviços.

## Persistência

```mermaid
erDiagram
    PRODUCTS ||--o{ GENERATED_COPIES : possui
    PRODUCTS {
        uuid id PK
        string sku UK
        string name
        string category
        string target_audience
        jsonb technical_attributes
        jsonb key_benefits
        timestamp created_at
        timestamp updated_at
    }
    GENERATED_COPIES {
        uuid id PK
        uuid product_id FK
        string input_hash
        string tone_of_voice
        jsonb input_snapshot
        jsonb instagram_copy
        jsonb whatsapp_copy
        jsonb seo_copy
        string model_name
        float inference_time_ms
        int tokens_used
        timestamp created_at
    }
    API_METRICS {
        uuid id PK
        string request_id
        string path
        string method
        string kind
        float latency_ms
        string cache_status
        int status_code
        string input_hash
        string model_name
        int tokens_used
        int tokens_saved
        timestamp created_at
    }
```

`api_metrics` não possui FK com produto, preservando a auditoria após exclusão. Há índices por SKU, produto/data, hash, request ID e data/tipo de evento. PostgreSQL armazena arrays lógicos como JSONB. Datas são persistidas com timezone e padrão UTC do contêiner PostgreSQL.

## Escopo assíncrono

Chamadas ao Gemini, SQL e Redis usam `await`; retentativas usam `asyncio.sleep`, liberando o event loop. Não há fila persistente nem worker independente. Uma evolução para trabalhos longos exigiria endpoint 202, tabela de jobs, outbox e worker com idempotência; não foi introduzida uma fila fictícia somente para elevar a contagem de serviços.
