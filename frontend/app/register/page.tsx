'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

function useAuth() {
  // API Gateway base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8080';
  
  const register = async ({ email, password, full_name }: { email: string; password: string; full_name: string }) => {
    try {
      console.log('Sending registration request:', { email, full_name, password: '***' });
      
      const res = await fetch(`${API_BASE}/api/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name }),
      });
      
      console.log('Response status:', res.status);
      
      if (!res.ok) {
        const error = await res.json();
        console.error('Registration error:', error);
        
        // Handle validation errors (422)
        if (error.errors && Array.isArray(error.errors)) {
          throw new Error(error.errors.join(', '));
        }
        
        // Handle other errors
        throw new Error(error.detail || 'Registration failed');
      }
      
      const data = await res.json();
      console.log('Registration successful:', data);
      return { success: true };
    } catch (err) {
      console.error('Registration exception:', err);
      return { success: false, error: err instanceof Error ? err.message : 'Registration failed' };
    }
  };

  const getToken = () => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  };

  return { register, getToken };
}

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const { getToken } = useAuth();

  useEffect(()=>{
    if (getToken()) router.replace('/select');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const result = await register({ email, password, full_name: fullName });
    if (result.success) {
      router.push('/login');
    } else {
      setError(result.error || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={submit} className="w-full max-w-md bg-white p-8 rounded shadow">
        <h2 className="text-2xl font-bold mb-4">Register</h2>
        {error && <div className="mb-2 text-red-600">{error}</div>}
        <label className="block mb-2">Full name</label>
        <input className="w-full p-2 border rounded mb-4" value={fullName} onChange={e=>setFullName(e.target.value)} />
        <label className="block mb-2">Email</label>
        <input className="w-full p-2 border rounded mb-4" value={email} onChange={e=>setEmail(e.target.value)} />
        <label className="block mb-2">Password</label>
        <input type="password" className="w-full p-2 border rounded mb-4" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="w-full bg-green-600 text-white p-2 rounded">Register</button>
      </form>
    </div>
  );
}
