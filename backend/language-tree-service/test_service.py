#!/usr/bin/env python3
from app.services.wikipedia_service import LanguageFamilyTreeExtractor

def test_service():
    extractor = LanguageFamilyTreeExtractor()
    print('Testing English...')
    relationships = extractor.get_direct_relationships('English')
    print(f'Found {len(relationships)} relationships for English:')
    for rel in relationships[:10]:  # Show first 10
        print(f'  {rel[0]} -> {rel[1]} -> {rel[2]}')
    print('Test completed successfully!')

if __name__ == "__main__":
    test_service()
