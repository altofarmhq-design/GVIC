import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  Plus, Database, Play, Pause, Trash2, RefreshCw, 
  ExternalLink, Clock, AlertCircle, CheckCircle, Edit 
} from "lucide-react";
import { api } from "@/lib/api";

export default function DataSourcesTab({ onRefresh }) {
  const [sources, setSources] = useState([]);
  const [collectedData, setCollectedData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    source_type: "api",
    url: "",
    method: "GET",
    auth_type: "none",
    auth_value: "",
    polling_interval: 60,
    data_mapping: { value: "value" },
    enabled: true
  });

  const fetchSources = useCallback(async () => {
    try {
      const [sourcesRes, collectedRes] = await Promise.all([
        api.getDataSources(),
        api.getCollectedData(20)
      ]);
      setSources(sourcesRes.data.sources || []);
      setCollectedData(collectedRes.data.data || []);
    } catch (error) {
      console.error("Failed to fetch data sources:", error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSources();
    const interval = setInterval(fetchSources, 10000);
    return () => clearInterval(interval);
  }, [fetchSources]);

  const resetForm = () => {
    setFormData({
      name: "",
      source_type: "api",
      url: "",
      method: "GET",
      auth_type: "none",
      auth_value: "",
      polling_interval: 60,
      data_mapping: { value: "value" },
      enabled: true
    });
    setEditingSource(null);
  };

  const handleOpenDialog = (source = null) => {
    if (source) {
      setEditingSource(source);
      setFormData({
        name: source.name,
        source_type: source.source_type,
        url: source.url || "",
        method: source.method || "GET",
        auth_type: source.auth_type || "none",
        auth_value: source.auth_value || "",
        polling_interval: source.polling_interval || 60,
        data_mapping: source.data_mapping || { value: "value" },
        enabled: source.enabled !== false
      });
    } else {
      resetForm();
    }
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (editingSource) {
        await api.updateDataSource(editingSource.id, formData);
      } else {
        await api.createDataSource(formData);
      }
      setDialogOpen(false);
      resetForm();
      fetchSources();
      onRefresh?.();
    } catch (error) {
      console.error("Failed to save data source:", error);
    }
  };

  const handleDelete = async (sourceId) => {
    if (!window.confirm("이 데이터 소스를 삭제하시겠습니까?")) return;
    try {
      await api.deleteDataSource(sourceId);
      fetchSources();
    } catch (error) {
      console.error("Failed to delete data source:", error);
    }
  };

  const handleFetch = async (sourceId) => {
    try {
      await api.fetchDataSource(sourceId);
      fetchSources();
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  };

  const handleProcess = async (sourceId) => {
    try {
      await api.processDataSource(sourceId);
      fetchSources();
      onRefresh?.();
    } catch (error) {
      console.error("Failed to process data:", error);
    }
  };

  const handleStart = async (sourceId) => {
    try {
      await api.startDataSource(sourceId);
      fetchSources();
    } catch (error) {
      console.error("Failed to start polling:", error);
    }
  };

  const handleStop = async (sourceId) => {
    try {
      await api.stopDataSource(sourceId);
      fetchSources();
    } catch (error) {
      console.error("Failed to stop polling:", error);
    }
  };

  const getStatusBadge = (source) => {
    if (source.is_running) {
      return <Badge className="bg-green-500/20 text-green-400">실행 중</Badge>;
    }
    if (source.last_status === "success") {
      return <Badge className="bg-blue-500/20 text-blue-400">대기 중</Badge>;
    }
    if (source.last_status === "error") {
      return <Badge className="bg-red-500/20 text-red-400">오류</Badge>;
    }
    return <Badge className="bg-slate-500/20 text-slate-400">미연결</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="datasources-tab">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">외부 데이터 소스</h2>
          <p className="text-slate-400">API 및 외부 데이터 소스를 연동하여 GVIC 엔진에 데이터를 공급합니다</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => handleOpenDialog()} data-testid="add-source-btn">
              <Plus className="w-4 h-4 mr-2" /> 소스 추가
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
            <DialogHeader>
              <DialogTitle className="text-slate-100">
                {editingSource ? "데이터 소스 수정" : "새 데이터 소스 추가"}
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                외부 API 또는 데이터 소스 정보를 입력하세요
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label className="text-slate-200">이름</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="데이터 소스 이름"
                  className="bg-slate-700 border-slate-600"
                  data-testid="source-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-slate-200">소스 유형</Label>
                  <Select
                    value={formData.source_type}
                    onValueChange={(v) => setFormData({ ...formData, source_type: v })}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="api">REST API</SelectItem>
                      <SelectItem value="webhook">Webhook</SelectItem>
                      <SelectItem value="manual">수동 입력</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">HTTP 메소드</Label>
                  <Select
                    value={formData.method}
                    onValueChange={(v) => setFormData({ ...formData, method: v })}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="GET">GET</SelectItem>
                      <SelectItem value="POST">POST</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-slate-200">URL</Label>
                <Input
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://api.example.com/data"
                  className="bg-slate-700 border-slate-600"
                  data-testid="source-url-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-slate-200">인증 유형</Label>
                  <Select
                    value={formData.auth_type}
                    onValueChange={(v) => setFormData({ ...formData, auth_type: v })}
                  >
                    <SelectTrigger className="bg-slate-700 border-slate-600">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      <SelectItem value="none">없음</SelectItem>
                      <SelectItem value="api_key">API Key</SelectItem>
                      <SelectItem value="bearer">Bearer Token</SelectItem>
                      <SelectItem value="basic">Basic Auth</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-200">폴링 간격 (초)</Label>
                  <Input
                    type="number"
                    value={formData.polling_interval}
                    onChange={(e) => setFormData({ ...formData, polling_interval: parseInt(e.target.value) || 60 })}
                    className="bg-slate-700 border-slate-600"
                    min={10}
                  />
                </div>
              </div>
              {formData.auth_type !== "none" && (
                <div className="space-y-2">
                  <Label className="text-slate-200">인증 값</Label>
                  <Input
                    type="password"
                    value={formData.auth_value}
                    onChange={(e) => setFormData({ ...formData, auth_value: e.target.value })}
                    placeholder="API 키 또는 토큰"
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label className="text-slate-200">데이터 매핑 경로</Label>
                <Input
                  value={formData.data_mapping?.value || "value"}
                  onChange={(e) => setFormData({ ...formData, data_mapping: { value: e.target.value } })}
                  placeholder="data.result.value"
                  className="bg-slate-700 border-slate-600"
                />
                <p className="text-xs text-slate-500">응답 JSON에서 값을 추출할 경로 (예: data.items.0.price)</p>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={formData.enabled}
                  onCheckedChange={(v) => setFormData({ ...formData, enabled: v })}
                />
                <Label className="text-slate-200">활성화</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>취소</Button>
              <Button onClick={handleSubmit} data-testid="save-source-btn">
                {editingSource ? "수정" : "추가"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Data Sources List */}
      <div className="grid gap-4">
        {sources.length === 0 ? (
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Database className="w-12 h-12 text-slate-500 mb-4" />
              <p className="text-slate-400 text-center">등록된 데이터 소스가 없습니다</p>
              <p className="text-slate-500 text-sm text-center mt-1">외부 API를 연동하여 데이터를 자동으로 수집할 수 있습니다</p>
            </CardContent>
          </Card>
        ) : (
          sources.map((source) => (
            <Card key={source.id} className="bg-slate-800/50 border-slate-700" data-testid={`source-card-${source.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-slate-100">{source.name}</h3>
                      {getStatusBadge(source)}
                      <Badge variant="outline" className="text-slate-400 border-slate-600">
                        {source.source_type.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-3 h-3" />
                        <span className="truncate max-w-md">{source.url || "URL 미설정"}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {source.polling_interval}초 간격
                        </span>
                        <span>수집 {source.fetch_count || 0}회</span>
                        {source.error_count > 0 && (
                          <span className="text-red-400">오류 {source.error_count}회</span>
                        )}
                      </div>
                      {source.last_fetch && (
                        <div className="text-xs text-slate-500">
                          마지막 수집: {new Date(source.last_fetch).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleFetch(source.id)}
                      title="데이터 가져오기"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleProcess(source.id)}
                      title="GVIC 처리"
                      className="text-violet-400 border-violet-500/50 hover:bg-violet-500/20"
                    >
                      <Play className="w-4 h-4" />
                    </Button>
                    {source.is_running ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStop(source.id)}
                        title="자동 수집 중지"
                        className="text-orange-400 border-orange-500/50 hover:bg-orange-500/20"
                      >
                        <Pause className="w-4 h-4" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStart(source.id)}
                        title="자동 수집 시작"
                        className="text-green-400 border-green-500/50 hover:bg-green-500/20"
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenDialog(source)}
                      title="수정"
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(source.id)}
                      title="삭제"
                      className="text-red-400 border-red-500/50 hover:bg-red-500/20"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Collected Data History */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100">최근 수집 데이터</CardTitle>
          <CardDescription className="text-slate-400">외부 소스에서 수집된 최근 데이터 목록</CardDescription>
        </CardHeader>
        <CardContent>
          {collectedData.length === 0 ? (
            <p className="text-slate-500 text-center py-8">수집된 데이터가 없습니다</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {collectedData.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    {item.processed ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-yellow-400" />
                    )}
                    <div>
                      <span className="text-slate-200 font-medium">{item.source_name}</span>
                      <span className="text-slate-400 ml-2">값: {item.extracted_value?.toFixed(4)}</span>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
