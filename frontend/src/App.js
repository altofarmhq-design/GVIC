import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { 
  LayoutDashboard, Play, Database, Bell, Settings, 
  Zap, RefreshCw, Network, Radio, Layers, Brain, Target
} from 'lucide-react';
import { api } from "@/lib/api";
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
  ParetoTab
} from "@/components/tabs";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState(null);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);

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
          <div className="ml-auto">
            <Button variant="outline" size="sm" onClick={fetchData} data-testid="refresh-button">
              <RefreshCw className="w-4 h-4 mr-1" /> 새로고침
            </Button>
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
            <TabsTrigger value="processing" className="data-[state=active]:bg-slate-700">
              <Play className="w-4 h-4 mr-2" /> 처리
            </TabsTrigger>
            <TabsTrigger value="models" className="data-[state=active]:bg-slate-700">
              <Layers className="w-4 h-4 mr-2" /> 모델
            </TabsTrigger>
            <TabsTrigger value="prediction" className="data-[state=active]:bg-slate-700">
              <Brain className="w-4 h-4 mr-2" /> 예측
            </TabsTrigger>
            <TabsTrigger value="pareto" className="data-[state=active]:bg-slate-700">
              <Target className="w-4 h-4 mr-2" /> 파레토
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="data-[state=active]:bg-slate-700">
              <Radio className="w-4 h-4 mr-2" /> 모니터링
            </TabsTrigger>
            <TabsTrigger value="integration" className="data-[state=active]:bg-slate-700">
              <Network className="w-4 h-4 mr-2" /> 통합
            </TabsTrigger>
            <TabsTrigger value="data" className="data-[state=active]:bg-slate-700">
              <Database className="w-4 h-4 mr-2" /> 데이터
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-slate-700">
              <Bell className="w-4 h-4 mr-2" /> 알림
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700">
              <Settings className="w-4 h-4 mr-2" /> 설정
            </TabsTrigger>
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

          <TabsContent value="monitoring">
            <MonitoringTab />
          </TabsContent>

          <TabsContent value="integration">
            <IntegrationTab onRefresh={fetchData} />
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
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-slate-500 text-sm">
        GVIC Engine v2.0.0 • 7개 특허 모듈 통합 시스템 (특허1-6, 6-J)
      </footer>
    </div>
  );
}

export default App;
