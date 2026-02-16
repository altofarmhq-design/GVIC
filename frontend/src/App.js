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
} from "@/components/ui/dropdown-menu";
import { 
  LayoutDashboard, RefreshCw, Zap, Users, LogOut, User, Settings,
  Upload, Brain, Cpu, Eye, ShieldAlert, Sparkles, Calculator,
  Play, Activity, Database, Lock, Key, Plug, Coins, Award
} from 'lucide-react';
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// 기존 탭
import { DashboardTab, SettingsTab } from "@/components/tabs";
import UsersTab from "@/components/tabs/UsersTab";

// 특허 기반 탭
import {
  JInputTab,
  LLIntentTab,
  HCoreTab,
  AGateTab,
  EShieldTab,
  GRefineTab,
  BCalcTab,
  CExecTab,
  FFieldTab,
  DLedgerTab,
  IIntegrityTab,
  APIWebhookTab,
  ConnectorTab,
  MyAssetsTab
} from "@/components/tabs/patent";

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

// 14개 탭 정의
const PATENT_TABS = [
  { id: "j-input", code: "J", name: "입력", icon: Upload, color: "blue", patent: "J" },
  { id: "ll-intent", code: "LL", name: "의도", icon: Brain, color: "violet", patent: "LL" },
  { id: "h-core", code: "H", name: "코어", icon: Cpu, color: "purple", patent: "H" },
  { id: "a-gate", code: "A", name: "게이트", icon: Eye, color: "cyan", patent: "A" },
  { id: "e-shield", code: "E", name: "방어막", icon: ShieldAlert, color: "red", patent: "E" },
  { id: "g-refine", code: "G", name: "정제", icon: Sparkles, color: "emerald", patent: "G" },
  { id: "b-calc", code: "B", name: "산출", icon: Calculator, color: "orange", patent: "B" },
  { id: "c-exec", code: "C", name: "집행", icon: Play, color: "indigo", patent: "C" },
  { id: "f-field", code: "F", name: "실행", icon: Activity, color: "pink", patent: "F" },
  { id: "d-ledger", code: "D", name: "원장", icon: Database, color: "teal", patent: "D" },
  { id: "i-integrity", code: "I", name: "무결성", icon: Lock, color: "slate", patent: "I" },
];

// Main Dashboard
function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [userPoints, setUserPoints] = useState(null);
  
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const dashRes = await api.getDashboard();
      setDashboard(dashRes.data);
      
      // 포인트 정보 조회
      try {
        const pointsRes = await api.getPointBalance();
        setUserPoints(pointsRes.data);
      } catch (e) {
        console.log("Points fetch optional:", e);
      }
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
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-100" data-testid="app-title">GVIC Engine</h1>
            <p className="text-slate-400 text-xs">12개 특허 모듈 통합 시스템</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
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
                  <span className="max-w-[80px] truncate text-xs">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700 w-64">
                <div className="px-3 py-2 border-b border-slate-700">
                  <p className="text-sm font-medium text-slate-100">{user?.name}</p>
                  <p className="text-xs text-slate-400">{user?.email}</p>
                  <div className="mt-1">{getRoleBadge(user?.role)}</div>
                </div>
                
                {/* 포인트 정보 */}
                <div className="px-3 py-3 border-b border-slate-700 bg-gradient-to-r from-amber-900/20 to-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Coins className="w-3 h-3 text-amber-400" />
                      내 포인트
                    </span>
                    <Badge variant="outline" className="text-amber-400 border-amber-600 text-xs">
                      {userPoints ? `${userPoints.available_points?.toLocaleString()}P` : '0P'}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div className="flex justify-between">
                      <span>현금 환산</span>
                      <span className="text-green-400">₩{userPoints ? (userPoints.cash_equivalent || 0).toLocaleString() : '0'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>환율</span>
                      <span className="text-slate-400">₩1 = 0.1P</span>
                    </div>
                  </div>
                </div>

                {/* 자산 현황 링크 */}
                <DropdownMenuItem 
                  onClick={() => setActiveTab("my-assets")} 
                  className="text-slate-300 cursor-pointer"
                >
                  <Award className="w-4 h-4 mr-2 text-purple-400" /> 내 자산 현황
                </DropdownMenuItem>
                
                <DropdownMenuItem onClick={handleLogout} className="text-red-400 cursor-pointer">
                  <LogOut className="w-4 h-4 mr-2" /> 로그아웃
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          {/* 탭 리스트 - 2줄로 구성 */}
          <div className="space-y-2">
            {/* 첫 번째 줄: 대시보드 + 특허 탭 (J ~ G) */}
            <TabsList className="bg-slate-800/50 p-1 flex-wrap h-auto gap-1">
              <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-700 gap-1 text-xs px-2 py-1.5">
                <LayoutDashboard className="w-3.5 h-3.5" /> 대시보드
              </TabsTrigger>
              
              {PATENT_TABS.slice(0, 6).map((tab) => (
                <TabsTrigger 
                  key={tab.id} 
                  value={tab.id} 
                  className={`data-[state=active]:bg-${tab.color}-600/30 gap-1 text-xs px-2 py-1.5`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  <span className="font-bold">{tab.code}</span>:{tab.name}
                </TabsTrigger>
              ))}
            </TabsList>

            {/* 두 번째 줄: 특허 탭 (B ~ I) + 설정/사용자 */}
            <TabsList className="bg-slate-800/50 p-1 flex-wrap h-auto gap-1">
              {PATENT_TABS.slice(6).map((tab) => (
                <TabsTrigger 
                  key={tab.id} 
                  value={tab.id} 
                  className={`data-[state=active]:bg-${tab.color}-600/30 gap-1 text-xs px-2 py-1.5`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  <span className="font-bold">{tab.code}</span>:{tab.name}
                </TabsTrigger>
              ))}
              
              <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700 gap-1 text-xs px-2 py-1.5">
                <Settings className="w-3.5 h-3.5" /> 설정
              </TabsTrigger>

              <TabsTrigger value="api-webhook" className="data-[state=active]:bg-purple-600/30 gap-1 text-xs px-2 py-1.5">
                <Key className="w-3.5 h-3.5" /> API연동
              </TabsTrigger>

              <TabsTrigger value="connector" className="data-[state=active]:bg-indigo-600/30 gap-1 text-xs px-2 py-1.5">
                <Plug className="w-3.5 h-3.5" /> 외부연동
              </TabsTrigger>
              
              {isAdmin() && (
                <TabsTrigger value="users" className="data-[state=active]:bg-slate-700 gap-1 text-xs px-2 py-1.5">
                  <Users className="w-3.5 h-3.5" /> 사용자
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          {/* 탭 컨텐츠 */}
          <TabsContent value="dashboard">
            <DashboardTab dashboard={dashboard} onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="j-input">
            <JInputTab />
          </TabsContent>

          <TabsContent value="ll-intent">
            <LLIntentTab />
          </TabsContent>

          <TabsContent value="h-core">
            <HCoreTab onUpdate={fetchData} />
          </TabsContent>

          <TabsContent value="a-gate">
            <AGateTab />
          </TabsContent>

          <TabsContent value="e-shield">
            <EShieldTab />
          </TabsContent>

          <TabsContent value="g-refine">
            <GRefineTab />
          </TabsContent>

          <TabsContent value="b-calc">
            <BCalcTab />
          </TabsContent>

          <TabsContent value="c-exec">
            <CExecTab />
          </TabsContent>

          <TabsContent value="f-field">
            <FFieldTab />
          </TabsContent>

          <TabsContent value="d-ledger">
            <DLedgerTab />
          </TabsContent>

          <TabsContent value="i-integrity">
            <IIntegrityTab />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsTab 
              sigma={dashboard?.sigma} 
              omega={dashboard?.omega}
              onUpdate={fetchData}
            />
          </TabsContent>

          <TabsContent value="api-webhook">
            <APIWebhookTab />
          </TabsContent>

          <TabsContent value="connector">
            <ConnectorTab />
          </TabsContent>

          <TabsContent value="users">
            <UsersTab />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-slate-500 text-xs">
        GVIC Engine v2.0.0 • 12개 특허 모듈 통합 시스템
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
