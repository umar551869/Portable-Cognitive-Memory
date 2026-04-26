from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from pcg.api.app import app
from pcg.processing import pipeline as pipeline_module
from pcg.retrieval import search as search_module
from pcg.utils.schemas import EntityExtractionResult, RelationshipExtractionResult


class FakeProvider:
    name = "fake"
    embedding_model = "fake-embed"

    async def extract_entities(self, text: str):
        return EntityExtractionResult.model_validate(
            {
                "entities": [
                    {
                        "temp_id": "chunking",
                        "name": "Chunking",
                        "type": "process",
                        "aliases": [],
                        "description": "Splits content into meaningful units.",
                        "metadata": {},
                    },
                    {
                        "temp_id": "extraction_accuracy",
                        "name": "Extraction Accuracy",
                        "type": "concept",
                        "aliases": [],
                        "description": "Quality of graph extraction.",
                        "metadata": {},
                    },
                ]
            }
        )

    async def extract_relationships(self, text: str, entities: list[str]):
        return RelationshipExtractionResult.model_validate(
            {
                "relationships": [
                    {
                        "source_name": "Chunking",
                        "target_name": "Extraction Accuracy",
                        "relation": "improves",
                        "weight": 1,
                        "evidence": "Chunking improves extraction accuracy.",
                    }
                ]
            }
        )

    async def embed(self, texts: list[str]):
        vectors = []
        for value in texts:
            base = float((sum(ord(ch) for ch in value) % 1000) / 1000.0)
            vectors.append([base, base / 2.0, 1.0 - base])
        return vectors


def main() -> None:
    fake_provider = FakeProvider()
    pipeline_module.get_provider = lambda *args, **kwargs: fake_provider
    search_module.get_provider = lambda *args, **kwargs: fake_provider

    client = TestClient(app)

    email = f"smoke-{uuid4().hex[:8]}@example.com"
    password = "SmokeTest123!"
    register_response = client.post(
        "/auth/register",
        json={"name": "Smoke Tester", "email": email, "password": password},
    )
    register_response.raise_for_status()
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    ingest_response = client.post(
        "/ingest",
        json={
            "source_path": "smoke_test.txt",
            "content": "Chunking improves extraction accuracy because smaller segments help isolate concepts.",
            "session_id": "smoke-test",
            "project_id": "pcg",
        },
        headers=headers,
    )
    ingest_response.raise_for_status()

    recall_response = client.get("/recall", params={"q": "How does chunking help?"}, headers=headers)
    recall_response.raise_for_status()

    graph_response = client.get("/graph", headers=headers)
    graph_response.raise_for_status()

    print("register:", register_response.status_code)
    print("ingest:", ingest_response.status_code, ingest_response.json())
    print("recall nodes:", len(recall_response.json()["nodes"]))
    print("graph nodes:", len(graph_response.json()["nodes"]))
    print("graph edges:", len(graph_response.json()["edges"]))


if __name__ == "__main__":
    main()
