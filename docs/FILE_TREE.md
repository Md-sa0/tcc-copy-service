# Árvore completa do projeto

Arquivos de código, configuração, testes e documentação. Omitidos somente segredos locais, dependências instaladas, caches, builds e resultados de execução. Os dois PDFs acadêmicos preexistentes foram preservados.

```text
copylab/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── BENCHMARK.md
│   ├── FILE_TREE.md
│   ├── OPERATIONS.md
│   └── VALIDATION.md
├── frontend/
│   ├── src/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── Dashboard.tsx
│   │   ├── main.tsx
│   │   ├── Previews.tsx
│   │   ├── ProductForm.tsx
│   │   ├── styles.css
│   │   ├── types.ts
│   │   ├── validation.test.ts
│   │   └── validation.ts
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── e2e.mjs
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── migrations/
│   ├── versions/
│   │   └── 0001_initial.py
│   ├── env.py
│   └── script.py.mako
├── scripts/
│   ├── __init__.py
│   ├── file_tree.py
│   ├── lock_requirements.py
│   └── seed_data.py
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── middleware.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── copies.py
│   │   ├── metrics.py
│   │   └── products.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── copies.py
│   │   ├── metrics.py
│   │   └── products.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generation.py
│   │   ├── hashing.py
│   │   └── llm.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_services.py
│   └── ui_server.py
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── benchmark.py
├── Capítulo 4 - Resultados e Discussão (TCC).pdf
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── requirements-dev.txt
├── requirements.lock
├── requirements.txt
├── seed_and_benchmark.py
├── Seção de Resultados e Discussão - TCC.pdf
└── test_falhas.py
```
