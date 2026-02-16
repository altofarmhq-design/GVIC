/**
 * SaaS Dashboard - 메인 대시보드 컴포넌트
 * 사업자 인텔리전스 허브의 핵심 대시보드
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Store, Package, TrendingUp, TrendingDown, AlertTriangle, 
  Lightbulb, Star, MessageSquare, RefreshCw, ArrowRight,
  CheckCircle, Clock, Zap, BarChart3
} from 'lucide-react';
import { api } from '@/lib/api';

export default function SaasDashboard({ onNavigate }) {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [shops, setShops] = useState([]);
  const [products, setProducts] = useState([]);
  const [subscription, setSubscription] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [shopsRes, productsRes, subRes] = await Promise.all([
        api.getShops().catch(() => ({ data: { shops: [] } })),
        api.getAllProducts().catch(() => ({ data: { products: [] } })),
        api.getSubscriptionStatus().catch(() => ({ data: null }))
      ]);
      
      setShops(shopsRes.data?.shops || []);
      setProducts(productsRes.data?.products || []);
      setSubscription(subRes.data);
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const activeShops = shops.filter(s => s.is_active).length;
  const activeProducts = products.filter(p => p.is_active).length;
  const analyzedProducts = products.filter(p => p.last_analysis_at).length;

  // 최근 분석 요약 (mock data for now)
  const recentInsights = {
    strengths: 12,
    suggestions: 8,
    complaints: 5,
    newNeeds: 3
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="saas-dashboard">
      {/* 웰컴 헤더 */}
      <div className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 rounded-xl p-6 border border-violet-500/30">
        <h2 className="text-2xl font-bold text-white mb-2">셀러 인텔리전스 허브</h2>
        <p className="text-slate-300">고객 리뷰에서 인사이트를 발굴하고, 제품을 개선하세요.</p>
        
        {/* 구독 상태 */}
        {subscription && (
          <div className="mt-4 flex items-center gap-4">
            <Badge className={`px-3 py-1 ${subscription.plan === 'free' ? 'bg-slate-600' : 'bg-violet-600'}`}>
              {subscription.plan_name || subscription.plan?.toUpperCase()}
            </Badge>
            <span className="text-sm text-slate-400">
              분석 {subscription.usage?.analysis_count || 0} / {subscription.limits?.monthly_analysis || '∞'}회 사용
            </span>
            {subscription.plan === 'free' && (
              <Button 
                size="sm" 
                variant="outline" 
                className="ml-auto border-violet-500 text-violet-400 hover:bg-violet-500/20"
                onClick={() => onNavigate?.('billing')}
              >
                플랜 업그레이드 <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            )}
          </div>
        )}
      </div>

      {/* 핵심 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700 hover:border-blue-500/50 transition-colors cursor-pointer" 
              onClick={() => onNavigate?.('shops')}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">등록 쇼핑몰</p>
                <p className="text-3xl font-bold text-white mt-1">{shops.length}</p>
                <p className="text-xs text-emerald-400 mt-1">활성 {activeShops}개</p>
              </div>
              <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
                <Store className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700 hover:border-violet-500/50 transition-colors cursor-pointer"
              onClick={() => onNavigate?.('products')}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">등록 제품</p>
                <p className="text-3xl font-bold text-white mt-1">{products.length}</p>
                <p className="text-xs text-violet-400 mt-1">분석 완료 {analyzedProducts}개</p>
              </div>
              <div className="w-12 h-12 bg-violet-500/20 rounded-xl flex items-center justify-center">
                <Package className="w-6 h-6 text-violet-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700 hover:border-emerald-500/50 transition-colors cursor-pointer"
              onClick={() => onNavigate?.('insights')}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">발견된 강점</p>
                <p className="text-3xl font-bold text-emerald-400 mt-1">{recentInsights.strengths}</p>
                <p className="text-xs text-slate-400 mt-1">유지/보강 필요</p>
              </div>
              <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                <Star className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700 hover:border-orange-500/50 transition-colors cursor-pointer"
              onClick={() => onNavigate?.('insights')}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">개선 필요</p>
                <p className="text-3xl font-bold text-orange-400 mt-1">{recentInsights.complaints + recentInsights.suggestions}</p>
                <p className="text-xs text-slate-400 mt-1">불만 {recentInsights.complaints} / 건의 {recentInsights.suggestions}</p>
              </div>
              <div className="w-12 h-12 bg-orange-500/20 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-orange-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4대 인사이트 요약 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-violet-400" />
              4대 인사이트 현황
            </CardTitle>
            <CardDescription>최근 분석에서 발견된 인사이트</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <InsightBar 
              label="강점" 
              value={recentInsights.strengths} 
              maxValue={30} 
              color="emerald"
              icon={<Star className="w-4 h-4" />}
              description="유지/마케팅 강화"
            />
            <InsightBar 
              label="건의사항" 
              value={recentInsights.suggestions} 
              maxValue={30} 
              color="blue"
              icon={<Lightbulb className="w-4 h-4" />}
              description="서비스 개선"
            />
            <InsightBar 
              label="불만" 
              value={recentInsights.complaints} 
              maxValue={30} 
              color="orange"
              icon={<AlertTriangle className="w-4 h-4" />}
              description="긴급 개선"
            />
            <InsightBar 
              label="신제품 욕구" 
              value={recentInsights.newNeeds} 
              maxValue={30} 
              color="violet"
              icon={<TrendingUp className="w-4 h-4" />}
              description="개발 기회"
            />
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-400" />
              빠른 시작
            </CardTitle>
            <CardDescription>시작하기 위한 단계</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <QuickStartItem 
              step={1}
              title="쇼핑몰 등록"
              description="분석할 쇼핑몰을 등록하세요"
              completed={shops.length > 0}
              onClick={() => onNavigate?.('shops')}
            />
            <QuickStartItem 
              step={2}
              title="제품 추가"
              description="리뷰를 분석할 제품을 등록하세요"
              completed={products.length > 0}
              onClick={() => onNavigate?.('products')}
            />
            <QuickStartItem 
              step={3}
              title="리뷰 분석"
              description="4대 인사이트를 확인하세요"
              completed={analyzedProducts > 0}
              onClick={() => onNavigate?.('insights')}
            />
            <QuickStartItem 
              step={4}
              title="API 연동"
              description="자동화를 위한 API 키를 발급하세요"
              completed={false}
              onClick={() => onNavigate?.('api-guide')}
            />
          </CardContent>
        </Card>
      </div>

      {/* 최근 제품 목록 */}
      {products.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white">최근 등록 제품</CardTitle>
              <CardDescription>분석 대기 중인 제품</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => onNavigate?.('products')}>
              전체 보기 <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {products.slice(0, 5).map((product) => (
                <div key={product.id || product.product_id} 
                     className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-violet-500/20 rounded-lg flex items-center justify-center">
                      <Package className="w-5 h-5 text-violet-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{product.name}</p>
                      <p className="text-slate-400 text-xs">{product.category || '미분류'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {product.last_analysis_at ? (
                      <Badge className="bg-emerald-500/20 text-emerald-400">분석 완료</Badge>
                    ) : (
                      <Badge className="bg-slate-600 text-slate-300">대기 중</Badge>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => onNavigate?.('insights', product.id)}>
                      분석
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 빈 상태 */}
      {shops.length === 0 && (
        <Card className="bg-slate-800/50 border-slate-700 border-dashed">
          <CardContent className="p-12 text-center">
            <div className="w-16 h-16 bg-violet-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Store className="w-8 h-8 text-violet-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">시작하기</h3>
            <p className="text-slate-400 mb-6">첫 번째 쇼핑몰을 등록하고 리뷰 분석을 시작하세요</p>
            <Button onClick={() => onNavigate?.('shops')} className="bg-violet-600 hover:bg-violet-700">
              <Store className="w-4 h-4 mr-2" /> 쇼핑몰 등록하기
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// 인사이트 바 컴포넌트
function InsightBar({ label, value, maxValue, color, icon, description }) {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const colorClasses = {
    emerald: 'bg-emerald-500 text-emerald-400',
    blue: 'bg-blue-500 text-blue-400',
    orange: 'bg-orange-500 text-orange-400',
    violet: 'bg-violet-500 text-violet-400'
  };
  
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={colorClasses[color]?.split(' ')[1]}>{icon}</span>
          <span className="text-slate-300 text-sm font-medium">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-white font-bold">{value}건</span>
          <span className="text-slate-500 text-xs">({description})</span>
        </div>
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}

// 빠른 시작 항목 컴포넌트
function QuickStartItem({ step, title, description, completed, onClick }) {
  return (
    <div 
      className={`flex items-center gap-4 p-4 rounded-lg cursor-pointer transition-colors ${
        completed 
          ? 'bg-emerald-500/10 border border-emerald-500/30' 
          : 'bg-slate-900/50 border border-slate-700/50 hover:border-violet-500/50'
      }`}
      onClick={onClick}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        completed ? 'bg-emerald-500' : 'bg-slate-700'
      }`}>
        {completed ? (
          <CheckCircle className="w-5 h-5 text-white" />
        ) : (
          <span className="text-white font-bold text-sm">{step}</span>
        )}
      </div>
      <div className="flex-1">
        <p className={`font-medium ${completed ? 'text-emerald-400' : 'text-white'}`}>{title}</p>
        <p className="text-slate-400 text-sm">{description}</p>
      </div>
      <ArrowRight className={`w-5 h-5 ${completed ? 'text-emerald-400' : 'text-slate-500'}`} />
    </div>
  );
}
