import { useState, useEffect, useCallback } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import "@/App.css";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { 
  LayoutDashboard, RefreshCw, Zap, LogOut, User, 
  Package, CreditCard, Key, Store, Settings, TrendingUp
} from 'lucide-react';
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// SaaS 탭 컴포넌트
import { SaasDashboard, MyProductsTab, BillingTab, ApiGuideTab } from "@/components/saas";

// 기존 설정 탭
import { SettingsTab } from "@/components/tabs";

import LoginPage from "@/pages/LoginPage";
import AuthCallback from "@/pages/AuthCallback";

// Protected Route
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

// SaaS 탭 정의
const SAAS_TABS = [
  { id: "dashboard", name: "대시보드", icon: LayoutDashboard, color: "violet" },
  { id: "products", name: "내 상품", icon: Package, color: "blue" },
  { id: "billing", name: "결제", icon: CreditCard, color: "emerald" },
  { id: "api-guide", name: "API 가이드", icon: Key, color: "orange" },
];

// Main Dashboard
function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const subRes = await api.getSubscriptionStatus().catch(() => ({ data: null }));
      setSubscription(subRes.data);
    } catch (error) {
      console.error("Fetch error:", error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleNavigate = (tab, productId = null) => {
    setActiveTab(tab);
    // productId는 나중에 분석 페이지로 전달할 때 사용
  };

  const getRoleBadge = (role) => {
    const styles = {
      super_admin: 'bg-purple-500/20 text-purple-400',
      admin: 'bg-red-500/20 text-red-400',
      operator: 'bg-blue-500/20 text-blue-400',
      visitor: 'bg-gray-500/20 text-gray-400',
    };
    const labels = {
      super_admin: '최고관리자',
      admin: '관리자',
      operator: '오퍼레이터',
      visitor: '방문객',
    };
    return <Badge className={styles[role] || styles.visitor}>{labels[role] || role}</Badge>;
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700 px-6 py-3">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100" data-testid="app-title">GVIC Seller Intelligence Hub</h1>
            <p className="text-slate-400 text-xs">고객 리뷰 기반 셀러 인사이트 플랫폼</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            {/* 구독 상태 */}
            {subscription && (
              <Badge className={`px-3 py-1 ${
                subscription.plan === 'free' ? 'bg-slate-600' : 'bg-violet-600'
              }`}>
                {subscription.plan_name || subscription.plan?.toUpperCase() || 'Free'}
              </Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={fetchData} data-testid="refresh-button">
              <RefreshCw className="w-4 h-4" />
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-2" data-testid="user-menu">
                  <div className="w-6 h-6 rounded-full bg-slate-600 flex items-center justify-center overflow-hidden">
                    {user?.picture ? (
                      <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-4 h-4 text-slate-300" />
                    )}
                  </div>
                  <span className="max-w-[100px] truncate text-xs">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700 w-64">
                <div className="px-3 py-2 border-b border-slate-700">
                  <p className="text-sm font-medium text-slate-100">{user?.name}</p>
                  <p className="text-xs text-slate-400">{user?.email}</p>
                  <div className="mt-1">{getRoleBadge(user?.role)}</div>
                </div>
                
                {/* 구독 정보 */}
                {subscription && (
                  <div className="px-3 py-3 border-b border-slate-700 bg-gradient-to-r from-violet-900/20 to-slate-800">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-400">현재 플랜</span>
                      <Badge className="bg-violet-600 text-xs">
                        {subscription.plan_name || subscription.plan?.toUpperCase()}
                      </Badge>
                    </div>
                    {subscription.usage && (
                      <div className="text-xs text-slate-500 space-y-1">
                        <div className="flex justify-between">
                          <span>분석 사용량</span>
                          <span className="text-violet-400">
                            {subscription.usage.analysis_count || 0} / {subscription.limits?.monthly_analysis || '∞'}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <DropdownMenuItem 
                  onClick={() => setActiveTab("billing")} 
                  className="text-slate-300 cursor-pointer"
                >
                  <CreditCard className="w-4 h-4 mr-2 text-emerald-400" /> 구독 관리
                </DropdownMenuItem>

                <DropdownMenuItem 
                  onClick={() => setActiveTab("api-guide")} 
                  className="text-slate-300 cursor-pointer"
                >
                  <Key className="w-4 h-4 mr-2 text-orange-400" /> API 키 관리
                </DropdownMenuItem>

                <DropdownMenuSeparator className="bg-slate-700" />
                
                <DropdownMenuItem onClick={handleLogout} className="text-red-400 cursor-pointer">
                  <LogOut className="w-4 h-4 mr-2" /> 로그아웃
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4 max-w-7xl mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          {/* 탭 리스트 */}
          <TabsList className="bg-slate-800/50 p-1 gap-1">
            {SAAS_TABS.map((tab) => (
              <TabsTrigger 
                key={tab.id} 
                value={tab.id} 
                className={`data-[state=active]:bg-${tab.color}-600/30 gap-2 px-4 py-2`}
                data-testid={`tab-${tab.id}`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </TabsTrigger>
            ))}
            <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700 gap-2 px-4 py-2">
              <Settings className="w-4 h-4" /> 설정
            </TabsTrigger>
          </TabsList>

          {/* 탭 컨텐츠 */}
          <TabsContent value="dashboard">
            <SaasDashboard onNavigate={handleNavigate} />
          </TabsContent>

          <TabsContent value="products">
            <MyProductsTab onAnalyze={(productId) => console.log('Analyze:', productId)} />
          </TabsContent>

          <TabsContent value="billing">
            <BillingTab />
          </TabsContent>

          <TabsContent value="api-guide">
            <ApiGuideTab />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsTab />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-slate-500 text-xs">
        GVIC Seller Intelligence Hub v3.0.0 • 고객 리뷰 기반 셀러 인사이트 플랫폼
      </footer>
    </div>
  );
}

// App Router
function AppRouter() {
  const location = useLocation();
  
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return <AppRouter />;
}

export default App;
