"""
Test script for Species Tree Service endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8003"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print("✅ Health endpoint working!")
        else:
            print("❌ Health endpoint failed")
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")

def test_taxonomy_extraction():
    """Test taxonomy extraction endpoint"""
    print("\n🔍 Testing taxonomy extraction endpoint...")
    try:
        scientific_name = "Homo sapiens"
        response = requests.get(f"{BASE_URL}/api/v1/taxonomy/{scientific_name}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Scientific Name: {data['scientific_name']}")
            print(f"Total Relationships: {data['total_relationships']}")
            print(f"First 3 tuples:")
            for i, tuple_item in enumerate(data['tuples'][:3]):
                print(f"  {i+1}. Parent: {tuple_item['parent_taxon']} -> Child: {tuple_item['child_taxon']}")
            print("✅ Taxonomy extraction working!")
            return True
        else:
            print(f"❌ Taxonomy extraction failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing taxonomy extraction: {e}")
        return False

def test_taxonomy_expansion():
    """Test taxonomy expansion endpoint"""
    print("\n🔍 Testing taxonomy expansion endpoint...")
    try:
        taxon_name = "Mammalia"
        rank = "class"
        response = requests.get(f"{BASE_URL}/api/v1/expand/{taxon_name}/{rank}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Parent Taxon: {data['parent_taxon']}")
            print(f"Parent Rank: {data['parent_rank']}")
            print(f"Child Rank: {data['child_rank']}")
            print(f"Total Children: {data['total_children']}")
            if data['tuples']:
                print(f"First 3 tuples:")
                for i, tuple_item in enumerate(data['tuples'][:3]):
                    print(f"  {i+1}. Parent: {tuple_item['parent_taxon']} -> Child: {tuple_item['child_taxon']}")
            print("✅ Taxonomy expansion working!")
            return True
        else:
            print(f"❌ Taxonomy expansion failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing taxonomy expansion: {e}")
        return False

def test_helper_endpoints():
    """Test helper endpoints"""
    print("\n🔍 Testing helper endpoints...")
    
    # Test domains
    try:
        response = requests.get(f"{BASE_URL}/api/v1/expand/domains")
        if response.status_code == 200:
            domains = response.json()
            print(f"Domains: {domains}")
            print("✅ Domains endpoint working!")
        else:
            print("❌ Domains endpoint failed")
    except Exception as e:
        print(f"❌ Error testing domains: {e}")
    
    # Test kingdoms
    try:
        response = requests.get(f"{BASE_URL}/api/v1/expand/kingdoms?domain=Eukarya")
        if response.status_code == 200:
            kingdoms = response.json()
            print(f"Kingdoms for Eukarya: {kingdoms}")
            print("✅ Kingdoms endpoint working!")
        else:
            print("❌ Kingdoms endpoint failed")
    except Exception as e:
        print(f"❌ Error testing kingdoms: {e}")
    
    # Test taxonomic ranks
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ranks")
        if response.status_code == 200:
            ranks = response.json()
            print(f"Total taxonomic ranks: {len(ranks)}")
            print(f"First 5 ranks: {ranks[:5]}")
            print("✅ Ranks endpoint working!")
        else:
            print("❌ Ranks endpoint failed")
    except Exception as e:
        print(f"❌ Error testing ranks: {e}")

if __name__ == "__main__":
    print("🧪 Testing Species Tree Service Endpoints")
    print("=" * 50)
    
    # Test all endpoints
    test_health()
    test_taxonomy_extraction()
    test_taxonomy_expansion() 
    test_helper_endpoints()
    
    print("\n🎉 Testing complete!")