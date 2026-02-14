import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '@/lib/api';
import { RefreshCw } from 'lucide-react';

/**
 * AuthCallback - Handles OAuth callback with session_id
 * REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processCallback = async () => {
      // Extract session_id from URL hash
      const hash = location.hash;
      const sessionIdMatch = hash.match(/session_id=([^&]+)/);
      
      if (!sessionIdMatch) {
        console.error('No session_id found in URL');
        navigate('/login', { replace: true });
        return;
      }

      const sessionId = sessionIdMatch[1];

      try {
        // Exchange session_id for user session
        const response = await api.googleSession(sessionId);
        
        if (response.data.success) {
          // Navigate to dashboard with user data
          navigate('/', { 
            replace: true, 
            state: { user: response.data.user } 
          });
        } else {
          throw new Error('Session exchange failed');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login', { 
          replace: true, 
          state: { error: 'Google 로그인에 실패했습니다' } 
        });
      }
    };

    processCallback();
  }, [navigate, location]);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500 mx-auto mb-4" />
        <p className="text-slate-400">로그인 처리 중...</p>
      </div>
    </div>
  );
}
