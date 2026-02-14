import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Database, FileText, Trash2, RefreshCw } from 'lucide-react';
import { api } from "@/lib/api";

export const DataTab = ({ logs = [], onLogsRefresh }) => {
  const [ioFormat, setIoFormat] = useState("json");
  const [ioData, setIoData] = useState('{"value": 10.5, "type": "market"}');
  const [ioResult, setIoResult] = useState(null);

  const defaultInputs = {
    json: '{"value": 10.5, "type": "market"}',
    csv: "value,type\n10.5,market",
    key_value: "value=10.5\ntype=market"
  };

  // 로그 데이터 안정화
  const stableLogs = useMemo(() => logs || [], [logs]);

  const handleFormatChange = (v) => {
    setIoFormat(v);
    setIoData(defaultInputs[v]);
  };

  const handleIOProcess = async () => {
    try {
      const response = await api.processIO(ioData, ioFormat);
      setIoResult(response.data);
    } catch (error) {
      console.error("IO process error:", error);
    }
  };

  const handleClearLogs = async () => {
    try {
      await api.clearLogs();
      onLogsRefresh?.();
    } catch (error) {
      console.error("Clear logs error:", error);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* IO Test */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5" /> 입출력 테스트
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-slate-300 text-sm mb-2 block">형식</label>
            <Select value={ioFormat} onValueChange={handleFormatChange}>
              <SelectTrigger className="bg-slate-900 border-slate-600 text-slate-100" data-testid="io-format-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-600">
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="key_value">Key-Value</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-slate-300 text-sm mb-2 block">데이터</label>
            <Textarea
              value={ioData}
              onChange={(e) => setIoData(e.target.value)}
              className="bg-slate-900 border-slate-600 text-slate-100 font-mono h-24"
              data-testid="io-data-input"
            />
          </div>
          <Button onClick={handleIOProcess} className="w-full" data-testid="io-process-button">
            <RefreshCw className="w-4 h-4 mr-2" /> 처리
          </Button>
          {ioResult && (
            <div className="bg-slate-900 rounded-lg p-3">
              <pre className="text-slate-300 text-xs overflow-auto">
                {JSON.stringify(ioResult, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Activity Logs */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <FileText className="w-5 h-5" /> 활동 로그
          </CardTitle>
          <Button variant="outline" size="sm" onClick={handleClearLogs} data-testid="clear-logs-button">
            <Trash2 className="w-4 h-4 mr-1" /> 초기화
          </Button>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-80" data-testid="logs-list">
            {stableLogs.length > 0 ? (
              <div className="space-y-2">
                {stableLogs.map((log, idx) => (
                  <div key={log.timestamp ? `${log.timestamp}-${idx}` : `log-${idx}`} className="bg-slate-900/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-blue-400 text-xs">{log.timestamp?.slice(0, 16) || '-'}</span>
                      <Badge variant="outline" className="text-xs">{log.phase || '-'}</Badge>
                    </div>
                    <p className="text-slate-300 text-sm">{log.action || '-'}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">로그가 없습니다</p>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataTab;
