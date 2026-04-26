from __future__ import annotations

import json
import time

import openai

from pcg.config.settings import settings
from pcg.providers.base import LLMProvider
from pcg.providers.prompts import build_entity_extraction_prompt, build_relationship_extraction_prompt
from pcg.utils.schemas import EntityExtractionResult, RelationshipExtractionResult


class LocalProvider(LLMProvider):
    name = "local"

    def __init__(self) -> None:
        self.client = openai.AsyncOpenAI(base_url=settings.local_llm_url, api_key="ollama")
        self.embedding_model = settings.local_embedding_model

    def _get_models(self) -> list[str]:
        models = [m.strip() for m in settings.local_llm_model.split(",") if m.strip()]
        if settings.local_llm_fallback_model and settings.local_llm_fallback_model not in models:
            models.append(settings.local_llm_fallback_model)
        return models

    async def extract_entities(self, text: str) -> EntityExtractionResult:
        try:
            prompt = build_entity_extraction_prompt(text)
            valid_types = {"concept", "process", "mechanism", "decision", "unknown"}
            
            for model in self._get_models():
                try:
                    start_time = time.time()
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                    )
                    elapsed = time.time() - start_time
                    content = response.choices[0].message.content or "{}"
                    print(f"  [LOCAL] Model {model} succeeded in {elapsed:.2f}s")
                    data = json.loads(content)
                    entities_raw = data.get("entities", []) or data.get("nodes", [])
                    
                    normalized = []
                    for entity in entities_raw:
                        if not isinstance(entity, dict): continue
                        entity_type = str(entity.get("type", "unknown"))
                        if entity_type not in valid_types: entity_type = "unknown"
                        name = str(entity.get("name", entity.get("id", "unnamed"))).strip()
                        if not name: continue
                        normalized.append({
                            "temp_id": str(entity.get("temp_id", entity.get("id", name))),
                            "name": name,
                            "type": entity_type,
                            "aliases": list(entity.get("aliases", [])) if isinstance(entity.get("aliases", []), list) else [],
                            "description": str(entity.get("description", "")),
                            "metadata": entity.get("metadata", {}) if isinstance(entity.get("metadata", {}), dict) else {},
                        })
                    return EntityExtractionResult.model_validate({"entities": normalized})
                except Exception as e:
                    print(f"  [LOCAL] Model {model} failed: {e}")
                    continue
            return EntityExtractionResult(entities=[])
        except Exception:
            return EntityExtractionResult(entities=[])

    async def extract_relationships(self, text: str, entities: list[str]) -> RelationshipExtractionResult:
        try:
            prompt = build_relationship_extraction_prompt(text, entities)
            
            for model in self._get_models():
                try:
                    start_time = time.time()
                    response = await self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                    )
                    elapsed = time.time() - start_time
                    content = response.choices[0].message.content or "{}"
                    print(f"  [LOCAL] Model {model} succeeded in {elapsed:.2f}s")
                    data = json.loads(content)
                    relationships = []
                    for relationship in data.get("relationships", []):
                        if not isinstance(relationship, dict): continue
                        relationships.append({
                            "source_name": str(relationship.get("source_name", "")).strip(),
                            "target_name": str(relationship.get("target_name", "")).strip(),
                            "relation": str(relationship.get("relation", "related")).strip(),
                            "weight": float(relationship.get("weight", 1.0) or 1.0),
                            "evidence": str(relationship.get("evidence", "")).strip() or None,
                        })
                    return RelationshipExtractionResult.model_validate({"relationships": relationships})
                except Exception as e:
                    print(f"  [LOCAL] Model {model} failed: {e}")
                    continue
            return RelationshipExtractionResult(relationships=[])
        except Exception:
            return RelationshipExtractionResult(relationships=[])

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = await self.client.embeddings.create(model=self.embedding_model, input=text)
            vectors.append(response.data[0].embedding)
        return vectors
