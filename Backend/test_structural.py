import asyncio
import json
from pcg.processing.structural_extractor import StructuralExtractor

def test_structural():
    extractor = StructuralExtractor()
    # Test on a known file
    result = extractor.extract("pcg/processing/pipeline.py")
    print(f"Nodes found: {len(result.get('nodes', []))}")
    print(f"Edges found: {len(result.get('edges', []))}")
    
    entities = extractor.convert_to_pcg_entities(result)
    print(f"Converted Entities: {len(entities)}")
    if entities:
        print(f"Example Entity: {json.dumps(entities[0], indent=2)}")

if __name__ == "__main__":
    test_structural()
