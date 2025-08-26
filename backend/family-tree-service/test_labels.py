#!/usr/bin/env python3

import requests
from typing import Dict, Set

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

def get_labels(qids: Set[str]) -> Dict[str, str]:
    """Batch-fetch English labels for a set of Q-ids (returns dict)."""
    if not qids:
        return {}

    params = {
        "action": "wbgetentities",
        "ids": "|".join(qids),  # pipe-separated list (not comma)
        "props": "labels",
        "languages": "en",
        "format": "json",
    }

    headers = {
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    print(f"Testing get_labels with QIDs: {qids}")
    print(f"Request URL: {WIKIDATA_API}")
    print(f"Request params: {params}")

    response = requests.get(WIKIDATA_API, params=params, headers=headers)
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Failed to fetch labels: {response.status_code}")
        print(f"Response text: {response.text}")
        raise RuntimeError(f"Failed to fetch labels: {response.status_code}")

    data = response.json()
    print(f"Response data: {data}")
    
    # Check for errors in response
    if "error" in data:
        print(f"Wikidata API error: {data['error']}")
        return {}
        
    entities = data.get("entities", {})

    # Build dict of qid -> label
    labels = {}
    for qid, entity in entities.items():
        print(f"Processing entity {qid}: {entity}")
        
        # Check if entity exists (not missing)
        if entity.get("missing"):
            print(f"Entity {qid} is missing from Wikidata")
            continue
            
        label_info = entity.get("labels", {}).get("en")
        print(f"Label info for {qid}: {label_info}")
        if label_info and "value" in label_info:
            labels[qid] = label_info["value"]
            print(f"Found label for {qid}: {label_info['value']}")
        else:
            print(f"No English label found for {qid}")

    print(f"Final labels dict: {labels}")
    return labels

if __name__ == "__main__":
    # Test with the QIDs from your log
    test_qids = {"Q468357", "Q76346", "Q937", "Q118253"}
    labels = get_labels(test_qids)
    print(f"Results: {labels}")
