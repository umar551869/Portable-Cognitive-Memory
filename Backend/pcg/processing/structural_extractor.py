from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List
import graphify.extract as ge
from pcg.utils.logging import get_logger

logger = get_logger("processing.structural")

# Map file extensions to graphify LanguageConfig
EXTENSION_MAP = {
    ".py": ge._PYTHON_CONFIG,
    ".js": ge._JS_CONFIG,
    ".ts": ge._TS_CONFIG,
    ".tsx": ge._TS_CONFIG,
    ".java": ge._JAVA_CONFIG,
    ".c": ge._C_CONFIG,
    ".h": ge._C_CONFIG,
    ".cpp": ge._CPP_CONFIG,
    ".hpp": ge._CPP_CONFIG,
    ".rb": ge._RUBY_CONFIG,
    ".cs": ge._CSHARP_CONFIG,
    ".kt": ge._KOTLIN_CONFIG,
    ".scala": ge._SCALA_CONFIG,
    ".php": ge._PHP_CONFIG,
    ".lua": ge._LUA_CONFIG,
    ".swift": ge._SWIFT_CONFIG,
}

class StructuralExtractor:
    """Uses graphify's deterministic AST logic to extract code structure."""
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext not in EXTENSION_MAP:
            return {"nodes": [], "edges": []}
            
        config = EXTENSION_MAP[ext]
        try:
            # graphify._extract_generic is the internal function used by graphify to run the AST pass
            result = ge._extract_generic(path, config)
            if "error" in result:
                logger.warning("structural_extraction_failed path=%s error=%s", file_path, result["error"])
                return {"nodes": [], "edges": []}
            
            return result
        except Exception as e:
            logger.exception("structural_extraction_exception path=%s error=%s", file_path, e)
            return {"nodes": [], "edges": []}

    def convert_to_pcg_entities(self, structural_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts graphify nodes to PCG-compatible entity format."""
        entities = []
        for node in structural_result.get("nodes", []):
            if node.get("file_type") == "code":
                # Determine type from label or presence in edges
                label = node.get("label", "")
                entity_type = "concept" # Default
                if "()" in label:
                    entity_type = "process" # Function/Method
                
                entities.append({
                    "temp_id": node["id"],
                    "name": label.replace("()", ""),
                    "type": entity_type,
                    "description": f"Structural code element found in {node.get('source_file')} at {node.get('source_location')}",
                    "aliases": [],
                    "metadata": {
                        "source": "graphify_ast",
                        "location": node.get("source_location"),
                        "file": node.get("source_file")
                    }
                })
        return entities

    def convert_to_pcg_relationships(self, structural_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts graphify edges to PCG-compatible relationship format."""
        relationships = []
        node_id_to_name = {n["id"]: n["label"].replace("()", "") for n in structural_result.get("nodes", [])}
        
        for edge in structural_result.get("edges", []):
            src_name = node_id_to_name.get(edge["source"])
            tgt_name = node_id_to_name.get(edge["target"])
            
            if src_name and tgt_name:
                relationships.append({
                    "source_name": src_name,
                    "target_name": tgt_name,
                    "relation": edge["relation"],
                    "weight": 1.0,
                    "evidence": f"AST extraction: {edge['relation']} relationship detected by tree-sitter."
                })
        return relationships
