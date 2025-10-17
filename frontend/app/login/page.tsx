'use client';
import React, { useState } from 'react';
import useAuth from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { LogIn, Mail, Lock, Network, ArrowLeft, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { getToken } = useAuth();

  useEffect(()=>{
    if (getToken()) router.replace('/select');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      const ok = await login(email, password);
      if (ok) router.push('/select');
      else setError('Invalid credentials. Please check your email and password.');
    } finally {
      setIsLoading(false);
    }
  };

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

      {/* Header */}
      <div className="relative z-10 p-6">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <button
            onClick={() => router.push('/')}
            className="flex items-center space-x-2 text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Home</span>
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] shadow-lg shadow-[#6B72FF]/30">
              <Network className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
              GenealogyTree
            </span>
          </div>
        </div>
      </div>

      {/* Login Form */}
      <div className="relative z-10 flex items-center justify-center min-h-[calc(100vh-120px)] px-4">
        <div className="w-full max-w-md">
          {/* Welcome Card */}
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 shadow-2xl shadow-[#6B72FF]/20">
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] flex items-center justify-center mx-auto mb-4 shadow-lg shadow-[#6B72FF]/30">
                <LogIn className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-[#F5F7FA] mb-2">Welcome Back</h1>
              <p className=" text-[15px] text-[#9CA3B5]">Sign in to continue your genealogical journey</p>
            </div>

            <form onSubmit={submit} className="space-y-6">
              {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Email Field */}
              <div>
                <label className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#9CA3B5]" />
                  <input
                    type="email"
                    required
                    className="w-full pl-11 pr-4 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-lg text-[#F5F7FA] placeholder-[#9CA3B5] focus:outline-none focus:ring-2 focus:ring-[#6B72FF] focus:border-transparent transition-all duration-200"
                    placeholder="Enter your email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#9CA3B5]" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    className="w-full pl-11 pr-12 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-lg text-[#F5F7FA] placeholder-[#9CA3B5] focus:outline-none focus:ring-2 focus:ring-[#6B72FF] focus:border-transparent transition-all duration-200"
                    placeholder="Enter your password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white font-semibold rounded-lg shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Signing In...</span>
                  </div>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            {/* Register Link */}
            <div className="mt-8 text-center">
              <p className="text-[#9CA3B5]">
                Don&apos;t have an account?{' '}
                <button
                  onClick={() => router.push('/register')}
                  className="text-[#6B72FF] hover:text-[#8B7BFF] font-medium transition-colors"
                >
                  Create one now
                </button>
              </p>
            </div>
          </div>
        </div>
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
}
