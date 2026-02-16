/**
 * Billing Tab - 결제 및 구독 관리
 * 구독 플랜 선택 및 결제 수단 관리
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  CreditCard, Check, Star, Zap, Crown, Building2,
  RefreshCw, AlertCircle, CheckCircle, Clock, ArrowRight
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export default function BillingTab() {
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [checkoutDialogOpen, setCheckoutDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedPayment, setSelectedPayment] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [plansRes, subRes, methodsRes] = await Promise.all([
        api.getPaymentPlans().catch(() => ({ data: { plans: [] } })),
        api.getSubscriptionStatus().catch(() => ({ data: null })),
        api.getPaymentMethods().catch(() => ({ data: { methods: [] } }))
      ]);
      setPlans(plansRes.data?.plans || defaultPlans);
      setSubscription(subRes.data);
      setPaymentMethods(methodsRes.data?.methods || defaultPaymentMethods);
    } catch (error) {
      console.error('Fetch error:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSelectPlan = (plan) => {
    setSelectedPlan(plan);
    setCheckoutDialogOpen(true);
  };

  const handleCheckout = async () => {
    if (!selectedPlan || !selectedPayment) {
      toast.error('결제 수단을 선택해주세요');
      return;
    }
    try {
      const res = await api.createUnifiedCheckout({
        plan_id: selectedPlan.id,
        payment_provider: selectedPayment.id,
        amount: selectedPlan.price
      });
      
      if (res.data?.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else if (res.data?.simulated) {
        toast.success('시뮬레이션 결제가 완료되었습니다');
        setCheckoutDialogOpen(false);
        fetchData();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || '결제 처리에 실패했습니다');
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('정말 구독을 취소하시겠습니까?')) return;
    try {
      await api.cancelSubscription();
      toast.success('구독이 취소되었습니다');
      fetchData();
    } catch (error) {
      toast.error('구독 취소에 실패했습니다');
    }
  };

  const planIcons = {
    free: Star,
    starter: Zap,
    growth: Crown,
    pro: Building2,
    enterprise: Building2
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="billing-tab">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">결제 및 구독</h2>
          <p className="text-slate-400">구독 플랜을 선택하고 관리하세요</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> 새로고침
        </Button>
      </div>

      {/* 현재 구독 상태 */}
      {subscription && (
        <Card className="bg-gradient-to-r from-violet-600/20 to-purple-600/20 border-violet-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">현재 플랜</p>
                <h3 className="text-2xl font-bold text-white mt-1">
                  {subscription.plan_name || subscription.plan?.toUpperCase() || 'Free'}
                </h3>
                <p className="text-slate-300 mt-2">
                  {subscription.plan === 'free' ? '무료 플랜' : `월 ₩${(subscription.price || 0).toLocaleString()}`}
                </p>
              </div>
              <div className="text-right">
                <Badge className={subscription.is_active ? 'bg-emerald-500' : 'bg-slate-600'}>
                  {subscription.is_active ? '활성' : '비활성'}
                </Badge>
                {subscription.billing_period_end && (
                  <p className="text-slate-400 text-sm mt-2">
                    갱신일: {new Date(subscription.billing_period_end).toLocaleDateString('ko-KR')}
                  </p>
                )}
              </div>
            </div>

            {/* 사용량 */}
            {subscription.usage && (
              <div className="mt-6 space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-400">분석 사용량</span>
                    <span className="text-white">
                      {subscription.usage.analysis_count || 0} / {subscription.limits?.monthly_analysis || '∞'}회
                    </span>
                  </div>
                  <Progress 
                    value={subscription.limits?.monthly_analysis 
                      ? (subscription.usage.analysis_count / subscription.limits.monthly_analysis) * 100 
                      : 0
                    } 
                    className="h-2"
                  />
                </div>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">등록 제품: </span>
                    <span className="text-white">{subscription.usage.product_count || 0} / {subscription.limits?.max_products || '∞'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">등록 쇼핑몰: </span>
                    <span className="text-white">{subscription.usage.shop_count || 0} / {subscription.limits?.max_shops || '∞'}</span>
                  </div>
                </div>
              </div>
            )}

            {subscription.plan !== 'free' && (
              <div className="mt-4 pt-4 border-t border-slate-700">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleCancelSubscription}
                  className="text-red-400 border-red-500/50 hover:bg-red-500/10"
                >
                  구독 취소
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 플랜 선택 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">구독 플랜 선택</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {(plans.length > 0 ? plans : defaultPlans).map((plan) => {
            const Icon = planIcons[plan.id] || Star;
            const isCurrentPlan = subscription?.plan === plan.id;
            
            return (
              <Card 
                key={plan.id}
                className={`bg-slate-800/50 border-slate-700 relative ${
                  plan.popular ? 'border-violet-500 ring-2 ring-violet-500/20' : ''
                } ${isCurrentPlan ? 'ring-2 ring-emerald-500/50' : ''}`}
              >
                {plan.popular && (
                  <Badge className="absolute -top-2 left-1/2 -translate-x-1/2 bg-violet-600">
                    인기
                  </Badge>
                )}
                {isCurrentPlan && (
                  <Badge className="absolute -top-2 right-4 bg-emerald-600">
                    현재 플랜
                  </Badge>
                )}
                <CardHeader>
                  <div className="w-12 h-12 bg-violet-500/20 rounded-xl flex items-center justify-center mb-2">
                    <Icon className="w-6 h-6 text-violet-400" />
                  </div>
                  <CardTitle className="text-white">{plan.name}</CardTitle>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-white">
                      {plan.price === 0 || plan.price === undefined ? '무료' : `₩${(plan.price || 0).toLocaleString()}`}
                    </span>
                    {plan.price > 0 && <span className="text-slate-400">/월</span>}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ul className="space-y-2">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-slate-300">
                        <Check className="w-4 h-4 text-emerald-400" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className={`w-full ${
                      isCurrentPlan 
                        ? 'bg-slate-600 cursor-not-allowed' 
                        : plan.popular 
                          ? 'bg-violet-600 hover:bg-violet-700' 
                          : 'bg-slate-700 hover:bg-slate-600'
                    }`}
                    onClick={() => !isCurrentPlan && handleSelectPlan(plan)}
                    disabled={isCurrentPlan}
                  >
                    {isCurrentPlan ? '현재 플랜' : (plan.price === 0 || plan.price === undefined) ? '시작하기' : '업그레이드'}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 결제 수단 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">결제 수단</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {(paymentMethods.length > 0 ? paymentMethods : defaultPaymentMethods).map((method) => (
            <Card 
              key={method.id}
              className={`bg-slate-800/50 border-slate-700 cursor-pointer transition-all hover:border-violet-500/50 ${
                selectedPayment?.id === method.id ? 'border-violet-500 ring-2 ring-violet-500/20' : ''
              }`}
              onClick={() => setSelectedPayment(method)}
            >
              <CardContent className="p-4 text-center">
                <div className="text-2xl mb-2">{method.icon}</div>
                <p className="text-white text-sm font-medium">{method.name}</p>
                {method.is_simulation && (
                  <Badge className="mt-2 bg-orange-500/20 text-orange-400 text-xs">시뮬레이션</Badge>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 결제 다이얼로그 */}
      <Dialog open={checkoutDialogOpen} onOpenChange={setCheckoutDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">결제 확인</DialogTitle>
            <DialogDescription>선택한 플랜과 결제 수단을 확인해주세요</DialogDescription>
          </DialogHeader>
          
          {selectedPlan && (
            <div className="py-4 space-y-4">
              <div className="p-4 bg-slate-800 rounded-lg">
                <p className="text-slate-400 text-sm">선택한 플랜</p>
                <p className="text-xl font-bold text-white">{selectedPlan.name}</p>
                <p className="text-violet-400">
                  월 ₩{(selectedPlan.price || 0).toLocaleString()}
                </p>
              </div>

              <div>
                <p className="text-slate-400 text-sm mb-2">결제 수단 선택</p>
                <div className="grid grid-cols-3 gap-2">
                  {(paymentMethods.length > 0 ? paymentMethods : defaultPaymentMethods).map((method) => (
                    <Button
                      key={method.id}
                      variant={selectedPayment?.id === method.id ? 'default' : 'outline'}
                      className={selectedPayment?.id === method.id ? 'bg-violet-600' : ''}
                      onClick={() => setSelectedPayment(method)}
                    >
                      {method.icon} {method.name}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setCheckoutDialogOpen(false)}>취소</Button>
            <Button 
              onClick={handleCheckout} 
              className="bg-violet-600 hover:bg-violet-700"
              disabled={!selectedPayment}
            >
              결제하기 <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// 기본 플랜 데이터
const defaultPlans = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    popular: false,
    features: ['월 10회 분석', '제품 3개', '쇼핑몰 1개', '기본 리포트']
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 29000,
    popular: false,
    features: ['월 50회 분석', '제품 5개', '쇼핑몰 1개', '상세 리포트', '이메일 알림']
  },
  {
    id: 'growth',
    name: 'Growth',
    price: 99000,
    popular: true,
    features: ['월 200회 분석', '제품 20개', '쇼핑몰 3개', '상세 리포트', 'API 접근', '웹훅 알림']
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 249000,
    popular: false,
    features: ['월 1,000회 분석', '제품 50개', '쇼핑몰 10개', '프리미엄 리포트', 'API 무제한', '우선 지원']
  }
];

// 기본 결제 수단
const defaultPaymentMethods = [
  { id: 'stripe', name: 'Stripe', icon: '💳', is_simulation: false },
  { id: 'kakaopay', name: '카카오페이', icon: '🟡', is_simulation: true },
  { id: 'naverpay', name: '네이버페이', icon: '🟢', is_simulation: true },
  { id: 'toss', name: '토스', icon: '🔵', is_simulation: true },
  { id: 'samsung', name: '삼성페이', icon: '⚫', is_simulation: true },
  { id: 'payco', name: 'Payco', icon: '🔴', is_simulation: true }
];
