'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import GenealogyTree from '@/components/GenealogyTree';
import VerticalNavbar from '@/components/VerticalNavbar';
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
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
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
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
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
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
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
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
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

  // Auto-load graph from URL parameter
  useEffect(() => {
    const loadGraphId = searchParams.get('loadGraph');
    if (loadGraphId && connectionStatus === 'connected') {
      // Auto-load the graph
      handleLoadGraph(loadGraphId);
      // Clean up URL parameter
      router.replace('/family_tree', { scroll: false });
    }
  }, [searchParams, connectionStatus, handleLoadGraph, router]);

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
    <main className="w-full h-screen flex flex-col overflow-hidden relative bg-[#0E0F19]">
      {/* Vertical Navbar */}
      <VerticalNavbar />
      
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Modern Dark Header with Glass Effect */}
      <div className="relative backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10">
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] rounded-xl flex items-center justify-center shadow-lg shadow-[#6B72FF]/30">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h1 className="text-[20px] font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
                Family Tree Explorer
              </h1>
            </div>
            
            {/* Connection Status with Modern Badge */}
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1.5 rounded-lg text-[12px] font-medium backdrop-blur-lg bg-white/5 border ${
                connectionStatus === 'connected' 
                  ? 'border-emerald-500/30 text-emerald-300' 
                  : connectionStatus === 'connecting'
                  ? 'border-amber-500/30 text-amber-300'
                  : 'border-red-500/30 text-red-300'
              }`}>
                <div className="flex items-center space-x-1.5">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 
                    connectionStatus === 'connecting' ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)] animate-pulse' : 
                    'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]'
                  }`}></div>
                  <span>{getConnectionStatusText()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Search Controls in Modern Card Layout */}
          <div className="flex items-center space-x-4 flex-wrap">
            {/* Person Name Input */}
            <div className="flex-1 min-w-48">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter person's name..."
                  className="w-full text-[12px] px-4 py-3 pl-10 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] placeholder-[#9CA3B5]"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      startGenealogySearch();
                    }
                  }}
                />
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Depth Input */}
            <div className="w-24">
              <input
                type="number"
                value={searchDepth}
                onChange={(e) => setSearchDepth(parseInt(e.target.value, 10))}
                placeholder="Depth"
                min="1"
                max="4"
                className="w-full text-[12px] px-3 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] text-center"
              />
            </div>

            {/* Search Button */}
            <button
              onClick={startGenealogySearch}
              disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
              className="px-6 text-[12px] py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>{connectionStatus === 'connected' ? 'Explore Tree' : 'Connecting...'}</span>
              </div>
            </button>
          </div>
        </div>
      </div>
      
      {/* React Flow Container with Modern Styling */}
      <div className="flex-1 relative">
        <GenealogyTree 
          websocketData={websocketData} 
          onExpandNode={handleExpandNode}
          onExpandNodeByQid={handleExpandNodeByQid}
          onClassifyRelationships={handleClassifyRelationships}
          expandDepth={2}
          triggerFitView={triggerFitView}
          onSaveGraph={openSaveModal}
          onLoadGraph={openLoadModal}
          onClearGraph={clearMessages}
          graphDataLength={currentGraphData.length}
        />
      </div>

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
                  This will save {currentGraphData.length} family relationships
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
                          <span>{graph.nodes_count} items</span>
                          {graph.depth_usage && <span>Depth: {graph.depth}</span>}
                          <span>{new Date(graph.updated_at).toLocaleDateString()}</span>
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