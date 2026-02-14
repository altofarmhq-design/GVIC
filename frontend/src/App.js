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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  LayoutDashboard, Play, Database, Bell, Settings, 
  Zap, RefreshCw, Network, Radio, Layers, Brain, Target, GitCompare, Cloud,
  Users, LogOut, User, Shield, FileText, Sparkles
} from 'lucide-react';
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { 
  DashboardTab, 
  ProcessingTab, 
  IntegrationTab, 
  DataTab, 
  AlertsTab, 
  SettingsTab,
  MonitoringTab,
  ModelsTab,
  PredictionTab,
  ParetoTab,
  ComparisonTab,
  DataSourcesTab,
  PipelineTab,
  GVICShowcaseTab
} from "@/components/tabs";
import UsersTab from "@/components/tabs/UsersTab";
import LoginPage from "@/pages/LoginPage";
import AuthCallback from "@/pages/AuthCallback";

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
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState(null);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const { user, logout, hasRole, hasPermission, isAdmin } = useAuth();
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    try {
      const [dashRes, statusRes, logsRes, alertsRes, modulesRes] = await Promise.all([
        api.getDashboard(),
        api.getStatus().catch(() => ({ data: {} })),
        api.getLogs(10),
        api.getAlerts(),
        api.getModules()
      ]);
      setDashboard(dashRes.data);
      setSystemStatus(statusRes.data);
      setLogs(logsRes.data.logs);
      setAlerts(alertsRes.data);
      setModules(modulesRes.data.modules);
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
      ext_admin: 'bg-orange-500/20 text-orange-400',
      ext_operator: 'bg-yellow-500/20 text-yellow-400',
      ext_visitor: 'bg-slate-500/20 text-slate-400'
    };
    const labels = {
      super_admin: '최고관리자',
      admin: '관리자',
      operator: '오퍼레이터',
      visitor: '방문객',
      ext_admin: '외부관리자',
      ext_operator: '외부오퍼레이터',
      ext_visitor: '외부방문객'
    };
    return <Badge className={styles[role] || styles.visitor}>{labels[role] || role}</Badge>;
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100" data-testid="app-title">GVIC Engine</h1>
            <p className="text-slate-400 text-sm">7개 특허 모듈 통합 시스템</p>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={fetchData} data-testid="refresh-button">
              <RefreshCw className="w-4 h-4 mr-1" /> 새로고침
            </Button>
            
            {/* User Menu */}
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
          <TabsList className="bg-slate-800 border border-slate-700 mb-6 flex-wrap" data-testid="main-tabs">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-700">
              <LayoutDashboard className="w-4 h-4 mr-2" /> 대시보드
            </TabsTrigger>
            
            {hasPermission('write') && (
              <TabsTrigger value="processing" className="data-[state=active]:bg-slate-700">
                <Play className="w-4 h-4 mr-2" /> 처리
              </TabsTrigger>
            )}
            
            {hasPermission('write') && (
              <TabsTrigger value="models" className="data-[state=active]:bg-slate-700">
                <Layers className="w-4 h-4 mr-2" /> 모델
              </TabsTrigger>
            )}
            
            {hasPermission('process') && (
              <TabsTrigger value="prediction" className="data-[state=active]:bg-slate-700">
                <Brain className="w-4 h-4 mr-2" /> 예측
              </TabsTrigger>
            )}
            
            {hasPermission('process') && (
              <TabsTrigger value="pareto" className="data-[state=active]:bg-slate-700">
                <Target className="w-4 h-4 mr-2" /> 파레토
              </TabsTrigger>
            )}
            
            <TabsTrigger value="comparison" className="data-[state=active]:bg-slate-700">
              <GitCompare className="w-4 h-4 mr-2" /> 비교
            </TabsTrigger>
            
            <TabsTrigger value="monitoring" className="data-[state=active]:bg-slate-700">
              <Radio className="w-4 h-4 mr-2" /> 모니터링
            </TabsTrigger>
            
            {hasPermission('write') && (
              <TabsTrigger value="integration" className="data-[state=active]:bg-slate-700">
                <Network className="w-4 h-4 mr-2" /> 통합
              </TabsTrigger>
            )}
            
            {hasPermission('write') && (
              <TabsTrigger value="datasources" className="data-[state=active]:bg-slate-700">
                <Cloud className="w-4 h-4 mr-2" /> 외부소스
              </TabsTrigger>
            )}
            
            {hasPermission('process') && (
              <TabsTrigger value="pipeline" className="data-[state=active]:bg-slate-700">
                <FileText className="w-4 h-4 mr-2" /> 분석
              </TabsTrigger>
            )}
            
            <TabsTrigger value="showcase" className="data-[state=active]:bg-slate-700 data-[state=active]:bg-amber-600">
              <Sparkles className="w-4 h-4 mr-2" /> 시그널분석
            </TabsTrigger>
            
            <TabsTrigger value="data" className="data-[state=active]:bg-slate-700">
              <Database className="w-4 h-4 mr-2" /> 데이터
            </TabsTrigger>
            
            <TabsTrigger value="alerts" className="data-[state=active]:bg-slate-700">
              <Bell className="w-4 h-4 mr-2" /> 알림
            </TabsTrigger>
            
            {hasRole(['super_admin', 'admin', 'operator']) && (
              <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700">
                <Settings className="w-4 h-4 mr-2" /> 설정
              </TabsTrigger>
            )}
            
            {isAdmin() && (
              <TabsTrigger value="users" className="data-[state=active]:bg-slate-700">
                <Users className="w-4 h-4 mr-2" /> 사용자
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="dashboard">
            <DashboardTab dashboard={dashboard} systemStatus={systemStatus} onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="processing">
            <ProcessingTab onProcess={fetchData} />
          </TabsContent>

          <TabsContent value="models">
            <ModelsTab onModelChange={fetchData} />
          </TabsContent>

          <TabsContent value="prediction">
            <PredictionTab onUpdate={fetchData} />
          </TabsContent>

          <TabsContent value="pareto">
            <ParetoTab onUpdate={fetchData} />
          </TabsContent>

          <TabsContent value="comparison">
            <ComparisonTab />
          </TabsContent>

          <TabsContent value="monitoring">
            <MonitoringTab />
          </TabsContent>

          <TabsContent value="integration">
            <IntegrationTab onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="datasources">
            <DataSourcesTab onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="pipeline">
            <PipelineTab />
          </TabsContent>

          <TabsContent value="showcase">
            <GVICShowcaseTab />
          </TabsContent>

          <TabsContent value="data">
            <DataTab logs={logs} onLogsRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="alerts">
            <AlertsTab alerts={alerts} onRefresh={fetchData} />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsTab 
              sigma={dashboard?.sigma} 
              omega={dashboard?.omega}
              modules={modules}
              onUpdate={fetchData}
            />
          </TabsContent>

          <TabsContent value="users">
            <UsersTab />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-slate-500 text-sm">
        GVIC Engine v2.0.0 • 7개 특허 모듈 통합 시스템 (특허1-6, 6-J)
      </footer>
    </div>
  );
}

// App Router Component
function AppRouter() {
  const location = useLocation();
  
  // Check for session_id in URL hash (Google OAuth callback)
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
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
