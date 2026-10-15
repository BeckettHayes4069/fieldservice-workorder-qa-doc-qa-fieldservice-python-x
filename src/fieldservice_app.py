from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fieldservice_client import InfraiClient


@dataclass
class WorkOrderQuestion:
    work_order_id: str
    question: str


def answer_question(request: WorkOrderQuestion, client: InfraiClient) -> str:
    embedding = client.embed(request.question)
    matches = client.query("field-work-orders", embedding, top_k=5)
    candidates = [item.get("metadata", {}).get("text", "") for item in matches.get("matches", matches if isinstance(matches, list) else [])]
    candidates = [text for text in candidates if text]
    if not candidates:
        return "No matching work-order notes found."
    ranked = client.rerank(request.question, candidates, top_k=1)
    if isinstance(ranked, dict) and ranked.get("results"):
        return ranked["results"][0].get("text", candidates[0])
    return candidates[0]


def seed_notes(client: InfraiClient, notes: List[str]) -> None:
    dimension = len(client.embed(notes[0]))
    client.ensure_collection("field-work-orders", dimension)
    vectors = [{"id": f"note-{i}", "values": client.embed(note), "metadata": {"text": note}} for i, note in enumerate(notes)]
    client.upsert("field-work-orders", vectors)


if __name__ == "__main__":
    from fieldservice_client import InfraiClient

    service = InfraiClient()
    seed_notes(service, ["Pump replaced; pressure test passed on WO-1042."])
    question = WorkOrderQuestion("WO-1042", "What did the technician report after replacing the pump?")
    print(answer_question(question, service))
