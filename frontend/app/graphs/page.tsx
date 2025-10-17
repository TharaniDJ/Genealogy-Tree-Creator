"use client";

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';
import AuthGuard from '@/components/AuthGuard';

type GraphType = 'language' | 'species' | 'family' | 'all';

interface SavedGraph {
  id: string;
  graph_name: string;
  graph_type: 'language' | 'species' | 'family';
  depth_usage: boolean;
  depth?: number;
  description?: string;
  nodes_count: number;
  created_at: string;
  updated_at: string;
}

const GraphsPage = () => {
  const router = useRouter();
  const { getToken } = useAuth();
  
  const [graphs, setGraphs] = useState<SavedGraph[]>([]);
  const [filteredGraphs, setFilteredGraphs] = useState<SavedGraph[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<GraphType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'size'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fetch all graphs
  const fetchGraphs = useCallback(async () => {
    setLoading(true);
    try {
      const token = getToken();
      if (!token) {
        router.push('/login');
        return;
      }

      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
      const response = await fetch(`${apiBase}/api/users/graphs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch graphs');
      }

      const data = await response.json();
      setGraphs(data);
      setFilteredGraphs(data);
    } catch (error) {
      console.error('Error fetching graphs:', error);
      alert('Failed to load graphs. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [getToken, router]);

  useEffect(() => {
    fetchGraphs();
  }, [fetchGraphs]);

  // Filter and sort graphs
  useEffect(() => {
    let filtered = [...graphs];

    // Filter by type
    if (selectedType !== 'all') {
      filtered = filtered.filter(g => g.graph_type === selectedType);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(g => 
        g.graph_name.toLowerCase().includes(query) ||
        g.description?.toLowerCase().includes(query)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.graph_name.localeCompare(b.graph_name);
          break;
        case 'date':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
        case 'size':
          comparison = a.nodes_count - b.nodes_count;
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

    setFilteredGraphs(filtered);
  }, [graphs, selectedType, searchQuery, sortBy, sortOrder]);

  // Open graph in corresponding page
  const handleOpenGraph = (graph: SavedGraph) => {
    const routes = {
      language: '/language_tree',
      species: '/taxonomy_tree',
      family: '/family_tree'
    };

    const route = routes[graph.graph_type];
    // Pass graph ID via query parameter for auto-loading
    router.push(`${route}?loadGraph=${graph.id}`);
  };

  // Delete graph
  const handleDeleteGraph = async (graphId: string, graphName: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent opening the graph
    
    if (!confirm(`Are you sure you want to delete "${graphName}"? This cannot be undone.`)) {
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

      // Refresh the list
      fetchGraphs();
      alert('Graph deleted successfully');
    } catch (error) {
      console.error('Error deleting graph:', error);
      alert('Failed to delete graph. Please try again.');
    }
  };

  // Get graph type icon and color
  const getGraphTypeInfo = (type: string) => {
    switch (type) {
      case 'language':
        return {
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          ),
          label: 'Language',
          color: 'from-blue-500 to-cyan-500',
          bgColor: 'bg-blue-500/10',
          borderColor: 'border-blue-500/30'
        };
      case 'species':
        return {
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          label: 'Species',
          color: 'from-green-500 to-emerald-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/30'
        };
      case 'family':
        return {
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          ),
          label: 'Family',
          color: 'from-purple-500 to-pink-500',
          bgColor: 'bg-purple-500/10',
          borderColor: 'border-purple-500/30'
        };
      default:
        return {
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          ),
          label: 'Graph',
          color: 'from-gray-500 to-gray-600',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/30'
        };
    }
  };

  // Stats
  const stats = {
    total: graphs.length,
    language: graphs.filter(g => g.graph_type === 'language').length,
    species: graphs.filter(g => g.graph_type === 'species').length,
    family: graphs.filter(g => g.graph_type === 'family').length
  };

  return (
    <div className="min-h-screen w-full bg-[#0E0F19] relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Header */}
      <div className="relative backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] rounded-xl flex items-center justify-center shadow-lg shadow-[#6B72FF]/30">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
                  My Graphs
                </h1>
                <p className="text-sm text-[#9CA3B5] mt-1">
                  View and manage all your saved genealogy trees
                </p>
              </div>
            </div>

            <button
              onClick={() => router.push('/select')}
              className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-xl transition-all duration-200 shadow-lg hover:scale-105"
            >
              ← Back to Home
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className={`p-4 rounded-xl backdrop-blur-lg border transition-all cursor-pointer ${
              selectedType === 'all' 
                ? 'bg-[#6B72FF]/20 border-[#6B72FF]/50' 
                : 'bg-white/5 border-white/10 hover:bg-white/10'
            }`}
              onClick={() => setSelectedType('all')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#9CA3B5]">Total Graphs</p>
                  <p className="text-2xl font-bold text-[#F5F7FA] mt-1">{stats.total}</p>
                </div>
                <div className="w-10 h-10 flex items-center justify-center">
                  <svg className="w-8 h-8 text-[#6B72FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className={`p-4 rounded-xl backdrop-blur-lg border transition-all cursor-pointer ${
              selectedType === 'language' 
                ? 'bg-blue-500/20 border-blue-500/50' 
                : 'bg-white/5 border-white/10 hover:bg-white/10'
            }`}
              onClick={() => setSelectedType('language')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#9CA3B5]">Language Trees</p>
                  <p className="text-2xl font-bold text-[#F5F7FA] mt-1">{stats.language}</p>
                </div>
                <div className="w-10 h-10 flex items-center justify-center">
                  <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                </div>
              </div>
            </div>

            <div className={`p-4 rounded-xl backdrop-blur-lg border transition-all cursor-pointer ${
              selectedType === 'species' 
                ? 'bg-green-500/20 border-green-500/50' 
                : 'bg-white/5 border-white/10 hover:bg-white/10'
            }`}
              onClick={() => setSelectedType('species')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#9CA3B5]">Species Trees</p>
                  <p className="text-2xl font-bold text-[#F5F7FA] mt-1">{stats.species}</p>
                </div>
                <div className="w-10 h-10 flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className={`p-4 rounded-xl backdrop-blur-lg border transition-all cursor-pointer ${
              selectedType === 'family' 
                ? 'bg-purple-500/20 border-purple-500/50' 
                : 'bg-white/5 border-white/10 hover:bg-white/10'
            }`}
              onClick={() => setSelectedType('family')}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#9CA3B5]">Family Trees</p>
                  <p className="text-2xl font-bold text-[#F5F7FA] mt-1">{stats.family}</p>
                </div>
                <div className="w-10 h-10 flex items-center justify-center">
                  <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Search and Sort Controls */}
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search graphs by name or description..."
                  className="w-full px-4 py-3 pl-12 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all text-[#F5F7FA] placeholder-[#9CA3B5]"
                />
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Sort By */}
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'name' | 'date' | 'size')}
                className="px-4 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 text-[#F5F7FA] cursor-pointer"
              >
                <option value="date">Sort by Date</option>
                <option value="name">Sort by Name</option>
                <option value="size">Sort by Size</option>
              </select>

              <button
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                className="px-4 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all text-[#F5F7FA]"
                title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Graphs Grid */}
      <div className="relative max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-[#6B72FF]"></div>
          </div>
        ) : filteredGraphs.length === 0 ? (
          <div className="text-center py-20">
            <div className="mb-4 flex justify-center">
              <div className="w-20 h-20 bg-white/5 rounded-2xl flex items-center justify-center">
                <svg className="w-12 h-12 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
            <h3 className="text-xl font-semibold text-[#F5F7FA] mb-2">
              {searchQuery || selectedType !== 'all' ? 'No graphs found' : 'No graphs yet'}
            </h3>
            <p className="text-[#9CA3B5] mb-6">
              {searchQuery || selectedType !== 'all' 
                ? 'Try adjusting your filters or search query' 
                : 'Create your first genealogy tree to get started'}
            </p>
            {!searchQuery && selectedType === 'all' && (
              <button
                onClick={() => router.push('/select')}
                className="px-6 py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] text-white rounded-xl transition-all shadow-lg hover:scale-105"
              >
                Create a Graph
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredGraphs.map((graph) => {
              const typeInfo = getGraphTypeInfo(graph.graph_type);
              
              return (
                <div
                  key={graph.id}
                  onClick={() => handleOpenGraph(graph)}
                  className={`group relative p-6 rounded-2xl backdrop-blur-lg bg-white/5 border ${typeInfo.borderColor} hover:bg-white/10 transition-all duration-300 cursor-pointer hover:scale-105 hover:shadow-2xl`}
                >
                  {/* Type Badge */}
                  <div className="absolute top-4 right-4">
                    <div className={`px-3 py-1 rounded-lg text-xs font-medium ${typeInfo.bgColor} border ${typeInfo.borderColor} text-[#F5F7FA] flex items-center gap-1`}>
                      <span>{typeInfo.icon}</span>
                      <span>{typeInfo.label}</span>
                    </div>
                  </div>

                  {/* Graph Icon */}
                  <div className={`w-14 h-14 bg-gradient-to-br ${typeInfo.color} rounded-xl flex items-center justify-center mb-4 shadow-lg text-2xl`}>
                    {typeInfo.icon}
                  </div>

                  {/* Graph Info */}
                  <h3 className="text-lg font-bold text-[#F5F7FA] mb-2 pr-20 line-clamp-2 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-[#6B72FF] group-hover:to-[#8B7BFF] group-hover:bg-clip-text transition-all">
                    {graph.graph_name}
                  </h3>

                  {graph.description && (
                    <p className="text-sm text-[#9CA3B5] mb-4 line-clamp-2">
                      {graph.description}
                    </p>
                  )}

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-xs text-[#9CA3B5] mb-4">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      <span>{graph.nodes_count} nodes</span>
                    </div>
                    {graph.depth_usage && graph.depth && (
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        <span>Depth: {graph.depth}</span>
                      </div>
                    )}
                  </div>

                  {/* Date */}
                  <div className="flex items-center gap-2 text-xs text-[#9CA3B5] mb-4">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>Updated {new Date(graph.updated_at).toLocaleDateString()}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenGraph(graph);
                      }}
                      className={`flex-1 px-4 py-2 bg-gradient-to-r ${typeInfo.color} hover:opacity-90 text-white rounded-lg transition-all text-sm font-medium shadow-lg`}
                    >
                      Open
                    </button>
                    <button
                      onClick={(e) => handleDeleteGraph(graph.id, graph.graph_name, e)}
                      className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded-lg transition-all text-sm font-medium"
                      title="Delete graph"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default function ProtectedGraphsPage() {
  return (
    <AuthGuard>
      <GraphsPage />
    </AuthGuard>
  );
}
