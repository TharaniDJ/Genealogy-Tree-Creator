

// import React, { useState, useEffect, useCallback } from 'react';
// import ReactFlow, {
//   Node,
//   Edge,
//   addEdge,
//   Connection,
//   useNodesState,
//   useEdgesState,
//   Controls,
//   Background,
//   BackgroundVariant,
//   ReactFlowProvider,
// } from 'reactflow';
// import 'reactflow/dist/style.css';
// import PersonNode from './PersonNode';
// import MarriageNode from './MarriageNode';

// const nodeTypes = {
//   person: PersonNode,
//   marriage: MarriageNode,
// };

// interface WebSocketMessage {
//   type: 'status' | 'personal_details' | 'relationship';
//   data: any;
// }

// interface PersonDetails {
//   entity: string;
//   qid: string;
//   birth_year?: string;
//   death_year?: string;
//   image_url?: string;
// }

// interface Relationship {
//   entity1: string;
//   relationship: string;
//   entity2: string;
// }

// interface ContextMenu {
//   show: boolean;
//   x: number;
//   y: number;
//   nodeId: string;
//   nodeType: 'person' | 'marriage';
// }

// interface GenealogyTreeProps {
//   websocketData?: WebSocketMessage[];
//   onExpandNode?: (personName: string, depth: number) => void;
//   expandDepth?: number; // Allow configurable expansion depth
// }

// // Internal component that uses useReactFlow
// function GenealogyTreeInternal({ 
//   websocketData = [], 
//   onExpandNode,
//   expandDepth = 3 // Increased default depth
// }: GenealogyTreeProps) {
//   const [nodes, setNodes, onNodesChange] = useNodesState([]);
//   const [edges, setEdges, onEdgesChange] = useEdgesState([]);
//   const [personDetails, setPersonDetails] = useState<Map<string, PersonDetails>>(new Map());
//   const [relationships, setRelationships] = useState<Relationship[]>([]);
//   const [progress, setProgress] = useState(0);
//   const [status, setStatus] = useState('');
//   const [contextMenu, setContextMenu] = useState<ContextMenu>({
//     show: false,
//     x: 0,
//     y: 0,
//     nodeId: '',
//     nodeType: 'person'
//   });
//   const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
//   const [expandingNode, setExpandingNode] = useState<string | null>(null);

//   const onConnect = useCallback(
//     (params: Connection) => setEdges((eds) => addEdge(params, eds)),
//     [setEdges]
//   );

//   // Handle node right-click
//   const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
//     event.preventDefault();
//     setContextMenu({
//       show: true,
//       x: event.clientX,
//       y: event.clientY,
//       nodeId: node.id,
//       nodeType: node.type as 'person' | 'marriage'
//     });
//   }, []);

//   // Hide context menu on click outside
//   useEffect(() => {
//     const handleClick = () => setContextMenu(prev => ({ ...prev, show: false }));
//     document.addEventListener('click', handleClick);
//     return () => document.removeEventListener('click', handleClick);
//   }, []);

//   // Helper function to get node by ID
//   const getNodeById = useCallback((nodeId: string) => {
//     return nodes.find(node => node.id === nodeId);
//   }, [nodes]);

//   // Enhanced error handling and connection management
//   useEffect(() => {
//     if (websocketData.length === 0) return;

//     const latestMessage = websocketData[websocketData.length - 1];
    
//     // Handle error messages
//     if (latestMessage.type === 'status') {
//       const message = latestMessage.data.message;
      
//       // Check for error conditions
//       if (message.includes('Error') || message.includes('not found') || message.includes('Connection error')) {
//         // Stop the expanding state for failed expansions
//         if (expandingNode) {
//           setExpandingNode(null);
//         }
        
//         // Show error in status but don't block UI
//         console.warn('Family tree expansion error:', message);
        
//         // Auto-hide error messages after 5 seconds
//         setTimeout(() => {
//           setStatus('');
//           setProgress(0);
//         }, 5000);
//       }
//     }
//   }, [websocketData, expandingNode]);

//   // Enhanced expand node functionality with better error feedback
//   const handleExpandNode = useCallback((nodeId: string) => {
//     const node = getNodeById(nodeId);
//     if (node && node.data.entity && onExpandNode) {
//       const personName = node.data.entity.replace(/\s+/g, '_');
      
//       // Check if this node has already been expanded recently (prevent spam)
//       if (expandingNode === nodeId) {
//         console.log('Node expansion already in progress');
//         return;
//       }
      
//       setExpandingNode(nodeId);
      
//       // Set a timeout to reset expanding state in case of no response
//       setTimeout(() => {
//         if (expandingNode === nodeId) {
//           setExpandingNode(null);
//           setStatus(`Expansion timeout for ${node.data.entity}`);
//           setProgress(0);
//         }
//       }, 30000); // 30 second timeout
      
//       // Call with configurable depth
//       onExpandNode(personName, expandDepth);
      
//       // Mark as expanded immediately for UI feedback
//       setExpandedNodes(prev => new Set([...prev, nodeId]));
//     }
//     setContextMenu(prev => ({ ...prev, show: false }));
//   }, [getNodeById, onExpandNode, expandDepth, expandingNode]);

//   // Clear expanding state when new data arrives
//   useEffect(() => {
//     if (expandingNode && websocketData.length > 0) {
//       // Check if we received new data after expansion
//       const hasNewData = websocketData.some(msg => 
//         msg.type === 'status' && msg.data.message.includes('Complete')
//       );
//       if (hasNewData) {
//         setExpandingNode(null);
//       }
//     }
//   }, [websocketData, expandingNode]);

//   // Delete node functionality
//   const handleDeleteNode = useCallback((nodeId: string) => {
//     // Remove the node and all connected edges
//     const newNodes = nodes.filter(node => node.id !== nodeId);
//     const newEdges = edges.filter(edge => 
//       edge.source !== nodeId && edge.target !== nodeId
//     );
    
//     setNodes(newNodes);
//     setEdges(newEdges);
    
//     // Remove from expanded nodes if it was expanded
//     setExpandedNodes(prev => {
//       const newSet = new Set(prev);
//       newSet.delete(nodeId);
//       return newSet;
//     });
    
//     setContextMenu(prev => ({ ...prev, show: false }));
//   }, [nodes, edges, setNodes, setEdges]);

//   // Add spouse functionality
//   const handleAddSpouse = useCallback((nodeId: string) => {
//     const node = getNodeById(nodeId);
//     if (!node || node.type !== 'person') return;
    
//     // Generate new spouse ID and position
//     const spouseId = `${nodeId}-spouse-${Date.now()}`;
//     const marriageId = `${nodeId}-${spouseId}-marriage`;
    
//     const spouseX = node.position.x + 350;
//     const spouseY = node.position.y;
//     const marriageX = node.position.x + 175;
//     const marriageY = node.position.y + 200;

//     // Create new spouse node
//     const newSpouseNode: Node = {
//       id: spouseId,
//       type: 'person',
//       position: { x: spouseX, y: spouseY },
//       data: {
//         label: 'New Spouse',
//         entity: 'New Spouse',
//         qid: 'temp',
//         nodeType: 'entity' as const,
//       },
//     };

//     // Create marriage node
//     const newMarriageNode: Node = {
//       id: marriageId,
//       type: 'marriage',
//       position: { x: marriageX, y: marriageY },
//       data: {
//         label: '♥',
//         spouse1: nodeId,
//         spouse2: spouseId,
//         nodeType: 'marriage' as const,
//       },
//     };

//     // Create edges
//     const newEdges: Edge[] = [
//       {
//         id: `${nodeId}-${marriageId}`,
//         source: nodeId,
//         target: marriageId,
//         type: 'straight',
//         style: { stroke: '#ec4899', strokeWidth: 2 },
//       },
//       {
//         id: `${spouseId}-${marriageId}`,
//         source: spouseId,
//         target: marriageId,
//         type: 'straight',
//         style: { stroke: '#ec4899', strokeWidth: 2 },
//       }
//     ];

//     setNodes([...nodes, newSpouseNode, newMarriageNode]);
//     setEdges([...edges, ...newEdges]);
//     setContextMenu(prev => ({ ...prev, show: false }));
//   }, [getNodeById, nodes, edges, setNodes, setEdges]);

//   // Add child functionality
//   const handleAddChild = useCallback((nodeId: string) => {
//     const node = getNodeById(nodeId);
//     if (!node) return;
    
//     // Generate new child ID and position
//     const childId = `${nodeId}-child-${Date.now()}`;
    
//     let childX = node.position.x;
//     let childY = node.position.y + 350;
//     let sourceId = nodeId;

//     // If it's a marriage node, position child below it
//     if (node.type === 'marriage') {
//       childX = node.position.x - 25; // Center under marriage node
//     } else {
//       // For person nodes, try to find their marriage node
//       const marriageNode = nodes.find(n => 
//         n.type === 'marriage' && 
//         (n.data.spouse1 === nodeId || n.data.spouse2 === nodeId)
//       );
//       if (marriageNode) {
//         sourceId = marriageNode.id;
//         childX = marriageNode.position.x - 25;
//         childY = marriageNode.position.y + 150;
//       }
//     }

//     // Create new child node
//     const newChildNode: Node = {
//       id: childId,
//       type: 'person',
//       position: { x: childX, y: childY },
//       data: {
//         label: 'New Child',
//         entity: 'New Child',
//         qid: 'temp',
//         nodeType: 'entity' as const,
//       },
//     };

//     // Create edge from parent/marriage to child
//     const newEdge: Edge = {
//       id: `parent-child-${childId}`,
//       source: sourceId,
//       target: childId,
//       type: 'smoothstep',
//       style: {
//         stroke: '#6b7280',
//         strokeWidth: 2,
//       },
//     };

//     setNodes([...nodes, newChildNode]);
//     setEdges([...edges, newEdge]);
//     setContextMenu(prev => ({ ...prev, show: false }));
//   }, [getNodeById, nodes, edges, setNodes, setEdges]);

//   // Enhanced context menu with better status indicators
//   const ContextMenuComponent = () => {
//     if (!contextMenu.show) return null;

//     const isExpanded = expandedNodes.has(contextMenu.nodeId);
//     const isExpanding = expandingNode === contextMenu.nodeId;
//     const node = getNodeById(contextMenu.nodeId);
//     const hasWikipediaEntry = node?.data.qid && node.data.qid !== 'temp' && node.data.qid !== 'unknown';

//     return (
//       <div
//         className="fixed bg-white border border-gray-300 rounded-lg shadow-lg py-2 z-50"
//         style={{
//           left: contextMenu.x,
//           top: contextMenu.y,
//         }}
//         onClick={(e) => e.stopPropagation()}
//       >
//         {contextMenu.nodeType === 'person' && (
//           <>
//             <button
//               className={`w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center ${
//                 isExpanding ? 'opacity-50 cursor-not-allowed' : 
//                 !hasWikipediaEntry ? 'opacity-75 text-gray-500' : ''
//               }`}
//               onClick={() => handleExpandNode(contextMenu.nodeId)}
//               disabled={isExpanding}
//               title={
//                 !hasWikipediaEntry ? 
//                 'This person may not have a Wikipedia entry' : 
//                 isExpanding ? 'Expansion in progress...' : 
//                 'Expand family tree'
//               }
//             >
//               <span className="mr-2">
//                 {isExpanding ? '⏳' : hasWikipediaEntry ? '🔍' : '❓'}
//               </span>
//               {isExpanding ? 'Expanding...' : 
//                !hasWikipediaEntry ? 'Try Expand (Limited Info)' :
//                isExpanded ? 'Expand More' : 'Expand Family Tree'}
//             </button>
//             <button
//               className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center"
//               onClick={() => handleAddSpouse(contextMenu.nodeId)}
//             >
//               <span className="mr-2">💑</span>
//               Add Spouse
//             </button>
//           </>
//         )}
//         <button
//           className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center"
//           onClick={() => handleAddChild(contextMenu.nodeId)}
//         >
//           <span className="mr-2">👶</span>
//           Add Child
//         </button>
//         <div className="border-t border-gray-200 my-1"></div>
//         <button
//           className="w-full px-4 py-2 text-left hover:bg-red-100 text-red-600 flex items-center"
//           onClick={() => handleDeleteNode(contextMenu.nodeId)}
//         >
//           <span className="mr-2">🗑️</span>
//           Delete Node
//         </button>
//       </div>
//     );
//   };

//   // Process WebSocket messages (existing logic)
//   useEffect(() => {
//     if (websocketData.length === 0) return;

//     const newPersonDetails = new Map<string, PersonDetails>();
//     const newRelationships: Relationship[] = [];
//     let latestStatus = '';
//     let latestProgress = 0;

//     websocketData.forEach((message) => {
//       switch (message.type) {
//         case 'status':
//           latestStatus = message.data.message;
//           latestProgress = message.data.progress;
//           break;
//         case 'personal_details':
//           newPersonDetails.set(message.data.entity, message.data);
//           break;
//         case 'relationship':
//           newRelationships.push(message.data);
//           break;
//       }
//     });

//     setPersonDetails(newPersonDetails);
//     setRelationships(newRelationships);
//     setStatus(latestStatus);
//     setProgress(latestProgress);
//   }, [websocketData]);

//   // Enhanced graph generation with better marriage handling
//   useEffect(() => {
//     if (personDetails.size === 0) return; // Allow graph creation even without relationships

//     const newNodes: Node[] = [];
//     const newEdges: Edge[] = [];
    
//     // Constants for layout
//     const PERSON_WIDTH = 200;
//     const PERSON_HEIGHT = 120;
//     const MARRIAGE_WIDTH = 60;
//     const MARRIAGE_HEIGHT = 60;
//     const HORIZONTAL_SPACING = 300;
//     const VERTICAL_SPACING = 350;
//     const MARRIAGE_OFFSET_Y = 220;
    
//     // Separate relationships by type
//     const marriageRelationships = relationships.filter(rel => 
//       rel.relationship === 'spouse of' || 
//       rel.relationship === 'married to' ||
//       rel.relationship === 'spouse' ||
//       rel.relationship === 'husband of' ||
//       rel.relationship === 'wife of'
//     );
    
//     const parentChildRelationships = relationships.filter(rel => 
//       rel.relationship === 'child of' ||
//       rel.relationship === 'parent of' ||
//       rel.relationship === 'father of' ||
//       rel.relationship === 'mother of'
//     );

//     // Create marriage mappings - FIXED to include all marriages
//     const marriages = new Map<string, { spouse1: string; spouse2: string; children: string[] }>();
//     const personToMarriages = new Map<string, string[]>();

//     // Process ALL marriages, including those in top layer
//     marriageRelationships.forEach(rel => {
//       const [person1, person2] = [rel.entity1, rel.entity2].sort();
//       const marriageId = `${person1}-${person2}-marriage`;
      
//       if (!marriages.has(marriageId)) {
//         marriages.set(marriageId, {
//           spouse1: person1,
//           spouse2: person2,
//           children: []
//         });
        
//         // Track marriages for each person
//         if (!personToMarriages.has(person1)) personToMarriages.set(person1, []);
//         if (!personToMarriages.has(person2)) personToMarriages.set(person2, []);
//         personToMarriages.get(person1)!.push(marriageId);
//         personToMarriages.get(person2)!.push(marriageId);
//       }
//     });

//     // Add children to marriages - ENHANCED logic
//     parentChildRelationships.forEach(rel => {
//       let parent, child;
      
//       // Handle different relationship directions
//       if (rel.relationship === 'child of') {
//         parent = rel.entity2;
//         child = rel.entity1;
//       } else if (rel.relationship === 'parent of' || 
//                  rel.relationship === 'father of' || 
//                  rel.relationship === 'mother of') {
//         parent = rel.entity1;
//         child = rel.entity2;
//       } else {
//         return;
//       }
      
//       // Find marriages involving this parent
//       const parentMarriages = personToMarriages.get(parent) || [];
//       parentMarriages.forEach(marriageId => {
//         const marriage = marriages.get(marriageId);
//         if (marriage && !marriage.children.includes(child)) {
//           marriage.children.push(child);
//         }
//       });
//     });

//     // ENHANCED generation calculation
//     const generations = new Map<string, number>();
//     const visited = new Set<string>();
    
//     // Find root person - prefer someone with no parents
//     const peopleWithParents = new Set<string>();
//     parentChildRelationships.forEach(rel => {
//       if (rel.relationship === 'child of') {
//         peopleWithParents.add(rel.entity1);
//       } else if (rel.relationship === 'parent of') {
//         peopleWithParents.add(rel.entity2);
//       }
//     });
    
//     const rootCandidates = Array.from(personDetails.keys()).filter(person => 
//       !peopleWithParents.has(person)
//     );
    
//     const rootPerson = rootCandidates.length > 0 ? rootCandidates[0] : Array.from(personDetails.keys())[0];
    
//     // BFS to assign generations - IMPROVED algorithm
//     const queue: { person: string; generation: number }[] = [{ person: rootPerson, generation: 0 }];
//     generations.set(rootPerson, 0);
    
//     while (queue.length > 0) {
//       const { person, generation } = queue.shift()!;
//       if (visited.has(person)) continue;
//       visited.add(person);
      
//       // Process parent-child relationships
//       parentChildRelationships.forEach(rel => {
//         if (rel.relationship === 'child of' && rel.entity2 === person && !generations.has(rel.entity1)) {
//           generations.set(rel.entity1, generation + 1);
//           queue.push({ person: rel.entity1, generation: generation + 1 });
//         } else if (rel.relationship === 'child of' && rel.entity1 === person && !generations.has(rel.entity2)) {
//           generations.set(rel.entity2, Math.max(generation - 1, 0));
//           queue.push({ person: rel.entity2, generation: Math.max(generation - 1, 0) });
//         } else if (rel.relationship === 'parent of' && rel.entity1 === person && !generations.has(rel.entity2)) {
//           generations.set(rel.entity2, generation + 1);
//           queue.push({ person: rel.entity2, generation: generation + 1 });
//         } else if (rel.relationship === 'parent of' && rel.entity2 === person && !generations.has(rel.entity1)) {
//           generations.set(rel.entity1, Math.max(generation - 1, 0));
//           queue.push({ person: rel.entity1, generation: Math.max(generation - 1, 0) });
//         }
//       });
//     }

//     // Assign same generation to spouses - ENHANCED
//     marriageRelationships.forEach(rel => {
//       const gen1 = generations.get(rel.entity1);
//       const gen2 = generations.get(rel.entity2);
      
//       if (gen1 !== undefined && gen2 === undefined) {
//         generations.set(rel.entity2, gen1);
//       } else if (gen2 !== undefined && gen1 === undefined) {
//         generations.set(rel.entity1, gen2);
//       } else if (gen1 !== undefined && gen2 !== undefined && gen1 !== gen2) {
//         // If spouses have different generations, use the higher one (older generation)
//         const targetGen = Math.min(gen1, gen2);
//         generations.set(rel.entity1, targetGen);
//         generations.set(rel.entity2, targetGen);
//       }
//     });

//     // Ensure all people have a generation assigned
//     Array.from(personDetails.keys()).forEach(person => {
//       if (!generations.has(person)) {
//         generations.set(person, 0); // Default to root generation
//       }
//     });

//     // Group elements by generation - ENHANCED
//     const generationGroups = new Map<number, { 
//       marriages: string[], 
//       singles: string[] 
//     }>();

//     // Initialize generation groups for all generations including negative ones
//     const allGenerations = new Set(Array.from(generations.values()));
//     const minGen = Math.min(...Array.from(allGenerations));
//     const maxGen = Math.max(...Array.from(allGenerations));
    
//     for (let gen = minGen; gen <= maxGen; gen++) {
//       generationGroups.set(gen, { marriages: [], singles: [] });
//     }

//     // Group marriages by generation - FIXED
//     Array.from(marriages.entries()).forEach(([marriageId, marriage]) => {
//       const gen1 = generations.get(marriage.spouse1) || 0;
//       const gen2 = generations.get(marriage.spouse2) || 0;
//       const generation = Math.min(gen1, gen2);
      
//       const group = generationGroups.get(generation);
//       if (group && personDetails.has(marriage.spouse1) && personDetails.has(marriage.spouse2)) {
//         group.marriages.push(marriageId);
//       }
//     });

//     // Group single people by generation
//     const marriedPeople = new Set<string>();
//     Array.from(marriages.values()).forEach(marriage => {
//       marriedPeople.add(marriage.spouse1);
//       marriedPeople.add(marriage.spouse2);
//     });

//     Array.from(personDetails.keys()).forEach(person => {
//       if (!marriedPeople.has(person)) {
//         const generation = generations.get(person) || 0;
//         const group = generationGroups.get(generation);
//         if (group) {
//           group.singles.push(person);
//         }
//       }
//     });

//     // Create nodes with improved positioning - FIXED
//     const nodePositions = new Map<string, { x: number; y: number }>();
    
//     Array.from(generationGroups.entries())
//       .sort(([a], [b]) => a - b) // Sort by generation (ancestors first)
//       .forEach(([generation, group]) => {
//         const y = generation * VERTICAL_SPACING + 300;
        
//         // Calculate total width needed for this generation
//         const marriageWidth = group.marriages.length * (HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH);
//         const singleWidth = group.singles.length * HORIZONTAL_SPACING;
//         const totalWidth = Math.max(marriageWidth + singleWidth, 400);
        
//         // Start from center and work outward
//         let currentX = -totalWidth / 2;
        
//         // Position marriages first - ENSURE ALL MARRIAGES ARE CREATED
//         group.marriages.forEach(marriageId => {
//           const marriage = marriages.get(marriageId)!;
          
//           // Get spouse details
//           const spouse1Details = personDetails.get(marriage.spouse1);
//           const spouse2Details = personDetails.get(marriage.spouse2);
          
//           // Only skip if neither spouse has details
//           if (!spouse1Details && !spouse2Details) return;
          
//           // Calculate positions for the marriage group
//           const marriageGroupWidth = HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH;
//           const groupCenterX = currentX + marriageGroupWidth / 2;
          
//           // Position spouses symmetrically around center
//           const spouse1X = groupCenterX - HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
//           const spouse2X = groupCenterX + HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
//           const marriageX = groupCenterX - MARRIAGE_WIDTH / 2;
//           const marriageY = y + MARRIAGE_OFFSET_Y;
          
//           // Store positions
//           nodePositions.set(marriage.spouse1, { x: spouse1X, y });
//           nodePositions.set(marriage.spouse2, { x: spouse2X, y });
//           nodePositions.set(marriageId, { x: marriageX, y: marriageY });
          
//           // Create spouse nodes - handle missing details gracefully
//           [marriage.spouse1, marriage.spouse2].forEach((person, index) => {
//             const details = index === 0 ? spouse1Details : spouse2Details;
//             const x = index === 0 ? spouse1X : spouse2X;
            
//             // Create node even if details are missing
//             newNodes.push({
//               id: person,
//               type: 'person',
//               position: { x, y },
//               data: {
//                 label: details?.entity || person,
//                 entity: details?.entity || person,
//                 qid: details?.qid || 'unknown',
//                 birth_year: details?.birth_year,
//                 death_year: details?.death_year,
//                 image_url: details?.image_url,
//                 nodeType: 'entity' as const,
//                 isExpanded: expandedNodes.has(person),
//               },
//             });
//           });

//           // Create marriage node - ALWAYS CREATE FOR ALL MARRIAGES
//           newNodes.push({
//             id: marriageId,
//             type: 'marriage',
//             position: { x: marriageX, y: marriageY },
//             data: {
//               label: '♥',
//               spouse1: marriage.spouse1,
//               spouse2: marriage.spouse2,
//               nodeType: 'marriage' as const,
//             },
//           });

//           // Connect spouses to marriage node
//           newEdges.push({
//             id: `${marriage.spouse1}-${marriageId}`,
//             source: marriage.spouse1,
//             target: marriageId,
//             type: 'straight',
//             style: { stroke: '#ec4899', strokeWidth: 2 },
//           });

//           newEdges.push({
//             id: `${marriage.spouse2}-${marriageId}`,
//             source: marriage.spouse2,
//             target: marriageId,
//             type: 'straight',
//             style: { stroke: '#ec4899', strokeWidth: 2 },
//           });

//           currentX += marriageGroupWidth;
//         });

//         // Position single people
//         group.singles.forEach(person => {
//           const details = personDetails.get(person);
//           if (!details) return;
          
//           const x = currentX;
//           nodePositions.set(person, { x, y });
          
//           newNodes.push({
//             id: person,
//             type: 'person',
//             position: { x, y },
//             data: {
//               label: details.entity,
//               entity: details.entity,
//               qid: details.qid,
//               birth_year: details.birth_year,
//               death_year: details.death_year,
//               image_url: details.image_url,
//               nodeType: 'entity' as const,
//               isExpanded: expandedNodes.has(person),
//             },
//           });

//           currentX += HORIZONTAL_SPACING;
//         });
//       });

//     // Create parent-child relationships - ENHANCED
//     parentChildRelationships.forEach((rel, index) => {
//       let parent, child;
      
//       // Handle different relationship directions
//       if (rel.relationship === 'child of') {
//         parent = rel.entity2;
//         child = rel.entity1;
//       } else if (rel.relationship === 'parent of' || 
//                  rel.relationship === 'father of' || 
//                  rel.relationship === 'mother of') {
//         parent = rel.entity1;
//         child = rel.entity2;
//       } else {
//         return;
//       }
      
//       // Only create edges if both parent and child have details or nodes
//       const hasParentNode = newNodes.some(n => n.id === parent);
//       const hasChildNode = newNodes.some(n => n.id === child);
      
//       if (!hasParentNode || !hasChildNode) return;
      
//       // Check if parent is in a marriage with children
//       let sourceId = parent;
//       const parentMarriages = personToMarriages.get(parent) || [];
      
//       for (const marriageId of parentMarriages) {
//         const marriage = marriages.get(marriageId);
//         if (marriage && marriage.children.includes(child)) {
//           sourceId = marriageId;
//           break;
//         }
//       }
      
//       newEdges.push({
//         id: `parent-child-${parent}-${child}-${index}`,
//         source: sourceId,
//         target: child,
//         type: 'smoothstep',
//         style: {
//           stroke: '#6b7280',
//           strokeWidth: 2,
//         },
//       });
//     });

//     console.log(`Generated tree: ${newNodes.length} nodes, ${newEdges.length} edges`);
//     console.log(`Marriages found: ${marriages.size}`);
//     console.log('Generation distribution:', 
//       Array.from(generations.entries()).reduce((acc, [person, gen]) => {
//         acc[gen] = (acc[gen] || 0) + 1;
//         return acc;
//       }, {} as Record<number, number>)
//     );

//     setNodes(newNodes);
//     setEdges(newEdges);
//   }, [personDetails, relationships, setNodes, setEdges, expandedNodes]);

//   return (
//     <div className="absolute inset-0 w-full h-full">
//       {/* Status Panel - Enhanced with expansion info */}
//       {(status || progress > 0 || expandingNode) && (
//         <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-md max-w-md">
//           <h2 className="text-lg font-bold mb-2">
//             {expandingNode ? 'Expanding Family Tree...' : 'Processing...'}
//           </h2>
//           {status && (
//             <div className="mb-2">
//               <p className="text-sm text-gray-600">{status}</p>
//               <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
//                 <div 
//                   className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
//                   style={{ width: `${progress}%` }}
//                 ></div>
//               </div>
//             </div>
//           )}
//           <div className="text-sm text-gray-500">
//             <p>People: {personDetails.size}</p>
//             <p>Relationships: {relationships.length}</p>
//             <p>Expanded nodes: {expandedNodes.size}</p>
//             <p>Expansion depth: {expandDepth}</p>
//           </div>
//         </div>
//       )}

//       {/* Enhanced Instructions */}
//       {nodes.length > 0 && (
//         <div className="absolute bottom-4 left-4 z-10 bg-white p-3 rounded-lg shadow-md max-w-xs">
//           <div className="text-xs text-gray-600 space-y-1">
//             <p className="font-semibold mb-2">Instructions:</p>
//             <p>• Right-click nodes for options</p>
//             <p>• Expand depth: {expandDepth} generations</p>
//             <p>• Drag to pan, scroll to zoom</p>
//             <p>🔗 Gray lines: Parent-child</p>
//             <p>💕 Pink lines: Marriage</p>
//           </div>
//         </div>
//       )}

//       <ContextMenuComponent />
      
//       <ReactFlow
//         nodes={nodes}
//         edges={edges}
//         onNodesChange={onNodesChange}
//         onEdgesChange={onEdgesChange}
//         onConnect={onConnect}
//         onNodeContextMenu={onNodeContextMenu}
//         nodeTypes={nodeTypes}
//         fitView
//         fitViewOptions={{ padding: 0.2 }}
//         panOnScroll
//         selectionOnDrag
//         panOnDrag
//         zoomOnScroll
//         zoomOnPinch
//         zoomOnDoubleClick
//         preventScrolling={false}
//         className="w-full h-full"
//       >
//         <Controls position="bottom-right" />
//         <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
//       </ReactFlow>
//     </div>
//   );
// }

// // Main component wrapped with ReactFlowProvider
// export default function GenealogyTree(props: GenealogyTreeProps) {
//   return (
//     <ReactFlowProvider>
//       <GenealogyTreeInternal {...props} />
//     </ReactFlowProvider>
//   );
// }

import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import PersonNode from './PersonNode';
import MarriageNode from './MarriageNode';

const nodeTypes = {
  person: PersonNode,
  marriage: MarriageNode,
};

// Family line colors for visual distinction
const FAMILY_COLORS = [
  '#3b82f6', // Blue
  '#ef4444', // Red
  '#10b981', // Green
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#f97316', // Orange
  '#84cc16', // Lime
];

interface WebSocketMessage {
  type: 'status' | 'personal_details' | 'relationship';
  data: any;
}

interface PersonDetails {
  entity: string;
  qid: string;
  birth_year?: string;
  death_year?: string;
  image_url?: string;
}

interface Relationship {
  entity1: string;
  relationship: string;
  entity2: string;
}

interface ContextMenu {
  show: boolean;
  x: number;
  y: number;
  nodeId: string;
  nodeType: 'person' | 'marriage';
}

interface GenealogyTreeProps {
  websocketData?: WebSocketMessage[];
  onExpandNode?: (personName: string, depth: number) => void;
  expandDepth?: number;
}

function GenealogyTreeInternal({ 
  websocketData = [], 
  onExpandNode,
  expandDepth = 3
}: GenealogyTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [personDetails, setPersonDetails] = useState<Map<string, PersonDetails>>(new Map());
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [contextMenu, setContextMenu] = useState<ContextMenu>({
    show: false,
    x: 0,
    y: 0,
    nodeId: '',
    nodeType: 'person'
  });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [expandingNode, setExpandingNode] = useState<string | null>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Handle node right-click
  const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    setContextMenu({
      show: true,
      x: event.clientX,
      y: event.clientY,
      nodeId: node.id,
      nodeType: node.type as 'person' | 'marriage'
    });
  }, []);

  // Hide context menu on click outside
  useEffect(() => {
    const handleClick = () => setContextMenu(prev => ({ ...prev, show: false }));
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  // Helper function to get node by ID
  const getNodeById = useCallback((nodeId: string) => {
    return nodes.find(node => node.id === nodeId);
  }, [nodes]);

  // Assign family colors based on lineage
  const assignFamilyColors = useCallback((marriages: Map<string, any>, parentChildRels: Relationship[]) => {
    const familyColors = new Map<string, string>();
    let colorIndex = 0;

    // For each person in a marriage, assign them and their ancestors the same color
    Array.from(marriages.values()).forEach(marriage => {
      const spouse1Color = FAMILY_COLORS[colorIndex % FAMILY_COLORS.length];
      const spouse2Color = FAMILY_COLORS[(colorIndex + 1) % FAMILY_COLORS.length];
      
      // Assign colors to each spouse's family line
      const assignLineageColor = (person: string, color: string, visited: Set<string> = new Set()) => {
        if (visited.has(person)) return;
        visited.add(person);
        
        if (!familyColors.has(person)) {
          familyColors.set(person, color);
        }
        
        // Color all ancestors of this person
        parentChildRels.forEach(rel => {
          if (rel.relationship === 'child of' && rel.entity1 === person) {
            assignLineageColor(rel.entity2, color, visited);
          } else if (rel.relationship === 'parent of' && rel.entity2 === person) {
            assignLineageColor(rel.entity1, color, visited);
          }
        });
      };

      assignLineageColor(marriage.spouse1, spouse1Color);
      assignLineageColor(marriage.spouse2, spouse2Color);
      
      colorIndex += 2;
    });

    return familyColors;
  }, []);

  // Enhanced error handling and connection management
  useEffect(() => {
    if (websocketData.length === 0) return;

    const latestMessage = websocketData[websocketData.length - 1];
    
    if (latestMessage.type === 'status') {
      const message = latestMessage.data.message;
      
      if (message.includes('Error') || message.includes('not found') || message.includes('Connection error')) {
        if (expandingNode) {
          setExpandingNode(null);
        }
        
        console.warn('Family tree expansion error:', message);
        
        setTimeout(() => {
          setStatus('');
          setProgress(0);
        }, 5000);
      }
    }
  }, [websocketData, expandingNode]);

  // Enhanced expand node functionality
  const handleExpandNode = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (node && node.data.entity && onExpandNode) {
      const personName = node.data.entity.replace(/\s+/g, '_');
      
      if (expandingNode === nodeId) {
        console.log('Node expansion already in progress');
        return;
      }
      
      setExpandingNode(nodeId);
      
      setTimeout(() => {
        if (expandingNode === nodeId) {
          setExpandingNode(null);
          setStatus(`Expansion timeout for ${node.data.entity}`);
          setProgress(0);
        }
      }, 30000);
      
      onExpandNode(personName, expandDepth);
      setExpandedNodes(prev => new Set([...prev, nodeId]));
    }
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, onExpandNode, expandDepth, expandingNode]);

  // Delete node functionality
  const handleDeleteNode = useCallback((nodeId: string) => {
    const newNodes = nodes.filter(node => node.id !== nodeId);
    const newEdges = edges.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    );
    
    setNodes(newNodes);
    setEdges(newEdges);
    
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      newSet.delete(nodeId);
      return newSet;
    });
    
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [nodes, edges, setNodes, setEdges]);

  // Add spouse functionality
  const handleAddSpouse = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (!node || node.type !== 'person') return;
    
    const spouseId = `${nodeId}-spouse-${Date.now()}`;
    const marriageId = `${nodeId}-${spouseId}-marriage`;
    
    const spouseX = node.position.x + 350;
    const spouseY = node.position.y;
    const marriageX = node.position.x + 175;
    const marriageY = node.position.y + 200;

    const newSpouseNode: Node = {
      id: spouseId,
      type: 'person',
      position: { x: spouseX, y: spouseY },
      data: {
        label: 'New Spouse',
        entity: 'New Spouse',
        qid: 'temp',
        nodeType: 'entity' as const,
      },
    };

    const newMarriageNode: Node = {
      id: marriageId,
      type: 'marriage',
      position: { x: marriageX, y: marriageY },
      data: {
        label: '♥',
        spouse1: nodeId,
        spouse2: spouseId,
        nodeType: 'marriage' as const,
      },
    };

    const newEdges: Edge[] = [
      {
        id: `${nodeId}-${marriageId}`,
        source: nodeId,
        target: marriageId,
        type: 'straight',
        style: { stroke: '#ec4899', strokeWidth: 2 },
      },
      {
        id: `${spouseId}-${marriageId}`,
        source: spouseId,
        target: marriageId,
        type: 'straight',
        style: { stroke: '#ec4899', strokeWidth: 2 },
      }
    ];

    setNodes([...nodes, newSpouseNode, newMarriageNode]);
    setEdges([...edges, ...newEdges]);
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, nodes, edges, setNodes, setEdges]);

  // Add child functionality
  const handleAddChild = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (!node) return;
    
    const childId = `${nodeId}-child-${Date.now()}`;
    
    let childX = node.position.x;
    let childY = node.position.y + 350;
    let sourceId = nodeId;

    if (node.type === 'marriage') {
      childX = node.position.x - 25;
    } else {
      const marriageNode = nodes.find(n => 
        n.type === 'marriage' && 
        (n.data.spouse1 === nodeId || n.data.spouse2 === nodeId)
      );
      if (marriageNode) {
        sourceId = marriageNode.id;
        childX = marriageNode.position.x - 25;
        childY = marriageNode.position.y + 150;
      }
    }

    const newChildNode: Node = {
      id: childId,
      type: 'person',
      position: { x: childX, y: childY },
      data: {
        label: 'New Child',
        entity: 'New Child',
        qid: 'temp',
        nodeType: 'entity' as const,
      },
    };

    const newEdge: Edge = {
      id: `parent-child-${childId}`,
      source: sourceId,
      target: childId,
      type: 'smoothstep',
      style: {
        stroke: '#6b7280',
        strokeWidth: 2,
      },
    };

    setNodes([...nodes, newChildNode]);
    setEdges([...edges, newEdge]);
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, nodes, edges, setNodes, setEdges]);

  // Clear expanding state when new data arrives
  useEffect(() => {
    if (expandingNode && websocketData.length > 0) {
      const hasNewData = websocketData.some(msg => 
        msg.type === 'status' && msg.data.message.includes('Complete')
      );
      if (hasNewData) {
        setExpandingNode(null);
      }
    }
  }, [websocketData, expandingNode]);

  // Enhanced context menu
  const ContextMenuComponent = () => {
    if (!contextMenu.show) return null;

    const isExpanded = expandedNodes.has(contextMenu.nodeId);
    const isExpanding = expandingNode === contextMenu.nodeId;
    const node = getNodeById(contextMenu.nodeId);
    const hasWikipediaEntry = node?.data.qid && node.data.qid !== 'temp' && node.data.qid !== 'unknown';

    return (
      <div
        className="fixed bg-white border border-gray-300 rounded-lg shadow-lg py-2 z-50"
        style={{
          left: contextMenu.x,
          top: contextMenu.y,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {contextMenu.nodeType === 'person' && (
          <>
            <button
              className={`w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center ${
                isExpanding ? 'opacity-50 cursor-not-allowed' : 
                !hasWikipediaEntry ? 'opacity-75 text-gray-500' : ''
              }`}
              onClick={() => handleExpandNode(contextMenu.nodeId)}
              disabled={isExpanding}
              title={
                !hasWikipediaEntry ? 
                'This person may not have a Wikipedia entry' : 
                isExpanding ? 'Expansion in progress...' : 
                'Expand family tree'
              }
            >
              <span className="mr-2">
                {isExpanding ? '⏳' : hasWikipediaEntry ? '🔍' : '❓'}
              </span>
              {isExpanding ? 'Expanding...' : 
               !hasWikipediaEntry ? 'Try Expand (Limited Info)' :
               isExpanded ? 'Expand More' : 'Expand Family Tree'}
            </button>
            <button
              className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center"
              onClick={() => handleAddSpouse(contextMenu.nodeId)}
            >
              <span className="mr-2">💑</span>
              Add Spouse
            </button>
          </>
        )}
        <button
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center"
          onClick={() => handleAddChild(contextMenu.nodeId)}
        >
          <span className="mr-2">👶</span>
          Add Child
        </button>
        <div className="border-t border-gray-200 my-1"></div>
        <button
          className="w-full px-4 py-2 text-left hover:bg-red-100 text-red-600 flex items-center"
          onClick={() => handleDeleteNode(contextMenu.nodeId)}
        >
          <span className="mr-2">🗑️</span>
          Delete Node
        </button>
      </div>
    );
  };

  // Process WebSocket messages
  useEffect(() => {
    if (websocketData.length === 0) return;

    const newPersonDetails = new Map<string, PersonDetails>();
    const newRelationships: Relationship[] = [];
    let latestStatus = '';
    let latestProgress = 0;

    websocketData.forEach((message) => {
      switch (message.type) {
        case 'status':
          latestStatus = message.data.message;
          latestProgress = message.data.progress;
          break;
        case 'personal_details':
          newPersonDetails.set(message.data.entity, message.data);
          break;
        case 'relationship':
          newRelationships.push(message.data);
          break;
      }
    });

    setPersonDetails(newPersonDetails);
    setRelationships(newRelationships);
    setStatus(latestStatus);
    setProgress(latestProgress);
  }, [websocketData]);

  // Enhanced graph generation with smart positioning and color coding
  useEffect(() => {
    if (personDetails.size === 0) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    // Constants for layout
    const PERSON_WIDTH = 200;
    const PERSON_HEIGHT = 120;
    const MARRIAGE_WIDTH = 60;
    const MARRIAGE_HEIGHT = 60;
    const HORIZONTAL_SPACING = 300;
    const VERTICAL_SPACING = 350;
    const MARRIAGE_OFFSET_Y = 220;
    
    // Separate relationships by type
    const marriageRelationships = relationships.filter(rel => 
      rel.relationship === 'spouse of' || 
      rel.relationship === 'married to' ||
      rel.relationship === 'spouse' ||
      rel.relationship === 'husband of' ||
      rel.relationship === 'wife of'
    );
    
    const parentChildRelationships = relationships.filter(rel => 
      rel.relationship === 'child of' ||
      rel.relationship === 'parent of' ||
      rel.relationship === 'father of' ||
      rel.relationship === 'mother of'
    );

    // Create marriage mappings
    const marriages = new Map<string, { spouse1: string; spouse2: string; children: string[] }>();
    const personToMarriages = new Map<string, string[]>();

    marriageRelationships.forEach(rel => {
      const [person1, person2] = [rel.entity1, rel.entity2].sort();
      const marriageId = `${person1}-${person2}-marriage`;
      
      if (!marriages.has(marriageId)) {
        marriages.set(marriageId, {
          spouse1: person1,
          spouse2: person2,
          children: []
        });
        
        if (!personToMarriages.has(person1)) personToMarriages.set(person1, []);
        if (!personToMarriages.has(person2)) personToMarriages.set(person2, []);
        personToMarriages.get(person1)!.push(marriageId);
        personToMarriages.get(person2)!.push(marriageId);
      }
    });

    // Add children to marriages
    parentChildRelationships.forEach(rel => {
      let parent, child;
      
      if (rel.relationship === 'child of') {
        parent = rel.entity2;
        child = rel.entity1;
      } else if (rel.relationship === 'parent of' || 
                 rel.relationship === 'father of' || 
                 rel.relationship === 'mother of') {
        parent = rel.entity1;
        child = rel.entity2;
      } else {
        return;
      }
      
      const parentMarriages = personToMarriages.get(parent) || [];
      parentMarriages.forEach(marriageId => {
        const marriage = marriages.get(marriageId);
        if (marriage && !marriage.children.includes(child)) {
          marriage.children.push(child);
        }
      });
    });

    // Assign family colors
    const familyColors = assignFamilyColors(marriages, parentChildRelationships);

    // ENHANCED generation calculation with family-aware positioning
    const generations = new Map<string, number>();
    const visited = new Set<string>();
    
    // Find root person
    const peopleWithParents = new Set<string>();
    parentChildRelationships.forEach(rel => {
      if (rel.relationship === 'child of') {
        peopleWithParents.add(rel.entity1);
      } else if (rel.relationship === 'parent of') {
        peopleWithParents.add(rel.entity2);
      }
    });
    
    const rootCandidates = Array.from(personDetails.keys()).filter(person => 
      !peopleWithParents.has(person)
    );
    
    const rootPerson = rootCandidates.length > 0 ? rootCandidates[0] : Array.from(personDetails.keys())[0];
    
    // BFS to assign generations
    const queue: { person: string; generation: number }[] = [{ person: rootPerson, generation: 0 }];
    generations.set(rootPerson, 0);
    
    while (queue.length > 0) {
      const { person, generation } = queue.shift()!;
      if (visited.has(person)) continue;
      visited.add(person);
      
      parentChildRelationships.forEach(rel => {
        if (rel.relationship === 'child of' && rel.entity2 === person && !generations.has(rel.entity1)) {
          generations.set(rel.entity1, generation + 1);
          queue.push({ person: rel.entity1, generation: generation + 1 });
        } else if (rel.relationship === 'child of' && rel.entity1 === person && !generations.has(rel.entity2)) {
          generations.set(rel.entity2, Math.max(generation - 1, 0));
          queue.push({ person: rel.entity2, generation: Math.max(generation - 1, 0) });
        } else if (rel.relationship === 'parent of' && rel.entity1 === person && !generations.has(rel.entity2)) {
          generations.set(rel.entity2, generation + 1);
          queue.push({ person: rel.entity2, generation: generation + 1 });
        } else if (rel.relationship === 'parent of' && rel.entity2 === person && !generations.has(rel.entity1)) {
          generations.set(rel.entity1, Math.max(generation - 1, 0));
          queue.push({ person: rel.entity1, generation: Math.max(generation - 1, 0) });
        }
      });
    }

    // Assign same generation to spouses
    marriageRelationships.forEach(rel => {
      const gen1 = generations.get(rel.entity1);
      const gen2 = generations.get(rel.entity2);
      
      if (gen1 !== undefined && gen2 === undefined) {
        generations.set(rel.entity2, gen1);
      } else if (gen2 !== undefined && gen1 === undefined) {
        generations.set(rel.entity1, gen2);
      } else if (gen1 !== undefined && gen2 !== undefined && gen1 !== gen2) {
        const targetGen = Math.min(gen1, gen2);
        generations.set(rel.entity1, targetGen);
        generations.set(rel.entity2, targetGen);
      }
    });

    // Ensure all people have a generation assigned
    Array.from(personDetails.keys()).forEach(person => {
      if (!generations.has(person)) {
        generations.set(person, 0);
      }
    });

    // IMPROVED positioning algorithm with family lineage consideration
    const generationGroups = new Map<number, { 
      marriages: Array<{id: string, data: any}>, 
      singles: string[] 
    }>();

    const allGenerations = new Set(Array.from(generations.values()));
    const minGen = Math.min(...Array.from(allGenerations));
    const maxGen = Math.max(...Array.from(allGenerations));
    
    for (let gen = minGen; gen <= maxGen; gen++) {
      generationGroups.set(gen, { marriages: [], singles: [] });
    }

    // Group marriages by generation and sort by family color
    Array.from(marriages.entries()).forEach(([marriageId, marriage]) => {
      const gen1 = generations.get(marriage.spouse1) || 0;
      const gen2 = generations.get(marriage.spouse2) || 0;
      const generation = Math.min(gen1, gen2);
      
      const group = generationGroups.get(generation);
      if (group && personDetails.has(marriage.spouse1) && personDetails.has(marriage.spouse2)) {
        group.marriages.push({
          id: marriageId,
          data: marriage
        });
      }
    });

    // Sort marriages within each generation by family color to group related families
    Array.from(generationGroups.values()).forEach(group => {
      group.marriages.sort((a, b) => {
        const colorA = familyColors.get(a.data.spouse1) || '';
        const colorB = familyColors.get(b.data.spouse1) || '';
        return colorA.localeCompare(colorB);
      });
    });

    // Group single people by generation
    const marriedPeople = new Set<string>();
    Array.from(marriages.values()).forEach(marriage => {
      marriedPeople.add(marriage.spouse1);
      marriedPeople.add(marriage.spouse2);
    });

    Array.from(personDetails.keys()).forEach(person => {
      if (!marriedPeople.has(person)) {
        const generation = generations.get(person) || 0;
        const group = generationGroups.get(generation);
        if (group) {
          group.singles.push(person);
        }
      }
    });

    // Create nodes with improved positioning
    const nodePositions = new Map<string, { x: number; y: number }>();
    
    Array.from(generationGroups.entries())
      .sort(([a], [b]) => a - b)
      .forEach(([generation, group]) => {
        const y = generation * VERTICAL_SPACING + 300;
        
        const marriageWidth = group.marriages.length * (HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH);
        const singleWidth = group.singles.length * HORIZONTAL_SPACING;
        const totalWidth = Math.max(marriageWidth + singleWidth, 400);
        
        let currentX = -totalWidth / 2;
        
        // Position marriages with family-aware ordering
        group.marriages.forEach(({ id: marriageId, data: marriage }) => {
          const spouse1Details = personDetails.get(marriage.spouse1);
          const spouse2Details = personDetails.get(marriage.spouse2);
          
          if (!spouse1Details && !spouse2Details) return;
          
          const marriageGroupWidth = HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH;
          const groupCenterX = currentX + marriageGroupWidth / 2;
          
          const spouse1X = groupCenterX - HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
          const spouse2X = groupCenterX + HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
          const marriageX = groupCenterX - MARRIAGE_WIDTH / 2;
          const marriageY = y + MARRIAGE_OFFSET_Y;
          
          nodePositions.set(marriage.spouse1, { x: spouse1X, y });
          nodePositions.set(marriage.spouse2, { x: spouse2X, y });
          nodePositions.set(marriageId, { x: marriageX, y: marriageY });
          
          // Create spouse nodes with family color information
          [marriage.spouse1, marriage.spouse2].forEach((person, index) => {
            const details = index === 0 ? spouse1Details : spouse2Details;
            const x = index === 0 ? spouse1X : spouse2X;
            
            newNodes.push({
              id: person,
              type: 'person',
              position: { x, y },
              data: {
                label: details?.entity || person,
                entity: details?.entity || person,
                qid: details?.qid || 'unknown',
                birth_year: details?.birth_year,
                death_year: details?.death_year,
                image_url: details?.image_url,
                nodeType: 'entity' as const,
                isExpanded: expandedNodes.has(person),
                familyColor: familyColors.get(person), // Add family color to node data
              },
            });
          });

          // Create marriage node
          newNodes.push({
            id: marriageId,
            type: 'marriage',
            position: { x: marriageX, y: marriageY },
            data: {
              label: '♥',
              spouse1: marriage.spouse1,
              spouse2: marriage.spouse2,
              nodeType: 'marriage' as const,
            },
          });

          // Connect spouses to marriage node (keep pink for marriage connections)
          newEdges.push({
            id: `${marriage.spouse1}-${marriageId}`,
            source: marriage.spouse1,
            target: marriageId,
            type: 'straight',
            style: { stroke: '#ec4899', strokeWidth: 2 },
          });

          newEdges.push({
            id: `${marriage.spouse2}-${marriageId}`,
            source: marriage.spouse2,
            target: marriageId,
            type: 'straight',
            style: { stroke: '#ec4899', strokeWidth: 2 },
          });

          currentX += marriageGroupWidth;
        });

        // Position single people
        group.singles.forEach(person => {
          const details = personDetails.get(person);
          if (!details) return;
          
          const x = currentX;
          nodePositions.set(person, { x, y });
          
          newNodes.push({
            id: person,
            type: 'person',
            position: { x, y },
            data: {
              label: details.entity,
              entity: details.entity,
              qid: details.qid,
              birth_year: details.birth_year,
              death_year: details.death_year,
              image_url: details.image_url,
              nodeType: 'entity' as const,
              isExpanded: expandedNodes.has(person),
              familyColor: familyColors.get(person),
            },
          });

          currentX += HORIZONTAL_SPACING;
        });
      });

    // Create parent-child relationships with family-specific colors
    parentChildRelationships.forEach((rel, index) => {
      let parent, child;
      
      if (rel.relationship === 'child of') {
        parent = rel.entity2;
        child = rel.entity1;
      } else if (rel.relationship === 'parent of' || 
                 rel.relationship === 'father of' || 
                 rel.relationship === 'mother of') {
        parent = rel.entity1;
        child = rel.entity2;
      } else {
        return;
      }
      
      const hasParentNode = newNodes.some(n => n.id === parent);
      const hasChildNode = newNodes.some(n => n.id === child);
      
      if (!hasParentNode || !hasChildNode) return;
      
      // Check if parent is in a marriage with children
      let sourceId = parent;
      const parentMarriages = personToMarriages.get(parent) || [];
      
      for (const marriageId of parentMarriages) {
        const marriage = marriages.get(marriageId);
        if (marriage && marriage.children.includes(child)) {
          sourceId = marriageId;
          break;
        }
      }
      
      // Get family color for this parent-child relationship
      const parentColor = familyColors.get(parent) || '#6b7280';
      
      newEdges.push({
        id: `parent-child-${parent}-${child}-${index}`,
        source: sourceId,
        target: child,
        type: 'smoothstep',
        style: {
          stroke: parentColor, // Use family-specific color
          strokeWidth: 3, // Slightly thicker for family lines
          strokeDasharray: sourceId === parent ? '5,5' : undefined, // Dashed if direct parent, solid if from marriage
        markerEnd: 'arrowclosed',
        },
        label: `${parent.split(' ')[0]}'s line`, // Optional: add family line label
      });
    });

    console.log(`Generated tree: ${newNodes.length} nodes, ${newEdges.length} edges`);
    console.log(`Marriages found: ${marriages.size}`);
    console.log('Family colors assigned:', Array.from(familyColors.entries()).slice(0, 5));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [personDetails, relationships, setNodes, setEdges, expandedNodes, assignFamilyColors]);

  return (
    <div className="absolute inset-0 w-full h-full">
      {/* Status Panel - Enhanced with expansion info */}
      {(status || progress > 0 || expandingNode) && (
        <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-md max-w-md">
          <h2 className="text-lg font-bold mb-2">
            {expandingNode ? 'Expanding Family Tree...' : 'Processing...'}
          </h2>
          {status && (
            <div className="mb-2">
              <p className="text-sm text-gray-600">{status}</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
          <div className="text-sm text-gray-500">
            <p>People: {personDetails.size}</p>
            <p>Relationships: {relationships.length}</p>
            <p>Expanded nodes: {expandedNodes.size}</p>
            <p>Expansion depth: {expandDepth}</p>
          </div>
        </div>
      )}

      {/* Enhanced Instructions with color legend */}
      {nodes.length > 0 && (
        <div className="absolute bottom-4 left-4 z-10 bg-white p-3 rounded-lg shadow-md max-w-xs">
          <div className="text-xs text-gray-600 space-y-1">
            <p className="font-semibold mb-2">Instructions:</p>
            <p>• Right-click nodes for options</p>
            <p>• Expansion depth: {expandDepth} generations</p>
            <p>• Drag to pan, scroll to zoom</p>
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="font-semibold">Edge Types:</p>
              <p>💕 Pink: Marriage connections</p>
              <p>🌈 Colored: Family lineages</p>
              <p>— Solid: From marriage</p>
              <p>- - Dashed: Direct parent</p>
            </div>
          </div>
        </div>
      )}

      {/* Color Legend for Family Lines */}
      {nodes.length > 0 && (
        <div className="absolute top-4 right-4 z-10 bg-white p-3 rounded-lg shadow-md max-w-sm">
          <div className="text-xs text-gray-600">
            <p className="font-semibold mb-2">Family Line Colors:</p>
            <div className="grid grid-cols-2 gap-1">
              {FAMILY_COLORS.slice(0, 6).map((color, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: color }}
                  ></div>
                  <span>Family {index + 1}</span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-gray-500">Each spouse's family line has a unique color to distinguish lineages.</p>
          </div>
        </div>
      )}

      <ContextMenuComponent />
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeContextMenu={onNodeContextMenu}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        panOnScroll
        selectionOnDrag
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick
        preventScrolling={false}
        className="w-full h-full"
      >
        <Controls position="bottom-right" />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}

// Main component wrapped with ReactFlowProvider
export default function GenealogyTree(props: GenealogyTreeProps) {
  return (
    <ReactFlowProvider>
      <GenealogyTreeInternal {...props} />
    </ReactFlowProvider>
  );
}