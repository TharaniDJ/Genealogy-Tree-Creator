'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';
import Image from 'next/image';
import { Network, GitBranch, Dna, Sparkles, ChevronRight, User, LogIn, UserPlus } from 'lucide-react';
import {
  Navbar,
  NavBody,
  NavItems,
  MobileNav,
  NavbarLogo,
  NavbarButton,
  MobileNavHeader,
  MobileNavToggle,
  MobileNavMenu,
} from "@/components/ui/resizable-navbar";

export default function LandingPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [userName, setUserName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
      <div className="relative z-10">
        <Navbar>
          {/* Desktop Navigation */}
          <NavBody>
            <NavbarLogo />
            <NavItems items={[
              { name: "Features", link: "#features" },
              { name: "Services", link: "#services" },
            ]} />
            <div className="flex items-center gap-4">
              {userName ? (
                <>
                  <div className="flex items-center space-x-3 px-4 py-2 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10">
                    <User className="w-5 h-5 text-[#9CA3B5]" />
                    <span className="text-[#F5F7FA] font-medium">Welcome, {userName}</span>
                  </div>
                  <NavbarButton 
                    variant="primary" 
                    onClick={() => router.push('/select')}
                  >
                    Continue
                  </NavbarButton>
                </>
              ) : (
                <>
                  <NavbarButton 
                    variant="secondary" 
                    onClick={() => router.push('/login')}
                    className="text-white"
                  >
                    Sign In
                  </NavbarButton>
                  <NavbarButton 
                    variant="primary" 
                    onClick={() => router.push('/register')}
                  >
                    Register
                  </NavbarButton>
                </>
              )}
            </div>
          </NavBody>

          {/* Mobile Navigation */}
          <MobileNav>
            <MobileNavHeader>
              <NavbarLogo />
              <MobileNavToggle
                isOpen={isMobileMenuOpen}
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              />
            </MobileNavHeader>

            <MobileNavMenu
              isOpen={isMobileMenuOpen}
              onClose={() => setIsMobileMenuOpen(false)}
            >
              <a
                href="#features"
                onClick={() => setIsMobileMenuOpen(false)}
                className="relative text-neutral-600 dark:text-neutral-300"
              >
                <span className="block">Features</span>
              </a>
              <a
                href="#services"
                onClick={() => setIsMobileMenuOpen(false)}
                className="relative text-neutral-600 dark:text-neutral-300"
              >
                <span className="block">Services</span>
              </a>
              <div className="flex w-full flex-col gap-4">
                {userName ? (
                  <>
                    <div className="flex items-center space-x-3 px-4 py-2 rounded-lg backdrop-blur-lg bg-white/5 border border-white/10">
                      <User className="w-5 h-5 text-[#9CA3B5]" />
                      <span className="text-[#F5F7FA] font-medium">Welcome, {userName}</span>
                    </div>
                    <NavbarButton
                      onClick={() => {
                        setIsMobileMenuOpen(false);
                        router.push('/select');
                      }}
                      variant="primary"
                      className="w-full"
                    >
                      Continue
                    </NavbarButton>
                  </>
                ) : (
                  <>
                    <NavbarButton
                      onClick={() => {
                        setIsMobileMenuOpen(false);
                        router.push('/login');
                      }}
                      variant="secondary"
                      className="w-full"
                    >
                      Sign In
                    </NavbarButton>
                    <NavbarButton
                      onClick={() => {
                        setIsMobileMenuOpen(false);
                        router.push('/register');
                      }}
                      variant="primary"
                      className="w-full"
                    >
                      Register
                    </NavbarButton>
                  </>
                )}
              </div>
            </MobileNavMenu>
          </MobileNav>
        </Navbar>
      </div>

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
      </div>

      {/* Services Section */}
      <div id="services" className="relative z-10">
        {/* Language Tree Section */}
        <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-16">
          <div className="max-w-7xl w-full mx-auto">
            <div className="flex flex-col lg:flex-row items-center gap-12">
              {/* Left - Image */}
              <div className="flex-1 relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#6B72FF]/20 to-[#8B7BFF]/20 rounded-3xl blur-2xl group-hover:blur-3xl transition-all duration-500"></div>
                <div className="relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl shadow-[#6B72FF]/20">
                  <Image 
                    src="/language.webp" 
                    alt="Language Tree" 
                    width={600} 
                    height={600}
                    className="object-cover w-full h-full transform group-hover:scale-110 transition-transform duration-700"
                  />
                </div>
              </div>
              
              {/* Right - Content */}
              <div className="flex-1 space-y-6">
                <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full backdrop-blur-lg bg-white/5 border border-white/10">
                  <GitBranch className="w-4 h-4 text-[#6B72FF]" />
                  <span className="text-sm text-[#9CA3B5] font-medium">Linguistic Evolution</span>
                </div>
                
                <h2 className="text-4xl md:text-5xl font-bold text-[#F5F7FA]">
                  Language Tree <span className="bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">Generation</span>
                </h2>
                
                <p className="text-lg text-[#9CA3B5] leading-relaxed">
                  Explore the fascinating connections between languages across the globe. Our Language Tree visualization 
                  maps linguistic evolution from ancient roots to modern dialects, revealing how languages influence 
                  and derive from one another through centuries of human communication.
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Trace language families from Proto-Indo-European to modern languages</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Discover linguistic relationships and historical influences</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Interactive exploration with detailed language information</p>
                  </div>
                </div>
                
                <button
                  onClick={() => router.push('/language_tree')}
                  className="group inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-bold shadow-xl shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 transition-all duration-300 hover:scale-105"
                >
                  <span>Explore Languages</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Family Tree Section */}
        <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-16 bg-gradient-to-b from-transparent via-[#6B72FF]/5 to-transparent">
          <div className="max-w-7xl w-full mx-auto">
            <div className="flex flex-col lg:flex-row-reverse items-center gap-12">
              {/* Right - Image */}
              <div className="flex-1 relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#5B62FF]/20 to-[#7B72FF]/20 rounded-3xl blur-2xl group-hover:blur-3xl transition-all duration-500"></div>
                <div className="relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl shadow-[#5B62FF]/20">
                  <Image 
                    src="/family.webp" 
                    alt="Family Tree" 
                    width={600} 
                    height={600}
                    className="object-cover w-full h-full transform group-hover:scale-110 transition-transform duration-700"
                  />
                </div>
              </div>
              
              {/* Left - Content */}
              <div className="flex-1 space-y-6">
                <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full backdrop-blur-lg bg-white/5 border border-white/10">
                  <Network className="w-4 h-4 text-[#5B62FF]" />
                  <span className="text-sm text-[#9CA3B5] font-medium">Genealogical Heritage</span>
                </div>
                
                <h2 className="text-4xl md:text-5xl font-bold text-[#F5F7FA]">
                  Family Tree <span className="bg-gradient-to-r from-[#5B62FF] to-[#7B72FF] bg-clip-text text-transparent">Generation</span>
                </h2>
                
                <p className="text-lg text-[#9CA3B5] leading-relaxed">
                  Build and explore personal genealogies and historical lineages with our intuitive Family Tree creator. 
                  Connect generations, preserve family histories, and discover the relationships that bind your heritage 
                  together through an interactive and beautifully visualized family network.
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#5B62FF] to-[#7B72FF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Create detailed family genealogies with multiple generations</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#5B62FF] to-[#7B72FF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Track relationships, marriages, and family connections</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#5B62FF] to-[#7B72FF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Preserve and share your family history for future generations</p>
                  </div>
                </div>
                
                <button
                  onClick={() => router.push('/family_tree')}
                  className="group inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-gradient-to-r from-[#5B62FF] to-[#7B72FF] text-white font-bold shadow-xl shadow-[#5B62FF]/30 hover:shadow-[#5B62FF]/50 transition-all duration-300 hover:scale-105"
                >
                  <span>Build Your Family Tree</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Species Tree Section */}
        <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-16">
          <div className="max-w-7xl w-full mx-auto">
            <div className="flex flex-col lg:flex-row items-center gap-12">
              {/* Left - Image */}
              <div className="flex-1 relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-[#8B7BFF]/20 to-[#9B8BFF]/20 rounded-3xl blur-2xl group-hover:blur-3xl transition-all duration-500"></div>
                <div className="relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl shadow-[#8B7BFF]/20">
                  <Image 
                    src="/species.webp" 
                    alt="Species Tree" 
                    width={600} 
                    height={600}
                    className="object-cover w-full h-full transform group-hover:scale-110 transition-transform duration-700"
                  />
                </div>
              </div>
              
              {/* Right - Content */}
              <div className="flex-1 space-y-6">
                <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full backdrop-blur-lg bg-white/5 border border-white/10">
                  <Dna className="w-4 h-4 text-[#8B7BFF]" />
                  <span className="text-sm text-[#9CA3B5] font-medium">Biodiversity Mapping</span>
                </div>
                
                <h2 className="text-4xl md:text-5xl font-bold text-[#F5F7FA]">
                  Species Tree <span className="bg-gradient-to-r from-[#8B7BFF] to-[#9B8BFF] bg-clip-text text-transparent">Generation</span>
                </h2>
                
                <p className="text-lg text-[#9CA3B5] leading-relaxed">
                  Navigate the tree of life with our comprehensive Species Tree visualization. Map taxonomic relationships, 
                  explore evolutionary paths, and discover the incredible biodiversity of our planet through interactive 
                  phylogenetic trees that span from microscopic organisms to complex life forms.
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#8B7BFF] to-[#9B8BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Explore taxonomic hierarchies from kingdoms to species</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#8B7BFF] to-[#9B8BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Visualize evolutionary relationships and common ancestors</p>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#8B7BFF] to-[#9B8BFF] flex items-center justify-center flex-shrink-0 mt-1">
                      <ChevronRight className="w-4 h-4 text-white" />
                    </div>
                    <p className="text-[#9CA3B5]">Access comprehensive biological and ecological information</p>
                  </div>
                </div>
                
                <button
                  onClick={() => router.push('/taxonomy_tree')}
                  className="group inline-flex items-center space-x-2 px-8 py-4 rounded-xl bg-gradient-to-r from-[#8B7BFF] to-[#9B8BFF] text-white font-bold shadow-xl shadow-[#8B7BFF]/30 hover:shadow-[#8B7BFF]/50 transition-all duration-300 hover:scale-105"
                >
                  <span>Discover Species</span>
                  <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Highlight */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-12">
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
