import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bell, Heart, RefreshCw } from 'lucide-react';
import { api } from "@/lib/api";

export const AlertsTab = ({ alerts, onRefresh }) => {
  const [healthResults, setHealthResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleHealthCheck = async () => {
    setLoading(true);
    try {
      const response = await api.runHealthCheck();
      setHealthResults(response.data);
      onRefresh();
    } catch (error) {
      console.error("Health check error:", error);
    }
    setLoading(false);
  };

  const stats = alerts?.statistics || { total: 0, active: 0, resolved: 0 };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-slate-100 flex items-center gap-2">
          <Bell className="w-5 h-5" /> 알림 센터
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Health Check Section */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-slate-200 font-medium">시스템 점검</h3>
            <Button 
              onClick={handleHealthCheck} 
              disabled={loading}
              className="bg-emerald-600 hover:bg-emerald-500"
              data-testid="health-check-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Heart className="w-4 h-4 mr-2" />}
              헬스체크 실행
            </Button>

            {healthResults && (
              <div className="space-y-2" data-testid="health-results">
                {Object.entries(healthResults.results || {}).map(([key, value]) => (
                  <div key={key} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                    <span className="text-slate-100 font-medium capitalize">{key}</span>
                    <Badge variant={value.status === 'healthy' ? 'default' : 'destructive'}>
                      {value.status === 'healthy' ? '정상' : '점검 필요'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stats Section */}
          <div className="space-y-4">
            <h3 className="text-slate-200 font-medium">알림 통계</h3>
            <div className="space-y-3" data-testid="alert-stats">
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">전체 알림</p>
                <p className="text-slate-100 text-2xl font-bold">{stats.total}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">활성 알림</p>
                <p className="text-amber-400 text-2xl font-bold">{stats.active}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-slate-400 text-sm">해결됨</p>
                <p className="text-emerald-400 text-2xl font-bold">{stats.resolved}</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AlertsTab;
