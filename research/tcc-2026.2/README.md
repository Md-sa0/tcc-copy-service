# Material suplementar CopyLab 2026.2

Coleta de 06/11/2026. Código: tag `tcc-2026.2`, commit `0c8d2a61ec7d513c56026b0a9f85f1572e39d66d`.

## Conteúdo

- `dados`: coleta principal, 600 requisições sequenciais, 120 chamadas diretas e resumo de 135 requisições concorrentes; manifesto, catálogo e JUnit (43 testes).
- `verificacao_seed42`: execução adicional, NÃO agregada às estatísticas principais.
- `source_snapshot`: fontes com os bytes do checkout Windows, para conferência dos hashes. O frontend completo está na tag de código.
- `historico`: consultas HTTP anteriores usadas apenas no Apêndice A.
- `fontes_e_buscas.md`: registro das consultas bibliográficas e dos limites de acesso.
- `constraints-windows-py314.txt`: versões instaladas no ambiente da coleta (Python 3.14.7, Windows). Outros sistemas podem exigir ajustes documentados.
- `SHA256SUMS.txt`: hashes dos arquivos, excluindo o próprio arquivo de hashes.

## Reprodução em checkout limpo

No PowerShell, com Python compatível e Git instalados:

```powershell
git clone --branch tcc-2026.2 --depth 1 https://github.com/Md-sa0/tcc-copy-service.git copylab-ensaio
cd copylab-ensaio
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest --junitxml=artifacts/repro-pytest.xml
.\.venv\Scripts\python.exe scripts/article_experiment.py --seed 20261106 --rounds 3
.\.venv\Scripts\python.exe scripts/article_experiment.py --seed 42 --rounds 1
```

Para fixar as versões, acrescente `-c CAMINHO/constraints-windows-py314.txt` à instalação. Mantenha o pacote extraído fora do checkout para não criar arquivos não rastreados. Em macOS/Linux, use `python3 -m venv .venv` e `.venv/bin/python`.

O script recusa árvore Git suja. Não usar `--allow-dirty` para coleta do artigo. Execute os comandos a partir da tag de código, não da tag de dados. Os resultados são gravados em `artifacts/article-experiment/`. A cópia `source_snapshot` não possui metadados Git: é para auditoria; use o clone para repetir.

Não são necessárias credenciais do Gemini ou servidores PostgreSQL/Redis para este ensaio. Ele usa SQLite, FakeRedis e MockProvider, com espera programada de 80 ms; esta espera não equivale à duração medida. As medições são locais em ASGITransport, sem TCP/navegador. A linha de base é chamada direta ao provedor, não um endpoint equivalente. Não mede qualidade publicitária nem economia financeira real. Novas execuções terão tempos diferentes; preservar seus próprios manifestos e não sobrescrever dados publicados.

Os hashes de fontes são dos bytes Windows: conversão CRLF/LF em outro checkout pode alterar o hash sem alterar o código. Compare com `source_snapshot` para auditar os bytes exatos.
