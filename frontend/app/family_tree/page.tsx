'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import GenealogyTree from '@/components/GenealogyTree';
import { useWebSocket } from '@/hooks/useWebSocket';
import useAuth from '@/hooks/useAuth';
import AuthGuard from '@/components/AuthGuard';

function FamilyTreePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { getToken } = useAuth();
  
  // WebSocket connection for real-time data through API Gateway
  const wsBase = process.env.NEXT_PUBLIC_FAMILY_API_URL || 'http://localhost:8080/api/family';
  const wsUrl = wsBase.replace(/^http/, 'ws') + '/ws';
  
  const { 
    messages: websocketData, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearMessages,
    sendMessage,
    addMessages
  } = useWebSocket(wsUrl, { token: getToken() });

  const [searchQuery, setSearchQuery] = useState('Albert Einstein');
  const [searchDepth, setSearchDepth] = useState(2);

  // Graph saving state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [graphName, setGraphName] = useState('');
  const [graphDescription, setGraphDescription] = useState('');
  const [savedGraphs, setSavedGraphs] = useState<any[]>([]);
  const [loadingGraphs, setLoadingGraphs] = useState(false);
  const [savingGraph, setSavingGraph] = useState(false);
  const [currentGraphData, setCurrentGraphData] = useState<any[]>([]);
  const [triggerFitView, setTriggerFitView] = useState(0);

  // Function to start genealogy search
  const startGenealogySearch = () => {
    if (connectionStatus === 'connected' && searchQuery.trim()) {
      // Convert search query to Wikipedia page title format (replace spaces with underscores)
      const pageTitle = searchQuery.trim().replace(/\s+/g, '_');
      
      // Send search request to backend in the required format
      sendMessage({
        action: "fetch_relationships",
        page_title: pageTitle,
        depth: searchDepth
      });
    }
  };

  // Handle expand node functionality (for initial name-based searches)
  const handleExpandNode = useCallback((personName: string, depth: number) => {
    if (connectionStatus === 'connected') {
      sendMessage({
        action: "fetch_relationships",
        page_title: personName,
        depth: depth
      });
    }
  }, [connectionStatus, sendMessage]);

  // NEW: Handle QID-based expansion (for node expansion)
  const handleExpandNodeByQid = useCallback((qid: string, depth: number, entityName?: string) => {
    if (connectionStatus !== 'connected') {
      console.error('WebSocket not connected');
      return;
    }

    try {
      console.log(`Sending QID expansion request: ${qid}, depth: ${depth}, entity: ${entityName}`);
      
      // Send QID expansion request to backend
      sendMessage({
        action: "expand_by_qid",
        qid: qid,
        depth: depth,
        entity_name: entityName
      });
      
    } catch (error) {
      console.error('Error sending QID expansion request:', error);
    }
  }, [connectionStatus, sendMessage]);

  // Add this handler in page.tsx, after handleExpandNodeByQid
const handleClassifyRelationships = useCallback((relationships: any[]) => {
  if (connectionStatus !== 'connected') {
    console.error('WebSocket not connected');
    return;
  }

  try {
    console.log(`Sending classification request for ${relationships.length} relationships`);
    
    sendMessage({
      action: "classify_relationships",
      relationships: relationships
    });
    
  } catch (error) {
    console.error('Error sending classification request:', error);
  }
}, [connectionStatus, sendMessage]);
  // Track graph data for saving
  useEffect(() => {
    setCurrentGraphData(websocketData);
  }, [websocketData]);

  // Save graph to backend
  const handleSaveGraph = useCallback(async () => {
    if (!graphName.trim()) {
      alert('Please enter a graph name');
      return;
    }

    if (currentGraphData.length === 0) {
      alert('Cannot save an empty graph');
      return;
    }

    setSavingGraph(true);
    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      
      const response = await fetch(`${apiBase}/api/users/graphs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          graph_name: graphName,
          graph_type: 'family',
          depth_usage: searchDepth > 0,
          depth: searchDepth > 0 ? searchDepth : undefined,
          graph_data: currentGraphData,
          description: graphDescription || undefined
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save graph');
      }

      alert(`Graph "${graphName}" saved successfully!`);
      setShowSaveModal(false);
      setGraphName('');
      setGraphDescription('');
    } catch (error: any) {
      console.error('Error saving graph:', error);
      alert(`Failed to save graph: ${error.message}`);
    } finally {
      setSavingGraph(false);
    }
  }, [graphName, graphDescription, currentGraphData, searchDepth, getToken]);

  // Load saved graphs list
  const loadSavedGraphs = useCallback(async () => {
    setLoadingGraphs(true);
    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      
      const response = await fetch(`${apiBase}/api/users/graphs?graph_type=family`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load saved graphs');
      }

      const graphs = await response.json();
      setSavedGraphs(graphs);
    } catch (error: any) {
      console.error('Error loading graphs:', error);
      alert(`Failed to load saved graphs: ${error.message}`);
    } finally {
      setLoadingGraphs(false);
    }
  }, [getToken]);

  // Load a specific graph
  const handleLoadGraph = useCallback(async (graphId: string) => {
    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      
      const response = await fetch(`${apiBase}/api/users/graphs/${graphId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load graph');
      }

      const graph = await response.json();
      
      // Clear current data and load saved graph
      clearMessages();
      
      // Add loaded messages to trigger tree rendering
      addMessages(graph.graph_data);

      // Trigger fitView after a short delay to allow the tree to render
      setTimeout(() => {
        setTriggerFitView(prev => prev + 1);
      }, 500);

      alert(`Loaded "${graph.graph_name}" with ${graph.graph_data.length} items`);
      setShowLoadModal(false);
    } catch (error: any) {
      console.error('Error loading graph:', error);
      alert(`Failed to load graph: ${error.message}`);
    }
  }, [getToken, clearMessages, addMessages]);

  // Delete a saved graph
  const handleDeleteGraph = useCallback(async (graphId: string, graphName: string) => {
    if (!confirm(`Are you sure you want to delete "${graphName}"?`)) {
      return;
    }

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      
      const response = await fetch(`${apiBase}/api/users/graphs/${graphId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete graph');
      }

      loadSavedGraphs();
      alert('Graph deleted successfully');
    } catch (error: any) {
      console.error('Error deleting graph:', error);
      alert(`Failed to delete graph: ${error.message}`);
    }
  }, [getToken, loadSavedGraphs]);

  // Open save modal
  const openSaveModal = useCallback(() => {
    if (currentGraphData.length === 0) {
      alert('Cannot save an empty graph. Please create a graph first.');
      return;
    }
    setGraphName(`${searchQuery} Family Tree - ${new Date().toLocaleDateString()}`);
    setGraphDescription('');
    setShowSaveModal(true);
  }, [currentGraphData.length, searchQuery]);

  // Open load modal
  const openLoadModal = useCallback(() => {
    setShowLoadModal(true);
    loadSavedGraphs();
  }, [loadSavedGraphs]);

  // Auto-connect on component mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Connection Error';
      default: return 'Disconnected';
    }
  };

  return (
    <main className="w-full h-screen overflow-hidden relative bg-[#0E0F19]">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-1/3 -right-48 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      {/* Control Panel - Fixed position */}
      <div className="absolute top-4 right-4 z-20 backdrop-blur-xl bg-white/5 border border-white/10 p-6 rounded-2xl shadow-2xl max-w-sm">
        <h1 className="text-xl font-bold mb-4 text-[#F5F7FA]">Family Tree Explorer</h1>
        
        {/* Connection Status */}
        <div className="mb-4 p-3 backdrop-blur-md bg-white/5 border border-white/10 rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#9CA3B5]">WebSocket Status:</span>
            <span className={getConnectionStatusColor()}>
              {getConnectionStatusText()}
            </span>
          </div>
        </div>

        {/* Search Input */}
        <div className="mb-4">
          <label htmlFor="search" className="block text-sm font-medium text-[#9CA3B5] mb-2">
            Search Person
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter person's name (e.g., Albert Einstein)"
            className="w-full px-4 py-2.5 backdrop-blur-md bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] focus:border-transparent text-[#F5F7FA] placeholder-[#9CA3B5]/50"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                startGenealogySearch();
              }
            }}
          />
        </div>

        {/* Depth Control */}
        <div className="mb-4">
          <label htmlFor="depth" className="block text-sm font-medium text-[#9CA3B5] mb-2">
            Search Depth: {searchDepth}
          </label>
          <input
            id="depth"
            type="range"
            min="1"
            max="4"
            value={searchDepth}
            onChange={(e) => setSearchDepth(parseInt(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#6B72FF]"
          />
          <div className="flex justify-between text-xs text-[#9CA3B5] mt-1">
            <span>1 (Close)</span>
            <span>4 (Extended)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={startGenealogySearch}
            disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white rounded-lg hover:shadow-lg hover:shadow-[#6B72FF]/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Search Genealogy Tree
          </button>

          <div className="flex gap-2">
            <button
              onClick={openSaveModal}
              disabled={currentGraphData.length === 0}
              className="flex-1 px-4 py-2.5 backdrop-blur-md bg-green-500/20 border border-green-500/30 text-green-400 rounded-lg hover:bg-green-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              💾 Save
            </button>
            <button
              onClick={openLoadModal}
              className="flex-1 px-4 py-2.5 backdrop-blur-md bg-amber-500/20 border border-amber-500/30 text-amber-400 rounded-lg hover:bg-amber-500/30 transition-all"
            >
              📂 Load
            </button>
          </div>

          <button
            onClick={() => {
              if (connectionStatus === 'connected') {
                sendMessage({
                  action: "fetch_relationships",
                  page_title: "Albert_Einstein",
                  depth: 2
                });
              }
            }}
            disabled={connectionStatus !== 'connected'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-[#8B7BFF]/20 border border-[#8B7BFF]/30 text-[#F5F7FA] rounded-lg hover:bg-[#8B7BFF]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Test Albert Einstein
          </button>
          
          <button
            onClick={connect}
            disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Connect to Server
          </button>
          
          <button
            onClick={disconnect}
            disabled={connectionStatus === 'disconnected'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-orange-500/20 border border-orange-500/30 text-orange-400 rounded-lg hover:bg-orange-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>
          
          <button
            onClick={clearMessages}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/30 transition-all"
          >
            Clear Tree Data
          </button>
        </div>

        {/* Data Statistics */}
        <div className="mt-4 text-sm text-[#9CA3B5] backdrop-blur-md bg-white/5 border border-white/10 p-3 rounded-lg">
          <p>Messages received: {websocketData.length}</p>
          <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
          <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
          <p className="text-[#8B7BFF] font-medium">QID-based expansion enabled</p>
        </div>

        {/* Recent Messages (Debug) */}
        {websocketData.length > 0 && (
          <div className="mt-4 text-xs text-[#9CA3B5] backdrop-blur-md bg-white/5 border border-white/10 p-3 rounded-lg max-h-32 overflow-y-auto">
            <p className="font-semibold mb-2 text-[#F5F7FA]">Recent Messages:</p>
            {websocketData.slice(-3).map((msg, index) => (
              <div key={index} className="mb-2 p-2 backdrop-blur-sm bg-white/5 border border-white/10 rounded text-xs">
                <span className="font-medium text-[#6B72FF]">{msg.type}:</span> <span className="text-[#9CA3B5]">{JSON.stringify(msg.data).slice(0, 50)}...</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Genealogy Tree - Takes full screen with BOTH expansion handlers */}
      <GenealogyTree 
        websocketData={websocketData} 
        onExpandNode={handleExpandNode}          // For initial name-based searches
        onExpandNodeByQid={handleExpandNodeByQid} // For QID-based node expansion
        onClassifyRelationships={handleClassifyRelationships}  // ADD THIS LINE
        expandDepth={2}                          // Default expansion depth for nodes
        triggerFitView={triggerFitView}         // Trigger fitView after loading
      />

      {/* Save Graph Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Save Family Tree</h2>
              <button
                onClick={() => setShowSaveModal(false)}
                className="text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="graphName" className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Graph Name *
                </label>
                <input
                  id="graphName"
                  type="text"
                  value={graphName}
                  onChange={(e) => setGraphName(e.target.value)}
                  placeholder="e.g., Einstein Family Tree"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5]"
                />
              </div>
              
              <div>
                <label htmlFor="graphDescription" className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Description (Optional)
                </label>
                <textarea
                  id="graphDescription"
                  value={graphDescription}
                  onChange={(e) => setGraphDescription(e.target.value)}
                  placeholder="Add notes about this family tree..."
                  rows={3}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5] resize-none"
                />
              </div>

              <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
                <p className="text-sm text-[#9CA3B5]">
                  💾 This will save {currentGraphData.length} family relationships
                  {searchDepth > 0 && ` (depth: ${searchDepth})`}
                </p>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowSaveModal(false)}
                disabled={savingGraph}
                className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveGraph}
                disabled={!graphName.trim() || savingGraph}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg transition-all disabled:cursor-not-allowed shadow-lg"
              >
                {savingGraph ? 'Saving...' : 'Save Graph'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Graph Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Load Saved Family Tree</h2>
              <button
                onClick={() => setShowLoadModal(false)}
                className="text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {loadingGraphs ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#6B72FF]"></div>
              </div>
            ) : savedGraphs.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 mx-auto text-[#9CA3B5] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                <p className="text-[#9CA3B5]">No saved family trees found</p>
                <p className="text-sm text-[#9CA3B5] mt-2">Create and save a tree to see it here</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {savedGraphs.map((graph) => (
                  <div
                    key={graph.id}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-[#F5F7FA] font-semibold">{graph.graph_name}</h3>
                        {graph.description && (
                          <p className="text-sm text-[#9CA3B5] mt-1">{graph.description}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-[#9CA3B5]">
                          <span>👥 {graph.nodes_count} items</span>
                          {graph.depth_usage && <span>🔍 Depth: {graph.depth}</span>}
                          <span>📅 {new Date(graph.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleLoadGraph(graph.id)}
                          className="px-3 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg transition-all text-sm"
                        >
                          Load
                        </button>
                        <button
                          onClick={() => handleDeleteGraph(graph.id, graph.graph_name)}
                          className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-all text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6">
              <button
                onClick={() => setShowLoadModal(false)}
                className="w-full px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

// Wrap with AuthGuard for authentication
export default function ProtectedFamilyTree() {
  return (
    <AuthGuard>
      <FamilyTreePage />
    </AuthGuard>
  );
}