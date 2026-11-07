# Teste de carga local — 05/11/2026

Foram executadas 240 consultas HTTP ao catálogo, histórico de copies, resumo e histórico de métricas, em três rodadas de 80 requisições. Não foram disparadas novas inferências pagas. Cada duração inclui a resposta HTTP completa; a espera na fila do cliente não está incluída.

| Concorrência | Requisições | Falhas | Mediana (ms) | p95 observado (ms) |
|---|---:|---:|---:|---:|
| 5 | 80 | 0 | 11,7 | 281,9 |
| 10 | 80 | 0 | 32,1 | 320,6 |
| 20 | 80 | 0 | 90,6 | 418,7 |

Teste de integração isolado: 30 gerações simultâneas do mesmo hash retornaram 200, com apenas uma chamada ao provedor simulado. A suíte backend passou com 43 casos; frontend com cinco casos, build aprovado e verificação das quatro telas em cinco larguras aprovada.

Ambiente: computador local, SQLite e FakeRedis. Os testes não determinam a capacidade máxima, não são teste de longa duração e não comprovam concorrência distribuída com Redis/PostgreSQL nem limites do Gemini real. A auditoria registra consultas de catálogo/copies realizadas neste teste, mas não as contabiliza como gerações. Observações brutas em `artifacts/stress-review.json` (arquivo local ignorado).

A revisão visual removeu a marca decorativa da prévia e o slogan do título da aba. Avisos de simulação e revisão do conteúdo permanecem, pois descrevem o funcionamento real.
