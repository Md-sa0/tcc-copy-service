# Contratos HTTP

Base no Compose: `http://localhost:8080/api/v1`. Especificação completa e schemas: `/openapi.json`; interface: `/docs`.

`POST /auth/register` e `POST /auth/login` são públicos. Após autenticar, a API cria uma sessão de sete dias em cookie `HttpOnly`; alterações exigem também o cookie e header `X-CSRF-Token`. `POST /auth/logout` revoga a sessão. Todas as demais rotas `/api/v1` exigem uma sessão válida. Cada conta tem catálogo, histórico, métricas e chave de provedor isolados.

| Método | Rota | Resultado |
|---|---|---|
| POST | `/auth/register` | 201, cria conta e inicia sessão; senha mínima de 12 caracteres |
| POST | `/auth/login` | 200, inicia sessão |
| GET | `/auth/me` | Conta autenticada |
| POST | `/auth/logout` | 204, revoga a sessão |
| POST | `/products` | 201, produto persistido |
| GET | `/products?q=&sku=&offset=0&limit=20` | Lista e total; busca parcial escapada ou SKU exato |
| GET | `/products/{uuid}` | Produto ou 404 |
| PUT | `/products/{uuid}` | Substituição completa do cadastro, 200 |
| DELETE | `/products/{uuid}` | 204, exclusão em cascata das copies |
| POST | `/copies/generate` | 200, copy persistida e HIT/MISS; `force_regenerate: true` ignora cache |
| GET | `/copies?product_id=&offset=0&limit=20` | Histórico persistido, mais recentes primeiro |
| GET | `/copies/{uuid}` | Versão persistida com snapshot |
| POST | `/copies/{uuid}/revisions` | 201, salva edição como nova versão, preservando a original |
| GET | `/metrics/summary?hours=24` | Resumo do modelo atualmente configurado |
| GET | `/metrics/requests?hours=24&kind=all&offset=0&limit=20` | Auditoria da conta autenticada |

`limit`: 1–100. `offset`: inteiro não negativo. `hours`: 1–8760. `kind`: `all`, `generation` ou `api`.

## Cadastro

```json
{
  "sku": "FONE-001",
  "name": "Fone Bluetooth Aura",
  "category": "Eletrônicos",
  "target_audience": "Estudantes e profissionais",
  "technical_attributes": {
    "conectividade": "Bluetooth 5.3",
    "autonomia": "24 horas"
  },
  "key_benefits": ["Uso sem fios", "Estojo para transporte"]
}
```

SKU: 1–64 caracteres alfanuméricos, ponto, hífen e sublinhado; começa com letra ou número. Nome: 2–200; categoria: 2–100; público: 3–500. Atributos: 1–30 pares string/string, cada chave/valor com 1–500 caracteres. Benefícios: 1–20 textos únicos com 1–500 caracteres. Campos extras são rejeitados. Textos em branco não são válidos.

## Geração

```json
{
  "product_id": "00000000-0000-4000-8000-000000000001",
  "tone_of_voice": "persuasivo",
  "force_regenerate": false
}
```

Substitua o UUID pelo `id` retornado no cadastro. Tons: `persuasivo`, `descontraído`, `institucional`, `promocional`; cada um orienta linguagem e abordagem próprias em Instagram, WhatsApp e SEO. Os prompts pedem legendas de Instagram com cerca de 450–800 caracteres, mensagens de WhatsApp com 250–500 e descrições SEO com 500–900, respeitando os limites máximos dos schemas e sem inventar fatos. O tom padrão é `persuasivo`. Com `force_regenerate: true`, a API ignora o cache e solicita uma nova inferência, que pode consumir créditos/cobrar no provedor configurado. Omitir o campo ou usar `false` mantém o comportamento normal.

Para salvar uma edição, envie `instagram_copy`, `whatsapp_copy` e `seo_copy` completos a `POST /copies/{uuid}/revisions`. Os mesmos limites e contratos de validação da resposta gerada são aplicados. A edição cria uma nova linha de histórico; a versão anterior permanece intacta. Editar não chama o provedor e não consome tokens.

A resposta contém `copy` (ID, produto, hash, snapshot, três canais, modelo, inferência, tokens, data) e `cache_status`. `copy.tokens_used` é o consumo da inferência original daquela versão, mesmo no HIT; o consumo da requisição atual é zero no HIT e fica em `api_metrics.tokens_used`.

Instagram: `hook`, `caption`, `hashtags`, `call_to_action`. WhatsApp: `message`, `call_to_action`. SEO: `meta_title` (até 60), `meta_description` (até 160), `bullet_points`, `long_description`. Resposta do provedor fora do schema retorna 502, sem truncamento silencioso.

## Headers

- `X-Process-Time`: duração interna em **segundos**, seis casas decimais, antes da auditoria.
- `X-Cache-Status`: `HIT`, `MISS` ou `BYPASS`. BYPASS vale para CRUD, validação e falhas antes da decisão de cache. MISS não implica sucesso: uma chamada ao provedor pode falhar.
- `X-Request-ID`: UUID gerado pelo servidor, presente também na auditoria.

## Falhas previstas

| Código | Significado |
|---|---|
| 401 | Sessão ausente, inválida ou expirada; credenciais de login incorretas |
| 403 | Token CSRF inválido ou origem não autorizada |
| 404 | Produto/copy inexistente |
| 409 | E-mail ou SKU duplicado na conta, ou produto excluído durante geração |
| 422 | Contrato de entrada inválido |
| 429 | Limite do Nginx atingido |
| 502 | Falha do provedor ou saída inválida |
| 503 | Redis indisponível, contenção prolongada, falha de transporte ou 429/503 esgotados |
| 504 | Timeout total ou de comunicação com o provedor |
| 500 | Falha interna não prevista; resposta sem segredos |

Falhas do provedor são sanitizadas e retornadas sem tentativas automáticas adicionais. Nginx pode rejeitar requisições antes da API; esses eventos aparecem nos logs do proxy, não em `api_metrics`.

## Migração do protótipo

`POST /v1/generate-copy` foi substituído pelo cadastro seguido de `POST /api/v1/copies/generate`. O identificador comercial antigo `product_id` passa a ser `sku`; `product_id` agora é uma FK UUID. Os tons antigos em inglês devem ser convertidos para os quatro valores em português. `benchmark.py` e `test_falhas.py` já usam os contratos novos.
