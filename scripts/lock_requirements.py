"""Freeze the installed runtime dependency closure; run from the project virtualenv."""

from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

roots = [
    Requirement(line)
    for line in Path("requirements.txt").read_text().splitlines()
    if line and not line.startswith("#")
]
pending = roots[:]
resolved = {}
while pending:
    requirement = pending.pop()
    name = canonicalize_name(requirement.name)
    if name in resolved:
        continue
    dist = distribution(name)
    resolved[name] = dist.version
    extras = {"", *requirement.extras}
    for value in dist.requires or []:
        child = Requirement(value)
        if child.marker is None or any(child.marker.evaluate({"extra": extra}) for extra in extras):
            pending.append(child)

lines = ["# Exact runtime versions validated locally; Python 3.12 Linux in Docker."]
for name, version in sorted(resolved.items()):
    suffix = "[standard]" if name == "uvicorn" else "[asyncio]" if name == "sqlalchemy" else ""
    lines.append(f"{name}{suffix}=={version}")
# Uvicorn's standard extra is platform conditional and isn't installed on Windows.
lines.append('uvloop==0.22.1; sys_platform != "win32" and platform_python_implementation == "CPython"')
Path("requirements.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")
