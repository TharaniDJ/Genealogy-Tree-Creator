'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';
import Image from 'next/image';
import { Network, GitBranch, Dna, Sparkles, ChevronRight, User, LogIn, UserPlus } from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [userName, setUserName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (token) {
      try {
        // Decode JWT to get user info (payload is base64 encoded)
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUserName(payload.full_name || 'User');
      } catch (e) {
        console.error('Failed to decode token:', e);
      }
    }
    setIsLoading(false);
  }, [getToken]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0E0F19]">
        <div className="animate-pulse">
          <Sparkles className="w-12 h-12 text-[#6B72FF]" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen relative bg-[#0E0F19]">
      {/* Animated gradient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-50">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-72 h-72 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Navbar */}
      <nav className="relative text-[12px] z-10 backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
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
              {userName ? (
                <>
                  <div className="flex items-center space-x-3 px-4 py-2 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10">
                    <User className="w-5 h-5 text-[#9CA3B5]" />
                    <span className="text-[#F5F7FA] font-medium">Welcome, {userName}</span>
                  </div>
                  <button
                    onClick={() => router.push('/select')}
                    className="group flex items-center space-x-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-semibold shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 transition-all duration-300 hover:scale-105"
                  >
                    <span>Continue</span>
                    <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => router.push('/login')}
                    className="flex items-center space-x-2 px-5 py-2.5 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA] font-medium hover:bg-white/10 transition-all duration-300 hover:scale-105"
                  >
                    <LogIn className="w-5 h-5" />
                    <span>Sign In</span>
                  </button>
                  <button
                    onClick={() => router.push('/register')}
                    className="flex items-center space-x-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-semibold shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 transition-all duration-300 hover:scale-105"
                  >
                    <UserPlus className="w-5 h-5" />
                    <span>Register</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center mb-16">
          <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full backdrop-blur-lg bg-white/5 border border-white/10 mb-8">
            <Sparkles className="w-4 h-4 text-[#8B7BFF]" />
            <span className="text-sm text-[#9CA3B5] font-medium">Powered by Wikipedia Data</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="text-[#F5F7FA]">Create Interactive</span>
            <br />
            <span className="bg-gradient-to-r from-[#6B72FF] via-[#8B7BFF] to-[#6B72FF] bg-clip-text text-transparent animate-gradient">
              Genealogical Trees
            </span>
          </h1>
          
          <p className="text-xl text-[#9CA3B5] max-w-3xl mx-auto mb-12 leading-relaxed">
            Build stunning, interactive tree structures for languages, species, and people. 
            From curious students to top researchers — explore, expand, and discover connections.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => router.push(userName ? '/select' : '/register')}
              className="group flex items-center space-x-2 px-8 py-4 rounded-xl bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-bold text-lg shadow-2xl shadow-[#6B72FF]/40 hover:shadow-[#6B72FF]/60 transition-all duration-300 hover:scale-105"
            >
              <span>{userName ? 'Get Started' : 'Start Free'}</span>
              <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="px-8 py-4 rounded-xl backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA] font-bold text-lg hover:bg-white/10 transition-all duration-300 hover:scale-105"
            >
              Learn More
            </button>
          </div>
        </div>

        {/* Feature Cards */}
        <div id="features" className="grid md:grid-cols-3 gap-8 mt-24">
          {/* Language Trees */}
          <div className="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-[#6B72FF]/20">
            <div className="absolute inset-0 bg-gradient-to-br from-[#6B72FF]/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center mb-6 shadow-lg shadow-[#6B72FF]/30 group-hover:scale-110 transition-transform duration-300">
                <GitBranch className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-[#F5F7FA] mb-3">Language Trees</h3>
              <p className="text-[#9CA3B5] leading-relaxed">
                Explore linguistic evolution and relationships. Trace language families from ancient roots to modern dialects.
              </p>
            </div>
          </div>

          {/* Species Trees */}
          <div className="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-[#8B7BFF]/20">
            <div className="absolute inset-0 bg-gradient-to-br from-[#8B7BFF]/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#7B72FF] to-[#9B8BFF] flex items-center justify-center mb-6 shadow-lg shadow-[#8B7BFF]/30 group-hover:scale-110 transition-transform duration-300">
                <Dna className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-[#F5F7FA] mb-3">Species Trees</h3>
              <p className="text-[#9CA3B5] leading-relaxed">
                Map taxonomic relationships and evolutionary paths. Discover biodiversity through interactive phylogenetic trees.
              </p>
            </div>
          </div>

          {/* Family Trees */}
          <div className="group relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-[#5B62FF]/20">
            <div className="absolute inset-0 bg-gradient-to-br from-[#5B62FF]/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative z-10">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#5B62FF] to-[#7B72FF] flex items-center justify-center mb-6 shadow-lg shadow-[#5B62FF]/30 group-hover:scale-110 transition-transform duration-300">
                <Network className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-[#F5F7FA] mb-3">Family Trees</h3>
              <p className="text-[#9CA3B5] leading-relaxed">
                Build personal genealogies and historical lineages. Connect generations and preserve family histories.
              </p>
            </div>
          </div>
        </div>

        {/* Features Highlight */}
        <div className="mt-24 backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-12">
          <h2 className="text-4xl font-bold text-center mb-12">
            <span className="bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
              Powerful Features
            </span>
          </h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 shadow-lg shadow-[#6B72FF]/30">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-[#F5F7FA] mb-2">Interactive Expansion</h4>
                <p className="text-[#9CA3B5]">Expand any node to reveal deeper connections and relationships dynamically</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 shadow-lg shadow-[#6B72FF]/30">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-[#F5F7FA] mb-2">Full Control</h4>
                <p className="text-[#9CA3B5]">Add, edit, or delete nodes with complete flexibility over your tree structure</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 shadow-lg shadow-[#6B72FF]/30">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-[#F5F7FA] mb-2">Depth-Wise Generation</h4>
                <p className="text-[#9CA3B5]">Generate trees to specific depths or explore complete relationships</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 shadow-lg shadow-[#6B72FF]/30">
                <ChevronRight className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-[#F5F7FA] mb-2">Save & Share</h4>
                <p className="text-[#9CA3B5]">Persist your work and share discoveries with colleagues or students</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center">
          <div className="backdrop-blur-xl bg-gradient-to-br from-[#6B72FF]/20 to-[#8B7BFF]/20 border border-white/10 rounded-3xl p-16 shadow-2xl shadow-[#6B72FF]/20">
            <h2 className="text-4xl md:text-5xl font-bold text-[#F5F7FA] mb-6">
              Ready to Explore?
            </h2>
            <p className="text-xl text-[#9CA3B5] mb-10 max-w-2xl mx-auto">
              Join researchers, students, and enthusiasts in mapping the connections that shape our world.
            </p>
            <button
              onClick={() => router.push(userName ? '/select' : '/register')}
              className="group inline-flex items-center space-x-2 px-10 py-5 rounded-xl bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-bold text-xl shadow-2xl shadow-[#6B72FF]/50 hover:shadow-[#6B72FF]/70 transition-all duration-300 hover:scale-105"
            >
              <span>{userName ? 'Open Dashboard' : 'Get Started Free'}</span>
              <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 mt-24 backdrop-blur-xl bg-white/5 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="relative w-8 h-8">
                <Image 
                  src="/logo.png" 
                  alt="GeneChain Logo" 
                  width={32} 
                  height={32}
                  className="object-contain"
                />
              </div>
              <span className="text-[#F5F7FA] font-semibold">GeneChain</span>
            </div>
            <p className="text-[#9CA3B5] text-sm">
              © 2025 GeneChain. Powered by Wikipedia Data.
            </p>
          </div>
        </div>
      </footer>

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
