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
} from 'reactflow';
import 'reactflow/dist/style.css';
import PersonNode from './PersonNode';
import MarriageNode from './MarriageNode';

const nodeTypes = {
  person: PersonNode,
  marriage: MarriageNode,
};

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

interface GenealogyTreeProps {
  websocketData?: WebSocketMessage[];
}

export default function GenealogyTree({ websocketData = [] }: GenealogyTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [personDetails, setPersonDetails] = useState<Map<string, PersonDetails>>(new Map());
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

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

  // Generate graph from relationships and person details
  useEffect(() => {
    if (personDetails.size === 0 || relationships.length === 0) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    const nodePositions = new Map<string, { x: number; y: number }>();
    
    // Separate relationships by type
    const marriageRelationships = relationships.filter(rel => 
      rel.relationship === 'spouse of' || rel.relationship === 'married to'
    );
    const parentChildRelationships = relationships.filter(rel => 
      rel.relationship === 'child of'
    );

    // Create marriage mappings
    const marriages = new Map<string, { spouse1: string; spouse2: string; children: string[] }>();
    const personToMarriages = new Map<string, string[]>();

    // Process marriages
    marriageRelationships.forEach(rel => {
      const marriageId = [rel.entity1, rel.entity2].sort().join('-marriage');
      if (!marriages.has(marriageId)) {
        marriages.set(marriageId, {
          spouse1: rel.entity1,
          spouse2: rel.entity2,
          children: []
        });
        
        // Track marriages for each person
        if (!personToMarriages.has(rel.entity1)) personToMarriages.set(rel.entity1, []);
        if (!personToMarriages.has(rel.entity2)) personToMarriages.set(rel.entity2, []);
        personToMarriages.get(rel.entity1)!.push(marriageId);
        personToMarriages.get(rel.entity2)!.push(marriageId);
      }
    });

    // Add children to marriages
    parentChildRelationships.forEach(rel => {
      const parent = rel.entity2;
      const child = rel.entity1;
      
      // Find marriages involving this parent
      const parentMarriages = personToMarriages.get(parent) || [];
      parentMarriages.forEach(marriageId => {
        const marriage = marriages.get(marriageId);
        if (marriage && !marriage.children.includes(child)) {
          marriage.children.push(child);
        }
      });
    });

    // Calculate generations for proper layout
    const generations = new Map<string, number>();
    const visited = new Set<string>();
    
    // Find root person (person with most connections or first person)
    const personConnections = new Map<string, number>();
    relationships.forEach(rel => {
      personConnections.set(rel.entity1, (personConnections.get(rel.entity1) || 0) + 1);
      personConnections.set(rel.entity2, (personConnections.get(rel.entity2) || 0) + 1);
    });
    
    const rootPerson = Array.from(personConnections.entries())
      .sort((a, b) => b[1] - a[1])[0]?.[0] || Array.from(personDetails.keys())[0];
    
    // BFS to assign generations
    const queue: { person: string; generation: number }[] = [{ person: rootPerson, generation: 0 }];
    generations.set(rootPerson, 0);
    
    while (queue.length > 0) {
      const { person, generation } = queue.shift()!;
      if (visited.has(person)) continue;
      visited.add(person);
      
      parentChildRelationships.forEach(rel => {
        if (rel.entity2 === person && !generations.has(rel.entity1)) {
          generations.set(rel.entity1, generation + 1);
          queue.push({ person: rel.entity1, generation: generation + 1 });
        } else if (rel.entity1 === person && !generations.has(rel.entity2)) {
          generations.set(rel.entity2, generation - 1);
          queue.push({ person: rel.entity2, generation: generation - 1 });
        }
      });
    }

    // Assign generations to spouses (same generation)
    marriageRelationships.forEach(rel => {
      const gen1 = generations.get(rel.entity1);
      const gen2 = generations.get(rel.entity2);
      if (gen1 !== undefined && gen2 === undefined) {
        generations.set(rel.entity2, gen1);
      } else if (gen2 !== undefined && gen1 === undefined) {
        generations.set(rel.entity1, gen2);
      }
    });

    // Layout by generations - create person nodes first
    const generationPersons = new Map<number, string[]>();
    const generationMarriages = new Map<number, string[]>();

    // Group people by generation (only those with details)
    Array.from(personDetails.keys()).forEach(person => {
      const generation = generations.get(person) || 0;
      if (!generationPersons.has(generation)) {
        generationPersons.set(generation, []);
      }
      generationPersons.get(generation)!.push(person);
    });

    // Group marriages by generation
    Array.from(marriages.entries()).forEach(([marriageId, marriage]) => {
      const gen1 = generations.get(marriage.spouse1) || 0;
      const gen2 = generations.get(marriage.spouse2) || 0;
      const generation = Math.min(gen1, gen2);
      
      if (!generationMarriages.has(generation)) {
        generationMarriages.set(generation, []);
      }
      generationMarriages.get(generation)!.push(marriageId);
    });

    // Create nodes with proper positioning
    Array.from(generationPersons.entries()).forEach(([generation, people]) => {
      const marriagesInGen = generationMarriages.get(generation) || [];
      const marriedPeople = new Set<string>();
      
      // Track which people are in marriages in this generation
      marriagesInGen.forEach(marriageId => {
        const marriage = marriages.get(marriageId)!;
        marriedPeople.add(marriage.spouse1);
        marriedPeople.add(marriage.spouse2);
      });

      let xOffset = 100;
      
      // Position marriages and their participants
      marriagesInGen.forEach(marriageId => {
        const marriage = marriages.get(marriageId)!;
        
        // Only create marriage node if both spouses have details
        const spouse1Details = personDetails.get(marriage.spouse1);
        const spouse2Details = personDetails.get(marriage.spouse2);
        if (!spouse1Details || !spouse2Details) return;
        
        const y = generation * 200 + 300;
        
        // Position spouses
        const spouse1X = xOffset;
        const spouse2X = xOffset + 280;
        const marriageX = xOffset + 140;
        
        nodePositions.set(marriage.spouse1, { x: spouse1X, y });
        nodePositions.set(marriage.spouse2, { x: spouse2X, y });
        nodePositions.set(marriageId, { x: marriageX, y });
        
        // Create spouse nodes
        const spouseDetails = [spouse1Details, spouse2Details];
        [marriage.spouse1, marriage.spouse2].forEach((person, index) => {
          const details = spouseDetails[index];
          
          newNodes.push({
            id: person,
            type: 'person',
            position: { x: index === 0 ? spouse1X : spouse2X, y },
            data: {
              label: details.entity,
              entity: details.entity,
              qid: details.qid,
              birth_year: details.birth_year,
              death_year: details.death_year,
              image_url: details.image_url,
              nodeType: 'entity' as const,
            },
          });
        });

        // Create marriage node
        newNodes.push({
          id: marriageId,
          type: 'marriage',
          position: { x: marriageX, y },
          data: {
            label: '♥',
            spouse1: marriage.spouse1,
            spouse2: marriage.spouse2,
            nodeType: 'marriage' as const,
          },
        });

        // Connect spouses to marriage node
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

        xOffset += 350;
      });

      // Position unmarried people
      const unmarriedPeople = people.filter(person => !marriedPeople.has(person));
      unmarriedPeople.forEach(person => {
        const details = personDetails.get(person);
        if (!details) return; // Skip if no details available
        
        const y = generation * 200 + 300;
        const x = xOffset;
        
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
          },
        });

        xOffset += 320;
      });
    });

    // Create parent-child relationships
    parentChildRelationships.forEach((rel, index) => {
      const parent = rel.entity2;
      const child = rel.entity1;
      
      // Only create edges if both parent and child have details
      if (!personDetails.has(parent) || !personDetails.has(child)) return;
      
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
      
      const sourcePos = nodePositions.get(sourceId);
      const targetPos = nodePositions.get(child);
      
      if (sourcePos && targetPos) {
        newEdges.push({
          id: `parent-child-${index}`,
          source: sourceId,
          target: child,
          type: 'smoothstep',
          style: {
            stroke: '#6b7280',
            strokeWidth: 2,
          },
        });
      }
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [personDetails, relationships, setNodes, setEdges]);

  return (
    <div className="w-full h-screen">
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-md max-w-md">
        <h2 className="text-lg font-bold mb-2">Genealogy Tree Generator</h2>
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
          <p>Marriages: {relationships.filter(r => r.relationship === 'spouse of').length / 2}</p>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          <p>💙 Gray edges: Parent-child relationships</p>
          <p>💖 Pink edges: Marriage relationships</p>
          <p>💕 Pink circles: Marriage nodes</p>
        </div>
      </div>
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Controls />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}