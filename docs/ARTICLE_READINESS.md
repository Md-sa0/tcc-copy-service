# Preparação do artigo — revisão em 20/10/2026

A base implementada permite iniciar a redação de problema, objetivos, arquitetura e método. A conclusão de eficácia depende de evidências reais ainda não obtidas nesta revisão. Mais telas ou mais serviços, isoladamente, não tornam a contribuição científica mais forte.

## Contribuição a demonstrar

Investigar se uma aplicação com validação estrita, geração estruturada e cache determinístico consegue reutilizar conteúdo publicitário multicanal com menor latência e menos inferências, preservando rastreabilidade e contratos de saída. Delimitar a implementação como um serviço de negócio modular integrado a serviços de infraestrutura; não descrevê-la como múltiplos microsserviços de negócio ou fila assíncrona persistente.

## Roteiro de demonstração

1. Acessar `http://localhost:8082` e selecionar **Como funciona**.
2. Mostrar os componentes realmente em execução: SQLite, cache simulado e IA simulada no modo local.
3. Clicar em **Executar demonstração**. A aplicação cria um produto e efetua chamadas reais à API local, com gerador simulado.
4. Observar 422 para dados incompletos, MISS inicial, HIT com o mesmo hash e ID da copy, e MISS/hash diferente ao mudar o tom.
5. Baixar o relatório JSON. Cada duração mede o tempo percebido pelo navegador, e não apenas a inferência.
6. Abrir **Ver produto e copies** para consultar o histórico; gerar no estúdio para visualizar os três canais.
7. Abrir as métricas. O erro 422 intencional aparece na auditoria: não indica um defeito nessa demonstração.

Os relatórios são evidências funcionais desta demonstração, não resultados de desempenho de Gemini. Novas execuções criam produtos adicionais e não apagam dados existentes.

## Evidências necessárias para finalizar resultados

| Questão | Procedimento | Evidência a guardar |
|---|---|---|
| Contratos de entrada e saída são respeitados? | Testes automatizados e chamadas reais válidas/inválidas; reportar respostas do LLM rejeitadas | Logs sanitizados, status HTTP e versões dos schemas |
| O cache reduz latência? | Rodadas frias/quentes com o mesmo catálogo e configuração; repetir o experimento | CSV bruto, n por classe, média, mediana, dispersão e percentis |
| O consumo diminui? | Medir usage_metadata nas gerações e contar chamadas evitadas | Tokens observados separados de economia estimada |
| Os registros sobrevivem à reinicialização? | Criar dados, reiniciar contêineres sem remover volumes, consultar IDs | Registro antes/depois e migrações executadas |
| O conteúdo é adequado ao produto e canal? | Avaliação humana com rubrica definida previamente | Notas por critério, avaliadores, amostra e discordâncias |
| Há comportamento controlado sob falhas? | Exercitar indisponibilidade, timeout, 429/503 e concorrência | Taxas de erro, tentativas e ausência/presença de duplicação |

Rubrica proposta para avaliação humana: fidelidade aos atributos, ausência de afirmações não fornecidas, clareza, adequação ao canal e adequação ao tom. Usar uma escala previamente definida (por exemplo, 1 a 5), justificar a seleção dos produtos e, se possível, dois avaliadores independentes. Não inventar notas nem inferir qualidade textual apenas da aceitação do JSON.

## Situação nesta revisão

Docker está instalado, mas o engine não responde e a virtualização de firmware está desativada. A demonstração local permanece viável. Nenhuma chamada paga ao Gemini foi feita nesta revisão. Sem executar a infraestrutura e o provedor reais, não declarar validação de produção nem generalizar os tempos da simulação.

Recomendação: começar a escrever introdução, objetivos, fundamentação e método agora; concluir resultados, discussão e conclusões depois do experimento real e da avaliação textual. O orientador deve validar o recorte, o protocolo e os critérios de avaliação.
