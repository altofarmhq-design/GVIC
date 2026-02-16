import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  ShoppingCart, 
  Package,
  Users,
  Tag,
  Search,
  Filter,
  TrendingUp,
  Coins,
  Star,
  Eye,
  ShoppingBag,
  Award,
  RefreshCw,
  ChevronRight,
  Layers,
  DollarSign,
  Check,
  X
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * 모듈 마켓 탭
 * - 판매 중인 모듈 목록
 * - 모듈 상세 및 구매
 * - 카테고리별 필터링
 * - 내 기여 모듈
 */
export const ModuleMarketTab = () => {
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [moduleDetail, setModuleDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [purchasing, setPurchasing] = useState(false);
  const [stats, setStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [activeTab, setActiveTab] = useState("browse"); // browse, my-contributions
  const [myContributions, setMyContributions] = useState([]);
  const [purchaseResult, setPurchaseResult] = useState(null);

  const categories = [
    { id: "all", name: "전체", icon: Layers },
    { id: "technology", name: "기술", icon: TrendingUp },
    { id: "business", name: "비즈니스", icon: DollarSign },
    { id: "patent_idea", name: "특허/아이디어", icon: Star },
    { id: "process", name: "프로세스", icon: RefreshCw },
    { id: "general", name: "일반", icon: Package }
  ];

  // 모듈 목록 조회
  const fetchModules = async () => {
    setLoading(true);
    try {
      const params = categoryFilter !== "all" ? `?category=${categoryFilter}` : "";
      const response = await axios.get(`${API_URL}/api/modules/list${params}`);
      setModules(response.data.modules || []);
    } catch (err) {
      console.error("Failed to fetch modules:", err);
    }
    setLoading(false);
  };

  // 통계 조회
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/modules/stats/overview`);
      setStats(response.data);
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  };

  // 모듈 상세 조회
  const fetchModuleDetail = async (moduleId) => {
    try {
      const response = await axios.get(`${API_URL}/api/modules/${moduleId}`);
      setModuleDetail(response.data);
    } catch (err) {
      console.error("Failed to fetch module detail:", err);
    }
  };

  // 내 기여 모듈 조회
  const fetchMyContributions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/points/asset-summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyContributions(response.data);
    } catch (err) {
      console.error("Failed to fetch contributions:", err);
    }
  };

  useEffect(() => {
    fetchModules();
    fetchStats();
    fetchMyContributions();
  }, [categoryFilter]);

  // 모듈 선택
  const selectModule = (module) => {
    setSelectedModule(module);
    fetchModuleDetail(module.module_id);
    setPurchaseResult(null);
  };

  // 모듈 구매
  const purchaseModule = async () => {
    if (!selectedModule) return;
    
    setPurchasing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/modules/purchase`,
        {
          module_id: selectedModule.module_id,
          purchase_price: selectedModule.price
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setPurchaseResult(response.data);
      fetchModules();
      fetchStats();
    } catch (err) {
      setPurchaseResult({ 
        success: false, 
        error: err.response?.data?.detail || "구매 실패" 
      });
    }
    setPurchasing(false);
  };

  // 필터링된 모듈
  const filteredModules = modules.filter(m => 
    searchQuery === "" || 
    m.module_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.feature_keywords?.some(k => k.includes(searchQuery.toLowerCase()))
  );

  const getCategoryIcon = (category) => {
    const cat = categories.find(c => c.id === category);
    return cat?.icon || Package;
  };

  const getCategoryName = (category) => {
    const cat = categories.find(c => c.id === category);
    return cat?.name || category;
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
              <ShoppingCart className="w-5 h-5 text-white" />
            </div>
            모듈 마켓
          </h2>
          <p className="text-slate-400 mt-1">자산화된 모듈을 구매하고 기여자에게 보상을 전달하세요</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => { fetchModules(); fetchStats(); }}>
          <RefreshCw className="w-4 h-4 mr-1" />
          새로고침
        </Button>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-900/40 to-slate-800 border-emerald-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                <Package className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-emerald-400 text-xs">판매 중 모듈</p>
                <p className="text-2xl font-bold text-white">{stats?.modules?.available || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-900/40 to-slate-800 border-blue-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <Layers className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-blue-400 text-xs">총 자산</p>
                <p className="text-2xl font-bold text-white">{stats?.assets?.total || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/40 to-slate-800 border-amber-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-amber-400 text-xs">총 거래액</p>
                <p className="text-2xl font-bold text-white">₩{(stats?.revenue?.total || 0).toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-900/40 to-slate-800 border-purple-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <Coins className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-purple-400 text-xs">기여자 보상</p>
                <p className="text-2xl font-bold text-white">₩{(stats?.revenue?.contributor_share || 0).toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 탭 선택 */}
      <div className="flex gap-2">
        <Button
          variant={activeTab === "browse" ? "default" : "outline"}
          onClick={() => setActiveTab("browse")}
          className={activeTab === "browse" ? "bg-emerald-600" : ""}
        >
          <ShoppingBag className="w-4 h-4 mr-2" />
          마켓 둘러보기
        </Button>
        <Button
          variant={activeTab === "my-contributions" ? "default" : "outline"}
          onClick={() => setActiveTab("my-contributions")}
          className={activeTab === "my-contributions" ? "bg-purple-600" : ""}
        >
          <Award className="w-4 h-4 mr-2" />
          내 기여 현황
        </Button>
      </div>

      {activeTab === "browse" && (
        <div className="grid grid-cols-3 gap-6">
          {/* 좌측: 모듈 목록 */}
          <div className="col-span-2 space-y-4">
            {/* 검색 및 필터 */}
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="모듈 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-800 border-slate-600 text-slate-100"
                />
              </div>
              <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setCategoryFilter(cat.id)}
                      className={`px-3 py-1.5 rounded-md text-xs flex items-center gap-1 transition-all ${
                        categoryFilter === cat.id
                          ? 'bg-emerald-600 text-white'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="w-3 h-3" />
                      {cat.name}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 모듈 그리드 */}
            <ScrollArea className="h-[500px]">
              {loading ? (
                <div className="flex items-center justify-center h-40">
                  <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
                </div>
              ) : filteredModules.length === 0 ? (
                <div className="text-center py-12">
                  <Package className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-500 text-lg">판매 중인 모듈이 없습니다</p>
                  <p className="text-slate-600 text-sm mt-2">새로운 자산이 모듈화되면 여기에 표시됩니다</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {filteredModules.map((module) => {
                    const CategoryIcon = getCategoryIcon(module.feature_category);
                    const isSelected = selectedModule?.module_id === module.module_id;
                    
                    return (
                      <Card
                        key={module.module_id}
                        onClick={() => selectModule(module)}
                        className={`cursor-pointer transition-all hover:border-emerald-600 ${
                          isSelected 
                            ? 'bg-emerald-900/30 border-emerald-500' 
                            : 'bg-slate-800/50 border-slate-700'
                        }`}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                                isSelected ? 'bg-emerald-500/30' : 'bg-slate-700'
                              }`}>
                                <CategoryIcon className={`w-4 h-4 ${isSelected ? 'text-emerald-400' : 'text-slate-400'}`} />
                              </div>
                              <Badge variant="outline" className="text-xs">
                                {getCategoryName(module.feature_category)}
                              </Badge>
                            </div>
                            <div className="text-right">
                              <p className="text-emerald-400 font-bold">₩{module.price?.toLocaleString()}</p>
                            </div>
                          </div>
                          
                          <h3 className="text-slate-100 font-medium mb-2 truncate">{module.module_name}</h3>
                          <p className="text-slate-500 text-xs mb-3 line-clamp-2">{module.description}</p>
                          
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <Layers className="w-3 h-3" />
                              {module.asset_count}개 자산
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {module.contributor_count}명 기여
                            </span>
                          </div>
                          
                          {module.feature_keywords?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3">
                              {module.feature_keywords.slice(0, 3).map((kw, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs bg-slate-700">
                                  {kw}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* 우측: 모듈 상세 및 구매 */}
          <div className="space-y-4">
            {selectedModule && moduleDetail ? (
              <>
                {/* 모듈 상세 */}
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-slate-100 text-lg flex items-center gap-2">
                      <Eye className="w-5 h-5 text-emerald-400" />
                      모듈 상세
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-1">{moduleDetail.module_name}</h3>
                      <p className="text-slate-400 text-sm">{moduleDetail.description}</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-slate-900 rounded-lg p-3">
                        <p className="text-slate-500 text-xs">가격</p>
                        <p className="text-emerald-400 font-bold text-lg">₩{moduleDetail.price?.toLocaleString()}</p>
                      </div>
                      <div className="bg-slate-900 rounded-lg p-3">
                        <p className="text-slate-500 text-xs">포함 자산</p>
                        <p className="text-white font-bold text-lg">{moduleDetail.asset_count}개</p>
                      </div>
                      <div className="bg-slate-900 rounded-lg p-3">
                        <p className="text-slate-500 text-xs">기여자 수</p>
                        <p className="text-white font-bold text-lg">{moduleDetail.contributor_count}명</p>
                      </div>
                      <div className="bg-slate-900 rounded-lg p-3">
                        <p className="text-slate-500 text-xs">평균 가치</p>
                        <p className="text-white font-bold text-lg">{(moduleDetail.avg_value_score * 100).toFixed(0)}점</p>
                      </div>
                    </div>
                    
                    {/* 보상 분배 미리보기 */}
                    <div className="bg-gradient-to-r from-purple-900/30 to-slate-800 rounded-lg p-4 border border-purple-700/50">
                      <p className="text-purple-400 text-sm font-medium mb-2">💰 구매 시 기여자 보상</p>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between text-slate-400">
                          <span>기여자 몫 (20%)</span>
                          <span className="text-purple-300">₩{(moduleDetail.price * 0.2).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>자산당 보상</span>
                          <span className="text-purple-300">₩{(moduleDetail.price * 0.2 / moduleDetail.asset_count).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-slate-400">
                          <span>포인트 환산</span>
                          <span className="text-amber-400">{((moduleDetail.price * 0.2 / moduleDetail.asset_count) * 1000).toLocaleString()}P/자산</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* 포함 자산 목록 */}
                    {moduleDetail.asset_details?.length > 0 && (
                      <div>
                        <p className="text-slate-300 text-sm font-medium mb-2">포함된 자산</p>
                        <ScrollArea className="h-[150px]">
                          <div className="space-y-2">
                            {moduleDetail.asset_details.map((asset, idx) => (
                              <div key={idx} className="bg-slate-900 rounded p-2 text-xs">
                                <div className="flex items-center justify-between mb-1">
                                  <Badge variant="outline" className="text-xs">
                                    {getCategoryName(asset.feature_category)}
                                  </Badge>
                                  <span className="text-slate-500">{(asset.value_score * 100).toFixed(0)}점</span>
                                </div>
                                <p className="text-slate-400 truncate">{asset.content_summary}</p>
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* 구매 버튼 */}
                <Button
                  onClick={purchaseModule}
                  disabled={purchasing}
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white py-6 text-lg"
                >
                  {purchasing ? (
                    <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                  ) : (
                    <ShoppingCart className="w-5 h-5 mr-2" />
                  )}
                  ₩{moduleDetail.price?.toLocaleString()} 구매하기
                </Button>

                {/* 구매 결과 */}
                {purchaseResult && (
                  <Card className={`border ${purchaseResult.success ? 'bg-green-900/20 border-green-600' : 'bg-red-900/20 border-red-600'}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {purchaseResult.success ? (
                          <Check className="w-5 h-5 text-green-400 mt-0.5" />
                        ) : (
                          <X className="w-5 h-5 text-red-400 mt-0.5" />
                        )}
                        <div>
                          <p className={`font-medium ${purchaseResult.success ? 'text-green-300' : 'text-red-300'}`}>
                            {purchaseResult.success ? '구매 완료!' : '구매 실패'}
                          </p>
                          {purchaseResult.success ? (
                            <div className="text-xs text-slate-400 mt-2 space-y-1">
                              <p>• {purchaseResult.unique_contributors}명 기여자에게 보상 전달</p>
                              <p>• 총 ₩{purchaseResult.contributor_share_total?.toLocaleString()} 분배</p>
                              <p>• 자산당 ₩{purchaseResult.reward_per_asset?.cash?.toLocaleString()} ({purchaseResult.reward_per_asset?.points?.toLocaleString()}P)</p>
                            </div>
                          ) : (
                            <p className="text-xs text-red-400 mt-1">{purchaseResult.error}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card className="bg-slate-800/30 border-slate-700 border-dashed h-full flex items-center justify-center min-h-[400px]">
                <div className="text-center py-8">
                  <ShoppingBag className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-500 text-lg">모듈을 선택하세요</p>
                  <p className="text-slate-600 text-sm mt-2">상세 정보와 구매 옵션을 확인할 수 있습니다</p>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* 내 기여 현황 탭 */}
      {activeTab === "my-contributions" && (
        <div className="grid grid-cols-2 gap-6">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100 flex items-center gap-2">
                <Award className="w-5 h-5 text-purple-400" />
                내 기여 요약
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900 rounded-lg p-4 text-center">
                  <p className="text-slate-500 text-sm">제출 시그널</p>
                  <p className="text-3xl font-bold text-white">{myContributions?.signals?.total || 0}</p>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 text-center">
                  <p className="text-slate-500 text-sm">자산화됨</p>
                  <p className="text-3xl font-bold text-purple-400">{myContributions?.signals?.asset_converted || 0}</p>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 text-center">
                  <p className="text-slate-500 text-sm">총 자산</p>
                  <p className="text-3xl font-bold text-emerald-400">{myContributions?.assets?.total || 0}</p>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 text-center">
                  <p className="text-slate-500 text-sm">보유 포인트</p>
                  <p className="text-3xl font-bold text-amber-400">{(myContributions?.points?.available || 0).toLocaleString()}</p>
                </div>
              </div>
              
              <div className="bg-gradient-to-r from-amber-900/30 to-slate-800 rounded-lg p-4">
                <p className="text-amber-400 text-sm font-medium">현금 환산 가치</p>
                <p className="text-2xl font-bold text-white">₩{(myContributions?.points?.cash_equivalent || 0).toLocaleString()}</p>
                <p className="text-slate-500 text-xs mt-1">1000P = ₩1</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-slate-100 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                기여 등급
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center py-6">
                <div className="w-20 h-20 mx-auto bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center mb-4">
                  <Award className="w-10 h-10 text-white" />
                </div>
                <p className="text-2xl font-bold text-white">{myContributions?.evaluation?.rank || 'Bronze'}</p>
                <p className="text-slate-400">Lv.{myContributions?.evaluation?.contribution_level?.level || 1} {myContributions?.evaluation?.contribution_level?.name || '입문자'}</p>
              </div>
              
              <div className="bg-slate-900 rounded-lg p-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-400">활동 점수</span>
                  <span className="text-white">{myContributions?.evaluation?.activity_score || 0}점</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-emerald-500 to-teal-500 h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100, myContributions?.evaluation?.activity_score || 0)}%` }}
                  />
                </div>
              </div>
              
              <p className="text-slate-500 text-xs text-center">
                더 많은 시그널을 제출하고 자산화하여 등급을 올리세요!
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ModuleMarketTab;
