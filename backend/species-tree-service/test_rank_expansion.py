#!/usr/bin/env python3
"""
Test script to validate the rank-specific expansion endpoint
"""

import requests
import json

def test_rank_specific_expansion():
    """Test the /expand/{taxon_name}/{rank} endpoint"""
    
    base_url = "http://127.0.0.1:8002/api/v1"
    
    # Test cases: [taxon_name, rank]
    test_cases = [
        ("Eukaryota", "domain"),
        ("Animalia", "kingdom"), 
        ("Chordata", "phylum"),
        ("Mammalia", "class"),
        ("Primates", "order")
    ]
    
    print("🧪 Testing rank-specific expansion endpoint...")
    print("=" * 60)
    
    for taxon_name, rank in test_cases:
        print(f"\n📊 Testing: {taxon_name} ({rank})")
        
        try:
            # Test the rank-specific endpoint
            url = f"{base_url}/expand/{taxon_name}/{rank}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Found {data.get('total_children', 0)} children")
                
                # Show some example children
                if data.get('tuples'):
                    print(f"   Sample children:")
                    for i, tuple_data in enumerate(data['tuples'][:3]):
                        parent = tuple_data['parent_taxon']
                        child = tuple_data['child_taxon'] 
                        print(f"     {i+1}. {parent['name']} ({parent['rank']}) → {child['name']} ({child['rank']})")
                        
                    if len(data['tuples']) > 3:
                        print(f"     ... and {len(data['tuples']) - 3} more")
                        
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Frontend should now use: /expand/{taxon_name}/{rank}")
    print("   Example: /expand/Eukaryota/domain")
    print("   Instead of: /expand/Eukaryota")

if __name__ == "__main__":
    test_rank_specific_expansion()