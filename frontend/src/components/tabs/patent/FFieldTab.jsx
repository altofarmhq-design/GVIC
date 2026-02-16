import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  Server,
  Thermometer,
  Cpu,
  HardDrive,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Play,
  Pause,
  BarChart3,
  Gauge,
  Shield,
  Clock,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Database,
  Lock
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * F:실행 - 물리 계층 자원 집행 시스템
 * (Physical Layer Resource Execution System Based on Entropy Control)
 */
export const FFieldTab = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  // 상태 데이터
  const [factoryBalance, setFactoryBalance] = useState(null);
  const [entropyStatus, setEntropyStatus] = useState(null);
  const [thresholds, setThresholds] = useState(null);
  const [fieldStats, setFieldStats] = useState(null);
  const [recentExecutions, setRecentExecutions] = useState([]);
  const [killSwitchLogs, setKillSwitchLogs] = useState([]);
  
  // 자원 사영 테스트
  const [projectionResult, setProjectionResult] = useState(null);
  const [projecting, setProjecting] = useState(false);

  // 데이터 로드
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [balanceRes, entropyRes, thresholdsRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/patent/f/factory-balance`),
        axios.get(`${API_URL}/api/patent/f/entropy-status`),
        axios.get(`${API_URL}/api/patent/f/thresholds`),
        axios.get(`${API_URL}/api/patent/f/stats`)
      ]);
      
      setFactoryBalance(balanceRes.data.factory_balance);
      setEntropyStatus(entropyRes.data.entropy_status);
      setThresholds(thresholdsRes.data.thresholds);
      setFieldStats(statsRes.data.stats);
    } catch (error) {
      console.error('데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // 자동 새로고침
  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(loadDashboardData, 5000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, loadDashboardData]);

  // 자원 사영 테스트
  const runProjectionTest = async () => {
    setProjecting(true);
    try {
      const response = await axios.post(`${API_URL}/api/patent/f/project-resources`, {
        execution_id: `EXEC_${Date.now()}`,
        total_value: 1000,
        public_allocation: 500,
        operation_allocation: 300,
        management_allocation: 200
      });
      setProjectionResult(response.data);
    } catch (error) {
      console.error('자원 사영 실패:', error);
    } finally {
      setProjecting(false);
    }
  };

  // 팩토리 재균형
  const runRebalance = async () => {
    try {
      await axios.post(`${API_URL}/api/patent/f/rebalance`);
      loadDashboardData();
    } catch (error) {
      console.error('재균형 실패:', error);
    }
  };

  // 엔트로피 피드백
  const runEntropyFeedback = async () => {
    try {
      await axios.post(`${API_URL}/api/patent/f/entropy-feedback`);
      loadDashboardData();
    } catch (error) {
      console.error('피드백 실패:', error);
    }
  };

  // 엔트로피 상태 색상
  const getEntropyStatusColor = (status) => {
    if (status === 'normal') return 'text-emerald-400';
    if (status === 'warning') return 'text-amber-400';
    return 'text-red-400';
  };

  // 효율 색상
  const getEfficiencyColor = (efficiency) => {
    if (efficiency >= 0.8) return 'bg-emerald-500';
    if (efficiency >= 0.6) return 'bg-amber-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-pink-500/20 to-rose-500/20 border border-pink-500/30">
            <Activity className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">F:실행 - 물리 계층 집행</h2>
            <p className="text-slate-400 text-sm">Physical Layer Resource Execution System</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            data-testid="f-field-auto-refresh-btn"
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'border-emerald-500 text-emerald-400' : ''}
          >
            {autoRefresh ? <Pause className="w-4 h-4 mr-1" /> : <Play className="w-4 h-4 mr-1" />}
            {autoRefresh ? '자동 갱신 중' : '자동 갱신'}
          </Button>
          <Button data-testid="f-field-refresh-btn" variant="outline" size="sm" onClick={loadDashboardData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </div>

      {/* 수식 표시 */}
      <Card className="bg-slate-800/50 border-pink-500/30">
        <CardContent className="py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-pink-500/50 text-pink-400">수리 모델</Badge>
              <code className="text-pink-300 text-sm font-mono">
                E_i(t) = ∫(R_alloc · F_i - κ × dS_i/dt) dt
              </code>
            </div>
            <div className="text-slate-400 text-xs">
              C:집행 → <span className="text-pink-400 font-bold">F:실행</span> → D:원장
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="dashboard" className="data-[state=active]:bg-pink-500/20">
            <Gauge className="w-4 h-4 mr-1" />
            대시보드
          </TabsTrigger>
          <TabsTrigger value="nodes" className="data-[state=active]:bg-pink-500/20">
            <Server className="w-4 h-4 mr-1" />
            물리 노드
          </TabsTrigger>
          <TabsTrigger value="entropy" className="data-[state=active]:bg-pink-500/20">
            <TrendingUp className="w-4 h-4 mr-1" />
            엔트로피
          </TabsTrigger>
          <TabsTrigger value="projection" className="data-[state=active]:bg-pink-500/20">
            <BarChart3 className="w-4 h-4 mr-1" />
            자원 사영
          </TabsTrigger>
        </TabsList>

        {/* 대시보드 탭 */}
        <TabsContent value="dashboard" className="space-y-4">
          {/* 상태 카드 */}
          <div className="grid grid-cols-4 gap-4">
            {/* 시스템 상태 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">시스템 상태</span>
                  {fieldStats?.system_health === 'normal' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                  )}
                </div>
                <div className="text-2xl font-bold text-white">
                  {fieldStats?.system_health === 'normal' ? '정상' : '주의'}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {entropyStatus?.status === 'normal' ? '엔트로피 안정' : '엔트로피 주의'}
                </div>
              </CardContent>
            </Card>

            {/* 활성 노드 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">활성 노드</span>
                  <Server className="w-5 h-5 text-blue-400" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {fieldStats?.physical_layer?.active_nodes || 3}
                  <span className="text-sm text-slate-400 ml-1">
                    / {fieldStats?.physical_layer?.total_nodes || 3}
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-1">물리 계층 노드</div>
              </CardContent>
            </Card>

            {/* 에너지 효율 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">에너지 효율</span>
                  <Zap className="w-5 h-5 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {((entropyStatus?.energy_efficiency || 0.67) * 100).toFixed(1)}%
                </div>
                <Progress 
                  value={(entropyStatus?.energy_efficiency || 0.67) * 100} 
                  className="h-1 mt-2"
                />
              </CardContent>
            </Card>

            {/* 총 집행 수 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-slate-400 text-sm">총 집행</span>
                  <Activity className="w-5 h-5 text-pink-400" />
                </div>
                <div className="text-2xl font-bold text-white">
                  {fieldStats?.physical_layer?.total_executions || 0}
                </div>
                <div className="text-xs text-slate-500 mt-1">물리 자원 사영</div>
              </CardContent>
            </Card>
          </div>

          {/* 팩토리 균형 상태 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-pink-400" />
                  팩토리 균형 상태
                </CardTitle>
                <div className="flex items-center gap-2">
                  {factoryBalance?.system_balanced ? (
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      균형
                    </Badge>
                  ) : (
                    <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                      <AlertTriangle className="w-3 h-3 mr-1" />
                      재균형 필요
                    </Badge>
                  )}
                  <Button data-testid="f-field-rebalance-btn" size="sm" variant="outline" onClick={runRebalance}>
                    <RefreshCw className="w-3 h-3 mr-1" />
                    재균형
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {factoryBalance?.regions && Object.entries(factoryBalance.regions).map(([region, data]) => (
                  <div key={region} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-white capitalize">
                        {region === 'public' ? '공공 (5)' : region === 'operation' ? '운영 (3)' : '관리 (2)'}
                      </span>
                      {data.is_balanced ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">평균 부하</span>
                        <span className="text-white">{(data.average_load * 100).toFixed(1)}%</span>
                      </div>
                      <Progress value={data.average_load * 100} className="h-2" />
                      
                      <div className="flex justify-between text-xs text-slate-500">
                        <span>목표: {(data.target_load * 100).toFixed(0)}%</span>
                        <span>편차: {(data.deviation_from_target * 100).toFixed(1)}%</span>
                      </div>
                      
                      <div className="text-xs text-slate-400 mt-2">
                        평형 상수: <span className="text-pink-400">{data.equilibrium_constant}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 임계치 현황 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Shield className="w-5 h-5 text-pink-400" />
                열역학적 임계치 (Kill-switch)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {thresholds && (
                  <>
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Thermometer className="w-4 h-4 text-red-400" />
                        <span className="text-sm text-slate-400">최대 온도</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.temperature_max}°C</div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-sm text-slate-400">최대 CPU</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.cpu_utilization_max}%</div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="w-4 h-4 text-purple-400" />
                        <span className="text-sm text-slate-400">최대 메모리</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.memory_utilization_max}%</div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-4 h-4 text-amber-400" />
                        <span className="text-sm text-slate-400">최대 엔트로피율</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.entropy_rate_max}</div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm text-slate-400">최대 신호 감쇄</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.signal_decay_max}</div>
                    </div>
                    
                    <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-pink-400" />
                        <span className="text-sm text-slate-400">최대 마모율</span>
                      </div>
                      <div className="text-xl font-bold text-white">{thresholds.hardware_wear_max}</div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 물리 노드 탭 */}
        <TabsContent value="nodes" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5 text-pink-400" />
                물리 노드 상태 (시뮬레이션)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {/* 공공 노드 */}
                <div className="bg-slate-900/50 rounded-lg p-4 border border-blue-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="font-medium text-white">NODE_PUBLIC_01</span>
                      <Badge className="bg-blue-500/20 text-blue-400">공공 영역</Badge>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">활성</Badge>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">온도</div>
                      <div className="flex items-center gap-2">
                        <Thermometer className="w-4 h-4 text-red-400" />
                        <span className="text-white">45°C</span>
                      </div>
                      <Progress value={45 / 85 * 100} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">CPU</div>
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-white">30%</span>
                      </div>
                      <Progress value={30} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">용량</div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-purple-400" />
                        <span className="text-white">100%</span>
                      </div>
                      <Progress value={100} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">평형 상수</div>
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-pink-400" />
                        <span className="text-white">1.0</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 운영 노드 */}
                <div className="bg-slate-900/50 rounded-lg p-4 border border-amber-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="font-medium text-white">NODE_OPERATION_01</span>
                      <Badge className="bg-amber-500/20 text-amber-400">운영 영역</Badge>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">활성</Badge>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">온도</div>
                      <div className="flex items-center gap-2">
                        <Thermometer className="w-4 h-4 text-red-400" />
                        <span className="text-white">50°C</span>
                      </div>
                      <Progress value={50 / 85 * 100} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">CPU</div>
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-white">40%</span>
                      </div>
                      <Progress value={40} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">용량</div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-purple-400" />
                        <span className="text-white">80%</span>
                      </div>
                      <Progress value={80} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">평형 상수</div>
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-pink-400" />
                        <span className="text-white">0.8</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 관리 노드 */}
                <div className="bg-slate-900/50 rounded-lg p-4 border border-purple-500/30">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="font-medium text-white">NODE_MANAGEMENT_01</span>
                      <Badge className="bg-purple-500/20 text-purple-400">관리 영역</Badge>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">활성</Badge>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">온도</div>
                      <div className="flex items-center gap-2">
                        <Thermometer className="w-4 h-4 text-red-400" />
                        <span className="text-white">42°C</span>
                      </div>
                      <Progress value={42 / 85 * 100} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">CPU</div>
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-white">25%</span>
                      </div>
                      <Progress value={25} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">용량</div>
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-purple-400" />
                        <span className="text-white">60%</span>
                      </div>
                      <Progress value={60} className="h-1 mt-1" />
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">평형 상수</div>
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-pink-400" />
                        <span className="text-white">0.6</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 엔트로피 탭 */}
        <TabsContent value="entropy" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* 엔트로피 상태 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-pink-400" />
                    엔트로피 상태
                  </CardTitle>
                  <Badge className={entropyStatus?.status === 'normal' 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : 'bg-amber-500/20 text-amber-400'}>
                    {entropyStatus?.status === 'normal' ? '정상' : '주의'}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-slate-900/50 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-slate-400">현재 엔트로피 (S)</span>
                    <span className="text-2xl font-bold text-white">
                      {entropyStatus?.current_entropy?.toFixed(6) || '0.000000'}
                    </span>
                  </div>
                  <Progress 
                    value={(entropyStatus?.current_entropy || 0) / (thresholds?.entropy_rate_max || 0.15) * 100} 
                    className="h-2"
                  />
                  <div className="text-xs text-slate-500 mt-1">
                    임계치: {thresholds?.entropy_rate_max || 0.15}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <div className="text-xs text-slate-400 mb-1">엔트로피 변화율</div>
                    <div className="flex items-center gap-2">
                      {(entropyStatus?.entropy_rate_dS_dt || 0) > 0 ? (
                        <TrendingUp className="w-4 h-4 text-red-400" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-emerald-400" />
                      )}
                      <span className="text-lg font-bold text-white">
                        {entropyStatus?.entropy_rate_dS_dt?.toFixed(6) || '0.000000'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">dS/dt</div>
                  </div>
                  
                  <div className="bg-slate-900/50 rounded-lg p-3">
                    <div className="text-xs text-slate-400 mb-1">열 발생량</div>
                    <div className="flex items-center gap-2">
                      <Thermometer className="w-4 h-4 text-red-400" />
                      <span className="text-lg font-bold text-white">
                        {entropyStatus?.heat_generation_estimate?.toFixed(4) || '0.0000'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">Q = T × dS</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 에너지 효율 */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-amber-400" />
                    에너지 효율
                  </CardTitle>
                  <Button data-testid="f-field-entropy-feedback-btn" size="sm" variant="outline" onClick={runEntropyFeedback}>
                    <ArrowRight className="w-3 h-3 mr-1" />
                    G:정제 피드백
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center py-6">
                  <div className="relative">
                    <svg className="w-32 h-32 transform -rotate-90">
                      <circle
                        cx="64" cy="64" r="56"
                        fill="none"
                        stroke="#1e293b"
                        strokeWidth="12"
                      />
                      <circle
                        cx="64" cy="64" r="56"
                        fill="none"
                        stroke={entropyStatus?.energy_efficiency >= 0.7 ? '#10b981' : '#f59e0b'}
                        strokeWidth="12"
                        strokeDasharray={`${(entropyStatus?.energy_efficiency || 0.67) * 351.86} 351.86`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-3xl font-bold text-white">
                          {((entropyStatus?.energy_efficiency || 0.67) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-slate-400">효율</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/50 rounded-lg p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">분석 샘플 수</span>
                    <span className="text-white">{entropyStatus?.samples_analyzed || 5}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-500 text-center">
                  마지막 분석: {entropyStatus?.analyzed_at 
                    ? new Date(entropyStatus.analyzed_at).toLocaleString('ko-KR')
                    : '-'}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 엔트로피 역전 유닛 설명 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-sm">1130: 엔트로피 역전 유닛</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="bg-slate-900/50 rounded-lg p-3">
                  <div className="text-pink-400 font-medium mb-1">기능</div>
                  <div className="text-slate-300">물리적 집행 과정의 엔트로피 증가를 역전시키기 위한 보정 계수 산출</div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3">
                  <div className="text-pink-400 font-medium mb-1">입력</div>
                  <div className="text-slate-300">현재 엔트로피 상태, 에너지 효율, 열 발생량</div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3">
                  <div className="text-pink-400 font-medium mb-1">출력</div>
                  <div className="text-slate-300">G:정제 노드로 피드백 계수 및 권장 조치 전달</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 자원 사영 탭 */}
        <TabsContent value="projection" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-pink-400" />
                  1110: 자원 사영 엔진
                </CardTitle>
                <Button data-testid="f-field-projection-test-btn" onClick={runProjectionTest} disabled={projecting}>
                  {projecting ? (
                    <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 mr-1" />
                  )}
                  사영 테스트 실행
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 입력 벡터 */}
              <div className="bg-slate-900/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-3">5:3:2 배분 벡터 (입력)</div>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">1000</div>
                    <div className="text-xs text-slate-400">총 가치</div>
                  </div>
                  <div className="text-center p-2 bg-blue-500/10 rounded-lg border border-blue-500/30">
                    <div className="text-2xl font-bold text-blue-400">500</div>
                    <div className="text-xs text-slate-400">공공 (5)</div>
                  </div>
                  <div className="text-center p-2 bg-amber-500/10 rounded-lg border border-amber-500/30">
                    <div className="text-2xl font-bold text-amber-400">300</div>
                    <div className="text-xs text-slate-400">운영 (3)</div>
                  </div>
                  <div className="text-center p-2 bg-purple-500/10 rounded-lg border border-purple-500/30">
                    <div className="text-2xl font-bold text-purple-400">200</div>
                    <div className="text-xs text-slate-400">관리 (2)</div>
                  </div>
                </div>
              </div>

              {/* 사영 결과 */}
              {projectionResult && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-slate-400">
                    <ArrowRight className="w-4 h-4" />
                    <span>물리량 사영 결과</span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    {projectionResult.projection_results?.map((result, idx) => (
                      <div key={idx} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-medium text-white">{result.node_id}</span>
                          <Badge className={
                            result.region === 'public' ? 'bg-blue-500/20 text-blue-400' :
                            result.region === 'operation' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-purple-500/20 text-purple-400'
                          }>
                            {result.region}
                          </Badge>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">입력값</span>
                            <span className="text-white">{result.input_value}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">사영값</span>
                            <span className="text-pink-400 font-bold">{result.projected_physical_value}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">엔트로피 비용</span>
                            <span className="text-amber-400">{result.entropy_cost}</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">정확도</span>
                            <span className="text-emerald-400">{(result.projection_accuracy * 100).toFixed(2)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 정합성 */}
                  <div className="bg-slate-900/50 rounded-lg p-4 border border-pink-500/30">
                    <div className="text-sm text-slate-400 mb-2">이론 vs 실제 정합성</div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-xl font-bold text-white">
                          {projectionResult.theoretical_vs_actual?.theoretical_total}
                        </div>
                        <div className="text-xs text-slate-400">이론적 총량</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-pink-400">
                          {projectionResult.theoretical_vs_actual?.actual_projected?.toFixed(2)}
                        </div>
                        <div className="text-xs text-slate-400">실제 사영량</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-emerald-400">
                          {projectionResult.theoretical_vs_actual?.accuracy}%
                        </div>
                        <div className="text-xs text-slate-400">정합도</div>
                      </div>
                    </div>
                  </div>

                  {/* 원장 동기화 */}
                  <div className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-lg">
                    <Database className="w-5 h-5 text-blue-400" />
                    <div className="flex-1">
                      <div className="text-sm text-white">D:원장 동기화</div>
                      <div className="text-xs text-slate-400">비가역적 증명 데이터로 변환하여 기록</div>
                    </div>
                    <Lock className="w-5 h-5 text-emerald-400" />
                    <div className="flex-1">
                      <div className="text-sm text-white">I:무결성 검증</div>
                      <div className="text-xs text-slate-400">1:1 대응 유효성 검증</div>
                    </div>
                  </div>
                </div>
              )}

              {!projectionResult && (
                <div className="text-center py-8 text-slate-400">
                  <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>"사영 테스트 실행" 버튼을 눌러 자원 사영을 테스트하세요</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FFieldTab;
