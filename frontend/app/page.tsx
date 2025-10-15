'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';

export default function RootRedirect(){
  const router = useRouter();
  const { getToken } = useAuth();

  useEffect(()=>{
    const t = getToken();
    if (t) router.replace('/select');
    else router.replace('/login');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  return null;
}
