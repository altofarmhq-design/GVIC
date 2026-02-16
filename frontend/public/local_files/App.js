/**
 * GVIC 통합 시스템 - 로컬 버전
 * 14개 특허 기반 탭 구성
 * 
 * 경로: C:\gvic\frontend\src\App.js
 */

import { useState, useEffect, useCallback } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import "./App.css";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./components/ui/dropdown-menu";
import { 
  LayoutDashboard, Upload, Brain, Target, Activity,
  Shield, Filter, Calculator, Package, Database,
  Lock, Factory, Download, Settings,
  Zap, RefreshCw, LogOut, User
} from 'lucide-react';
import { api } from "./lib/api";
import { useAuth } from "./contexts/AuthContext";
import { DashboardTab, SettingsTab } from "./components/tabs";
import {
  JInputTab,
  LLIntentTab,
  HCoreTab,
  AGateTab,
  EShieldTab,
  GRefineTab,
  BCalcTab,
  CExecTab,
  DLedgerTab,
  IIntegrityTab,
  FFieldTab,
  OutputTab
} from "./components/tabs/PatentTabs";
import LoginPage from "./pages/LoginPage";
import AuthCallback from "./pages/AuthCallback";

// Protected Route Component
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

// Main Dashboard Component
function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [dashRes, statusRes] = await Promise.all([
        api.getDashboard(),
        api.getStatus().catch(() => ({ data: {} }))
      ]);
      setDashboard(dashRes.data);
      setSystemStatus(statusRes.data);
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
      visitor: 'bg-gray-500/20 text-gray-400'
    };
    const labels = {
      super_admin: '최고관리자',
      admin: '관리자',
      operator: '오퍼레이터',
      visitor: '방문객'
    };
    return <Badge className={styles[role] || styles.visitor}>{labels[role] || role}</Badge>;
  };

  // 탭 구성 (14개)
  const tabs = [
    // 관리
    { id: "dashboard", label: "대시보드", icon: LayoutDashboard, color: "slate" },
    // 입력단
    { id: "j-input", label: "J:입력", icon: Upload, color: "blue", section: "입력단" },
    { id: "ll-intent", label: "LL:의도", icon: Brain, color: "purple" },
    // 코어
    { id: "h-core", label: "H:코어", icon: Target, color: "amber", section: "코어" },
    { id: "a-gate", label: "A:인지", icon: Activity, color: "cyan" },
    { id: "e-shield", label: "E:검역", icon: Shield, color: "red" },
    { id: "g-refine", label: "G:정제", icon: Filter, color: "emerald" },
    { id: "b-calc", label: "B:산출", icon: Calculator, color: "violet" },
    { id: "c-exec", label: "C:모듈화", icon: Package, color: "orange" },
    { id: "d-ledger", label: "D:축적", icon: Database, color: "teal" },
    { id: "i-integrity", label: "I:무결성", icon: Lock, color: "indigo" },
    // 출력단
    { id: "f-field", label: "F:상품화", icon: Factory, color: "pink", section: "출력단" },
    { id: "output", label: "출력", icon: Download, color: "sky" },
    // 관리
    { id: "settings", label: "설정", icon: Settings, color: "slate", section: "관리" },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100">GVIC Engine</h1>
            <p className="text-slate-400 text-sm">시그널 온톨로지 자산화 플랫폼 (12개 특허 기반)</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Badge variant="outline" className="text-slate-400 border-slate-600">
              로컬 환경
            </Badge>
            <Button variant="outline" size="sm" onClick={fetchData}>
              <RefreshCw className="w-4 h-4 mr-1" /> 새로고침
            </Button>
            
            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-slate-600 flex items-center justify-center overflow-hidden">
                    {user?.picture ? (
                      <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-4 h-4 text-slate-300" />
                    )}
                  </div>
                  <span className="max-w-[100px] truncate">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium text-slate-100">{user?.name}</p>
                  <p className="text-xs text-slate-400">{user?.email}</p>
                  <div className="mt-1">{getRoleBadge(user?.role)}</div>
                </div>
                <DropdownMenuSeparator className="bg-slate-700" />
                <DropdownMenuItem onClick={handleLogout} className="text-red-400 focus:text-red-400 cursor-pointer">
                  <LogOut className="w-4 h-4 mr-2" /> 로그아웃
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800 border border-slate-700 mb-6 flex-wrap h-auto gap-1 p-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <TabsTrigger 
                  key={tab.id}
                  value={tab.id} 
                  className={`data-[state=active]:bg-${tab.color}-600 data-[state=active]:text-white`}
                >
                  <Icon className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* 대시보드 */}
          <TabsContent value="dashboard">
            <DashboardTab dashboard={dashboard} systemStatus={systemStatus} onRefresh={fetchData} />
          </TabsContent>

          {/* 입력단 */}
          <TabsContent value="j-input">
            <JInputTab />
          </TabsContent>

          <TabsContent value="ll-intent">
            <LLIntentTab />
          </TabsContent>

          {/* 코어 */}
          <TabsContent value="h-core">
            <HCoreTab />
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

          <TabsContent value="d-ledger">
            <DLedgerTab />
          </TabsContent>

          <TabsContent value="i-integrity">
            <IIntegrityTab />
          </TabsContent>

          {/* 출력단 */}
          <TabsContent value="f-field">
            <FFieldTab />
          </TabsContent>

          <TabsContent value="output">
            <OutputTab />
          </TabsContent>

          {/* 관리 */}
          <TabsContent value="settings">
            <SettingsTab 
              sigma={dashboard?.sigma} 
              omega={dashboard?.omega}
              onUpdate={fetchData}
            />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-slate-500 text-sm">
        GVIC Engine v2.0.0 • 시그널 온톨로지 자산화 플랫폼 • 12개 특허 기반
      </footer>
    </div>
  );
}

// App Router Component
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
