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
      glowColor: '#6B72FF',
    },
    {
      title: 'Language Family Tree',
      description: 'Explore linguistic evolution and relationships. Trace language families from ancient roots to modern dialects.',
      icon: GitBranch,
      gradient: 'from-[#8B7BFF] to-[#9B8BFF]',
      route: '/language_tree',
      glowColor: '#8B7BFF',
    },
    {
      title: 'Species Taxonomy Tree',
      description: 'Map taxonomic relationships and evolutionary paths. Discover biodiversity through interactive phylogenetic trees.',
      icon: Dna,
      gradient: 'from-[#5B62FF] to-[#7B72FF]',
      route: '/taxonomy_tree',
      glowColor: '#5B62FF',
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
      <nav className="relative z-10 backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10">
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
              <div className="flex items-center space-x-3 px-4 py-2 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10">
                <User className="w-5 h-5 text-[#9CA3B5]" />
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
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            <span className="text-[#F5F7FA]">Choose Your</span>
            <br />
            <span className="bg-gradient-to-r from-[#6B72FF] via-[#8B7BFF] to-[#6B72FF] bg-clip-text text-transparent animate-gradient">
              Genealogical Journey
            </span>
          </h1>
          <p className="text-xl text-[#9CA3B5] max-w-2xl mx-auto">
            Select a tree type to start exploring connections, building relationships, and discovering insights.
          </p>
        </div>

        {/* Tree Options */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {treeOptions.map((option, index) => {
            const Icon = option.icon;
            return (
              <button
                key={index}
                onClick={() => router.push(option.route)}
                className="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl text-left"
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
                <div className={`absolute inset-0 bg-gradient-to-br ${option.gradient} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`}></div>

                <div className="relative z-10">
                  <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${option.gradient} flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform duration-300`}
                    style={{ boxShadow: `0 10px 30px ${option.glowColor}30` }}
                  >
                    <Icon className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="text-2xl font-bold text-[#F5F7FA] mb-3 flex items-center justify-between">
                    {option.title}
                    <ChevronRight className="w-6 h-6 text-[#9CA3B5] group-hover:text-[#F5F7FA] group-hover:translate-x-1 transition-all duration-300" />
                  </h3>

                  <p className="text-[#9CA3B5] leading-relaxed mb-6">
                    {option.description}
                  </p>

                  <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r ${option.gradient} text-white font-semibold text-sm shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300`}>
                    <span>Get Started</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Features Section */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-12">
          <h2 className="text-3xl font-bold text-center mb-10">
            <span className="bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
              What You Can Do
            </span>
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: 'Interactive Nodes', desc: 'Expand and explore dynamically' },
              { title: 'Full Control', desc: 'Add, edit, or delete freely' },
              { title: 'Depth Options', desc: 'Generate to any depth level' },
              { title: 'Save & Share', desc: 'Persist and collaborate' },
            ].map((feature, idx) => (
              <div key={idx} className="text-center p-6 rounded-xl backdrop-blur-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center mx-auto mb-4 shadow-lg shadow-[#6B72FF]/30">
                  <ChevronRight className="w-6 h-6 text-white" />
                </div>
                <h4 className="text-lg font-semibold text-[#F5F7FA] mb-2">{feature.title}</h4>
                <p className="text-sm text-[#9CA3B5]">{feature.desc}</p>
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
