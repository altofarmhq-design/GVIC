/**
 * My Products Tab - 내 상품 관리
 * 쇼핑몰 및 제품 등록/관리
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Store, Package, Plus, RefreshCw, Trash2, Edit, ExternalLink,
  CheckCircle, XCircle, AlertTriangle, BarChart2
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export default function MyProductsTab({ onAnalyze }) {
  const [shops, setShops] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('shops');
  
  // Dialog states
  const [shopDialogOpen, setShopDialogOpen] = useState(false);
  const [productDialogOpen, setProductDialogOpen] = useState(false);
  const [selectedShop, setSelectedShop] = useState(null);
  
  // Form states
  const [shopForm, setShopForm] = useState({
    name: '',
    platform: 'naver',
    url: '',
    description: ''
  });
  const [productForm, setProductForm] = useState({
    name: '',
    product_url: '',
    product_id_external: '',
    category: '',
    price: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [shopsRes, productsRes] = await Promise.all([
        api.getShops().catch(() => ({ data: { shops: [] } })),
        api.getAllProducts().catch(() => ({ data: { products: [] } }))
      ]);
      setShops(shopsRes.data?.shops || []);
      setProducts(productsRes.data?.products || []);
    } catch (error) {
      console.error('Fetch error:', error);
      toast.error('데이터를 불러오는데 실패했습니다');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRegisterShop = async () => {
    try {
      await api.registerShop(shopForm);
      toast.success('쇼핑몰이 등록되었습니다');
      setShopDialogOpen(false);
      setShopForm({ name: '', platform: 'naver', url: '', description: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '등록에 실패했습니다');
    }
  };

  const handleRegisterProduct = async () => {
    if (!selectedShop) {
      toast.error('쇼핑몰을 먼저 선택해주세요');
      return;
    }
    try {
      await api.registerProduct(selectedShop.shop_id, productForm);
      toast.success('제품이 등록되었습니다');
      setProductDialogOpen(false);
      setProductForm({ name: '', product_url: '', product_id_external: '', category: '', price: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '등록에 실패했습니다');
    }
  };

  const handleDeleteShop = async (shopId) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;
    try {
      await api.deleteShop(shopId);
      toast.success('쇼핑몰이 삭제되었습니다');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '삭제에 실패했습니다');
    }
  };

  const platformOptions = [
    { value: 'naver', label: '네이버 스마트스토어', icon: '🟢' },
    { value: 'coupang', label: '쿠팡', icon: '🔴' },
    { value: '11st', label: '11번가', icon: '🟠' },
    { value: 'gmarket', label: 'G마켓', icon: '🟡' },
    { value: 'auction', label: '옥션', icon: '🔵' },
    { value: 'self', label: '자사몰', icon: '⚫' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="my-products-tab">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">내 상품 관리</h2>
          <p className="text-slate-400">쇼핑몰과 제품을 등록하고 관리하세요</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" /> 새로고침
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800">
          <TabsTrigger value="shops" className="data-[state=active]:bg-violet-600">
            <Store className="w-4 h-4 mr-2" /> 쇼핑몰 ({shops.length})
          </TabsTrigger>
          <TabsTrigger value="products" className="data-[state=active]:bg-violet-600">
            <Package className="w-4 h-4 mr-2" /> 제품 ({products.length})
          </TabsTrigger>
        </TabsList>

        {/* 쇼핑몰 탭 */}
        <TabsContent value="shops" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={shopDialogOpen} onOpenChange={setShopDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-violet-600 hover:bg-violet-700">
                  <Plus className="w-4 h-4 mr-2" /> 쇼핑몰 등록
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-700">
                <DialogHeader>
                  <DialogTitle className="text-white">새 쇼핑몰 등록</DialogTitle>
                  <DialogDescription>리뷰를 분석할 쇼핑몰 정보를 입력하세요</DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>플랫폼</Label>
                    <Select 
                      value={shopForm.platform} 
                      onValueChange={(v) => setShopForm({ ...shopForm, platform: v })}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        {platformOptions.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.icon} {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>쇼핑몰 이름</Label>
                    <Input 
                      value={shopForm.name}
                      onChange={(e) => setShopForm({ ...shopForm, name: e.target.value })}
                      placeholder="예: 내 스마트스토어"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>쇼핑몰 URL</Label>
                    <Input 
                      value={shopForm.url}
                      onChange={(e) => setShopForm({ ...shopForm, url: e.target.value })}
                      placeholder="https://smartstore.naver.com/myshop"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>설명 (선택)</Label>
                    <Input 
                      value={shopForm.description}
                      onChange={(e) => setShopForm({ ...shopForm, description: e.target.value })}
                      placeholder="쇼핑몰 설명"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShopDialogOpen(false)}>취소</Button>
                  <Button onClick={handleRegisterShop} className="bg-violet-600 hover:bg-violet-700">등록</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {shops.length === 0 ? (
            <Card className="bg-slate-800/50 border-slate-700 border-dashed">
              <CardContent className="p-12 text-center">
                <Store className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">등록된 쇼핑몰이 없습니다</h3>
                <p className="text-slate-400 mb-4">첫 번째 쇼핑몰을 등록해주세요</p>
                <Button onClick={() => setShopDialogOpen(true)} className="bg-violet-600">
                  <Plus className="w-4 h-4 mr-2" /> 쇼핑몰 등록
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {shops.map((shop) => (
                <Card key={shop.shop_id} className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-violet-500/20 rounded-xl flex items-center justify-center">
                          <Store className="w-6 h-6 text-violet-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-semibold text-white">{shop.name}</h3>
                            {shop.is_active ? (
                              <Badge className="bg-emerald-500/20 text-emerald-400">
                                <CheckCircle className="w-3 h-3 mr-1" /> 활성
                              </Badge>
                            ) : (
                              <Badge className="bg-slate-600 text-slate-300">
                                <XCircle className="w-3 h-3 mr-1" /> 비활성
                              </Badge>
                            )}
                          </div>
                          <p className="text-slate-400 text-sm">
                            {platformOptions.find(p => p.value === shop.platform)?.icon} {' '}
                            {platformOptions.find(p => p.value === shop.platform)?.label}
                          </p>
                          <a 
                            href={shop.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-violet-400 text-sm hover:underline flex items-center gap-1"
                          >
                            {shop.url} <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-slate-600">
                          제품 {shop.product_count || 0}개
                        </Badge>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => {
                            setSelectedShop(shop);
                            setActiveTab('products');
                          }}
                        >
                          <Package className="w-4 h-4 mr-1" /> 제품 추가
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDeleteShop(shop.shop_id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 제품 탭 */}
        <TabsContent value="products" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <Select 
                value={selectedShop?.shop_id || ''} 
                onValueChange={(v) => setSelectedShop(shops.find(s => s.shop_id === v))}
              >
                <SelectTrigger className="w-[250px] bg-slate-800 border-slate-700">
                  <SelectValue placeholder="쇼핑몰 선택" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  {shops.map(shop => (
                    <SelectItem key={shop.shop_id} value={shop.shop_id}>
                      {shop.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Dialog open={productDialogOpen} onOpenChange={setProductDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-violet-600 hover:bg-violet-700" disabled={!selectedShop}>
                  <Plus className="w-4 h-4 mr-2" /> 제품 등록
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-700">
                <DialogHeader>
                  <DialogTitle className="text-white">새 제품 등록</DialogTitle>
                  <DialogDescription>
                    {selectedShop?.name}에 제품을 추가합니다
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>제품명</Label>
                    <Input 
                      value={productForm.name}
                      onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                      placeholder="예: 프리미엄 무선 이어폰"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>제품 URL</Label>
                    <Input 
                      value={productForm.product_url}
                      onChange={(e) => setProductForm({ ...productForm, product_url: e.target.value })}
                      placeholder="제품 상세 페이지 URL"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>카테고리</Label>
                    <Input 
                      value={productForm.category}
                      onChange={(e) => setProductForm({ ...productForm, category: e.target.value })}
                      placeholder="예: 전자기기 > 이어폰"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>가격 (선택)</Label>
                    <Input 
                      value={productForm.price}
                      onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
                      placeholder="예: 99,000원"
                      className="bg-slate-800 border-slate-700"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setProductDialogOpen(false)}>취소</Button>
                  <Button onClick={handleRegisterProduct} className="bg-violet-600 hover:bg-violet-700">등록</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {products.length === 0 ? (
            <Card className="bg-slate-800/50 border-slate-700 border-dashed">
              <CardContent className="p-12 text-center">
                <Package className="w-12 h-12 text-slate-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">등록된 제품이 없습니다</h3>
                <p className="text-slate-400 mb-4">쇼핑몰을 선택하고 제품을 등록해주세요</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {products
                .filter(p => !selectedShop || p.shop_id === selectedShop.shop_id)
                .map((product) => (
                <Card key={product.product_id} className="bg-slate-800/50 border-slate-700">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-violet-500/20 rounded-lg flex items-center justify-center">
                          <Package className="w-5 h-5 text-violet-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">{product.name}</h4>
                          <p className="text-slate-400 text-sm">{product.category || '미분류'}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {product.last_analysis_at ? (
                          <Badge className="bg-emerald-500/20 text-emerald-400">분석 완료</Badge>
                        ) : (
                          <Badge className="bg-slate-600 text-slate-300">미분석</Badge>
                        )}
                        <Button 
                          size="sm" 
                          onClick={() => onAnalyze?.(product.product_id)}
                          className="bg-violet-600 hover:bg-violet-700"
                        >
                          <BarChart2 className="w-4 h-4 mr-1" /> 분석
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
