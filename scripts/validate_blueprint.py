"""Validate documentation placeholders and example graph. No app/runtime tests."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
for p in root.rglob("*.md"):
    assert not re.search(r"\{\{[A-Z_0-9]+\}\}", p.read_text()), f"Unfilled placeholder: {p}"
for p in (root / "packages/contracts").glob("*.json"):
    json.loads(p.read_text())
graph = json.loads((root / "packages/contracts/hr-intake.workflow.json").read_text())
ids = [n["id"] for n in graph["nodes"]]
assert len(ids) == len(set(ids)) <= 50
parents = {i: set() for i in ids}
children = {i: [] for i in ids}
for edge in graph["edges"]:
    assert edge["source"] in parents and edge["target"] in parents
    parents[edge["target"]].add(edge["source"])
    children[edge["source"]].append(edge["target"])
visited, active = set(), set()
def walk(i):
    assert i not in active, "Cycle"
    if i in visited:
        return
    active.add(i)
    for child in children[i]:
        walk(child)
    active.remove(i)
    visited.add(i)
walk("intake")
assert visited == set(ids), "Unreachable node"
def ancestors(i):
    result = set(parents[i])
    for parent in parents[i]:
        result.update(ancestors(parent))
    return result
for n in graph["nodes"]:
    for mapping in n["inputs"].values():
        if "node" in mapping:
            assert mapping["node"] in ancestors(n["id"]), "Mapping must reference ancestor"
print("PASS: placeholders, JSON syntax, graph IDs, DAG, reachability, ancestor mappings")
print("Not verified: runtime, node handlers, integrations, frontend, deployment")
