import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Network, ArrowRightLeft, GitBranch, Link2, Send, RefreshCw 
} from 'lucide-react';
import { MetricCard } from "@/components/MetricCard";
import { api } from "@/lib/api";

export const IntegrationTab = ({ onRefresh }) => {
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const [adapters, setAdapters] = useState([]);
  const [mappings, setMappings] = useState([]);
  const [routingRules, setRoutingRules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [exchangeData, setExchangeData] = useState('{"order_id": "ORD-001", "customer_id": "CUST-100", "amount": 1500}');
  const [sourceDomain, setSourceDomain] = useState("erp");
  const [messageType, setMessageType] = useState("order");
  const [exchangeResult, setExchangeResult] = useState(null);

  useEffect(() => {
    fetchIntegrationData();
  }, []);

  const fetchIntegrationData = async () => {
    try {
      const [statusRes, adaptersRes, mappingsRes, rulesRes] = await Promise.all([
        api.getIntegrationStatus(),
        api.getAdapters(),
        api.getMappings(),
        api.getRoutingRules()
      ]);
      setIntegrationStatus(statusRes.data);
      setAdapters(adaptersRes.data.adapters || []);
      setMappings(mappingsRes.data.mappings || []);
      setRoutingRules(rulesRes.data.rules || []);
    } catch (error) {
      console.error("Fetch integration data error:", error);
    }
  };

  const handleExchange = async () => {
    setLoading(true);
    try {
      const data = JSON.parse(exchangeData);
      const response = await api.executeExchange(data, sourceDomain, messageType);
      setExchangeResult(response.data);
      fetchIntegrationData();
      onRefresh();
    } catch (error) {
      console.error("Exchange error:", error);
      setExchangeResult({ success: false, errors: [error.message] });
    }
    setLoading(false);
  };

  const monitor = integrationStatus?.monitor || {};

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard 
          icon={Network} 
          label="어댑터" 
          value={integrationStatus?.adapters?.total || 0}
          variant="cyan"
        />
        <MetricCard 
          icon={Link2} 
          label="매핑" 
          value={integrationStatus?.semantic_mappings?.total_mappings || 0}
          variant="teal"
        />
        <MetricCard 
          icon={GitBranch} 
          label="라우팅 규칙" 
          value={integrationStatus?.routing?.total_rules || 0}
          variant="amber"
        />
        <MetricCard 
          icon={ArrowRightLeft} 
          label="총 교환" 
          value={integrationStatus?.total_exchanges || 0}
          variant="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Exchange Test */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Send className="w-5 h-5" /> 데이터 교환 테스트
            </CardTitle>
            <CardDescription className="text-slate-400">
              특허6-J: 도메인 간 데이터 교환 시뮬레이션
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-300 text-sm mb-1 block">소스 도메인</label>
                <Select value={sourceDomain} onValueChange={setSourceDomain}>
                  <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="source-domain-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="erp">ERP</SelectItem>
                    <SelectItem value="crm">CRM</SelectItem>
                    <SelectItem value="scm">SCM</SelectItem>
                    <SelectItem value="mes">MES</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-slate-300 text-sm mb-1 block">메시지 유형</label>
                <Select value={messageType} onValueChange={setMessageType}>
                  <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="message-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="order">주문</SelectItem>
                    <SelectItem value="customer">고객</SelectItem>
                    <SelectItem value="inventory">재고</SelectItem>
                    <SelectItem value="production">생산</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="text-slate-300 text-sm mb-1 block">데이터 (JSON)</label>
              <Textarea
                value={exchangeData}
                onChange={(e) => setExchangeData(e.target.value)}
                className="bg-slate-900 border-slate-600 text-slate-100 font-mono h-24"
                data-testid="exchange-data-input"
              />
            </div>
            <Button 
              onClick={handleExchange} 
              disabled={loading}
              className="w-full bg-violet-600 hover:bg-violet-500"
              data-testid="exchange-button"
            >
              {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRightLeft className="w-4 h-4 mr-2" />}
              교환 실행
            </Button>
            
            {exchangeResult && (
              <div className={`mt-4 p-3 rounded-lg ${exchangeResult.success ? 'bg-emerald-900/30 border border-emerald-600' : 'bg-red-900/30 border border-red-600'}`}>
                <p className={`font-medium mb-2 ${exchangeResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                  {exchangeResult.success ? '✓ 교환 성공' : '✗ 교환 실패'}
                </p>
                {exchangeResult.target_domains && (
                  <p className="text-slate-300 text-sm">
                    대상 도메인: {exchangeResult.target_domains.join(', ')}
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Adapters & Monitor */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Network className="w-5 h-5" /> 도메인 어댑터
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-60" data-testid="adapters-list">
              <div className="space-y-2">
                {adapters.map((adapter, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                    <div>
                      <p className="text-slate-100 font-medium">{adapter.domain_id}</p>
                      <p className="text-slate-500 text-xs">{adapter.protocol} • {adapter.domain_type}</p>
                    </div>
                    <div className="text-right">
                      <Badge variant={adapter.health_score > 0.8 ? 'default' : 'destructive'}>
                        {(adapter.health_score * 100).toFixed(0)}%
                      </Badge>
                      <p className="text-slate-500 text-xs mt-1">
                        {adapter.message_count}건 처리
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Monitor Stats */}
            <div className="mt-4 pt-4 border-t border-slate-700">
              <h4 className="text-slate-300 text-sm mb-3">실시간 모니터</h4>
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">처리량</p>
                  <p className="text-slate-100 font-medium">{monitor.throughput?.toFixed(2) || 0}/s</p>
                </div>
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">평균 지연</p>
                  <p className="text-slate-100 font-medium">{monitor.average_latency_ms?.toFixed(1) || 0}ms</p>
                </div>
                <div className="bg-slate-900/50 rounded p-2 text-center">
                  <p className="text-slate-500 text-xs">에러</p>
                  <p className="text-red-400 font-medium">{monitor.total_errors || 0}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Mappings & Routing Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Semantic Mappings */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <Link2 className="w-5 h-5" /> 의미 매핑
            </CardTitle>
            <CardDescription className="text-slate-400">
              도메인 간 필드 매핑 ({mappings.length}건)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48" data-testid="mappings-list">
              <div className="space-y-2">
                {mappings.map((mapping, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-2 flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-400">{mapping.source_domain}.{mapping.source_field}</span>
                      <ArrowRightLeft className="w-3 h-3 text-slate-500" />
                      <span className="text-emerald-400">{mapping.target_domain}.{mapping.target_field}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {(mapping.similarity_score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Routing Rules */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-slate-100 flex items-center gap-2">
              <GitBranch className="w-5 h-5" /> 라우팅 규칙
            </CardTitle>
            <CardDescription className="text-slate-400">
              메시지 라우팅 규칙 ({routingRules.length}건)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48" data-testid="routing-rules-list">
              <div className="space-y-2">
                {routingRules.map((rule, idx) => (
                  <div key={idx} className="bg-slate-900/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-slate-100 font-medium">{rule.name}</span>
                      <Badge variant={rule.enabled ? 'default' : 'secondary'}>
                        우선순위: {rule.priority}
                      </Badge>
                    </div>
                    <div className="text-slate-400 text-xs">
                      <span className="text-blue-400">{rule.source_domain}</span>
                      <span className="mx-1">→</span>
                      <span className="text-emerald-400">{rule.target_domains?.join(', ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default IntegrationTab;
