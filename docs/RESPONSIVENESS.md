# Responsividade e agilidade — 20/10/2026

Revisão limitada à interface. Testes no Chromium local, build de produção, API com SQLite/cache e IA simulados. Não representam internet móvel, dispositivo físico ou latência do Gemini.

## Ajustes

- Menu em 320 px ultrapassava a página em 3 px. Espaçamento ajustado, mantendo botões com área mínima de 44 × 44 px nessa largura.
- Dashboard carregado sob demanda, com mensagem de carregamento. Removida a divisão manual de chunks que puxava bibliotecas compartilhadas e gráficos para a entrada.
- JavaScript inicialmente carregado: de 696.859 para 322.076 bytes descomprimidos (**53,8% menos**). Isso mede tamanho de recursos, não uma redução equivalente garantida no tempo. Os gráficos continuam disponíveis quando se abre Métricas.

## Evidências

- 20 combinações: estúdio, catálogo, guia e métricas em 320, 390, 768, 1024 e 1440 px. Nenhuma ultrapassou a largura da página após o ajuste. A tabela de métricas mantém sua própria rolagem horizontal em telas pequenas.
- Três contextos novos de navegador: interface pronta com API conectada e dois frames de renderização em **123, 127 e 129 ms**.
- Uma amostra com CPU artificialmente quatro vezes mais lenta: **388 ms**; uma tarefa longa de 65 ms. Não equivale a medir um celular real.
- Navegação por clique até o título/dados e dois frames: **46–863 ms** nas 20 combinações. Maior tempo na abertura das métricas sob demanda. Inclui espera do Playwright e não deve ser chamado de INP.
- Sem erros JavaScript observados. Build, cinco testes frontend e E2E de cadastro, geração, cache, clipboard, previews, métricas, móvel e guia aprovados.
- Capturas de telas e resultados brutos: `artifacts/responsiveness/`. Captura do estúdio de 320 px inspecionada visualmente.

Executar novamente com o servidor ligado: `npm run test:responsive --prefix frontend`. URL padrão `http://localhost:8082`; pode ser substituída por `E2E_BASE_URL`. A verificação de layout e navegação apenas consulta dados; requer catálogo e histórico com registros. `REVIEW_LABEL` define o nome do JSON; padrão `baseline`.

Conclusão: adaptação e velocidade local satisfatórias para a demonstração. Não foram medidos percentis de usuários reais, rede móvel, carga concorrente ou inferência real neste trabalho. As medições são amostras de laboratório, não SLA.
