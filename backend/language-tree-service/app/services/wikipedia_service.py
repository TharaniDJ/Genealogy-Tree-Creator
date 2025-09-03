"""Glottolog-based language relationship extraction service.

Replaces prior Wikipedia/Wikidata implementation.
Exposes a compatible async API expected by the rest of the backend but now:
 - Uses local Glottolog data (relative path resolution)
 - Streams relationships to the frontend in batches via WebSocket
 - Relationships are emitted as dictionaries: {"entity1", "relationship", "entity2"}
     where entity1 is the child (more specific) and entity2 its parent (ancestor/family).
"""

from __future__ import annotations

from typing import List, Dict, Optional, Set, Any
from pathlib import Path
import asyncio

from app.core.websocket_manager import WebSocketManager

try:
    from pyglottolog import Glottolog  # type: ignore
    from pyglottolog.languoids import Languoid  # type: ignore
except ImportError:  # Fallback: we will raise informative errors at call time
    Glottolog = None  # type: ignore
    Languoid = None  # type: ignore

# ---------------------------------------------------------------------------
# Glottolog Explorer (minimal subset adapted from standalone script)
# ---------------------------------------------------------------------------

class _GlottologExplorer:
    def __init__(self, glottolog_path: Path):
        if Glottolog is None:
            raise RuntimeError("pyglottolog is not installed. Add it to dependencies.")
        if not glottolog_path.exists():
            raise RuntimeError(f"Glottolog path not found: {glottolog_path}")
        self.glottolog = Glottolog(str(glottolog_path))
        # Use Any to keep runtime flexible if library types differ
        self._name_index: Dict[str, List[Any]] = {}
        self._id_index: Dict[str, Any] = {}
        self._build_cache()

    def _build_cache(self):
        for lg in self.glottolog.languoids():
            # Cache by id
            self._id_index[lg.id] = lg
            # Cache by lowercase name (may be multiple)
            key = lg.name.lower()
            self._name_index.setdefault(key, []).append(lg)

    def find(self, name_or_code: str) -> Optional[Any]:
        # Exact id
        if name_or_code in self._id_index:
            return self._id_index[name_or_code]
        key = name_or_code.lower()
        if key in self._name_index:
            candidates = self._name_index[key]
            # If multiple with same name, just return the first (could be improved)
            return candidates[0]
        # Simple contains fuzzy
        for nkey, vals in self._name_index.items():
            if key in nkey:
                return vals[0]
        return None

    def ancestors(self, lg: Any, max_depth: int) -> List[Any]:
        res: List[Any] = []
        cur = lg.parent
        depth = 0
        while cur and depth < max_depth:
            res.append(cur)
            cur = cur.parent
            depth += 1
        return res

    def descendants(self, lg: Any, max_depth: int) -> List[Any]:
        res: List[Any] = []
        if max_depth <= 0:
            return res
        # BFS
        frontier: List[tuple[Any, int]] = [(lg, 0)]
        while frontier:
            node, depth_level = frontier.pop(0)
            if depth_level == max_depth:
                continue
            for child in getattr(node, 'children', []) or []:
                res.append(child)
                frontier.append((child, depth_level + 1))
        return [d for d in res if getattr(d, 'id', None) != getattr(lg, 'id', None)]


# Singleton explorer (lazy init)
_explorer: Optional[_GlottologExplorer] = None


def _get_explorer() -> _GlottologExplorer:
    global _explorer
    if _explorer is not None:
        return _explorer
    # Resolve repo root: ../../../../ -> repo root then glottolog dir
    repo_root = Path(__file__).resolve().parents[4]
    glottolog_path = repo_root / "glottolog-5.2.1"
    _explorer = _GlottologExplorer(glottolog_path)
    return _explorer


# ---------------------------------------------------------------------------
# Public API (async) expected by the rest of the backend
# ---------------------------------------------------------------------------

async def fetch_language_relationships(language_name: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect language relationships using local Glottolog data.

    Returns list of edges (child -> parent) formatted as:
        {"entity1": child_name, "relationship": "member_of", "entity2": parent_name}

    The same edges are streamed in batches via the websocket (if provided) using
        {"type": "relationships_batch", "data": [edges...]}
    """
    try:
        explorer = _get_explorer()
    except Exception as e:
        if websocket_manager:
            await websocket_manager.send_status(f"Initialization error: {e}", 100)
        return []

    if websocket_manager:
        await websocket_manager.send_status("Resolving language...", 0)

    languoid = explorer.find(language_name)
    if not languoid:
        if websocket_manager:
            await websocket_manager.send_status(f"Language not found: {language_name}", 100)
        return []

    if websocket_manager:
        level_value = getattr(languoid.level, 'name', str(languoid.level))
        await websocket_manager.send_json({
            "type": "base_language",
            "data": {
                "name": languoid.name,
                "glottocode": languoid.id,
                "level": level_value
            }
        })

    # Collect ancestor edges (child -> parent chain up to depth)
    ancestors = explorer.ancestors(languoid, depth)
    edges: List[Dict[str, str]] = []
    visited_pairs: Set[tuple[str, str]] = set()

    prev = languoid
    for anc in ancestors:
        pair = (prev.id, anc.id)
        if pair not in visited_pairs:
            edges.append({
                "entity1": prev.name,
                "entity1_glottocode": prev.id,
                "relationship": "member_of",
                "entity2": anc.name,
                "entity2_glottocode": anc.id
            })
            visited_pairs.add(pair)
        prev = anc

    if websocket_manager:
        await websocket_manager.send_status("Ancestors collected, traversing descendants...", 40)

    # Collect descendant edges (each descendant -> its parent) within depth
    descendants = explorer.descendants(languoid, depth)
    for desc in descendants:
        parent = desc.parent
        if parent is None:
            continue
        pair = (desc.id, parent.id)
        if pair in visited_pairs:
            continue
        edges.append({
            "entity1": desc.name,
            "entity1_glottocode": desc.id,
            "relationship": "member_of",
            "entity2": parent.name,
            "entity2_glottocode": parent.id
        })
        visited_pairs.add(pair)

    # Optionally include siblings (same parent) only at depth 0 of start
    if languoid.parent:
        for sib in languoid.parent.children:
            if sib.id == languoid.id:
                continue
            pair = (sib.id, languoid.parent.id)
            if pair in visited_pairs:
                continue
            edges.append({
                "entity1": sib.name,
                "entity1_glottocode": sib.id,
                "relationship": "member_of",
                "entity2": languoid.parent.name,
                "entity2_glottocode": languoid.parent.id
            })
            visited_pairs.add(pair)

    # Stream in batches
    if websocket_manager:
        batch_size = 25
        total = len(edges)
        for i in range(0, total, batch_size):
            batch = edges[i:i + batch_size]
            await websocket_manager.send_json({
                "type": "relationships_batch",
                "data": batch
            })
            pct = 40 + int(55 * (i + len(batch)) / max(total, 1))  # progress 40..95
            await websocket_manager.send_status("Streaming relationships...", pct)
        await websocket_manager.send_status("Relationship collection complete", 100)

    return edges


async def check_language_validity(language_name: str) -> bool:
    """Return True if the language can be resolved in Glottolog."""
    try:
        explorer = _get_explorer()
    except Exception:
        return False
    return explorer.find(language_name) is not None


# Backwards compatibility: previously there were detail functions; callers should
# stop relying on them. We keep stubs returning None so imports won't break.
async def get_language_details(language_name: str) -> Optional[Dict]:  # pragma: no cover - legacy stub
    return None

async def get_language_details_by_qid(qid: str) -> Optional[Dict]:  # pragma: no cover - legacy stub
    return None
