"""Generate the documented project tree without secrets and runtime dependencies."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
excluded_dirs = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "artifacts",
    "artifacts-benchmarks",
}
excluded_files = {".env", "resultado_cache.json", "resultado_teste_falha.json", "metricas_benchmark.json"}


def walk(folder, prefix=""):
    entries = sorted(
        (
            p
            for p in folder.iterdir()
            if p.name not in excluded_dirs | excluded_files and not p.name.endswith((".pyc", ".tsbuildinfo"))
        ),
        key=lambda p: (p.is_file(), p.name.lower()),
    )
    result = []
    for index, path in enumerate(entries):
        last = index == len(entries) - 1
        result.append(prefix + ("└── " if last else "├── ") + path.name + ("/" if path.is_dir() else ""))
        if path.is_dir():
            result.extend(walk(path, prefix + ("    " if last else "│   ")))
    return result


target = root / "docs" / "FILE_TREE.md"
target.touch(exist_ok=True)
target.write_text(
    "# Árvore completa do projeto\n\nArquivos de código, configuração, testes e documentação. "
    "Omitidos somente segredos locais, dependências instaladas, caches, builds e resultados de execução. "
    "Os dois PDFs acadêmicos preexistentes foram preservados.\n\n```text\ncopylab/\n"
    + "\n".join(walk(root))
    + "\n```\n",
    encoding="utf-8",
)
