'use client';
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import useAuth from '@/hooks/useAuth';

export default function AuthGuard({ children }: { children: React.ReactNode }){
  const router = useRouter();
  const { getToken } = useAuth();
  const [checked, setChecked] = useState(false);

  useEffect(()=>{
    const t = getToken();
    if (!t) {
      router.replace('/login');
      return;
    }
    setChecked(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[]);

  if (!checked) return null;
  return <>{children}</>;
}
