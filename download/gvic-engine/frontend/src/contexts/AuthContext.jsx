import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check auth status on mount
  const checkAuth = useCallback(async () => {
    try {
      const response = await api.getMe();
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const response = await api.login(email, password);
    if (response.data.success) {
      // Store token
      localStorage.setItem('token', response.data.token);
      setUser(response.data.user);
      setIsAuthenticated(true);
    }
    return response.data;
  };

  const register = async (email, password, passwordConfirm, name) => {
    const response = await api.register(email, password, passwordConfirm, name);
    // 승인 대기 상태이므로 자동 로그인하지 않음
    return response.data;
  };

  const googleLogin = (sessionId) => {
    return api.googleSession(sessionId);
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  const hasRole = (requiredRoles) => {
    if (!user) return false;
    // super_admin과 admin은 모든 내부 권한 접근 가능
    if (user.role === 'super_admin' || user.role === 'admin') return true;
    return requiredRoles.includes(user.role);
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    // super_admin과 admin은 모든 권한
    if (user.role === 'super_admin' || user.role === 'admin') return true;
    
    const rolePermissions = {
      // 내부 역할
      operator: ['read', 'write', 'process', 'report'],
      visitor: ['read'],
      // 외부 역할 (모두 visitor와 동일)
      ext_admin: ['read'],
      ext_operator: ['read'],
      ext_visitor: ['read']
    };
    
    return rolePermissions[user.role]?.includes(permission) || false;
  };

  const isInternalUser = () => {
    if (!user) return false;
    return ['super_admin', 'admin', 'operator', 'visitor'].includes(user.role);
  };

  const isAdmin = () => {
    if (!user) return false;
    return ['super_admin', 'admin'].includes(user.role);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      isAuthenticated,
      login,
      register,
      googleLogin,
      logout,
      hasRole,
      hasPermission,
      isInternalUser,
      isAdmin,
      checkAuth
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
