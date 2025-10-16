# Depth Handling Update - Full Tree Mode

## Overview
Fixed graph saving logic to correctly distinguish between depth-based exploration and full tree exploration. When using "Explore Full Tree", the saved graph now correctly sets `depth_usage: false` since there's no depth limit in full tree mode.

## Problem
Previously, when saving a graph generated from "Explore Full Tree", the system would incorrectly save `depth_usage: true` and include a depth value, even though full tree exploration doesn't use depth-based limiting.

## Solution

### 1. Added State Tracking
Added a new state variable to track which exploration mode was used:

```typescript
const [isFullTreeMode, setIsFullTreeMode] = useState(false);
```

### 2. Updated Search Functions

**Depth-Based Search (Search button):**
```typescript
const handleSearch = useCallback(() => {
  setIsFullTreeMode(false); // Depth-based search
  resetGraphState('Searching...');
  sendMessage(`${language},${depth}`);
}, [language, depth, resetGraphState, sendMessage]);
```

**Full Tree Search (Explore Full Tree button):**
```typescript
const handleSearchFull = useCallback(() => {
  setIsFullTreeMode(true); // Full tree mode (no depth limit)
  resetGraphState('Fetching full language tree...');
  sendMessage({ action: 'fetch_full_tree', language: rootLabel });
}, [language, resetGraphState, sendMessage]);
```

### 3. Updated Save Logic

The `handleSaveGraph` function now uses `isFullTreeMode` to determine depth usage:

```typescript
body: JSON.stringify({
  graph_name: graphName,
  graph_type: 'language',
  depth_usage: !isFullTreeMode && depth > 0,  // ✅ False for full tree mode
  depth: !isFullTreeMode && depth > 0 ? depth : undefined,  // ✅ Undefined for full tree
  graph_data: relationships,
  description: graphDescription || undefined
})
```

### 4. Updated UI Feedback

The save modal now displays different messages based on the mode:

```typescript
<p className="text-sm text-[#9CA3B5]">
  💾 This will save {buildRelationshipsPayload().length} language relationships
  {!isFullTreeMode && depth > 0 && ` (depth: ${depth})`}
  {isFullTreeMode && ' (full tree - no depth limit)'}
</p>
```

## Behavior Matrix

| Action | `isFullTreeMode` | `depth_usage` | `depth` | Description |
|--------|-----------------|---------------|---------|-------------|
| Click "Search" with depth=2 | `false` | `true` | `2` | Depth-based exploration |
| Click "Search" with depth=0 | `false` | `false` | `undefined` | No depth limit (legacy) |
| Click "Explore Full Tree" | `true` | `false` | `undefined` | Full tree exploration |

## Examples

### Example 1: Depth-Based Search
```json
{
  "graph_name": "English Language Family - Depth 3",
  "graph_type": "language",
  "depth_usage": true,
  "depth": 3,
  "graph_data": [...],
  "description": "Explored up to 3 levels from English"
}
```

### Example 2: Full Tree Exploration
```json
{
  "graph_name": "English Complete Language Tree",
  "graph_type": "language",
  "depth_usage": false,
  "depth": undefined,  // Not included in JSON
  "graph_data": [...],
  "description": "Complete language family tree without depth limit"
}
```

## Files Modified

1. ✅ `frontend/app/language_tree/page.tsx`
   - Added `isFullTreeMode` state variable
   - Updated `handleSearch()` to set mode to false
   - Updated `handleSearchFull()` to set mode to true
   - Updated `handleSaveGraph()` to use mode for depth_usage logic
   - Updated save modal UI to display mode-specific messages

## Testing

### Test Case 1: Depth-Based Search
1. Enter "English" in language field
2. Set depth to 2
3. Click "Search" button
4. Wait for graph to generate
5. Click "Save Graph"
6. Verify modal shows: `(depth: 2)`
7. Save the graph
8. Check database: `depth_usage: true, depth: 2`

### Test Case 2: Full Tree Search
1. Enter "English" in language field
2. Click "Explore Full Tree" button
3. Wait for graph to generate
4. Click "Save Graph"
5. Verify modal shows: `(full tree - no depth limit)`
6. Save the graph
7. Check database: `depth_usage: false, depth: null`

### Test Case 3: Mode Persistence
1. Click "Search" (depth mode)
2. Then click "Explore Full Tree" (full tree mode)
3. Save graph
4. Verify it saves with full tree mode settings

### Test Case 4: Loading Saved Graphs
1. Load a graph saved with depth_usage: true
2. The depth value should be restored
3. Load a graph saved with depth_usage: false
4. No depth value should be shown

## API Impact

### Backend Compatibility
The backend API already supports optional `depth_usage` and `depth` fields:

```python
class GraphBase(BaseModel):
    graph_name: str
    graph_type: str  # "language", "species", or "family"
    depth_usage: bool = False
    depth: Optional[int] = None
    description: Optional[str] = None
    graph_data: List[Dict]
```

No backend changes required! ✅

## Benefits

✅ **Accurate Metadata** - Saved graphs correctly reflect how they were generated
✅ **Better UX** - Users can see at a glance if a graph used depth limiting
✅ **Proper Filtering** - Can filter/sort saved graphs by exploration method
✅ **Data Integrity** - No misleading depth values for full tree explorations
✅ **Clear Intent** - Save modal clearly indicates the exploration mode

## Future Enhancements

1. **Filter in Load Modal** - Add filter to show only depth-based or full-tree graphs
2. **Mode Icon** - Display icon in saved graph list indicating exploration mode
3. **Statistics** - Show statistics like "X depth-based graphs, Y full-tree graphs"
4. **Mode Badge** - Add colored badge in load modal for visual distinction

---

**Last Updated:** October 17, 2025
**Status:** ✅ Complete and Ready for Testing
**Impact:** Frontend only (no backend changes required)
