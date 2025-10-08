#!/usr/bin/env python3
"""
Test script to validate the updated TaxonomicEntity structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.taxonomy_extractor import TaxonomyExtractor
from app.models.taxonomy import TaxonomicEntity, TaxonomicTuple
import json

def test_new_structure():
    """Test the new TaxonomicEntity structure"""
    print("Testing updated TaxonomicEntity structure...")
    
    # Test creating TaxonomicEntity objects
    try:
        parent_entity = TaxonomicEntity(rank="Kingdom", name="Animalia")
        child_entity = TaxonomicEntity(rank="Phylum", name="Chordata")
        print(f"✅ TaxonomicEntity creation successful")
        print(f"   Parent: {parent_entity.rank} - {parent_entity.name}")
        print(f"   Child: {child_entity.rank} - {child_entity.name}")
    except Exception as e:
        print(f"❌ TaxonomicEntity creation failed: {e}")
        return False
    
    # Test creating TaxonomicTuple with new structure
    try:
        tuple_obj = TaxonomicTuple(
            parent_taxon=parent_entity,
            has_child=True,
            child_taxon=child_entity
        )
        print(f"✅ TaxonomicTuple creation successful")
        print(f"   Tuple: {tuple_obj.parent_taxon.name} -> {tuple_obj.child_taxon.name}")
    except Exception as e:
        print(f"❌ TaxonomicTuple creation failed: {e}")
        return False
    
    # Test extraction with new structure
    try:
        extractor = TaxonomyExtractor()
        result = extractor.extract_as_tuples("Homo sapiens")
        if result:
            print(f"✅ Extraction successful! Found {result.total_relationships} relationships")
            
            # Show first few relationships with new structure
            print("Sample relationships:")
            for i, rel in enumerate(result.tuples[:3]):
                print(f"  {i+1}. {rel.parent_taxon.rank}:{rel.parent_taxon.name} -> {rel.child_taxon.rank}:{rel.child_taxon.name}")
            
            # Test JSON serialization
            try:
                result_dict = result.model_dump()
                print("✅ JSON serialization successful")
                print(f"   Structure: {list(result_dict.keys())}")
                return True
            except Exception as e:
                print(f"❌ JSON serialization failed: {e}")
                return False
        else:
            print("❌ No results returned from extraction")
            return False
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

if __name__ == "__main__":
    success = test_new_structure()
    if success:
        print("\n🎉 All tests passed! The new TaxonomicEntity structure is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")