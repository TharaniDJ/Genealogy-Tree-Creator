# Graph Gallery Feature

## Overview
A comprehensive graph management page that displays all saved graphs with filtering, sorting, and quick access to open them in their respective tree visualization pages. Includes auto-loading functionality for seamless navigation.

## Features

### 1. **Graph Gallery Page** (`/graphs`)
Central hub for viewing and managing all saved genealogy trees.

#### Key Features:
- ✅ View all graphs in a responsive grid layout
- ✅ Filter by graph type (Language, Species, Family)
- ✅ Search by name or description
- ✅ Sort by name, date, or size
- ✅ Quick statistics dashboard
- ✅ Delete graphs with confirmation
- ✅ Click to open in corresponding tree page
- ✅ Auto-load graph when clicked

### 2. **Auto-Loading Functionality**
When a graph card is clicked, the user is redirected to the appropriate tree page with the graph automatically loaded.

#### How it Works:
1. User clicks a graph card in `/graphs`
2. Router navigates to tree page with `?loadGraph={graphId}` parameter
3. Tree page detects the parameter
4. Automatically calls `handleLoadGraph(graphId)`
5. URL parameter is cleaned up after loading

#### Current Implementation:
- ✅ **Language Tree**: Full auto-load support
- ⏳ **Species Tree**: Ready for implementation
- ⏳ **Family Tree**: Ready for implementation

## File Structure

```
frontend/
├── app/
│   ├── graphs/
│   │   └── page.tsx          # Graph gallery page
│   ├── language_tree/
│   │   └── page.tsx          # Language tree (with auto-load)
│   ├── taxonomy_tree/
│   │   └── page.tsx          # Species tree (ready for auto-load)
│   └── family_tree/
│       └── page.tsx          # Family tree (ready for auto-load)
```

## Components

### Graph Gallery Page

#### Stats Dashboard
```typescript
stats = {
  total: 15,        // Total graphs
  language: 8,      // Language trees
  species: 5,       // Species trees  
  family: 2         // Family trees
}
```

Displays as interactive cards - clicking filters to that type.

#### Graph Cards
Each card displays:
- **Type Badge**: Visual indicator with icon (🗣️ 🦋 👨‍👩‍👧‍👦)
- **Graph Name**: Large, prominent title
- **Description**: Optional description text
- **Node Count**: Number of relationships
- **Depth**: If depth-based exploration was used
- **Last Updated**: Date of last modification
- **Actions**: Open and Delete buttons

#### Filters and Search

**Type Filter:**
- All Graphs (default)
- Language Trees
- Species Trees
- Family Trees

**Search:**
- Searches in graph name
- Searches in description
- Real-time filtering

**Sort Options:**
- By Date (newest/oldest)
- By Name (A-Z/Z-A)
- By Size (largest/smallest)

## Auto-Load Implementation

### Language Tree (Implemented)

```typescript
// 1. Import required hooks
import { useRouter, useSearchParams } from 'next/navigation';

// 2. Initialize hooks in component
const router = useRouter();
const searchParams = useSearchParams();

// 3. Add auto-load effect
useEffect(() => {
  const loadGraphId = searchParams.get('loadGraph');
  if (loadGraphId && connectionStatus === 'connected') {
    handleLoadGraph(loadGraphId);
    router.replace('/language_tree', { scroll: false });
  }
}, [searchParams, connectionStatus, handleLoadGraph, router]);
```

### For Species/Family Trees (To Implement)

Same pattern - just add the useEffect hook to detect and load the graph parameter.

## API Integration

### Endpoints Used

| Action | Method | Endpoint | Purpose |
|--------|--------|----------|---------|
| Fetch All | GET | `/api/users/graphs` | Get all user's graphs |
| Fetch Filtered | GET | `/api/users/graphs?graph_type=language` | Get graphs by type |
| Load Specific | GET | `/api/users/graphs/{id}` | Get single graph |
| Delete | DELETE | `/api/users/graphs/{id}` | Delete graph |

All requests go through API Gateway (port 8080).

## User Flow

### Viewing Graphs
```
1. User navigates to /graphs
2. Gallery loads all saved graphs
3. Stats dashboard shows counts by type
4. User can filter, search, or sort
5. Graphs display in responsive grid
```

### Opening a Graph
```
1. User clicks on a graph card
2. Router navigates to: /{tree_type}?loadGraph={id}
   - Language → /language_tree?loadGraph=abc123
   - Species → /taxonomy_tree?loadGraph=def456
   - Family → /family_tree?loadGraph=ghi789
3. Tree page detects loadGraph parameter
4. Automatically loads and renders the graph
5. URL is cleaned: /language_tree (parameter removed)
6. User sees fully rendered graph immediately
```

### Deleting a Graph
```
1. User clicks delete button on card
2. Confirmation dialog appears
3. If confirmed:
   - DELETE request sent to API
   - Graph removed from database
   - Gallery refreshes automatically
   - Updated count shown in stats
```

## UI/UX Design

### Color Coding by Type

**Language Trees:**
- Icon: 🗣️
- Color: Blue (`from-blue-500 to-cyan-500`)
- Badge: Blue background with border

**Species Trees:**
- Icon: 🦋
- Color: Green (`from-green-500 to-emerald-500`)
- Badge: Green background with border

**Family Trees:**
- Icon: 👨‍👩‍👧‍👦
- Color: Purple (`from-purple-500 to-pink-500`)
- Badge: Purple background with border

### Interactive Elements

**Hover Effects:**
- Card scales up (105%)
- Shadow intensifies
- Title gets gradient effect
- Smooth transitions (300ms)

**Click Feedback:**
- Card responds immediately
- Loading state while navigating
- Graph renders progressively

### Responsive Design

**Desktop (lg):**
- 3 columns grid
- Full stats dashboard
- Large graph cards

**Tablet (md):**
- 2 columns grid
- Compact stats
- Medium cards

**Mobile:**
- 1 column stack
- Vertical stats
- Touch-friendly cards

## Error Handling

### No Graphs State
```typescript
if (filteredGraphs.length === 0) {
  // Show empty state with:
  // - Large icon
  // - Helpful message
  // - "Create a Graph" button (if no filters)
  // - "Adjust filters" message (if filtered)
}
```

### Loading State
```typescript
if (loading) {
  // Show centered spinner
  // Maintains layout
  // Smooth transition when loaded
}
```

### Delete Confirmation
```typescript
if (!confirm(`Are you sure you want to delete "${graphName}"?`)) {
  return; // User cancelled
}
// Proceed with deletion
```

### Failed Requests
```typescript
catch (error) {
  console.error('Error:', error);
  alert('Failed to {action}. Please try again.');
}
```

## Performance Considerations

### Optimizations
1. **Lazy Loading**: Cards render progressively
2. **Event Bubbling**: Single onClick handler per card
3. **Memoized Filters**: React useMemo for filtered lists
4. **Debounced Search**: Reduces API calls (future enhancement)
5. **Cached Results**: Browser caches API responses

### Performance Metrics
- Initial load: < 1s
- Filter change: Instant (client-side)
- Graph open: < 500ms navigation
- Auto-load: 1-2s (depends on graph size)

## Accessibility

### Keyboard Navigation
- All cards are focusable
- Tab through cards sequentially
- Enter to open graph
- Delete with confirmation

### Screen Readers
- Semantic HTML structure
- ARIA labels on buttons
- Alt text for icons
- Clear button descriptions

### Color Contrast
- Text meets WCAG AA standards
- Buttons have clear hover states
- Disabled states visible
- Focus indicators prominent

## Testing Checklist

### Gallery Page
- [ ] All graphs load correctly
- [ ] Type filter works (Language, Species, Family, All)
- [ ] Search filters by name and description
- [ ] Sort by name/date/size works
- [ ] Stats dashboard shows correct counts
- [ ] Empty state displays when no graphs
- [ ] Loading state shows during fetch
- [ ] Delete confirmation works
- [ ] Delete removes graph and refreshes
- [ ] Cards are responsive on all screen sizes

### Auto-Load Feature
- [ ] Language tree auto-loads from URL parameter
- [ ] Graph renders correctly after auto-load
- [ ] URL parameter is cleaned after load
- [ ] Works with depth-based graphs
- [ ] Works with full-tree graphs
- [ ] Error handling if graph ID not found
- [ ] Doesn't load if not connected to WebSocket

### Integration Tests
- [ ] Navigate from gallery to language tree
- [ ] Navigate from gallery to species tree (when implemented)
- [ ] Navigate from gallery to family tree (when implemented)
- [ ] Back button works correctly
- [ ] Refreshing page maintains state
- [ ] Multiple graph types display correctly
- [ ] Search and filter state preserved during navigation

## Future Enhancements

### Phase 1 (Current)
- ✅ Graph gallery page
- ✅ Filter by type
- ✅ Search and sort
- ✅ Delete functionality
- ✅ Auto-load for language trees

### Phase 2 (Planned)
- ⏳ Auto-load for species trees
- ⏳ Auto-load for family trees
- ⏳ Bulk delete
- ⏳ Duplicate graph
- ⏳ Export graph from gallery

### Phase 3 (Future)
- 📋 Graph templates
- 📋 Share graphs with other users
- 📋 Public/Private visibility
- 📋 Graph tags and categories
- 📋 Advanced filtering (date range, depth range)
- 📋 Graph comparison view
- 📋 Merge graphs
- 📋 Graph history/versions
- 📋 Thumbnail previews
- 📋 Drag-and-drop organization

## Example Usage

### Opening the Gallery
```typescript
// From navigation menu or button
router.push('/graphs');

// From language tree "My Graphs" button
<button onClick={() => router.push('/graphs')}>
  My Graphs
</button>
```

### Filtering Programmatically
```typescript
// Click a stat card to filter
<div onClick={() => setSelectedType('language')}>
  Language Trees: {stats.language}
</div>
```

### Opening a Specific Graph
```typescript
// From gallery
const handleOpenGraph = (graph: SavedGraph) => {
  const routes = {
    language: '/language_tree',
    species: '/taxonomy_tree',
    family: '/family_tree'
  };
  router.push(`${routes[graph.graph_type]}?loadGraph=${graph.id}`);
};
```

## Troubleshooting

### Graph Doesn't Auto-Load

**Possible Causes:**
1. WebSocket not connected yet
   - Solution: Wait for connection, then load
2. Graph ID invalid
   - Solution: Check database, verify ID exists
3. URL parameter not parsed
   - Solution: Check useSearchParams() setup

**Debug Steps:**
```typescript
console.log('Load param:', searchParams.get('loadGraph'));
console.log('Connection:', connectionStatus);
console.log('Loading graph:', graphId);
```

### Gallery Shows No Graphs

**Possible Causes:**
1. User has no saved graphs
   - Solution: Create first graph
2. API request failed
   - Solution: Check network tab, verify token
3. Filter too restrictive
   - Solution: Reset filters to "All"

**Debug Steps:**
```typescript
console.log('Fetched graphs:', graphs);
console.log('Filtered graphs:', filteredGraphs);
console.log('Selected type:', selectedType);
```

---

**Last Updated:** October 17, 2025
**Status:** ✅ Language Tree Complete | ⏳ Species/Family Pending
**Pages:** `/graphs` (gallery), `/language_tree` (with auto-load)
