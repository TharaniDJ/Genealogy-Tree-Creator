"use client";

import React, { useState, useEffect } from 'react';
import { X, Users, Globe, MapPin, ExternalLink, Loader2 } from 'lucide-react';

interface LanguageInfo {
  speakers?: string;
  iso_code?: string;
  distribution_map_url?: string;
}

interface LanguageDetailsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  languageName: string;
  qid?: string;
  category?: string;
}

const LanguageDetailsSidebar: React.FC<LanguageDetailsSidebarProps> = ({
  isOpen,
  onClose,
  languageName,
  qid,
  category
}) => {
  const [languageInfo, setLanguageInfo] = useState<LanguageInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && qid) {
      fetchLanguageInfo();
    }
  }, [isOpen, qid]);

  const fetchLanguageInfo = async () => {
    if (!qid) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const base = process.env.NEXT_PUBLIC_LANGUAGE_API_URL || 'http://localhost:8001';
      const response = await fetch(`${base}/info/${qid}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch language info: ${response.statusText}`);
      }
      
      const data = await response.json();
      setLanguageInfo(data);
    } catch (err) {
      console.error('Error fetching language info:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch language information');
    } finally {
      setLoading(false);
    }
  };

  const formatSpeakers = (speakers?: string) => {
    if (!speakers) return 'Unknown';
    
    const num = parseInt(speakers, 10);
    if (isNaN(num)) return speakers;
    
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(1)}B`;
    } else if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    } else if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  const humanizeCategory = (cat?: string) => {
    if (!cat) return '';
    return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-96 backdrop-blur-xl bg-white/5 border-l border-white/10 shadow-2xl shadow-[#6B72FF]/10 z-50 transform transition-transform duration-300 ease-in-out">
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <div>
              <h2 className="text-xl font-bold text-[#F5F7FA] truncate">{languageName}</h2>
              {category && (
                <p className="text-sm text-[#9CA3B5] mt-1">{humanizeCategory(category)}</p>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors duration-200"
            >
              <X className="w-5 h-5 text-[#9CA3B5] hover:text-[#F5F7FA]" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {!qid ? (
              <div className="flex items-center justify-center h-32 text-[#9CA3B5]">
                <div className="text-center">
                  <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No Wikidata ID available</p>
                </div>
              </div>
            ) : loading ? (
              <div className="flex items-center justify-center h-32 text-[#9CA3B5]">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin text-[#6B72FF]" />
                  <p>Loading language information...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-32 text-red-400">
                <div className="text-center">
                  <X className="w-8 h-8 mx-auto mb-2" />
                  <p className="text-sm">{error}</p>
                  <button 
                    onClick={fetchLanguageInfo}
                    className="mt-2 text-[#6B72FF] hover:text-[#8B7BFF] text-sm underline"
                  >
                    Try again
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Basic Information */}
                <div className="backdrop-blur-lg bg-white/5 rounded-xl p-4 border border-white/10">
                  <h3 className="font-semibold text-[#F5F7FA] mb-3 flex items-center">
                    <Globe className="w-4 h-4 mr-2 text-[#6B72FF]" />
                    Basic Information
                  </h3>
                  
                  <div className="space-y-3">
                    {languageInfo?.speakers && (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center text-[#9CA3B5]">
                          <Users className="w-4 h-4 mr-2" />
                          <span className="text-sm">Speakers</span>
                        </div>
                        <span className="font-medium text-[#F5F7FA]">
                          {formatSpeakers(languageInfo.speakers)}
                        </span>
                      </div>
                    )}
                    
                    {languageInfo?.iso_code && (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center text-[#9CA3B5]">
                          <MapPin className="w-4 h-4 mr-2" />
                          <span className="text-sm">ISO Code</span>
                        </div>
                        <span className="font-mono font-medium text-[#F5F7FA] bg-white/10 px-2 py-1 rounded text-sm">
                          {languageInfo.iso_code}
                        </span>
                      </div>
                    )}

                    {qid && (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center text-[#9CA3B5]">
                          <ExternalLink className="w-4 h-4 mr-2" />
                          <span className="text-sm">Wikidata ID</span>
                        </div>
                        <a 
                          href={`https://www.wikidata.org/wiki/${qid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono font-medium text-[#6B72FF] hover:text-[#8B7BFF] bg-[#6B72FF]/10 px-2 py-1 rounded text-sm transition-colors"
                        >
                          {qid}
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Distribution Map */}
                {languageInfo?.distribution_map_url && (
                  <div className="backdrop-blur-lg bg-white/5 rounded-xl p-4 border border-white/10">
                    <h3 className="font-semibold text-[#F5F7FA] mb-3 flex items-center">
                      <MapPin className="w-4 h-4 mr-2 text-[#6B72FF]" />
                      Distribution Map
                    </h3>
                    
                    <div className="relative rounded-lg overflow-hidden bg-white/5">
                      <img
                        src={languageInfo.distribution_map_url}
                        alt={`Distribution map for ${languageName}`}
                        className="w-full h-auto"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const parent = target.parentElement;
                          if (parent) {
                            parent.innerHTML = '<div class="flex items-center justify-center h-32 text-[#9CA3B5]"><p class="text-sm">Failed to load distribution map</p></div>';
                          }
                        }}
                      />
                    </div>
                    
                    <a 
                      href={languageInfo.distribution_map_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center mt-2 text-sm text-[#6B72FF] hover:text-[#8B7BFF] transition-colors"
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      View full size
                    </a>
                  </div>
                )}

                {/* No data message */}
                {languageInfo && !languageInfo.speakers && !languageInfo.iso_code && !languageInfo.distribution_map_url && (
                  <div className="flex items-center justify-center h-32 text-[#9CA3B5]">
                    <div className="text-center">
                      <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>No additional information available</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default LanguageDetailsSidebar;
