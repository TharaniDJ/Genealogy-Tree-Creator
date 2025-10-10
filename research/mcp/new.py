import requests
import json
import os
import sys

# Load Gemini API key from environment for safety
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# MCP server endpoint (local by default)
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:5005/mcp')

def query_mcp(query, timeout=3):
    """Send a request to the MCP server. If the server is unreachable, return a small mock response.

    Returns a dict similar to the expected MCP response shape.
    """
    payload = {
        "version": "1.0",
        "tool": "wikipedia",
        "inputs": [{"text": query}]
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(MCP_SERVER_URL, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: could not reach MCP server at {MCP_SERVER_URL}: {e}", file=sys.stderr)
        # Fallback mock response (minimal, for offline testing)
        mock_text = (
            "Opisthokonta is a eukaryotic clade that includes animals, fungi, and several closely related groups."
            " Direct children include: Metazoa (animals), Fungi, and several protist lineages like Choanoflagellata and Ichthyosporea."
        )
        return {"outputs": [{"text": mock_text}]}


def query_gemini(prompt, timeout=10):
    """Query Gemini-like API. If no API key is present, return a simple extraction based on the prompt (mock)."""
    if not GEMINI_API_KEY:
        print("No GEMINI_API_KEY set in environment — using local mock response.", file=sys.stderr)
        # Very small heuristic: look for keywords in the prompt and return a short answer
        if 'Opisthokonta' in prompt:
            return {"text": "Metazoa (animals), Fungi, Choanoflagellata, Ichthyosporea"}
        return {"text": "No information available (mock)."}

    url = "https://api.genai.google.com/v1/models/gemini-2.5-flash:generateContent"
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"contents": prompt}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        response.raise_for_status()
        # The real Gemini response may have a different shape; try to be defensive
        j = response.json()
        if isinstance(j, dict):
            # prefer 'text' if present
            if 'text' in j:
                return {"text": j['text']}
            # fallback: try nested content
            if 'outputs' in j and isinstance(j['outputs'], list) and j['outputs']:
                return {"text": j['outputs'][0].get('text', '')}
        return {"text": json.dumps(j)}
    except requests.exceptions.RequestException as e:
        print(f"Error contacting Gemini API: {e}", file=sys.stderr)
        return {"text": "Error contacting Gemini API (see stderr)."}


def get_opisthokonta_children():
    # Query MCP server for information about Opisthokonta
    mcp_response = query_mcp("Opisthokonta")
    mcp_data = ""
    try:
        mcp_data = mcp_response.get("outputs", [{}])[0].get("text", "")
    except Exception:
        mcp_data = str(mcp_response)

    prompt = f"Based on the following information, list the direct children of Opisthokonta:\n\n{mcp_data}"
    gemini_response = query_gemini(prompt)
    # Defensive extraction
    if isinstance(gemini_response, dict):
        return gemini_response.get('text', str(gemini_response))
    return str(gemini_response)


if __name__ == "__main__":
    result = get_opisthokonta_children()
    print(result)
