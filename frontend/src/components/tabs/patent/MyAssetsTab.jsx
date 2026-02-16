import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { 
  Coins, 
  TrendingUp, 
  Award,
  Gift,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  FileText,
  Zap,
  Target,
  Crown,
  Star,
  Wallet,
  History,
  Info,
  DollarSign
} from 'lucide-react';
import { api } from "@/lib/api";

/**
 * 내 자산 현황 탭
 * - 포인트 잔액 및 거래 내역
 * - 자산 축적 현황
 * - 기여 레벨 및 등급
 * - 포인트 전환 (유료 전환용)
 */
export const MyAssetsTab = () => {
  const [pointBalance, setPointBalance] = useState(null);
  const [assetSummary, setAssetSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [earningRules, setEarningRules] = useState([]);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [convertAmount, setConvertAmount] = useState("");

  const fetchData = async () => {
    setLoading(true);
    try {
      const [balanceRes, summaryRes, transRes, rulesRes, rateRes] = await Promise.all([
        api.getPointBalance(),
        api.getAssetSummary(),
        api.getPointTransactions(20),
        api.getEarningRules(),
        api.getExchangeRate()
      ]);
      
      setPointBalance(balanceRes.data);
      setAssetSummary(summaryRes.data);
      setTransactions(transRes.data.transactions || []);
      setEarningRules(rulesRes.data.rules || []);
      setExchangeRate(rateRes.data);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleConvertPoints = async () => {
    const amount = parseFloat(convertAmount);
    if (!amount || amount <= 0) return;
    
    try {
      await api.convertPoints(amount);
      setConvertAmount("");
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "전환 실패");
    }
  };

  const getRankInfo = (rank) => {
    const ranks = {
      Diamond: { color: "bg-cyan-500", icon: Crown, gradient: "from-cyan-400 to-blue-500" },
      Platinum: { color: "bg-slate-300", icon: Star, gradient: "from-slate-300 to-slate-400" },
      Gold: { color: "bg-amber-500", icon: Award, gradient: "from-amber-400 to-amber-600" },
      Silver: { color: "bg-slate-400", icon: Award, gradient: "from-slate-300 to-slate-500" },
      Bronze: { color: "bg-orange-600", icon: Award, gradient: "from-orange-500 to-orange-700" }
    };
    return ranks[rank] || ranks.Bronze;
  };

  const getLevelColor = (level) => {
    const colors = {
      1: "from-slate-500 to-slate-600",
      2: "from-green-500 to-green-600",
      3: "from-blue-500 to-blue-600",
      4: "from-purple-500 to-purple-600",
      5: "from-amber-400 to-amber-600"
    };
    return colors[level] || colors[1];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  const evaluation = assetSummary?.evaluation || {};
  const contributionLevel = evaluation.contribution_level || { level: 1, name: "입문자" };
  const rankInfo = getRankInfo(evaluation.rank);
  const RankIcon = rankInfo.icon;

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
              <Wallet className="w-5 h-5 text-white" />
            </div>
            내 자산 현황
          </h2>
          <p className="text-slate-400 mt-1">포인트 잔액, 자산 축적 현황 및 기여도</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData}>
          <RefreshCw className="w-4 h-4 mr-1" />
          새로고침
        </Button>
      </div>

      {/* 상단 요약 카드 */}
      <div className="grid grid-cols-4 gap-4">
        {/* 포인트 잔액 */}
        <Card className="bg-gradient-to-br from-amber-900/40 to-slate-800 border-amber-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-amber-400 text-sm flex items-center gap-1">
                  <Coins className="w-4 h-4" />
                  보유 포인트
                </p>
                <p className="text-3xl font-bold text-white mt-1">
                  {(pointBalance?.available_points || 0).toLocaleString()}
                  <span className="text-lg text-amber-400 ml-1">P</span>
                </p>
                <p className="text-slate-400 text-xs mt-1">
                  현금 환산: ₩{(pointBalance?.cash_equivalent || 0).toLocaleString()}
                </p>
              </div>
              <div className="w-12 h-12 bg-amber-500/20 rounded-full flex items-center justify-center">
                <Coins className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 총 자산 */}
        <Card className="bg-gradient-to-br from-purple-900/40 to-slate-800 border-purple-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-400 text-sm flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  자산화 완료
                </p>
                <p className="text-3xl font-bold text-white mt-1">
                  {assetSummary?.assets?.total || 0}
                  <span className="text-lg text-purple-400 ml-1">건</span>
                </p>
                <p className="text-slate-400 text-xs mt-1">
                  평균 가치: {assetSummary?.assets?.avg_value_score || 0}점
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center">
                <Award className="w-6 h-6 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 시그널 통계 */}
        <Card className="bg-gradient-to-br from-blue-900/40 to-slate-800 border-blue-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-400 text-sm flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  제출 시그널
                </p>
                <p className="text-3xl font-bold text-white mt-1">
                  {assetSummary?.signals?.total || 0}
                  <span className="text-lg text-blue-400 ml-1">건</span>
                </p>
                <p className="text-slate-400 text-xs mt-1">
                  분석됨: {assetSummary?.signals?.wanted || 0} | 자산화: {assetSummary?.signals?.unwanted || 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                <FileText className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 등급 */}
        <Card className={`bg-gradient-to-br ${rankInfo.gradient} border-0`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white/80 text-sm flex items-center gap-1">
                  <RankIcon className="w-4 h-4" />
                  내 등급
                </p>
                <p className="text-3xl font-bold text-white mt-1">
                  {evaluation.rank || "Bronze"}
                </p>
                <p className="text-white/70 text-xs mt-1">
                  Lv.{contributionLevel.level} {contributionLevel.name}
                </p>
              </div>
              <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                <RankIcon className="w-6 h-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* 좌측: 포인트 상세 및 전환 */}
        <div className="space-y-4">
          {/* 기여 레벨 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                기여 레벨
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getLevelColor(contributionLevel.level)} flex items-center justify-center`}
                    >
                      <span className="text-white font-bold text-sm">{contributionLevel.level}</span>
                    </div>
                    <div>
                      <p className="text-slate-100 font-medium">{contributionLevel.name}</p>
                      <p className="text-slate-500 text-xs">활동 점수: {evaluation.activity_score || 0}점</p>
                    </div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>다음 레벨까지</span>
                    <span>{Math.min(100, evaluation.activity_score || 0)}%</span>
                  </div>
                  <Progress value={Math.min(100, evaluation.activity_score || 0)} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 포인트 전환 */}
          <Card className="bg-gradient-to-br from-green-900/30 to-slate-800 border-green-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-slate-100 text-base flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                포인트 전환
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-slate-900/50 rounded-lg p-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">환율</span>
                  <span className="text-green-400 font-medium">₩1 = 0.1P</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-slate-400">전환 가능</span>
                  <span className="text-white font-medium">{(pointBalance?.available_points || 0).toLocaleString()}P</span>
                </div>
              </div>
              
              <div>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    placeholder="전환할 포인트"
                    value={convertAmount}
                    onChange={(e) => setConvertAmount(e.target.value)}
                    className="bg-slate-900 border-slate-600 text-slate-100"
                  />
                  <Button 
                    onClick={handleConvertPoints}
                    disabled={!convertAmount || parseFloat(convertAmount) <= 0}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    전환
                  </Button>
                </div>
                {convertAmount && parseFloat(convertAmount) > 0 && (
                  <p className="text-xs text-green-400 mt-2">
                    → ₩{(parseFloat(convertAmount) / 0.1).toLocaleString()} 환산
                  </p>
                )}
              </div>
              
              <p className="text-xs text-slate-500">
                * 유료 전환 시 포인트를 현금으로 대체할 수 있습니다
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 중앙: 거래 내역 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base flex items-center justify-between">
              <span className="flex items-center gap-2">
                <History className="w-5 h-5 text-slate-400" />
                포인트 내역
              </span>
              <Badge variant="outline" className="text-slate-400">
                {transactions.length}건
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              {transactions.length === 0 ? (
                <div className="text-center py-8">
                  <History className="w-12 h-12 text-slate-600 mx-auto mb-2" />
                  <p className="text-slate-500">거래 내역이 없습니다</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {transactions.map((tx, idx) => (
                    <div 
                      key={idx} 
                      className="bg-slate-900 rounded-lg p-3 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          tx.type === "earn" ? "bg-green-500/20" : 
                          tx.type === "spend" ? "bg-red-500/20" : "bg-blue-500/20"
                        }`}>
                          {tx.type === "earn" ? (
                            <ArrowUpRight className="w-4 h-4 text-green-400" />
                          ) : tx.type === "spend" ? (
                            <ArrowDownRight className="w-4 h-4 text-red-400" />
                          ) : (
                            <DollarSign className="w-4 h-4 text-blue-400" />
                          )}
                        </div>
                        <div>
                          <p className="text-slate-200 text-sm">{tx.description}</p>
                          <p className="text-slate-500 text-xs">
                            {new Date(tx.timestamp).toLocaleString('ko-KR')}
                          </p>
                        </div>
                      </div>
                      <div className={`text-sm font-medium ${
                        tx.amount > 0 ? "text-green-400" : "text-red-400"
                      }`}>
                        {tx.amount > 0 ? "+" : ""}{tx.amount.toLocaleString()}P
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* 우측: 적립 기준 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 text-base flex items-center gap-2">
              <Info className="w-5 h-5 text-blue-400" />
              포인트 적립 기준
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {earningRules.map((rule, idx) => (
                  <div 
                    key={idx} 
                    className="bg-slate-900 rounded-lg p-3 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                        <Gift className="w-4 h-4 text-amber-400" />
                      </div>
                      <div>
                        <p className="text-slate-200 text-sm">{rule.description}</p>
                        <p className="text-slate-500 text-xs">{rule.action}</p>
                      </div>
                    </div>
                    <Badge className="bg-amber-500/20 text-amber-400">
                      +{rule.points}P
                    </Badge>
                  </div>
                ))}
                
                {/* 전환 정보 */}
                <div className="bg-green-900/20 rounded-lg p-4 mt-4 border border-green-700/50">
                  <p className="text-green-400 text-sm font-medium mb-2">💰 포인트 전환</p>
                  <p className="text-slate-400 text-xs">
                    유료 전환 시 적립된 포인트를 현금으로 대체하여 사용할 수 있습니다.
                  </p>
                  <div className="mt-2 text-xs text-slate-500">
                    • 환율: ₩1 = 0.1 포인트<br/>
                    • 예시: 1,000P = ₩10,000
                  </div>
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MyAssetsTab;
