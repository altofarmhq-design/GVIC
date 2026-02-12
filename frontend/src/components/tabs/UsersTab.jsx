import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Users, Shield, Trash2, RefreshCw, Crown, Eye, Settings2
} from 'lucide-react';

export default function UsersTab() {
  const { user: currentUser, hasRole } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, user: null });
  const [roleDialog, setRoleDialog] = useState({ open: false, user: null, newRole: '' });

  const fetchUsers = async () => {
    try {
      const response = await api.getUsers();
      setUsers(response.data.users);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDeleteUser = async () => {
    if (!deleteDialog.user) return;
    try {
      await api.deleteUser(deleteDialog.user.user_id);
      fetchUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
    setDeleteDialog({ open: false, user: null });
  };

  const handleChangeRole = async () => {
    if (!roleDialog.user || !roleDialog.newRole) return;
    try {
      await api.updateUser(roleDialog.user.user_id, { role: roleDialog.newRole });
      fetchUsers();
    } catch (error) {
      console.error('Failed to update role:', error);
    }
    setRoleDialog({ open: false, user: null, newRole: '' });
  };

  const getRoleBadge = (role) => {
    const styles = {
      super_admin: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
      admin: 'bg-red-500/20 text-red-400 border-red-500/50',
      operator: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
      visitor: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
      ext_admin: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
      ext_operator: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      ext_visitor: 'bg-slate-500/20 text-slate-400 border-slate-500/50'
    };
    const labels = {
      super_admin: '최고관리자',
      admin: '관리자',
      operator: '오퍼레이터',
      visitor: '방문객',
      ext_admin: '외부관리자',
      ext_operator: '외부오퍼레이터',
      ext_visitor: '외부방문객'
    };
    const icons = {
      super_admin: <Crown className="w-3 h-3 mr-1" />,
      admin: <Shield className="w-3 h-3 mr-1" />,
      operator: <Settings2 className="w-3 h-3 mr-1" />,
      visitor: <Eye className="w-3 h-3 mr-1" />,
      ext_admin: <Shield className="w-3 h-3 mr-1" />,
      ext_operator: <Settings2 className="w-3 h-3 mr-1" />,
      ext_visitor: <Eye className="w-3 h-3 mr-1" />
    };
    return (
      <Badge variant="outline" className={`${styles[role] || styles.visitor} flex items-center`}>
        {icons[role] || icons.visitor}
        {labels[role] || role}
      </Badge>
    );
  };

  const isExternalRole = (role) => role?.startsWith('ext_');

  if (!hasRole(['super_admin', 'admin'])) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Shield className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400">관리자 권한이 필요합니다</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="users-tab">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">사용자 관리</h2>
          <p className="text-slate-400">시스템 사용자 및 권한을 관리합니다</p>
        </div>
        <Button variant="outline" onClick={fetchUsers}>
          <RefreshCw className="w-4 h-4 mr-2" /> 새로고침
        </Button>
      </div>

      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5" /> 등록된 사용자 ({users.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {users.map((user) => (
              <div 
                key={user.user_id}
                className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg"
                data-testid={`user-card-${user.user_id}`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center overflow-hidden">
                    {user.picture ? (
                      <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-lg font-semibold text-slate-300">
                        {user.name?.charAt(0)?.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-100">{user.name}</span>
                      {user.user_id === currentUser?.user_id && (
                        <Badge className="bg-violet-500/20 text-violet-400">나</Badge>
                      )}
                    </div>
                    <span className="text-sm text-slate-400">{user.email}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {getRoleBadge(user.role)}
                  <Badge variant="outline" className="text-slate-400 border-slate-600">
                    {user.auth_provider === 'google' ? 'Google' : '이메일'}
                  </Badge>
                  {user.user_id !== currentUser?.user_id && (
                    <>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setRoleDialog({ open: true, user, newRole: user.role })}
                      >
                        <Shield className="w-4 h-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        className="text-red-400 border-red-500/50 hover:bg-red-500/20"
                        onClick={() => setDeleteDialog({ open: true, user })}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Role Change Dialog */}
      <Dialog open={roleDialog.open} onOpenChange={(open) => !open && setRoleDialog({ open: false, user: null, newRole: '' })}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-100">역할 변경</DialogTitle>
            <DialogDescription className="text-slate-400">
              {roleDialog.user?.name}의 역할을 변경합니다
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={roleDialog.newRole} onValueChange={(v) => setRoleDialog(prev => ({ ...prev, newRole: v }))}>
              <SelectTrigger className="bg-slate-700 border-slate-600">
                <SelectValue placeholder="역할 선택" />
              </SelectTrigger>
              <SelectContent className="bg-slate-700 border-slate-600">
                <SelectItem value="super_admin" disabled={currentUser?.role !== 'super_admin'}>최고관리자 (전체 권한 + 시스템 설정)</SelectItem>
                <SelectItem value="admin">관리자 (전체 권한)</SelectItem>
                <SelectItem value="operator">오퍼레이터 (처리/리포트)</SelectItem>
                <SelectItem value="visitor">방문객 (읽기 전용)</SelectItem>
                <SelectItem value="ext_admin">외부관리자 (읽기 전용)</SelectItem>
                <SelectItem value="ext_operator">외부오퍼레이터 (읽기 전용)</SelectItem>
                <SelectItem value="ext_visitor">외부방문객 (읽기 전용)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRoleDialog({ open: false, user: null, newRole: '' })}>취소</Button>
            <Button onClick={handleChangeRole}>변경</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onOpenChange={(open) => !open && setDeleteDialog({ open: false, user: null })}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-100">사용자 삭제</DialogTitle>
            <DialogDescription className="text-slate-400">
              정말로 {deleteDialog.user?.name}을(를) 삭제하시겠습니까?
              이 작업은 되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog({ open: false, user: null })}>취소</Button>
            <Button variant="destructive" onClick={handleDeleteUser}>삭제</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
