'use client';
import React, { useState } from 'react';
import useAuth from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { getToken } = useAuth();

  useEffect(()=>{
    if (getToken()) router.replace('/select');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const ok = await login(email, password);
    if (ok) router.push('/select');
    else setError('Invalid credentials');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={submit} className="w-full max-w-md bg-white p-8 rounded shadow">
        <h2 className="text-2xl font-bold mb-4">Login</h2>
        {error && <div className="mb-2 text-red-600">{error}</div>}
        <label className="block mb-2">Email</label>
        <input className="w-full p-2 border rounded mb-4" value={email} onChange={e=>setEmail(e.target.value)} />
        <label className="block mb-2">Password</label>
        <input type="password" className="w-full p-2 border rounded mb-4" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="w-full bg-blue-600 text-white p-2 rounded">Login</button>
      </form>
    </div>
  );
}
