import { useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_GATEWAY_URL;

// Simple cookie helpers (client-side). Note: HttpOnly cookies must be set by server.
function setCookie(name: string, value: string, expiresDays?: number) {
  const secure = location.protocol === 'https:' ? '; Secure' : '';
  const expires = expiresDays
    ? new Date(Date.now() + expiresDays * 864e5).toUTCString()
    : undefined;
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}${expires ? '; expires=' + expires : ''}; path=/; SameSite=Lax${secure}`;
}

function setCookieWithMaxAge(name: string, value: string, maxAgeSeconds?: number) {
  const secure = location.protocol === 'https:' ? '; Secure' : '';
  const maxAge = typeof maxAgeSeconds === 'number' ? `; max-age=${maxAgeSeconds}` : '';
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}${maxAge}; path=/; SameSite=Lax${secure}`;
}

function getCookie(name: string) {
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  for (const c of cookies) {
    const [k, ...v] = c.split('=');
    if (decodeURIComponent(k) === name) return decodeURIComponent(v.join('='));
  }
  return null;
}

function removeCookie(name: string) {
  // Set to past date
  document.cookie = `${encodeURIComponent(name)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

export default function useAuth() {
  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/users/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) return false;
      const data = await res.json();

      // Prefer server-provided expiry if present (in seconds or ISO string)
      if (data.expires_in) {
        // expires_in assumed seconds
        setCookieWithMaxAge('token', data.access_token, Number(data.expires_in));
      } else if (data.expires_at) {
        // expires_at assumed ISO datetime
        const expiresDate = new Date(data.expires_at);
        const days = Math.ceil((expiresDate.getTime() - Date.now()) / 864e5);
        setCookie('token', data.access_token, days > 0 ? days : 1);
      } else {
        // default: 1 hour
        setCookieWithMaxAge('token', data.access_token, 3600);
      }

      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  }, []);

  const register = useCallback(async (payload: any) => {
    try {
      const res = await fetch(`${API_BASE}/api/users/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      return res.ok;
    } catch (e) {
      console.error(e);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    removeCookie('token');
  }, []);

  const getToken = useCallback(() => getCookie('token'), []);

  return { login, register, logout, getToken };
}
