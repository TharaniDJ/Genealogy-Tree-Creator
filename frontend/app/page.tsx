// 'use client';

// import React, { useState, useEffect } from 'react';
// import GenealogyTree from '@/components/GenealogyTree';
// import { useWebSocket } from '@/hooks/useWebSocket';

// export default function Home() {
//   // WebSocket connection for real-time data
//   const { 
//     messages: websocketData, 
//     connectionStatus, 
//     connect, 
//     disconnect, 
//     clearMessages,
//     sendMessage 
//   } = useWebSocket('ws://localhost:8000/ws');

//   const [searchQuery, setSearchQuery] = useState('Albert Einstein');
//   const [searchDepth, setSearchDepth] = useState(2);

//   // Function to start genealogy search
//   const startGenealogySearch = () => {
//     if (connectionStatus === 'connected' && searchQuery.trim()) {
//       // Convert search query to Wikipedia page title format (replace spaces with underscores)
//       const pageTitle = searchQuery.trim().replace(/\s+/g, '_');
      
//       // Send search request to backend in the required format
//       sendMessage({
//         action: "fetch_relationships",
//         page_title: pageTitle,
//         depth: searchDepth
//       });
//     }
//   };

//   // Auto-connect on component mount
//   useEffect(() => {
//     connect();
//     return () => {
//       disconnect();
//     };
//   }, [connect, disconnect]);

//   const getConnectionStatusColor = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'text-green-600';
//       case 'connecting': return 'text-yellow-600';
//       case 'error': return 'text-red-600';
//       default: return 'text-gray-600';
//     }
//   };

//   const getConnectionStatusText = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'Connected';
//       case 'connecting': return 'Connecting...';
//       case 'error': return 'Connection Error';
//       default: return 'Disconnected';
//     }
//   };

//   return (
//     <main className="min-h-screen bg-gray-50">

//       <div className="absolute top-4 right-4 z-20 bg-white p-4 rounded-lg shadow-md max-w-sm">
//         <h1 className="text-xl font-bold mb-4">Genealogy Tree Creator</h1>
        
//         {/* Connection Status */}
//         <div className="mb-4 p-2 bg-gray-50 rounded">
//           <div className="flex items-center justify-between text-sm">
//             <span>WebSocket Status:</span>
//             <span className={getConnectionStatusColor()}>
//               {getConnectionStatusText()}
//             </span>
//           </div>
//         </div>

//         {/* Search Input */}
//         <div className="mb-4">
//           <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Person
//           </label>
//           <input
//             id="search"
//             type="text"
//             value={searchQuery}
//             onChange={(e) => setSearchQuery(e.target.value)}
//             placeholder="Enter person's name (e.g., Albert Einstein)"
//             className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//             onKeyPress={(e) => {
//               if (e.key === 'Enter') {
//                 startGenealogySearch();
//               }
//             }}
//           />
//         </div>

//         {/* Depth Control */}
//         <div className="mb-4">
//           <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Depth: {searchDepth}
//           </label>
//           <input
//             id="depth"
//             type="range"
//             min="1"
//             max="4"
//             value={searchDepth}
//             onChange={(e) => setSearchDepth(parseInt(e.target.value))}
//             className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
//           />
//           <div className="flex justify-between text-xs text-gray-500 mt-1">
//             <span>1 (Close)</span>
//             <span>4 (Extended)</span>
//           </div>
//         </div>

//         {/* Action Buttons */}
//         <div className="space-y-2">
//           <button
//             onClick={startGenealogySearch}
//             disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
//             className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Search Genealogy Tree
//           </button>

//           <button
//             onClick={() => {
//               if (connectionStatus === 'connected') {
//                 sendMessage({
//                   action: "fetch_relationships",
//                   page_title: "Albert_Einstein",
//                   depth: 2
//                 });
//               }
//             }}
//             disabled={connectionStatus !== 'connected'}
//             className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Test Albert Einstein
//           </button>
          
//           <button
//             onClick={connect}
//             disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
//             className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Connect to Server
//           </button>
          
//           <button
//             onClick={disconnect}
//             disabled={connectionStatus === 'disconnected'}
//             className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Disconnect
//           </button>
          
//           <button
//             onClick={clearMessages}
//             className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
//           >
//             Clear Tree Data
//           </button>
//         </div>

//         {/* Data Statistics */}
//         <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-2 rounded">
//           <p>Messages received: {websocketData.length}</p>
//           <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
//           <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
//         </div>

//         {/* Recent Messages (Debug) */}
//         {websocketData.length > 0 && (
//           <div className="mt-4 text-xs text-gray-600 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
//             <p className="font-semibold mb-1">Recent Messages:</p>
//             {websocketData.slice(-3).map((msg, index) => (
//               <div key={index} className="mb-1 p-1 bg-white rounded text-xs">
//                 <span className="font-medium">{msg.type}:</span> {JSON.stringify(msg.data).slice(0, 50)}...
//               </div>
//             ))}
//           </div>
//         )}
//       </div>
      
//       <GenealogyTree websocketData={websocketData} />
//     </main>
//   );
// }

// 'use client';

// import React, { useState, useEffect } from 'react';
// import GenealogyTree from '@/components/GenealogyTree';
// import { useWebSocket } from '@/hooks/useWebSocket';

// export default function Home() {
//   // WebSocket connection for real-time data
//   const { 
//     messages: websocketData, 
//     connectionStatus, 
//     connect, 
//     disconnect, 
//     clearMessages,
//     sendMessage 
//   } = useWebSocket('ws://localhost:8000/ws');

//   const [searchQuery, setSearchQuery] = useState('Albert Einstein');
//   const [searchDepth, setSearchDepth] = useState(2);

//   // Function to start genealogy search
//   const startGenealogySearch = () => {
//     if (connectionStatus === 'connected' && searchQuery.trim()) {
//       // Convert search query to Wikipedia page title format (replace spaces with underscores)
//       const pageTitle = searchQuery.trim().replace(/\s+/g, '_');
      
//       // Send search request to backend in the required format
//       sendMessage({
//         action: "fetch_relationships",
//         page_title: pageTitle,
//         depth: searchDepth
//       });
//     }
//   };

//   // Auto-connect on component mount
//   useEffect(() => {
//     connect();
//     return () => {
//       disconnect();
//     };
//   }, [connect, disconnect]);

//   const getConnectionStatusColor = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'text-green-600';
//       case 'connecting': return 'text-yellow-600';
//       case 'error': return 'text-red-600';
//       default: return 'text-gray-600';
//     }
//   };

//   const getConnectionStatusText = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'Connected';
//       case 'connecting': return 'Connecting...';
//       case 'error': return 'Connection Error';
//       default: return 'Disconnected';
//     }
//   };

//   return (
//     <main className="w-full h-screen overflow-hidden relative">
//       {/* Control Panel - Fixed position */}
//       <div className="absolute top-4 right-4 z-20 bg-white p-4 rounded-lg shadow-md max-w-sm">
//         <h1 className="text-xl font-bold mb-4">Genealogy Tree Creator</h1>
        
//         {/* Connection Status */}
//         <div className="mb-4 p-2 bg-gray-50 rounded">
//           <div className="flex items-center justify-between text-sm">
//             <span>WebSocket Status:</span>
//             <span className={getConnectionStatusColor()}>
//               {getConnectionStatusText()}
//             </span>
//           </div>
//         </div>

//         {/* Search Input */}
//         <div className="mb-4">
//           <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Person
//           </label>
//           <input
//             id="search"
//             type="text"
//             value={searchQuery}
//             onChange={(e) => setSearchQuery(e.target.value)}
//             placeholder="Enter person's name (e.g., Albert Einstein)"
//             className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//             onKeyPress={(e) => {
//               if (e.key === 'Enter') {
//                 startGenealogySearch();
//               }
//             }}
//           />
//         </div>

//         {/* Depth Control */}
//         <div className="mb-4">
//           <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Depth: {searchDepth}
//           </label>
//           <input
//             id="depth"
//             type="range"
//             min="1"
//             max="4"
//             value={searchDepth}
//             onChange={(e) => setSearchDepth(parseInt(e.target.value))}
//             className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
//           />
//           <div className="flex justify-between text-xs text-gray-500 mt-1">
//             <span>1 (Close)</span>
//             <span>4 (Extended)</span>
//           </div>
//         </div>

//         {/* Action Buttons */}
//         <div className="space-y-2">
//           <button
//             onClick={startGenealogySearch}
//             disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
//             className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Search Genealogy Tree
//           </button>

//           <button
//             onClick={() => {
//               if (connectionStatus === 'connected') {
//                 sendMessage({
//                   action: "fetch_relationships",
//                   page_title: "Albert_Einstein",
//                   depth: 2
//                 });
//               }
//             }}
//             disabled={connectionStatus !== 'connected'}
//             className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Test Albert Einstein
//           </button>
          
//           <button
//             onClick={connect}
//             disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
//             className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Connect to Server
//           </button>
          
//           <button
//             onClick={disconnect}
//             disabled={connectionStatus === 'disconnected'}
//             className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Disconnect
//           </button>
          
//           <button
//             onClick={clearMessages}
//             className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
//           >
//             Clear Tree Data
//           </button>
//         </div>

//         {/* Data Statistics */}
//         <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-2 rounded">
//           <p>Messages received: {websocketData.length}</p>
//           <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
//           <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
//         </div>

//         {/* Recent Messages (Debug) */}
//         {websocketData.length > 0 && (
//           <div className="mt-4 text-xs text-gray-600 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
//             <p className="font-semibold mb-1">Recent Messages:</p>
//             {websocketData.slice(-3).map((msg, index) => (
//               <div key={index} className="mb-1 p-1 bg-white rounded text-xs">
//                 <span className="font-medium">{msg.type}:</span> {JSON.stringify(msg.data).slice(0, 50)}...
//               </div>
//             ))}
//           </div>
//         )}
//       </div>
      
//       {/* Genealogy Tree - Takes full screen */}
//       <GenealogyTree websocketData={websocketData} />
//     </main>
//   );
// }

'use client';

import React, { useState, useEffect } from 'react';
import GenealogyTree from '@/components/GenealogyTree';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function Home() {
  // WebSocket connection for real-time data
  const { 
    messages: websocketData, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearMessages,
    sendMessage 
  } = useWebSocket('ws://localhost:8000/ws');

  const [searchQuery, setSearchQuery] = useState('Albert Einstein');
  const [searchDepth, setSearchDepth] = useState(2);

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

  // Handle expand node functionality
  const handleExpandNode = (personName: string, depth: number) => {
    if (connectionStatus === 'connected') {
      sendMessage({
        action: "fetch_relationships",
        page_title: personName,
        depth: depth
      });
    }
  };

  // Auto-connect on component mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'connecting': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'error': return 'bg-red-50 text-red-700 border-red-200';
      default: return 'bg-slate-50 text-slate-700 border-slate-200';
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
    <main className="w-full h-screen overflow-hidden relative bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Modern Control Panel with Glass Effect */}
      <div className="absolute top-4 right-4 z-20 bg-white/80 backdrop-blur-xl border border-white/20 shadow-lg shadow-blue-500/5 rounded-2xl p-6 max-w-sm">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-indigo-600/5 to-purple-600/5 rounded-2xl"></div>
        <div className="relative">
          {/* Header with Icon */}
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Genealogy Tree Creator
            </h1>
          </div>
          
          {/* Connection Status */}
          <div className="mb-6 p-3 bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl border border-blue-100">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700">Connection Status:</span>
              <div className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center space-x-1 ${getConnectionStatusColor()}`}>
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-emerald-500' : 
                  connectionStatus === 'connecting' ? 'bg-amber-500' : 'bg-red-500'
                }`}></div>
                <span>{getConnectionStatusText()}</span>
              </div>
            </div>
          </div>

          {/* Search Input */}
          <div className="mb-4">
            <label htmlFor="search" className="block text-sm font-semibold text-slate-700 mb-2">
              Search Person
            </label>
            <div className="relative">
              <input
                id="search"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter person's name (e.g., Albert Einstein)"
                className="w-full px-4 py-3 pl-10 bg-white/70 backdrop-blur-sm border border-blue-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all duration-200 shadow-sm hover:shadow-md text-slate-700 placeholder-slate-400"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    startGenealogySearch();
                  }
                }}
              />
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          {/* Depth Control */}
          <div className="mb-6">
            <label htmlFor="depth" className="block text-sm font-semibold text-slate-700 mb-2">
              Search Depth: <span className="text-blue-600">{searchDepth}</span>
            </label>
            <input
              id="depth"
              type="range"
              min="1"
              max="4"
              value={searchDepth}
              onChange={(e) => setSearchDepth(parseInt(e.target.value))}
              className="w-full h-2 bg-gradient-to-r from-blue-200 to-indigo-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>1 (Close)</span>
              <span>4 (Extended)</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 mb-4">
            <button
              onClick={startGenealogySearch}
              disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
              className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Search Genealogy Tree</span>
              </div>
            </button>

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
              className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center justify-center space-x-2">
                <span>🧪</span>
                <span>Test Albert Einstein</span>
              </div>
            </button>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={connect}
                disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
                className="px-3 py-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium rounded-lg transition-all duration-200 shadow-sm hover:shadow-md disabled:cursor-not-allowed text-sm transform hover:scale-105 disabled:hover:scale-100"
              >
                Connect
              </button>
              
              <button
                onClick={disconnect}
                disabled={connectionStatus === 'disconnected'}
                className="px-3 py-2 bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium rounded-lg transition-all duration-200 shadow-sm hover:shadow-md disabled:cursor-not-allowed text-sm transform hover:scale-105 disabled:hover:scale-100"
              >
                Disconnect
              </button>
            </div>
            
            <button
              onClick={clearMessages}
              className="w-full px-4 py-2 bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-medium rounded-lg transition-all duration-200 shadow-sm hover:shadow-md transform hover:scale-105"
            >
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Clear Tree Data</span>
              </div>
            </button>
          </div>

          {/* Data Statistics */}
          <div className="p-3 bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl border border-blue-100">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Statistics</h3>
            <div className="text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-600">Messages:</span>
                <span className="font-medium text-blue-600">{websocketData.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">People:</span>
                <span className="font-medium text-emerald-600">{websocketData.filter(m => m.type === 'personal_details').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Relationships:</span>
                <span className="font-medium text-purple-600">{websocketData.filter(m => m.type === 'relationship').length}</span>
              </div>
            </div>
          </div>

          {/* Recent Messages (Debug) */}
          {websocketData.length > 0 && (
            <div className="mt-4 p-3 bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl border border-blue-100 max-h-32 overflow-y-auto">
              <p className="text-xs font-semibold text-slate-700 mb-2">Recent Messages:</p>
              <div className="space-y-1">
                {websocketData.slice(-3).map((msg, index) => (
                  <div key={index} className="p-2 bg-white/70 rounded-lg text-xs border border-blue-100">
                    <span className="font-medium text-blue-600">{msg.type}:</span> 
                    <span className="text-slate-600 ml-1">{JSON.stringify(msg.data).slice(0, 50)}...</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Genealogy Tree - Takes full screen */}
      <GenealogyTree 
        websocketData={websocketData} 
        onExpandNode={handleExpandNode}
      />
    </main>
  );
}

