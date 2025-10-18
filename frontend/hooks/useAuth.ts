import { useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL ;

export default function useAuth(){
  const login = useCallback(async (email: string, password: string) => {
    try{
      const res = await fetch(`${API_BASE}/api/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      return true;
    }catch(e){
      console.error(e);
      return false;
    }
  }, []);

  const register = useCallback(async (payload: any) => {
    try{
      const res = await fetch(`${API_BASE}/api/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return res.ok;
    }catch(e){
      console.error(e);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
  }, []);

  const getToken = useCallback(()=> localStorage.getItem('token'), []);

  return { login, register, logout, getToken };
}
