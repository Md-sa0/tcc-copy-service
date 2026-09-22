# Protocolo experimental e validade das métricas

O benchmark produz observações reais da execução em curso. Não há números de desempenho fixos embutidos no dashboard nem resultados de Gemini inventados.

## Desenho

1. Em uma base dedicada, iniciar os quatro serviços e aguardar readiness.
2. Registrar hardware, sistema, região/conexão de rede, versões Docker, modelo, data, configuração do prompt, TTL, concorrência e limites de cota. Guardar o commit do código.
3. Rodar o script com produtos novos (padrão): 10 cadastros em categorias distintas, UUIDs/SKUs exclusivos por execução.
4. Fase `cold`: uma solicitação por produto. Aguardar todas terminarem.
5. Fase `warm`: repetir os mesmos produtos/tom. Há barreira entre cada rodada.
6. Classificar HIT/MISS pelos headers/resposta observados, nunca pela fase presumida. Expiração, falha inicial, TTL curto ou uso de `--reuse-catalog` podem mudar a classe esperada.
7. Exportar dados e repetir o experimento completo várias vezes. Reportar tamanho da amostra, dispersão e falhas, além das médias. Dez produtos são uma carga inicial de demonstração, não prova de generalização estatística.

Exemplo de uma execução: concorrência 2, três repetições quentes, pausa 0,25 s por worker. Cada execução pode consumir pelo menos dez inferências reais se Gemini estiver habilitado. Não se apagam caches/dados compartilhados para fabricar uma condição fria.

## Artefatos

- `requests.csv`: run_id, fase, repetição, SKU/UUID, código HTTP, status do cache, latências cliente/API, hash, request ID, modelo, tokens usados/economizados estimados e tipo de erro.
- `results.json`: observações, período UTC, configuração de carga, provedor/modelo, versão Python, sumário e ressalvas.
- `report.md`: tabela pronta para revisão, com contagem, média, mediana, p95 e p99 separados por HIT/MISS.

Falhas de transporte têm código 0; falhas HTTP preservam o código. O script exporta resultados de geração mesmo se houver falhas e termina com código 1. Uma falha de preparação/cadastro interrompe a carga antes das medições. A configuração do provedor não deve mudar durante uma execução.

## Fórmulas

Considere somente gerações HTTP 2xx para latência comparativa e cache hit ratio.

```text
cache_hit_ratio = hits / (hits + misses)
economia_latencia_% = 100 × (1 − media_hit / media_miss)
tokens_estimados_evitados = Σ tokens_da_inferencia_original_de_cada_hit
economia_tokens_estimada_% = 100 × evitados / (consumidos + evitados)
```

A economia de latência pode ser negativa sob contenção; não é artificialmente limitada a zero. Denominador ausente/zero ou uma das classes sem amostra produz `null`, exibido como “—”. Mock usa zero tokens e, portanto, não exibe uma economia percentual artificial.

O dashboard agrega por modelo atualmente configurado e janela temporal. Falhas anteriores à definição do modelo entram na contagem de erro. CRUD, GET de copies, healthchecks e consulta às próprias métricas não contaminam o resumo de geração. O histórico de auditoria pode mostrar todos os modelos, com identificação explícita.

## Latências distintas

- `client_latency_ms`: do envio HTTP até receber o corpo, incluindo rede/proxy, processamento e auditoria.
- `api_metrics.latency_ms` / `X-Process-Time × 1000`: até a resposta estar produzida, antes de gravar a própria métrica; sem rede do cliente.
- `generated_copies.inference_time_ms`: tempo do provedor, incluindo retries/backoff quando ocorrem; não é a latência de um HIT.

O benchmark resume a latência do cliente, enquanto o dashboard resume a latência interna. Os números podem divergir legitimamente. Em pedidos concorrentes do mesmo hash, um HIT pode incluir espera pelo primeiro gerador e ter latência próxima à de MISS.

## Limitações e ameaças à validade

Tokens economizados são um cenário contrafactual estimado pelo consumo original, não uma medição de uma chamada que ocorreu. Consumo informado pelo SDK inclui os tokens que ele reportar; não há decomposição de custo financeiro ou preço por categoria. Requisições que o provedor faturou mas falharam antes de expor `usage_metadata` não são contabilizadas; comparar com o console de faturamento para análises financeiras.

Pydantic valida estrutura, limites e tipos, não qualidade persuasiva nem veracidade factual. O mock só testa o fluxo. SQLite/FakeRedis são úteis para testes isolados, não evidência de desempenho de PostgreSQL/Redis. Resultados locais de QA devem permanecer separados do experimento real do TCC.

A revalidação local pode rejeitar respostas mesmo com Structured Outputs; isso é comportamento previsto e deve ser reportado como falha. Cache e banco não têm transação atômica conjunta. Retentativas, cota, pausas, jitter, rede, concorrência, carga do provedor, tamanhos de prompt e aquecimento influenciam os resultados. Não atribuir causalidade ou significância estatística apenas a uma execução curta.
