from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
import asyncio
import app.services.wikipedia_service as wiki
from app.core.shared import websocket_manager
import re
from urllib.parse import urlparse, unquote, quote

router = APIRouter()


def _extract_wikipedia_title_from_url(url: str) -> str | None:
    """Extract the page title from a Wikipedia URL (desktop or mobile)."""
    if not isinstance(url, str) or not url:
        return None
    try:
        u = urlparse(url.strip())
        host = (u.netloc or '').lower()
        if not host.endswith("wikipedia.org"):
            return None
        # Accept /wiki/Title or /w/index.php?title=Title
        path = u.path or ''
        if path.startswith('/wiki/'):
            title = path.split('/wiki/', 1)[1]
            return unquote(title.replace('_', ' ')) if title else None
        if path.endswith('/w/index.php'):
            # Try query param title
            qs = u.query or ''
            m = re.search(r'(?:^|&)title=([^&]+)', qs)
            if m:
                return unquote(m.group(1).replace('_', ' '))
        return None
    except Exception:
        return None


def _normalized(s: str) -> str:
    try:
        return wiki._strip_language_tokens(s or "").strip().lower()
    except Exception:
        return (s or "").strip().lower()


def _title_mismatch(input_name: str, resolved_title: str) -> bool:
    """Heuristic: if resolved title does not match input even after stripping tokens, ask user.

    Returns True when we should prompt the user for confirmation/choice.
    """
    a = _normalized(input_name)
    b = _normalized(resolved_title)
    if not a or not b:
        return False
    if a == b:
        return False
    # Allow simple containment (e.g., Fingallian vs Fingallian language)
    if a in b or b in a:
        return False
    return True

@router.websocket("/ws/relationships")
async def websocket_language_relationships(websocket: WebSocket):
    """
    WebSocket endpoint for real-time language relationship exploration.
    
    Send: "language_name,depth" (e.g., "English,2")
    Receive: Real-time updates with relationships and language details
    """
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, connection_id)
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            raw = data
            data = data.strip("\"")
            print(f"Received WebSocket request: {data}")
            
            try:
                # Try to parse JSON-based actions first
                parsed = None
                if raw.strip().startswith("{"):
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = None

                if isinstance(parsed, dict) and parsed.get("action"):
                    action = parsed.get("action")
                    # 1) Return title suggestions for a query
                    if action == "suggest_titles":
                        query = parsed.get("query")
                        context = parsed.get("context") or "search"
                        depth = parsed.get("depth")
                        existing_graph_value = parsed.get("existingGraph")
                        node_label = parsed.get("nodeLabel")
                        if not isinstance(query, str) or not query.strip():
                            raise ValueError("Missing or invalid 'query' for suggest_titles")
                        results = wiki.search_wikipedia_titles(query, limit=10)
                        payload = {
                            "type": "title_choices",
                            "data": {
                                "query": query,
                                "context": context,
                                "depth": depth,
                                "nodeLabel": node_label,
                                "results": results,
                                # Pass through existing graph if present (for expand path)
                                "existingGraph": existing_graph_value if context == "expand_node" else None,
                            },
                        }
                        await websocket_manager.send_json(payload, connection_id)
                        continue

                    # 2) Start from a chosen Wikipedia title (user-approved)
                    if action == "choose_title":
                        chosen_title = parsed.get("title")
                        context = parsed.get("context") or "search"
                        depth = parsed.get("depth")
                        existing_graph_value = parsed.get("existingGraph") or []
                        node_label = parsed.get("nodeLabel")
                        if not isinstance(chosen_title, str) or not chosen_title.strip():
                            raise ValueError("Missing or invalid 'title' for choose_title")

                        # For search context: fetch relationships at requested depth
                        if context == "search":
                            if not isinstance(depth, int):
                                try:
                                    depth_int = int(depth) if depth is not None else 2
                                except Exception:
                                    depth_int = 2
                            else:
                                depth_int = depth
                            await websocket_manager.send_status(
                                f"Using Wikipedia page '{chosen_title}'...", 0, connection_id
                            )

                            async def from_title_task():
                                try:
                                    relationships = await wiki.fetch_language_relationships(
                                        str(chosen_title), int(depth_int), websocket_manager, connection_id, use_exact_title=True
                                    )
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "complete",
                                            "data": {
                                                "language": chosen_title,
                                                "depth": depth,
                                                "total_relationships": len(relationships),
                                                "relationships": relationships
                                            }
                                        }, connection_id)
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error processing chosen title: {str(e)}", connection_id)

                            task = asyncio.create_task(from_title_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue

                        # Full tree context: fetch relationships without depth limit
                        if context == "fetch_full_tree":
                            await websocket_manager.send_status(
                                f"Using Wikipedia page '{chosen_title}' (full tree)...", 0, connection_id
                            )

                            async def from_title_full_task():
                                try:
                                    relationships = await wiki.fetch_language_relationships(
                                        str(chosen_title), None, websocket_manager, connection_id, use_exact_title=True
                                    )
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "complete",
                                            "data": {
                                                "language": chosen_title,
                                                "depth": None,
                                                "total_relationships": len(relationships),
                                                "relationships": relationships
                                            }
                                        }, connection_id)
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error processing chosen title (full tree): {str(e)}", connection_id)

                            task = asyncio.create_task(from_title_full_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue

                        # For expand_node context: call the expand flow with existing graph
                        if context == "expand_node":
                            label_to_expand = node_label or chosen_title
                            await websocket_manager.send_status(
                                f"Expanding node using '{chosen_title}'...", 0, connection_id
                            )

                            async def expand_from_title_task():
                                try:
                                    newly_added, merged_graph = await wiki.expand_node_in_graph(
                                        original_graph=existing_graph_value or [],
                                        node_to_expand=label_to_expand,
                                        websocket_manager=websocket_manager,
                                        connection_id=connection_id,
                                    )
                                    def to_rel_dict(t):
                                        return {"language1": t[0], "relationship": t[1], "language2": t[2]}
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json(
                                            {
                                                "type": "expand_complete",
                                                "data": {
                                                    "label": label_to_expand,
                                                    "added": [to_rel_dict(t) for t in newly_added],
                                                    "merged": [to_rel_dict(t) for t in merged_graph],
                                                },
                                            },
                                            connection_id,
                                        )
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error expanding from chosen title: {str(e)}", connection_id)

                            task = asyncio.create_task(expand_from_title_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue

                    # 3) Start directly from a Wikipedia URL
                    if action == "start_with_url":
                        url = parsed.get("url")
                        context = parsed.get("context") or "search"
                        depth = parsed.get("depth")
                        existing_graph_value = parsed.get("existingGraph") or []
                        node_label = parsed.get("nodeLabel")
                        if not isinstance(url, str) or not url.strip():
                            raise ValueError("Missing or invalid 'url' for start_with_url")
                        title_from_url = _extract_wikipedia_title_from_url(url)
                        if not title_from_url:
                            await websocket_manager.send_error("Unable to extract a Wikipedia title from the provided URL.", connection_id)
                            continue
                        if context == "search":
                            if not isinstance(depth, int):
                                try:
                                    depth_int = int(depth) if depth is not None else 2
                                except Exception:
                                    depth_int = 2
                            else:
                                depth_int = depth
                            async def url_search_task():
                                try:
                                    relationships = await wiki.fetch_language_relationships(
                                        str(title_from_url), int(depth_int), websocket_manager, connection_id, use_exact_title=True
                                    )
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "complete",
                                            "data": {
                                                "language": title_from_url,
                                                "depth": depth,
                                                "total_relationships": len(relationships),
                                                "relationships": relationships
                                            }
                                        }, connection_id)
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error processing URL: {str(e)}", connection_id)
                            task = asyncio.create_task(url_search_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue
                        if context == "expand_node":
                            label_to_expand = node_label or title_from_url
                            async def url_expand_task():
                                try:
                                    newly_added, merged_graph = await wiki.expand_node_in_graph(
                                        original_graph=existing_graph_value or [],
                                        node_to_expand=label_to_expand,
                                        websocket_manager=websocket_manager,
                                        connection_id=connection_id,
                                    )
                                    def to_rel_dict(t):
                                        return {"language1": t[0], "relationship": t[1], "language2": t[2]}
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json(
                                            {
                                                "type": "expand_complete",
                                                "data": {
                                                    "label": label_to_expand,
                                                    "added": [to_rel_dict(t) for t in newly_added],
                                                    "merged": [to_rel_dict(t) for t in merged_graph],
                                                },
                                            },
                                            connection_id,
                                        )
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error expanding from URL: {str(e)}", connection_id)
                            task = asyncio.create_task(url_expand_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue
                        if context == "fetch_full_tree":
                            async def url_full_task():
                                try:
                                    relationships = await wiki.fetch_language_relationships(
                                        str(title_from_url), None, websocket_manager, connection_id, use_exact_title=True
                                    )
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "complete",
                                            "data": {
                                                "language": title_from_url,
                                                "depth": None,
                                                "total_relationships": len(relationships),
                                                "relationships": relationships
                                            }
                                        }, connection_id)
                                except asyncio.CancelledError:
                                    raise
                                except Exception as e:
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_error(f"Error processing URL (full tree): {str(e)}", connection_id)
                            task = asyncio.create_task(url_full_task())
                            websocket_manager.set_active_task(connection_id, task)
                            await task
                            continue
                    if action == "expand_node":
                        # Expected payload: { action: 'expand_node', label: string, existingGraph: LanguageRelationship[]|Tuple[] }
                        label_value = parsed.get("label")
                        existing_graph_value = parsed.get("existingGraph")
                        if not isinstance(label_value, str) or not label_value.strip():
                            raise ValueError("Missing or invalid 'label' for expand_node")
                        label = label_value.strip()

                        # Pre-resolve page title; if unresolved send suggestions and stop here
                        resolved = wiki.get_wikipedia_language_page_title(label)
                        if not resolved:
                            results = wiki.search_wikipedia_titles(label, limit=10)
                            await websocket_manager.send_json(
                                {
                                    "type": "title_choices",
                                    "data": {
                                        "query": label,
                                        "context": "expand_node",
                                        "nodeLabel": label,
                                        "results": results,
                                        "existingGraph": existing_graph_value,
                                    },
                                },
                                connection_id,
                            )
                            continue
                        # If resolved title looks mismatched, prompt user with suggestions including the resolved one
                        if _title_mismatch(label, resolved):
                            choices = wiki.search_wikipedia_titles(label, limit=10) or []
                            # Prepend resolved suggestion if not present
                            if not any((c.get("title") or "") == resolved for c in choices):
                                choices = (
                                    [{
                                        "title": resolved,
                                        "snippet": "Resolved title",
                                        "url": f"https://en.wikipedia.org/wiki/{quote(resolved.replace(' ', '_'))}",
                                    }] + choices
                                )
                            await websocket_manager.send_json(
                                {
                                    "type": "title_choices",
                                    "data": {
                                        "query": label,
                                        "context": "expand_node",
                                        "nodeLabel": label,
                                        "results": choices,
                                        "existingGraph": existing_graph_value,
                                    },
                                },
                                connection_id,
                            )
                            continue

                        await websocket_manager.send_status(
                            f"Expanding node '{label}' using Wikipedia and LLM...",
                            0,
                            connection_id,
                        )

                        async def expand_node_task(node_label: str, existing_graph):
                            try:
                                newly_added, merged_graph = await wiki.expand_node_in_graph(
                                    original_graph=existing_graph or [],
                                    node_to_expand=node_label,
                                    websocket_manager=websocket_manager,
                                    connection_id=connection_id,
                                )

                                # Convert tuples to LanguageRelationship-like dicts for frontend
                                def to_rel_dict(t):
                                    return {
                                        "language1": t[0],
                                        "relationship": t[1],
                                        "language2": t[2],
                                    }

                                added_payload = [to_rel_dict(t) for t in newly_added]
                                merged_payload = [to_rel_dict(t) for t in merged_graph]

                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_json(
                                        {
                                            "type": "expand_complete",
                                            "data": {
                                                "label": node_label,
                                                "added": added_payload,
                                                "merged": merged_payload,
                                            },
                                        },
                                        connection_id,
                                    )
                            except asyncio.CancelledError:
                                print(f"Expand node task cancelled for connection {connection_id}")
                                raise
                            except Exception as e:
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_error(
                                        f"Error expanding node '{node_label}': {str(e)}",
                                        connection_id,
                                    )

                        task = asyncio.create_task(expand_node_task(label, existing_graph_value))
                        websocket_manager.set_active_task(connection_id, task)
                        await task
                        continue
                    if action == "expand_by_qid":
                        await websocket_manager.send_error(
                            "Expansion by QID is no longer supported.",
                            connection_id
                        )
                        continue
                        
                    elif action == "expand_by_label":
                        # Fallback: expand using a label by reusing depth-1 fetch
                        label_value = parsed.get("label")
                        if not isinstance(label_value, str) or not label_value.strip():
                            raise ValueError("Missing or invalid 'label' for expand_by_label")
                        label = label_value.strip()
                        # Pre-resolve before attempting
                        resolved = wiki.get_wikipedia_language_page_title(label)
                        if not resolved:
                            results = wiki.search_wikipedia_titles(label, limit=10)
                            await websocket_manager.send_json(
                                {
                                    "type": "title_choices",
                                    "data": {
                                        "query": label,
                                        "context": "expand_node",
                                        "nodeLabel": label,
                                        "results": results,
                                        "existingGraph": None,
                                    },
                                },
                                connection_id,
                            )
                            continue
                        if _title_mismatch(label, resolved):
                            choices = wiki.search_wikipedia_titles(label, limit=10) or []
                            if not any((c.get("title") or "") == resolved for c in choices):
                                choices = (
                                    [{
                                        "title": resolved,
                                        "snippet": "Resolved title",
                                        "url": f"https://en.wikipedia.org/wiki/{quote(resolved.replace(' ', '_'))}",
                                    }] + choices
                                )
                            await websocket_manager.send_json(
                                {
                                    "type": "title_choices",
                                    "data": {
                                        "query": label,
                                        "context": "expand_node",
                                        "nodeLabel": label,
                                        "results": choices,
                                        "existingGraph": None,
                                    },
                                },
                                connection_id,
                            )
                            continue
                        await websocket_manager.send_status(
                            f"Expanding node '{label}' (depth 1)...",
                            0,
                            connection_id
                        )
                        
                        # Create a task for the expansion operation
                        async def expand_by_label_task(label_name: str):
                            try:
                                relationships = await wiki.fetch_language_relationships(
                                    label_name,
                                    1,
                                    websocket_manager,
                                    connection_id
                                )
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_json({
                                        "type": "expand_complete",
                                        "data": {"label": label_name, "added": len(relationships)}
                                    }, connection_id)
                            except asyncio.CancelledError:
                                print(f"Expand by label task cancelled for connection {connection_id}")
                                raise
                            except Exception as e:
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_error(f"Error expanding node: {str(e)}", connection_id)
                        
                        # Start the task and register it
                        task = asyncio.create_task(expand_by_label_task(label))
                        websocket_manager.set_active_task(connection_id, task)
                        await task
                        continue

                    elif action == "fetch_full_tree":
                        language_value = parsed.get("language")
                        if not isinstance(language_value, str) or not language_value.strip():
                            raise ValueError("Missing or invalid 'language' for fetch_full_tree")
                        language_name = language_value.strip()

                        await websocket_manager.send_status(
                            f"Fetching full hierarchy for {language_name}...",
                            0,
                            connection_id
                        )

                        async def full_tree_task():
                            try:
                                # Pre-resolve exact title; on failure or mismatch, prompt for choices and stop
                                resolved = wiki.get_wikipedia_language_page_title(language_name)
                                if not resolved:
                                    results = wiki.search_wikipedia_titles(language_name, limit=10)
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "title_choices",
                                            "data": {
                                                "query": language_name,
                                                "context": "fetch_full_tree",
                                                "depth": None,
                                                "results": results,
                                            }
                                        }, connection_id)
                                    return
                                if _title_mismatch(language_name, resolved):
                                    choices = wiki.search_wikipedia_titles(language_name, limit=10) or []
                                    if not any((c.get("title") or "") == resolved for c in choices):
                                        choices = (
                                            [{
                                                "title": resolved,
                                                "snippet": "Resolved title",
                                                "url": f"https://en.wikipedia.org/wiki/{quote(resolved.replace(' ', '_'))}",
                                            }] + choices
                                        )
                                    if websocket_manager.is_connection_active(connection_id):
                                        await websocket_manager.send_json({
                                            "type": "title_choices",
                                            "data": {
                                                "query": language_name,
                                                "context": "fetch_full_tree",
                                                "depth": None,
                                                "results": choices,
                                            }
                                        }, connection_id)
                                    return
                                # Proceed with full tree since title resolved & matches
                                relationships = await wiki.fetch_language_relationships(
                                    language_name,
                                    None,
                                    websocket_manager,
                                    connection_id
                                )

                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_json({
                                        "type": "complete",
                                        "data": {
                                            "language": language_name,
                                            "depth": None,
                                            "total_relationships": len(relationships),
                                            "relationships": relationships
                                        }
                                    }, connection_id)
                            except asyncio.CancelledError:
                                print(f"Full-tree task cancelled for connection {connection_id}")
                                raise
                            except Exception as e:
                                if websocket_manager.is_connection_active(connection_id):
                                    await websocket_manager.send_error(f"Error processing full tree request: {str(e)}", connection_id)

                        task = asyncio.create_task(full_tree_task())
                        websocket_manager.set_active_task(connection_id, task)
                        await task
                        continue

                # Legacy format: "language_name,depth"
                # Parse the request
                if "," in data:
                    language_name, depth_str = data.split(",", 1)
                    depth = int(depth_str.strip())
                else:
                    raise ValueError("Invalid format. Expected 'language_name,depth' or a JSON action")
                
                if depth < 1 or depth > 5:
                    raise ValueError("Depth must be between 1 and 5")
                
                print(f"Processing request for {language_name} with depth {depth}")
                
                # Send initial status
                await websocket_manager.send_status(
                    f"Starting language tree exploration for {language_name}...", 
                    0, 
                    connection_id
                )
                
                # Create a task for the main exploration
                async def exploration_task():
                    try:
                        # Try to resolve exact title first; if not found, provide suggestions and stop
                        resolved = wiki.get_wikipedia_language_page_title(language_name)
                        if not resolved:
                            results = wiki.search_wikipedia_titles(language_name, limit=10)
                            if websocket_manager.is_connection_active(connection_id):
                                await websocket_manager.send_json({
                                    "type": "title_choices",
                                    "data": {
                                        "query": language_name,
                                        "context": "search",
                                        "depth": depth,
                                        "results": results,
                                    }
                                }, connection_id)
                            return
                        # If heuristic indicates mismatch, present suggestions (include resolved first)
                        if _title_mismatch(language_name, resolved):
                            choices = wiki.search_wikipedia_titles(language_name, limit=10) or []
                            if not any((c.get("title") or "") == resolved for c in choices):
                                choices = (
                                    [{
                                        "title": resolved,
                                        "snippet": "Resolved title",
                                        "url": f"https://en.wikipedia.org/wiki/{quote(resolved.replace(' ', '_'))}",
                                    }] + choices
                                )
                            if websocket_manager.is_connection_active(connection_id):
                                await websocket_manager.send_json({
                                    "type": "title_choices",
                                    "data": {
                                        "query": language_name,
                                        "context": "search",
                                        "depth": depth,
                                        "results": choices,
                                    }
                                }, connection_id)
                            return
                        # Fetch relationships with real-time updates
                        relationships = await wiki.fetch_language_relationships(
                            language_name, 
                            depth, 
                            websocket_manager,
                            connection_id
                        )
                        
                        # Send final result if connection is still active
                        if websocket_manager.is_connection_active(connection_id):
                            await websocket_manager.send_json({
                                "type": "complete",
                                "data": {
                                    "language": language_name,
                                    "depth": depth,
                                    "total_relationships": len(relationships),
                                    "relationships": relationships
                                }
                            }, connection_id)
                    except asyncio.CancelledError:
                        print(f"Exploration task cancelled for connection {connection_id}")
                        raise
                    except Exception as e:
                        if websocket_manager.is_connection_active(connection_id):
                            await websocket_manager.send_error(f"Error processing request: {str(e)}", connection_id)
                
                # Start the task and register it
                task = asyncio.create_task(exploration_task())
                websocket_manager.set_active_task(connection_id, task)
                await task
                
            except ValueError as e:
                await websocket_manager.send_error(f"Invalid request: {str(e)}", connection_id)
            except asyncio.CancelledError:
                print(f"WebSocket task cancelled for connection {connection_id}")
                break
            except Exception as e:
                print(f"Error processing WebSocket request: {e}")
                await websocket_manager.send_error(f"Error processing request: {str(e)}", connection_id)
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {connection_id}")
    finally:
        websocket_manager.disconnect(connection_id)

@router.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for service status updates"""
    connection_id = str(uuid.uuid4())
    await websocket_manager.connect(websocket, connection_id)
    
    try:
        # Send initial status
        await websocket_manager.send_json({
            "type": "status",
            "data": {
                "service": "language-tree-service",
                "status": "connected",
                "connection_id": connection_id,
                "active_connections": websocket_manager.get_connection_count()
            }
        }, connection_id)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()  # Wait for ping/keepalive
            
    except WebSocketDisconnect:
        print(f"Status WebSocket disconnected: {connection_id}")
    finally:
        websocket_manager.disconnect(connection_id)
