"""Versioned, deliberately small DAG language. No eval or executable mappings."""

import hashlib
import json
import re
from collections import defaultdict, deque
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyConfig(StrictModel):
    pass


class TelegramTriggerConfig(StrictModel):
    connection_id: str = ""


class AgentConfig(StrictModel):
    agent_id: str = ""


class MapConfig(StrictModel):
    fields: dict[str, Any] = Field(default_factory=lambda: {"text": "{{ input.body }}"})


class RouterConfig(StrictModel):
    field: str = "data.body"
    operator: Literal["contains", "equals", "exists"] = "contains"
    value: str = ""


class SendConfig(StrictModel):
    connection_id: str = ""
    chat_id: str = "{{ input.chat_id }}"
    text: str = "{{ data.reply }}"


class RecordConfig(StrictModel):
    text: str = "{{ data.body }}"


REGISTRY = {
    "manual_trigger": (
        "Manual trigger",
        "Triggers",
        "Start with test data",
        EmptyConfig,
        ["out"],
    ),
    "telegram_trigger": (
        "Telegram trigger",
        "Triggers",
        "Messages received by your bot",
        TelegramTriggerConfig,
        ["out"],
    ),
    "data_map": (
        "Edit fields",
        "Transform",
        "Map data between nodes",
        MapConfig,
        ["out"],
    ),
    "ai_agent": (
        "AI agent",
        "AI",
        "Understand and draft a reply",
        AgentConfig,
        ["out"],
    ),
    "if_else": (
        "If / Else",
        "Logic",
        "Choose one matching branch",
        RouterConfig,
        ["true", "false"],
    ),
    "human_approval": (
        "Human approval",
        "Logic",
        "Review the exact action before sending",
        EmptyConfig,
        ["out"],
    ),
    "telegram_send": (
        "Telegram send",
        "Actions",
        "Send an approved message",
        SendConfig,
        ["out"],
    ),
    "record_action": (
        "Record result",
        "Actions",
        "Save a result in this run",
        RecordConfig,
        ["out"],
    ),
}


def manifests():
    return [
        dict(
            type=t,
            version="1",
            name=v[0],
            category=v[1],
            description=v[2],
            config_schema=v[3].model_json_schema(),
            defaults=v[3]().model_dump(),
            outputs=v[4],
        )
        for t, v in REGISTRY.items()
    ]


class Node(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")
    type: str
    label: str = Field(min_length=1, max_length=160)
    x: float = Field(default=0, ge=-100000, le=100000, allow_inf_nan=False)
    y: float = Field(default=0, ge=-100000, le=100000, allow_inf_nan=False)
    config: dict = Field(default_factory=dict)
    version: Literal["1"] = "1"


class Edge(StrictModel):
    source: str
    target: str
    source_handle: str = "out"


class Graph(StrictModel):
    schema_version: Literal[1] = 1
    nodes: list[Node] = Field(min_length=1, max_length=50)
    edges: list[Edge] = Field(max_length=100)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def validate_graph(raw: dict) -> tuple[dict | None, list[str]]:
    if len(json.dumps(raw)) > 1_000_000:
        return None, ["Graph exceeds 1 MB."]
    try:
        graph = Graph.model_validate(raw)
    except ValidationError as exc:
        return None, [
            f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()
        ]
    errors: list[str] = []
    nodes = {n.id: n for n in graph.nodes}
    if len(nodes) != len(graph.nodes):
        errors.append("Node IDs must be unique.")
    triggers = [n for n in graph.nodes if n.type.endswith("_trigger")]
    if len(triggers) != 1:
        errors.append("A workflow needs exactly one trigger in this Lite release.")
    outgoing, incoming = defaultdict(list), defaultdict(list)
    handles: set[tuple[str, str]] = set()
    for edge in graph.edges:
        if edge.source not in nodes or edge.target not in nodes:
            errors.append("An edge references a missing node.")
            continue
        source, target = nodes[edge.source], nodes[edge.target]
        ports = REGISTRY.get(source.type, (None, None, None, None, []))[4]
        if edge.source_handle not in ports:
            errors.append(f"{source.label}: invalid output port {edge.source_handle}.")
        if target.type.endswith("_trigger"):
            errors.append("Triggers cannot have incoming connections.")
        key = (edge.source, edge.source_handle)
        if key in handles:
            errors.append(f"{source.label}: each output connects to one next node.")
        handles.add(key)
        outgoing[edge.source].append(edge.target)
        incoming[edge.target].append(edge.source)
    for n in graph.nodes:
        if n.type not in REGISTRY:
            errors.append(f"Unsupported node: {n.type}.")
            continue
        try:
            n.config = REGISTRY[n.type][3].model_validate(n.config).model_dump()
            if n.type == "data_map":
                if len(n.config["fields"]) > 30 or any(
                    not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,59}", k)
                    for k in n.config["fields"]
                ):
                    errors.append(f"{n.label}: use at most 30 simple field names.")
        except ValidationError as exc:
            errors.extend(
                f"{n.label}: {e['msg']} ({'.'.join(map(str, e['loc']))})"
                for e in exc.errors()
            )
        if n.type == "telegram_send" and (
            not incoming[n.id]
            or any(nodes[s].type != "human_approval" for s in incoming[n.id])
        ):
            errors.append(
                f"{n.label}: connect Human approval directly before Telegram send."
            )
        if n.type == "human_approval" and (
            len(outgoing[n.id]) != 1
            or nodes[outgoing[n.id][0]].type not in ("telegram_send", "record_action")
        ):
            errors.append(f"{n.label}: approval must lead directly to one action.")
        if n.type == "if_else" and not all(
            (n.id, p) in handles for p in ("true", "false")
        ):
            errors.append(f"{n.label}: connect both true and false branches.")
    counts = {n: len(incoming[n]) for n in nodes}
    queue = deque(n for n in nodes if not counts[n])
    visited = []
    while queue:
        n = queue.popleft()
        visited.append(n)
        for target in outgoing[n]:
            counts[target] -= 1
            if not counts[target]:
                queue.append(target)
    if len(visited) != len(nodes):
        errors.append("Cycles are not supported; remove the loop.")
    if len(triggers) == 1:
        reachable, todo = set(), [triggers[0].id]
        while todo:
            n = todo.pop()
            if n not in reachable:
                reachable.add(n)
                todo.extend(outgoing[n])
        if set(nodes) - reachable:
            errors.append("Every node must be reachable from the trigger.")
    return graph.model_dump(), list(dict.fromkeys(errors))


def lookup(path: str, context: dict):
    current: Any = context
    for part in path.strip().split("."):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", part) or part.startswith("__"):
            raise ValueError("Invalid mapping path")
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Mapping field is missing: {path}")
        current = current[part]
    return current


def render(value: Any, context: dict):
    if isinstance(value, dict):
        return {k: render(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [render(v, context) for v in value]
    if not isinstance(value, str):
        return value
    match = re.fullmatch(r"\{\{\s*([^{}]+?)\s*\}\}", value)
    if match:
        return lookup(match[1], context)
    return re.sub(
        r"\{\{\s*([^{}]+?)\s*\}\}", lambda m: str(lookup(m[1], context)), value
    )


def next_node(graph: dict, node_id: str, port="out") -> str | None:
    return next(
        (
            e["target"]
            for e in graph["edges"]
            if e["source"] == node_id and e.get("source_handle", "out") == port
        ),
        None,
    )
