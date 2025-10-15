'use client';
import React from 'react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';

function SelectPageInner(){
  const router = useRouter();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow w-full max-w-lg">
        <h2 className="text-2xl font-bold mb-4">Which tree do you want to draw?</h2>
        <div className="grid grid-cols-1 gap-4">
          <button onClick={()=>router.push('/family_tree')} className="p-4 bg-blue-500 text-white rounded">Family Tree</button>
          <button onClick={()=>router.push('/language_tree')} className="p-4 bg-purple-500 text-white rounded">Language Family Tree</button>
          <button onClick={()=>router.push('/taxonomy_tree')} className="p-4 bg-green-500 text-white rounded">Species Taxonomy Tree</button>
        </div>
      </div>
    </div>
  );
}

export default function SelectPage(){
  return (
    <AuthGuard>
      <SelectPageInner />
    </AuthGuard>
  );
}
