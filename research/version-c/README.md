# Evidências da versão C corrigida

Código da coleta: c5fe4581e57ab83d598e96f0191a6dd7f9c90960. Código da suíte final: b39fccb4066923a1d524688616d525e166402a22 (derivado de a492fe4); o fluxo da API e o script da coleta são idênticos entre esses commits. Os arquivos deste diretório foram depositados em commit posterior, sem alterar o código avaliado.

- `pytest.xml`: JUnit de 57 testes aprovados; duração interna 17,863 s.
- `pytest.log`: saída da mesma execução; duração exibida pelo pytest 17,89 s. As duas fronteiras de medição não são idênticas.
- `observations.csv`: 150 requisições pela mesma rota autenticada (75 por braço).
- `summary.json`: médias, contagens, catálogo, ambiente e ordem sorteada dos braços.
- `manifest.json`: hashes SHA-256 dos artefatos e comandos.
- `experiment.log`: log da coleta.

Reprodução: instalar requirements.lock e requirements-dev.txt e executar `python -m pytest -q --junitxml=research/version-c/pytest.xml` e `python -m scripts.version_c_experiment` a partir da raiz. Não definir TEST_DATABASE_URL/TEST_REDIS_URL para reproduzir o ambiente local SQLite/FakeRedis. A suíte em CI usa PostgreSQL e Redis, e seu JUnit é um artefato distinto.

A coleta utiliza credencial fictícia persistida, MockTransport, MockProvider com espera programada de 80 ms e zero tokens reais. Três rodadas, cinco produtos, cinco solicitações por produto e braço. Cada braço/rodada usa banco e cache novos, cadastro fora do cronômetro e uma geração de aquecimento não medida seguida de limpeza do cache. O histórico conserva essa geração em ambos os braços. Ordem dos braços sorteada com semente fixa. O cronômetro externo circunda a chamada HTTPX/ASGI autenticada, incluindo a auditoria da aplicação, sem rede TCP; validação adicional no cliente fica fora do cronômetro. O braço forçado passa pelo mesmo bloqueio, provedor, validação e persistência e atualiza o cache; não é uma chamada direta ao provedor nem um sistema sem cache instalado.

Reutilização: média 30,481609 ms, 60 HIT/15 MISS, 15 chamadas. Regeneração forçada: média 108,861784 ms, 75 MISS, 75 chamadas. Redução descritiva 71,999715%; 150 respostas HTTP 200 validadas. Contagens excluem aquecimento. Os registros não medem qualidade publicitária nem desempenho remoto de LLM.
