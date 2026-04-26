from __future__ import annotations

import json
from typing import Sequence


DISALLOWED_RELATIONS = {
    "uses",
    "has",
    "contains",
    "includes",
    "stores",
    "connects_to",
    "integrates_with",
    "part_of",
    "belongs_to",
    "built_with",
    "implemented_in",
}

PREFERRED_RELATIONS = (
    "enables",
    "improves",
    "prevents",
    "converts",
    "depends_on",
    "produces",
    "leads_to",
    "requires",
    "optimizes",
    "ensures",
    "retrieves",
    "reduces",
    "increases",
    "validates",
    "organizes",
)


def build_entity_extraction_prompt(text: str) -> str:
    return f"""
You are extracting a HIGH-VALUE cognitive knowledge graph from technical text.
This is NOT a system diagram and NOT a tool dependency map.

Goal:
- capture concepts, mechanisms, processes, and decisions
- capture reasoning, cause-effect, constraints, and workflows
- ignore low-value architecture trivia

Hard rules:
- DO NOT center the graph on products, APIs, frameworks, or databases unless the text is directly reasoning about their unique behavior.
- DO NOT produce tool-centric entities like "Gemini", "Supabase", "FastAPI", "SQLite", or "Ollama" as primary nodes unless they represent the actual concept being analyzed.
- Prefer abstract concepts over vendor names.
- If the text says "chunking improves extraction accuracy", extract "chunking" and "extraction accuracy", not the library used.
- If the text says "embeddings are stored in a vector database", extract "embeddings" and "semantic retrieval", not just the product.

Good entities:
- deduplication
- semantic search
- chunking
- entity resolution
- graph expansion
- fallback handling
- retrieval ranking
- raw logs as source of truth

Bad entities:
- generic components
- service names without conceptual value
- low-level implementation labels that do not improve thinking

Return strict JSON with this schema:
{{
  "entities": [
    {{
      "temp_id": "string",
      "name": "string",
      "type": "concept|process|mechanism|decision|unknown",
      "aliases": ["string"],
      "description": "short explanation of why the concept matters",
      "metadata": {{}}
    }}
  ]
}}

Text:
{text}
""".strip()


def build_relationship_extraction_prompt(text: str, entities: Sequence[str]) -> str:
    entity_json = json.dumps(list(entities), ensure_ascii=True)
    preferred = ", ".join(PREFERRED_RELATIONS)
    forbidden = ", ".join(sorted(DISALLOWED_RELATIONS))
    return f"""
You are extracting HIGH-VALUE cognitive relationships between known concepts.
This is NOT a component wiring diagram.

Known entities:
{entity_json}

Rules:
- Use ONLY the known entities above.
- DO NOT invent new entities.
- DO NOT create generic architecture edges.
- REJECT low-value relations such as: {forbidden}
- Prefer meaningful relations such as: {preferred}
- Each relationship should express reasoning, transformation, dependency, optimization, validation, or cause-effect.
- Keep only relationships that improve recall quality for how the system works or why a design choice matters.
- Skip weak or obvious tool/dependency edges.

Return strict JSON with this schema:
{{
  "relationships": [
    {{
      "source_name": "one of the known entities",
      "target_name": "one of the known entities",
      "relation": "string",
      "weight": 1,
      "evidence": "short supporting excerpt or rationale"
    }}
  ]
}}

Text:
{text}
""".strip()
