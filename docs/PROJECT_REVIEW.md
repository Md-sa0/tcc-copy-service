# Revisão geral do projeto — 20/10/2026

## Parecer

A aplicação já tem escopo técnico suficiente para sustentar a descrição de arquitetura e método do TCC: catálogo persistente, geração multicanal, contratos de entrada e saída, cache versionado, coordenação de concorrência, auditoria, interface web e implantação declarativa. A prioridade agora é obter evidências com os serviços reais, não acrescentar telas ou dividir artificialmente o backend.

A revisão local não equivale a homologação de produção. O ambiente demonstrado usa SQLite, FakeRedis e gerador simulado. É possível começar introdução, objetivos, fundamentação e método; resultados e conclusões exigem o experimento real.

## Problemas corrigidos

| Área | Problema encontrado | Correção e verificação |
|---|---|---|
| Geração | A espera pelo lock e a inferência tinham orçamentos separados, podendo ultrapassar o timeout do cliente | Prazo compartilhado para a operação; teste de lock ocupado retorna 504 sem chamar o provedor ou apagar o lock alheio |
| Cache | Um JSON válido de outro produto podia ser aceito sob a chave errada | Conferência de snapshot, hash, produto, tom e modelo; entrada incompatível é descartada e regenerada |
| Auditoria | Uso de tokens era perdido quando o provedor retornava conteúdo inválido ou vazio | Consumo informado é preservado no erro e gravado nas métricas; sem salvar conteúdo inválido ou repetir erro de contrato |
| Datas | SQLite devolvia timestamps UTC sem fuso, interpretados pelo navegador como horário local | Contratos serializam timestamps com UTC explícito; testes para produto, copy e auditoria |
| Benchmark | Ausência do cabeçalho de latência virava zero; respostas inesperadas podiam interromper a coleta; média zero causava divisão inválida | Latência desconhecida permanece nula, respostas inválidas são registradas como erros e denominador zero não gera percentual |
| Dependências web | O npm audit apontou oito ocorrências, incluindo dependências transitivas das ferramentas de build | Atualização do lock e migração para Tailwind 4 com plugin PostCSS; auditoria final sem ocorrências; build, testes e navegador aprovados |
| Integração contínua | Auditoria npm excluía dependências de desenvolvimento | Workflow também verifica as ferramentas de build |

A migração de estilos segue o [guia oficial do Tailwind](https://tailwindcss.com/docs/upgrade-guide). O frontend passa a exigir navegadores modernos compatíveis com Tailwind 4: Chrome 111+, Safari 16.4+ e Firefox 128+.

## Verificações realizadas

- Backend: **41 testes aprovados**, incluindo CRUD, validação 422, autenticação, cascata, concorrência, cache, falhas e novas regressões.
- Frontend: **5 testes aprovados** e build TypeScript/Vite concluído.
- Navegador: fluxo completo aprovado para cadastro, edição, geração, HIT, clipboard, três canais, métricas, versão móvel, demonstração guiada e download do relatório. Capturas desktop/móvel inspecionadas.
- Ruff: análise estática aprovada. `pip check`: dependências instaladas consistentes (não é auditoria de vulnerabilidades Python).
- `npm audit`: zero vulnerabilidades conhecidas na árvore instalada nesta data, incluindo dependências de desenvolvimento. Isso não constitui auditoria completa de segurança da aplicação.
- Compose: configuração validada. Alembic: geração offline do SQL concluída; isso não comprova migração aplicada em PostgreSQL.
- Benchmark local `874c80603462`: **20/20 respostas bem-sucedidas**, dez MISS e dez HIT, com CSV/JSON/Markdown em `artifacts/review-benchmarks/874c80603462`. Esses números validam a coleta em modo simulado; não devem ser usados como desempenho do Gemini.
- Aviso remanescente: depreciação interna de typing no SDK Google com Python 3.14; não causou falha. O contêiner usa Python 3.12.

## Limites e próximos passos

1. **Infraestrutura real:** Docker está instalado, mas o engine não inicia neste computador. Habilitar a virtualização e executar Compose; aplicar/verificar migrações, testar reinicialização preservando volumes e repetir os testes com PostgreSQL/Redis. O CI está configurado, mas sua execução remota não foi observada nesta revisão.
2. **LLM real:** executar a amostra com Gemini, registrar modelo, versões, tentativas, tokens informados, rejeições de schema e falhas. Não houve chamada paga nesta revisão. Tokens de falhas sem metadados do provedor permanecem desconhecidos; não interpretar ausência de medição como ausência de cobrança.
3. **Validade científica:** repetir rodadas frias/quentes, guardar observações brutas, separar latência da API da percebida pelo cliente e avaliar o texto com rubrica humana. JSON válido não garante fidelidade publicitária.
4. **Escopo arquitetural:** há um serviço de negócio modular e serviços de infraestrutura. Não há fila durável de tarefas; execução assíncrona refere-se ao I/O. O lock reduz inferências simultâneas, mas não garante execução exatamente uma vez em quedas entre banco e cache.
5. **Operação pública:** antes de disponibilizar para usuários externos, definir HTTPS, gestão de usuários/permissões se necessária, backups e restauração, retenção de auditoria e limites de consumo. A chave compartilhada atual é adequada ao recorte demonstrativo, não substitui isolamento entre organizações.
6. **Repositório:** banco de demonstração, logs e pacotes de instalação foram retirados do versionamento na preparação do envio, preservando as cópias locais. Capturas e evidências selecionadas continuam disponíveis no repositório. As regras de ignore impedem a inclusão automática de novos dados de execução.

## Como verificar agora

Acessar `http://localhost:8082/#como-funciona`, executar a demonstração e consultar o catálogo e as métricas. O servidor precisa continuar ligado. Para iniciar novamente, usar `iniciar-demo.cmd` na pasta do projeto.

O roteiro de coleta para o artigo está em [ARTICLE_READINESS.md](ARTICLE_READINESS.md).
