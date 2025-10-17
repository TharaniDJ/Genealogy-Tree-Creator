'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';
import { Network, GitBranch, Dna, ChevronRight, LogOut, User } from 'lucide-react';
import useAuth from '@/hooks/useAuth';
import Image from 'next/image';
function SelectPageInner() {
  const router = useRouter();
  const { logout, getToken } = useAuth();
  const [userName, setUserName] = useState<string>('User');

  useEffect(() => {
    const token = getToken();
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUserName(payload.full_name || 'User');
      } catch (e) {
        console.error('Failed to decode token:', e);
      }
    }
  }, [getToken]);

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const treeOptions = [
    {
      title: 'Family Tree',
      description: 'Build personal genealogies and historical lineages. Connect generations and preserve family histories.',
      icon: Network,
      gradient: 'from-[#6B72FF] to-[#8B7BFF]',
      route: '/family_tree',
      glowColor: '#15cf94',
      iconType: 'family',
    },
    {
      title: 'Language Family Tree',
      description: 'Explore linguistic evolution and relationships. Trace language families from ancient roots to modern dialects.',
      icon: GitBranch,
      gradient: 'from-[#8B7BFF] to-[#9B8BFF]',
      route: '/language_tree',
      glowColor: '#4269f5',
      iconType: 'language',
    },
    {
      title: 'Species Taxonomy Tree',
      description: 'Map taxonomic relationships and evolutionary paths. Discover biodiversity through interactive phylogenetic trees.',
      icon: Dna,
      gradient: 'from-[#5B62FF] to-[#7B72FF]',
      route: '/taxonomy_tree',
      glowColor: '#15bfcf',
      iconType: 'species',
    },
  ];

  return (
    <div className="min-h-screen relative bg-[#0E0F19]">
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-50">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-72 h-72 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Navbar */}
      <nav className="relative text-[12px] z-10 backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Image
                  src="/logo.png"
                  alt="GeneChain Logo"
                  width={50}
                  height={50}
                  className="object-contain"
                />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
                GeneChain
              </span>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/graphs')}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA] font-medium hover:bg-white/10 transition-all duration-300 hover:scale-105"
              >
                <Network className="w-5 h-5" />
                <span>My Graphs</span>
              </button>
              <button
                onClick={() => router.push('/account')}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA] font-medium hover:bg-white/10 transition-all duration-300 hover:scale-105"
              >
                <User className="w-5 h-5" />
                <span>Account</span>
              </button>
              <div className="flex items-center space-x-3 px-4 py-2 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10">
                <span className="text-[#F5F7FA] font-medium">{userName}</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA] font-medium hover:bg-white/10 transition-all duration-300 hover:scale-105"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-3">
            <span className="text-[#F5F7FA]">Choose Your</span>{' '}
            <span className="bg-gradient-to-r from-[#6B72FF] via-[#8B7BFF] to-[#6B72FF] bg-clip-text text-transparent animate-gradient">
              Tree Type
            </span>
          </h1>
          <p className="text-base text-[#9CA3B5] max-w-xl mx-auto">
            Select a tree type to start exploring and building your genealogical data.
          </p>
        </div>

        {/* Tree Options */}
        <div className="grid md:grid-cols-3 gap-6 mb-10">
          {treeOptions.map((option, index) => {
            const Icon = option.icon;
            return (
              <button
                key={index}
                onClick={() => router.push(option.route)}
                className="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-black transition-all duration-300 hover:scale-102 hover:shadow-xl flex flex-col items-center justify-center"
                style={{
                  boxShadow: `0 0 0 0 ${option.glowColor}40`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = `0 20px 60px ${option.glowColor}40`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = `0 0 0 0 ${option.glowColor}40`;
                }}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${option.gradient} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`}></div>

                <div className="relative z-10 w-full text-center">
                  {option.iconType === 'language' ? (
                    <div className="flex items-center justify-center mb-4">
                      <svg 
                        width="60" 
                        height="60" 
                        viewBox="0 0 16 16" 
                        fill="none" 
                        xmlns="http://www.w3.org/2000/svg"
                        className="group-hover:scale-110 transition-transform duration-300"
                      >
                        <path 
                          fillRule="evenodd" 
                          clipRule="evenodd" 
                          d="M4 0H6V2H10V4H8.86807C8.57073 5.66996 7.78574 7.17117 6.6656 8.35112C7.46567 8.73941 8.35737 8.96842 9.29948 8.99697L10.2735 6H12.7265L15.9765 16H13.8735L13.2235 14H9.77647L9.12647 16H7.0235L8.66176 10.9592C7.32639 10.8285 6.08165 10.3888 4.99999 9.71246C3.69496 10.5284 2.15255 11 0.5 11H0V9H0.5C1.5161 9 2.47775 8.76685 3.33437 8.35112C2.68381 7.66582 2.14629 6.87215 1.75171 6H4.02179C4.30023 6.43491 4.62904 6.83446 4.99999 7.19044C5.88743 6.33881 6.53369 5.23777 6.82607 4H0V2H4V0ZM12.5735 12L11.5 8.69688L10.4265 12H12.5735Z" 
                          fill={option.glowColor}
                        />
                      </svg>
                    </div>
                  ) : option.iconType === 'family' ? (
                    <div className="flex items-center justify-center mb-4">
                      <svg 
                        width="60" 
                        height="60" 
                        viewBox="0 0 512 512" 
                        xmlns="http://www.w3.org/2000/svg"
                        className="group-hover:scale-110 transition-transform duration-300"
                      >
                        <path 
                          fill={option.glowColor}
                          d="M78.642,118.933c22.879,0,41.415-18.551,41.415-41.414c0-22.888-18.536-41.423-41.415-41.423c-22.887,0-41.422,18.535-41.422,41.423C37.219,100.383,55.755,118.933,78.642,118.933z"
                        />
                        <path 
                          fill={option.glowColor}
                          d="M255.706,228.731v0.062c0.101,0,0.193-0.031,0.294-0.031c0.101,0,0.194,0.031,0.294,0.031v-0.062c15.563-0.317,28.082-12.976,28.082-28.601c0-15.648-12.52-28.299-28.082-28.617v-0.062c-0.1,0-0.193,0.031-0.294,0.031c-0.101,0-0.193-0.031-0.294-0.031v0.062c-15.563,0.318-28.082,12.969-28.082,28.617C227.624,215.754,240.143,228.413,255.706,228.731z"
                        />
                        <path 
                          fill={option.glowColor}
                          d="M433.358,118.933c22.887,0,41.423-18.551,41.423-41.414c0-22.888-18.536-41.423-41.423-41.423c-22.879,0-41.414,18.535-41.414,41.423C391.944,100.383,410.48,118.933,433.358,118.933z"
                        />
                        <path 
                          fill={option.glowColor}
                          d="M512,319.675V180.463c0-20.076-21.834-41.91-41.903-41.91h-5.799l-28.818,28.818l-28.214-28.214c-17.839,2.609-33.564,13.665-41.918,30.018l-33.494,97.967c-1.154,2.245-3.298,3.84-5.792,4.281c-2.493,0.442-5.048-0.31-6.914-2.036l-20.835-18.04c-6.232-5.769-14.409-8.974-22.902-8.974H256h-19.41c-8.494,0-16.67,3.206-22.903,8.974l-20.835,18.04c-1.866,1.726-4.422,2.478-6.914,2.036c-2.494-0.442-4.638-2.036-5.792-4.281l-33.494-97.967c-9.6-18.791-28.926-30.622-50.032-30.622H78.216H41.903C21.834,138.553,0,160.387,0,180.463v139.211c0,10.035,8.13,18.172,18.165,18.172c4.939,0,0,0,12.682,0l6.906,118.724c0,10.677,8.664,19.333,19.341,19.333c4.506,0,12.814,0,21.122,0c8.307,0,16.615,0,21.121,0c10.677,0,19.341-8.656,19.341-19.333l6.906-118.724l-0.086-84.765c0-1.339,0.914-2.493,2.222-2.818c1.309-0.31,2.648,0.309,3.26,1.502l26.573,65.401c3.205,6.256,9.152,10.654,16.074,11.886c6.921,1.23,14.021-0.844,19.186-5.614l25.426-18.729c0.852-0.782,2.083-0.983,3.136-0.542c1.061,0.472,1.742,1.518,1.742,2.663l0.094,73.508l4.777,82.187c0,7.387,6,13.379,13.395,13.379c3.112,0,8.865,0,14.618,0c5.753,0,11.506,0,14.618,0c7.394,0,13.394-5.992,13.394-13.379l4.777-82.187l0.093-73.508c0-1.146,0.681-2.192,1.742-2.663c1.053-0.442,2.284-0.24,3.136,0.542l25.426,18.729c5.164,4.77,12.264,6.844,19.187,5.614c6.921-1.231,12.868-5.629,16.073-11.886l26.572-65.401c0.612-1.192,1.951-1.812,3.26-1.502c1.308,0.325,2.222,1.479,2.222,2.818l-0.031,32.332l-27.881,86.648c-0.659,2.051-0.302,4.296,0.967,6.039c1.27,1.742,3.298,2.772,5.451,2.772h23.91l4.405,75.699c0,10.677,8.664,19.333,19.341,19.333c4.506,0,12.814,0,21.121,0c8.308,0,16.615,0,21.122,0c10.677,0,19.34-8.656,19.34-19.333l4.406-75.699h26.418c2.152,0,4.181-1.03,5.451-2.772c1.27-1.743,1.626-3.988,0.968-6.039L500.1,336.67C507.037,334.107,512,327.495,512,319.675z M85.424,159.087v74.592H63.389v-74.592H85.424z"
                        />
                      </svg>
                    </div>
                  ) : option.iconType === 'species' ? (
                    <div className="flex items-center justify-center mb-4">
                      <svg 
                        width="60" 
                        height="60" 
                        viewBox="0 0 20 20" 
                        xmlns="http://www.w3.org/2000/svg"
                        className="group-hover:scale-110 transition-transform duration-300"
                      >
                        <rect x="0" fill="none" width="20" height="20"/>
                        <g>
                          <path 
                            fill={option.glowColor}
                            d="M11.9 8.4c1.3 0 2.1-1.9 2.1-3.1 0-1-.5-2.2-1.5-2.2-1.3 0-2.1 1.9-2.1 3.1 0 1 .5 2.2 1.5 2.2zm-3.8 0c1 0 1.5-1.2 1.5-2.2C9.6 4.9 8.8 3 7.5 3 6.5 3 6 4.2 6 5.2c-.1 1.3.7 3.2 2.1 3.2zm7.4-1c-1.3 0-2.2 1.8-2.2 3.1 0 .9.4 1.8 1.3 1.8 1.3 0 2.2-1.8 2.2-3.1 0-.9-.5-1.8-1.3-1.8zm-8.7 3.1c0-1.3-1-3.1-2.2-3.1-.9 0-1.3.9-1.3 1.8 0 1.3 1 3.1 2.2 3.1.9 0 1.3-.9 1.3-1.8zm3.2-.2c-2 0-4.7 3.2-4.7 5.4 0 1 .7 1.3 1.5 1.3 1.2 0 2.1-.8 3.2-.8 1 0 1.9.8 3 .8.8 0 1.7-.2 1.7-1.3 0-2.2-2.7-5.4-4.7-5.4z"
                          />
                        </g>
                      </svg>
                    </div>
                  ) : (
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${option.gradient} flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}
                      style={{ boxShadow: `0 8px 20px ${option.glowColor}30` }}
                    >
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  )}

                  <h3 className="text-[18px] text-center font-bold text-[#F5F7FA] mb-2">
                    {option.title}
                  </h3>

                  <p className="text-[14px] text-center text-[#9CA3B5] leading-relaxed mb-4">
                    {option.description}
                  </p>

                  <div 
                    className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg border-2 font-semibold text-xs shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ borderColor: option.glowColor }}
                  >
                    <span style={{ color: option.glowColor }}>Select</span>
                    <ChevronRight className="w-3 h-3" style={{ color: option.glowColor }} />
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Features Section */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold text-center mb-6">
            <span className="bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
              What You Can Do
            </span>
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: 'Interactive Nodes', desc: 'Expand and explore dynamically' },
              { title: 'Full Control', desc: 'Add, edit, or delete freely' },
              { title: 'Depth Options', desc: 'Generate to any depth level' },
              { title: 'Save & Share', desc: 'Persist and collaborate' },
            ].map((feature, idx) => (
              <div key={idx} className="text-center p-4 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center mx-auto mb-3 shadow-lg shadow-[#6B72FF]/30">
                  <ChevronRight className="w-5 h-5 text-white" />
                </div>
                <h4 className="text-sm font-semibold text-[#F5F7FA] mb-1">{feature.title}</h4>
                <p className="text-xs text-[#9CA3B5]">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
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
        .animate-gradient {
          background-size: 200% auto;
          animation: gradient 3s ease infinite;
        }
      `}</style>
    </div>
  );
}

export default function SelectPage() {
  return (
    <AuthGuard>
      <SelectPageInner />
    </AuthGuard>
  );
}
