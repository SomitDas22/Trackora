import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './components/ui/dialog';
import { Textarea } from './components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Clock, Play, Pause, LogOut, UserCheck, Coffee, Calendar, History, BarChart3 } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

const AuthPage = ({ onLogin, orgBranding }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    email_or_phone: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let response;
      if (isLogin) {
        response = await axios.post(`${API}/auth/login`, {
          email_or_phone: formData.email_or_phone,
          password: formData.password
        });
      } else {
        response = await axios.post(`${API}/auth/register`, {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          password: formData.password
        });
      }

      localStorage.setItem('token', response.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // Fetch user data after successful authentication
      const userResponse = await axios.get(`${API}/auth/me`);
      onLogin(userResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          {orgBranding.company_logo && (
            <div className="flex justify-center mb-4">
              <img 
                src={orgBranding.company_logo} 
                alt={orgBranding.company_name} 
                className="h-16 w-16 object-contain"
              />
            </div>
          )}
          <CardTitle className="text-2xl font-bold text-gray-800">
            {isLogin ? 'Welcome Back' : 'Join Our Team'}
          </CardTitle>
          <p className="text-gray-600">{orgBranding.company_name}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    required
                  />
                </div>
              </>
            )}
            
            {isLogin && (
              <div>
                <Label htmlFor="email_or_phone">Email or Phone</Label>
                <Input
                  id="email_or_phone"
                  type="text"
                  value={formData.email_or_phone}
                  onChange={(e) => setFormData({...formData, email_or_phone: e.target.value})}
                  required
                />
              </div>
            )}
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>
            
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
                {error}
              </div>
            )}
            
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={loading}
              data-testid={isLogin ? "login-submit-btn" : "register-submit-btn"}
            >
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
            </Button>
          </form>
          
          <div className="mt-4 text-center space-y-2">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-600 hover:underline block w-full"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
            
            {isLogin && (
              <button
                type="button"
                onClick={() => window.location.href = '/admin-login'}
                className="text-xs text-gray-500 hover:text-gray-700 hover:underline"
                data-testid="admin-login-link"
              >
                Admin Login
              </button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const formatTime = (seconds) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Tree Node Component
const TreeNode = ({ node, level = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  const getIcon = () => {
    switch (node.type) {
      case 'department':
        return <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center text-white text-xs font-bold">D</div>;
      case 'manager':
        return <div className="w-6 h-6 bg-green-500 rounded flex items-center justify-center text-white text-xs font-bold">M</div>;
      case 'project':
        return <div className="w-6 h-6 bg-purple-500 rounded flex items-center justify-center text-white text-xs font-bold">P</div>;
      case 'employee':
        return <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center text-white text-xs font-bold">E</div>;
      default:
        return <div className="w-6 h-6 bg-gray-500 rounded flex items-center justify-center text-white text-xs font-bold">?</div>;
    }
  };

  const getBadgeColor = () => {
    switch (node.type) {
      case 'department': return 'bg-blue-100 text-blue-800';
      case 'manager': return 'bg-green-100 text-green-800';
      case 'project': return 'bg-purple-100 text-purple-800';
      case 'employee': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="ml-4" style={{ marginLeft: `${level * 20}px` }}>
      <div className="flex items-center space-x-2 p-2 hover:bg-slate-600 rounded cursor-pointer">
        {node.children && node.children.length > 0 && (
          <button onClick={() => setIsExpanded(!isExpanded)} className="text-slate-300">
            {isExpanded ? '▼' : '▶'}
          </button>
        )}
        {getIcon()}
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-white font-medium">{node.name}</span>
            <Badge className={`text-xs ${getBadgeColor()}`}>
              {node.type}
            </Badge>
            {node.status && node.status !== 'Active' && (
              <Badge className="text-xs bg-red-100 text-red-800">{node.status}</Badge>
            )}
          </div>
          {node.email && (
            <div className="text-slate-400 text-sm">{node.email}</div>
          )}
          {node.description && (
            <div className="text-slate-400 text-sm">{node.description}</div>
          )}
          {node.designation && (
            <div className="text-slate-400 text-sm">{node.designation}</div>
          )}
          {(node.start_date || node.end_date) && (
            <div className="text-slate-400 text-sm">
              {node.start_date && `Start: ${new Date(node.start_date).toLocaleDateString()}`}
              {node.start_date && node.end_date && ' | '}
              {node.end_date && `End: ${new Date(node.end_date).toLocaleDateString()}`}
            </div>
          )}
        </div>
      </div>
      
      {isExpanded && node.children && node.children.length > 0 && (
        <div className="ml-4">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

const AdminLoginPage = ({ onAdminLogin, orgBranding }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/admin/auth/login`, {
        email: formData.email,
        password: formData.password
      });

      localStorage.setItem('adminToken', response.data.access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // Fetch admin data
      const adminResponse = await axios.get(`${API}/admin/auth/me`);
      onAdminLogin(adminResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Admin authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-blue-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-slate-700">
        <CardHeader className="text-center">
          {orgBranding.company_logo && (
            <div className="flex justify-center mb-4">
              <img 
                src={orgBranding.company_logo} 
                alt={orgBranding.company_name} 
                className="h-16 w-16 object-contain"
              />
            </div>
          )}
          <CardTitle className="text-2xl font-bold text-gray-800">
            Admin Login
          </CardTitle>
          <p className="text-gray-600">{orgBranding.company_name} - Admin Panel</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="admin-email">Admin Email</Label>
              <Input
                id="admin-email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="admin@worktracker.com"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="admin-password">Password</Label>
              <Input
                id="admin-password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>
            
            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
                {error}
              </div>
            )}
            
            <Button 
              type="submit" 
              className="w-full bg-slate-700 hover:bg-slate-800"
              disabled={loading}
              data-testid="admin-login-submit"
            >
              {loading ? 'Signing In...' : 'Admin Sign In'}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => window.location.href = '/'}
              className="text-blue-600 hover:underline text-sm"
              data-testid="back-to-user-login"
            >
              ← Back to Employee Login
            </button>
          </div>
          
          <div className="mt-2 text-xs text-center text-gray-500 bg-gray-50 p-2 rounded">
            Default Admin: admin@worktracker.com / admin123
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Manager/Admin Dashboard Cards
const EmployeeLeaveRequestsCard = () => {
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchLeaveRequests = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/manager/leave-requests`);
      setLeaveRequests(response.data);
    } catch (err) {
      console.error('Error fetching leave requests:', err);
      setLeaveRequests([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReject = async (requestId, status, reason = '') => {
    try {
      await axios.put(`${API}/manager/leave-requests/${requestId}`, {
        status: status,
        manager_reason: reason
      });
      alert(`Leave request ${status} successfully!`);
      fetchLeaveRequests(); // Refresh the list
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to ${status} leave request`);
    }
  };

  const ApprovalDialog = ({ request, onClose }) => {
    const [reason, setReason] = useState('');
    const [action, setAction] = useState('');

    const handleSubmit = () => {
      if (action === 'rejected' && !reason.trim()) {
        alert('Please provide a reason for rejection');
        return;
      }
      handleApproveReject(request.id, action, reason);
      onClose();
    };

    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Process Leave Request</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <div><strong>Employee:</strong> {request.employee_name}</div>
              <div><strong>Type:</strong> {request.leave_type}</div>
              <div><strong>Duration:</strong> {request.start_date} to {request.end_date} ({request.days_count} days)</div>
              <div><strong>Reason:</strong> {request.reason}</div>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="reason">Manager Comment (Required for rejection)</Label>
                <Textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Provide feedback or reason for decision"
                  rows={3}
                />
              </div>
              
              <div className="flex space-x-2">
                <Button 
                  onClick={() => { setAction('approved'); handleSubmit(); }}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  Approve
                </Button>
                <Button 
                  onClick={() => { setAction('rejected'); handleSubmit(); }}
                  variant="outline"
                  className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                >
                  Reject
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  const [selectedRequest, setSelectedRequest] = useState(null);

  return (
    <>
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
        onClick={() => { fetchLeaveRequests(); setShowModal(true); }}
      >
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Employee Leave Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-orange-600">⏳</span>
              <UserCheck className="h-6 w-6 text-slate-500" />
            </div>
            <div className="text-sm text-gray-600">
              Pending approval requests
            </div>
            <div className="text-xs text-blue-600 font-medium pt-1">
              Click to review →
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Employee Leave Requests</DialogTitle>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto space-y-3">
            {loading ? (
              <p>Loading leave requests...</p>
            ) : leaveRequests.length > 0 ? (
              leaveRequests.map(request => (
                <Card key={request.id} className="border">
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-2 flex-1">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="font-medium text-lg">{request.employee_name}</div>
                            <div className="text-sm text-gray-600">{request.leave_type}</div>
                          </div>
                          <div>
                            <div className="text-sm font-medium">Duration</div>
                            <div className="text-sm text-gray-600">
                              {request.start_date} to {request.end_date}
                            </div>
                            <div className="text-sm text-gray-600">({request.days_count} days)</div>
                          </div>
                        </div>
                        <div>
                          <div className="text-sm font-medium">Reason</div>
                          <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                            {request.reason}
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          Applied: {new Date(request.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="ml-4 flex flex-col space-y-2">
                        <Button 
                          onClick={() => setSelectedRequest(request)}
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          Review
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No pending leave requests</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {selectedRequest && (
        <ApprovalDialog 
          request={selectedRequest} 
          onClose={() => setSelectedRequest(null)} 
        />
      )}
    </>
  );
};

const LeaveSettingsCard = () => {
  const [settings, setSettings] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    casual_leave_quarterly: 2,
    sick_leave_quarterly: 2,
    leave_without_pay_quarterly: 5
  });

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/leave-settings`);
      setSettings(response.data);
      setFormData(response.data);
    } catch (err) {
      console.error('Error fetching leave settings:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.put(`${API}/admin/leave-settings`, formData);
      alert('Leave settings updated successfully!');
      setSettings(formData);
      setShowModal(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update leave settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return (
    <>
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
        onClick={() => setShowModal(true)}
      >
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Leave Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-purple-600">📋</span>
              <Calendar className="h-6 w-6 text-slate-500" />
            </div>
            <div className="text-sm text-gray-600">
              {settings ? 'Configure quarterly allocations' : 'Loading...'}
            </div>
            {settings && (
              <div className="text-xs text-gray-500 space-y-1">
                <div>Casual: {settings.casual_leave_quarterly}/quarter</div>
                <div>Sick: {settings.sick_leave_quarterly}/quarter</div>
                <div>LWP: {settings.leave_without_pay_quarterly}/quarter</div>
              </div>
            )}
            <div className="text-xs text-blue-600 font-medium pt-1">
              Click to configure →
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configure Leave Settings</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-4">
              <div>
                <Label htmlFor="casual_leave">Casual Leave (per quarter)</Label>
                <Input
                  id="casual_leave"
                  type="number"
                  min="0"
                  value={formData.casual_leave_quarterly}
                  onChange={(e) => setFormData({...formData, casual_leave_quarterly: parseInt(e.target.value)})}
                  required
                />
                <div className="text-xs text-gray-500 mt-1">
                  Current: {settings?.casual_leave_quarterly || 0} days per quarter
                </div>
              </div>

              <div>
                <Label htmlFor="sick_leave">Sick Leave (per quarter)</Label>
                <Input
                  id="sick_leave"
                  type="number"
                  min="0"
                  value={formData.sick_leave_quarterly}
                  onChange={(e) => setFormData({...formData, sick_leave_quarterly: parseInt(e.target.value)})}
                  required
                />
                <div className="text-xs text-gray-500 mt-1">
                  Current: {settings?.sick_leave_quarterly || 0} days per quarter
                </div>
              </div>

              <div>
                <Label htmlFor="lwp">Leave without Pay (per quarter)</Label>
                <Input
                  id="lwp"
                  type="number"
                  min="0"
                  value={formData.leave_without_pay_quarterly}
                  onChange={(e) => setFormData({...formData, leave_without_pay_quarterly: parseInt(e.target.value)})}
                  required
                />
                <div className="text-xs text-gray-500 mt-1">
                  Current: {settings?.leave_without_pay_quarterly || 0} days per quarter
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-3 rounded text-sm text-blue-800">
              <strong>Note:</strong> Changes will affect all employees' quarterly leave allocations from the next calculation cycle.
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Updating...' : 'Update Settings'}
              </Button>
              <Button type="button" onClick={() => setShowModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};

const AdminDashboard = ({ admin, onLogout, orgBranding }) => {
  const [users, setUsers] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userSessions, setUserSessions] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [adminUsers, setAdminUsers] = useState([]);
  const [holidaysData, setHolidaysData] = useState(null);
  const [managerAssignments, setManagerAssignments] = useState(null);
  const [showCreateAdminModal, setShowCreateAdminModal] = useState(false);
  const [showHolidayModal, setShowHolidayModal] = useState(false);
  const [newAdminData, setNewAdminData] = useState({ name: '', email: '', password: '' });
  const [newHolidayData, setNewHolidayData] = useState({ date: '', name: '', type: 'Mandatory' });
  const [usersOnLeave, setUsersOnLeave] = useState(null);
  const [showAdminUsersPage, setShowAdminUsersPage] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [showEditAdminModal, setShowEditAdminModal] = useState(false);
  const [showHolidayListPage, setShowHolidayListPage] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [showEditHolidayModal, setShowEditHolidayModal] = useState(false);
  const [showEmployeePage, setShowEmployeePage] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [showEditEmployeeModal, setShowEditEmployeeModal] = useState(false);
  const [showCreateEmployeeModal, setShowCreateEmployeeModal] = useState(false);
  const [newEmployeeData, setNewEmployeeData] = useState({
    name: '', email: '', phone: '', password: '',
    dob: '', blood_group: '', emergency_contact: '', address: '',
    aadhar_card: '', designation: '', department: '', joining_date: '', release_date: ''
  });
  const [showManagerAssignmentPage, setShowManagerAssignmentPage] = useState(false);
  const [organizationTree, setOrganizationTree] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [managers, setManagers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [showCreateDepartmentModal, setShowCreateDepartmentModal] = useState(false);
  const [showCreateManagerModal, setShowCreateManagerModal] = useState(false);
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false);
  const [newDepartmentData, setNewDepartmentData] = useState({ name: '', description: '' });
  const [newManagerData, setNewManagerData] = useState({ employee_id: '', department_id: '' });
  const [newProjectData, setNewProjectData] = useState({
    name: '', description: '', department_id: '', manager_id: '', employee_ids: [],
    start_date: '', end_date: '', status: 'Active'
  });
  const [selectedEmployeesForProject, setSelectedEmployeesForProject] = useState([]);
  const [showOrgSettingsPage, setShowOrgSettingsPage] = useState(false);
  const [organizationSettings, setOrganizationSettings] = useState(null);
  const [orgSettingsData, setOrgSettingsData] = useState({
    company_name: '', establishment_date: '', company_email: '',
    founder_name: '', founder_email: '', address: '', phone: '', website: ''
  });
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoPreview, setLogoPreview] = useState(null);

  // Fetch all users
  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (err) {
      console.error('Error fetching users:', err);
    }
  };

  // Fetch admin dashboard stats
  const fetchAdminStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/dashboard-stats`);
      setAdminStats(response.data);
    } catch (err) {
      console.error('Error fetching admin stats:', err);
    }
  };

  // Fetch admin users
  const fetchAdminUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/admin-users`);
      setAdminUsers(response.data);
    } catch (err) {
      console.error('Error fetching admin users:', err);
    }
  };

  // Fetch holidays data
  const fetchHolidaysData = async () => {
    try {
      const response = await axios.get(`${API}/admin/holidays-management`);
      setHolidaysData(response.data);
    } catch (err) {
      console.error('Error fetching holidays data:', err);
    }
  };

  // Fetch manager assignments
  const fetchManagerAssignments = async () => {
    try {
      const response = await axios.get(`${API}/admin/manager-assignments`);
      setManagerAssignments(response.data);
    } catch (err) {
      console.error('Error fetching manager assignments:', err);
    }
  };

  // Fetch users on leave
  const fetchUsersOnLeave = async () => {
    try {
      const response = await axios.get(`${API}/admin/users-on-leave`);
      setUsersOnLeave(response.data);
    } catch (err) {
      console.error('Error fetching users on leave:', err);
    }
  };

  // Fetch employees
  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/admin/employees`);
      setEmployees(response.data);
    } catch (err) {
      console.error('Error fetching employees:', err);
    }
  };

  // Fetch organization tree
  const fetchOrganizationTree = async () => {
    try {
      const response = await axios.get(`${API}/admin/organization-tree`);
      setOrganizationTree(response.data);
    } catch (err) {
      console.error('Error fetching organization tree:', err);
    }
  };

  // Fetch departments
  const fetchDepartments = async () => {
    try {
      const response = await axios.get(`${API}/admin/departments`);
      setDepartments(response.data);
    } catch (err) {
      console.error('Error fetching departments:', err);
    }
  };

  // Fetch managers
  const fetchManagers = async () => {
    try {
      const response = await axios.get(`${API}/admin/managers`);
      setManagers(response.data);
    } catch (err) {
      console.error('Error fetching managers:', err);
    }
  };

  // Fetch projects
  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/admin/projects`);
      setProjects(response.data);
    } catch (err) {
      console.error('Error fetching projects:', err);
    }
  };

  // Fetch organization settings
  const fetchOrganizationSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/organization-settings`);
      setOrganizationSettings(response.data);
      setOrgSettingsData({
        company_name: response.data.company_name || '',
        establishment_date: response.data.establishment_date || '',
        company_email: response.data.company_email || '',
        founder_name: response.data.founder_name || '',
        founder_email: response.data.founder_email || '',
        address: response.data.address || '',
        phone: response.data.phone || '',
        website: response.data.website || ''
      });
    } catch (err) {
      console.error('Error fetching organization settings:', err);
    }
  };

  // Update organization settings
  const updateOrganizationSettings = async () => {
    if (!orgSettingsData.company_name) {
      alert('Company name is required');
      return;
    }
    
    try {
      await axios.put(`${API}/admin/organization-settings`, orgSettingsData);
      alert('Organization settings updated successfully!');
      fetchOrganizationSettings(); // Refresh the data
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update organization settings');
    }
  };

  // Handle logo file selection
  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please select a PNG or JPEG image file');
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      alert('File size too large. Please select an image under 5MB');
      return;
    }

    setLogoUploading(true);

    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const logoBase64 = e.target.result;
          setLogoPreview(logoBase64);

          // Upload to backend
          const response = await axios.post(`${API}/admin/upload-logo-base64`, {
            logo_base64: logoBase64
          });

          alert('Logo uploaded successfully!');
          
          // Refresh organization settings to get the new logo
          await fetchOrganizationSettings();
          
        } catch (err) {
          alert(err.response?.data?.detail || 'Failed to upload logo');
          setLogoPreview(null);
        } finally {
          setLogoUploading(false);
        }
      };
      
      reader.onerror = () => {
        alert('Error reading file');
        setLogoUploading(false);
      };
      
      reader.readAsDataURL(file);
    } catch (err) {
      alert('Error processing file');
      setLogoUploading(false);
    }
  };

  // Remove logo
  const removeLogo = async () => {
    if (!window.confirm('Are you sure you want to remove the current logo?')) {
      return;
    }

    setLogoUploading(true);
    try {
      await axios.delete(`${API}/admin/remove-logo`);
      alert('Logo removed successfully!');
      setLogoPreview(null);
      
      // Refresh organization settings
      await fetchOrganizationSettings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to remove logo');
    } finally {
      setLogoUploading(false);
    }
  };

  // Fetch user sessions
  const fetchUserSessions = async (userId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/user/${userId}/sessions`);
      setUserSessions(response.data);
      setSelectedUser(users.find(u => u.id === userId));
    } catch (err) {
      console.error('Error fetching user sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchAdminStats();
    fetchAdminUsers();
    fetchHolidaysData();
    fetchManagerAssignments();
    fetchUsersOnLeave();
    fetchEmployees();
    fetchOrganizationTree();
    fetchDepartments();
    fetchManagers();
    fetchProjects();
    fetchOrganizationSettings();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    delete axios.defaults.headers.common['Authorization'];
    onLogout();
  };

  // Create new admin
  const createNewAdmin = async () => {
    if (!newAdminData.name || !newAdminData.email || !newAdminData.password) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.post(`${API}/admin/create-admin`, newAdminData);
      setShowCreateAdminModal(false);
      setNewAdminData({ name: '', email: '', password: '' });
      await fetchAdminUsers();
      alert('Admin created successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create admin');
    }
  };

  // Add new holiday
  const addNewHoliday = async () => {
    if (!newHolidayData.date || !newHolidayData.name || !newHolidayData.type) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.post(`${API}/admin/add-holiday`, newHolidayData);
      setShowHolidayModal(false);
      setNewHolidayData({ date: '', name: '', type: 'Mandatory' });
      await fetchHolidaysData();
      alert('Holiday added successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add holiday');
    }
  };

  // Delete holiday
  const deleteHoliday = async (holidayId) => {
    if (!confirm('Are you sure you want to delete this holiday?')) return;

    try {
      await axios.delete(`${API}/admin/holiday/${holidayId}`);
      await fetchHolidaysData();
      alert('Holiday deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete holiday');
    }
  };

  // Update admin
  const updateAdmin = async () => {
    if (!editingAdmin.name || !editingAdmin.email) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.put(`${API}/admin/update-admin/${editingAdmin.id}`, {
        name: editingAdmin.name,
        email: editingAdmin.email
      });
      setShowEditAdminModal(false);
      setEditingAdmin(null);
      await fetchAdminUsers();
      alert('Admin updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update admin');
    }
  };

  // Delete admin
  const deleteAdmin = async (adminId) => {
    if (!confirm('Are you sure you want to delete this admin? This action cannot be undone.')) return;

    try {
      await axios.delete(`${API}/admin/delete-admin/${adminId}`);
      await fetchAdminUsers();
      alert('Admin deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete admin');
    }
  };

  const openEditAdmin = (admin) => {
    setEditingAdmin({ ...admin });
    setShowEditAdminModal(true);
  };

  // Update holiday
  const updateHoliday = async () => {
    if (!editingHoliday.name || !editingHoliday.date || !editingHoliday.type) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.put(`${API}/admin/update-holiday/${editingHoliday.id}`, {
        name: editingHoliday.name,
        date: editingHoliday.date,
        type: editingHoliday.type
      });
      setShowEditHolidayModal(false);
      setEditingHoliday(null);
      await fetchHolidaysData();
      alert('Holiday updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update holiday');
    }
  };

  // Delete holiday (updated for single holiday)
  const deleteHolidayById = async (holidayId) => {
    if (!confirm('Are you sure you want to delete this holiday?')) return;

    try {
      await axios.delete(`${API}/admin/holiday/${holidayId}`);
      await fetchHolidaysData();
      alert('Holiday deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete holiday');
    }
  };

  const openEditHoliday = (holiday) => {
    setEditingHoliday({ ...holiday });
    setShowEditHolidayModal(true);
  };

  // Create new employee
  const createNewEmployee = async () => {
    if (!newEmployeeData.name || !newEmployeeData.email || !newEmployeeData.phone || !newEmployeeData.password) {
      alert('Please fill in all required fields (Name, Email, Phone, Password)');
      return;
    }

    try {
      await axios.post(`${API}/admin/create-employee`, newEmployeeData);
      setShowCreateEmployeeModal(false);
      setNewEmployeeData({
        name: '', email: '', phone: '', password: '',
        dob: '', blood_group: '', emergency_contact: '', address: '',
        aadhar_card: '', designation: '', department: '', joining_date: '', release_date: ''
      });
      await fetchEmployees();
      alert('Employee created successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create employee');
    }
  };

  // Update employee
  const updateEmployee = async () => {
    if (!editingEmployee.name || !editingEmployee.email || !editingEmployee.phone) {
      alert('Please fill in all required fields (Name, Email, Phone)');
      return;
    }

    try {
      await axios.put(`${API}/admin/update-employee/${editingEmployee.id}`, {
        name: editingEmployee.name,
        email: editingEmployee.email,
        phone: editingEmployee.phone,
        dob: editingEmployee.dob,
        blood_group: editingEmployee.blood_group,
        emergency_contact: editingEmployee.emergency_contact,
        address: editingEmployee.address,
        aadhar_card: editingEmployee.aadhar_card,
        designation: editingEmployee.designation,
        department: editingEmployee.department,
        joining_date: editingEmployee.joining_date,
        release_date: editingEmployee.release_date
      });
      setShowEditEmployeeModal(false);
      setEditingEmployee(null);
      await fetchEmployees();
      alert('Employee updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update employee');
    }
  };

  // Delete employee
  const deleteEmployee = async (empId) => {
    if (!confirm('Are you sure you want to delete this employee? This will also delete all their sessions and leave records.')) return;

    try {
      await axios.delete(`${API}/admin/delete-employee/${empId}`);
      await fetchEmployees();
      alert('Employee deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete employee');
    }
  };

  const openEditEmployee = (employee) => {
    setEditingEmployee({ ...employee });
    setShowEditEmployeeModal(true);
  };

  // Create department
  const createDepartment = async () => {
    if (!newDepartmentData.name) {
      alert('Please enter department name');
      return;
    }

    try {
      await axios.post(`${API}/admin/create-department`, newDepartmentData);
      setShowCreateDepartmentModal(false);
      setNewDepartmentData({ name: '', description: '' });
      await Promise.all([fetchDepartments(), fetchOrganizationTree()]);
      alert('Department created successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create department');
    }
  };

  // Create manager
  const createManager = async () => {
    if (!newManagerData.employee_id || !newManagerData.department_id) {
      alert('Please select both employee and department');
      return;
    }

    try {
      await axios.post(`${API}/admin/create-manager`, newManagerData);
      setShowCreateManagerModal(false);
      setNewManagerData({ employee_id: '', department_id: '' });
      await Promise.all([fetchManagers(), fetchOrganizationTree()]);
      alert('Manager assigned successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to assign manager');
    }
  };

  // Create project
  const createProject = async () => {
    if (!newProjectData.name || !newProjectData.department_id || !newProjectData.manager_id) {
      alert('Please fill in all required fields');
      return;
    }

    const projectData = {
      ...newProjectData,
      employee_ids: selectedEmployeesForProject
    };

    try {
      await axios.post(`${API}/admin/create-project`, projectData);
      setShowCreateProjectModal(false);
      setNewProjectData({
        name: '', description: '', department_id: '', manager_id: '', employee_ids: [],
        start_date: '', end_date: '', status: 'Active'
      });
      setSelectedEmployeesForProject([]);
      await Promise.all([fetchProjects(), fetchOrganizationTree()]);
      alert('Project created successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create project');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Admin Header */}
      <div className="bg-slate-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            {orgBranding.company_logo && (
              <img 
                src={orgBranding.company_logo} 
                alt={orgBranding.company_name} 
                className="h-10 w-10 object-contain"
              />
            )}
            <div>
              <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
              <p className="text-slate-300">{orgBranding.company_name} Administration</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-slate-300">Logged in as</div>
              <div className="text-white font-medium">{admin.name}</div>
            </div>
            <Button 
              onClick={handleLogout} 
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              data-testid="admin-logout-btn"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="overview" className="flex items-center gap-2" data-testid="admin-overview-tab">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center gap-2" data-testid="admin-users-tab">
              <UserCheck className="h-4 w-4" />
              Users
            </TabsTrigger>
            <TabsTrigger value="sessions" className="flex items-center gap-2" data-testid="admin-sessions-tab">
              <Clock className="h-4 w-4" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2" data-testid="admin-settings-tab">
              <UserCheck className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {adminStats && (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-blue-100">Total Users</p>
                          <p className="text-3xl font-bold">{adminStats.total_users}</p>
                        </div>
                        <UserCheck className="h-8 w-8 text-blue-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-green-100">Active Today</p>
                          <p className="text-3xl font-bold">{adminStats.active_today}</p>
                        </div>
                        <Clock className="h-8 w-8 text-green-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-purple-100">Users on Leave</p>
                          <p className="text-3xl font-bold">
                            {usersOnLeave ? usersOnLeave.users_on_leave_today : 0}
                          </p>
                        </div>
                        <UserCheck className="h-8 w-8 text-purple-200" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-orange-100">Leaves This Month</p>
                          <p className="text-3xl font-bold">{adminStats.leaves_this_month}</p>
                        </div>
                        <Coffee className="h-8 w-8 text-orange-200" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* New Management Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Admin Users Card */}
                  <Card 
                    className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
                    onClick={() => setShowAdminUsersPage(true)}
                    data-testid="admin-users-card"
                  >
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-lg font-semibold">Admin Users</CardTitle>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowCreateAdminModal(true);
                        }}
                        size="sm"
                        className="bg-slate-600 hover:bg-slate-700"
                        data-testid="create-admin-btn"
                      >
                        Add Admin
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-slate-700">{adminUsers.length}</span>
                          <UserCheck className="h-6 w-6 text-slate-500" />
                        </div>
                        <div className="space-y-1 max-h-24 overflow-y-auto">
                          {adminUsers.slice(0, 3).map(admin => (
                            <div key={admin.id} className="text-xs text-gray-600 flex items-center gap-1">
                              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                              {admin.name}
                            </div>
                          ))}
                          {adminUsers.length > 3 && (
                            <div className="text-xs text-gray-500">+{adminUsers.length - 3} more</div>
                          )}
                        </div>
                        <div className="text-xs text-blue-600 font-medium pt-1">
                          Click to manage →
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Employees Card */}
                  <Card 
                    className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
                    onClick={() => setShowEmployeePage(true)}
                    data-testid="employees-card"
                  >
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg font-semibold">Employees</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-blue-700">{users.length}</span>
                          <UserCheck className="h-6 w-6 text-blue-500" />
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-green-50 p-1 rounded text-center">
                            <div className="font-medium text-green-700">{users.filter(u => u.total_sessions > 0).length}</div>
                            <div className="text-green-600">Active</div>
                          </div>
                          <div className="bg-gray-50 p-1 rounded text-center">
                            <div className="font-medium text-gray-700">{users.filter(u => u.total_sessions === 0).length}</div>
                            <div className="text-gray-600">New</div>
                          </div>
                        </div>
                        <div className="text-xs text-blue-600 font-medium pt-1">
                          Click to manage →
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Holiday List Card */}
                  <Card 
                    className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
                    onClick={() => setShowHolidayListPage(true)}
                    data-testid="holiday-list-card"
                  >
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-lg font-semibold">Holiday List</CardTitle>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowHolidayModal(true);
                        }}
                        size="sm"
                        className="bg-yellow-600 hover:bg-yellow-700"
                        data-testid="add-holiday-btn"
                      >
                        Add Holiday
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-yellow-700">
                            {holidaysData ? holidaysData.holidays_this_year : 0}
                          </span>
                          <Calendar className="h-6 w-6 text-yellow-500" />
                        </div>
                        <div className="space-y-1 max-h-24 overflow-y-auto">
                          {holidaysData && holidaysData.holidays.slice(0, 3).map(holiday => (
                            <div key={holiday.id} className="text-xs text-gray-600 flex items-center justify-between">
                              <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${holiday.type === 'Mandatory' ? 'bg-red-400' : 'bg-yellow-400'}`}></div>
                                {holiday.name}
                              </div>
                              <span className="text-gray-500">{new Date(holiday.date).toLocaleDateString()}</span>
                            </div>
                          ))}
                          {holidaysData && holidaysData.holidays.length > 3 && (
                            <div className="text-xs text-gray-500">+{holidaysData.holidays.length - 3} more</div>
                          )}
                        </div>
                        <div className="text-xs text-blue-600 font-medium pt-1">
                          Click to manage →
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Assign Manager Card */}
                  <Card 
                    className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
                    onClick={() => setShowManagerAssignmentPage(true)}
                    data-testid="manager-assignments-card"
                  >
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg font-semibold">Manager Assignments</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-indigo-700">
                            {organizationTree ? organizationTree.summary.managers : 0}
                          </span>
                          <UserCheck className="h-6 w-6 text-indigo-500" />
                        </div>
                        {organizationTree && (
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="bg-indigo-50 p-1 rounded text-center">
                              <div className="font-medium text-indigo-700">{organizationTree.summary.departments}</div>
                              <div className="text-indigo-600">Departments</div>
                            </div>
                            <div className="bg-green-50 p-1 rounded text-center">
                              <div className="font-medium text-green-700">{organizationTree.summary.projects}</div>
                              <div className="text-green-600">Projects</div>
                            </div>
                          </div>
                        )}
                        <div className="text-xs text-blue-600 font-medium pt-1">
                          Click to manage →
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Additional Admin Cards - Second Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Employee Leave Requests Card */}
                  <EmployeeLeaveRequestsCard />

                  {/* Organization Settings Card */}
                  <Card 
                    className="hover:shadow-lg transition-shadow cursor-pointer hover:bg-gray-50"
                    onClick={() => setShowOrgSettingsPage(true)}
                    data-testid="org-settings-card"
                  >
                    <CardHeader>
                      <CardTitle className="text-lg font-semibold">Organization Settings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-2xl font-bold text-slate-700">⚙️</span>
                          <Clock className="h-6 w-6 text-slate-500" />
                        </div>
                        <div className="text-sm text-gray-600">
                          {organizationSettings ? organizationSettings.company_name : 'Configure company details'}
                        </div>
                        <div className="text-xs text-blue-600 font-medium pt-1">
                          Click to configure →
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Leave Settings Card */}
                  <LeaveSettingsCard />
                </div>

                {/* Recent Sessions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <History className="h-5 w-5" />
                      Recent Sessions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {adminStats.recent_sessions.length > 0 ? (
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Employee</TableHead>
                              <TableHead>Date</TableHead>
                              <TableHead>Login</TableHead>
                              <TableHead>Logout</TableHead>
                              <TableHead>Effective Hours</TableHead>
                              <TableHead>Type</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {adminStats.recent_sessions.map((session, index) => (
                              <TableRow key={index}>
                                <TableCell className="font-medium">
                                  <div>
                                    <div>{session.user_name}</div>
                                    <div className="text-xs text-gray-500">{session.user_email}</div>
                                  </div>
                                </TableCell>
                                <TableCell>{new Date(session.date).toLocaleDateString('en-IN')}</TableCell>
                                <TableCell>{session.login_time}</TableCell>
                                <TableCell>{session.logout_time}</TableCell>
                                <TableCell className="font-mono">{session.effective_hours}h</TableCell>
                                <TableCell>
                                  <Badge variant={session.day_type === 'Half Day' ? 'secondary' : 'default'}>
                                    {session.day_type}
                                  </Badge>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No recent sessions found</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserCheck className="h-5 w-5" />
                  All Users
                </CardTitle>
                <p className="text-gray-600">Manage and view all employee accounts</p>
              </CardHeader>
              <CardContent>
                {users.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Employee</TableHead>
                          <TableHead>Contact</TableHead>
                          <TableHead>Joined</TableHead>
                          <TableHead>Sessions</TableHead>
                          <TableHead>Leaves</TableHead>
                          <TableHead>Last Login</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {users.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell className="font-medium">
                              <div>
                                <div>{user.name}</div>
                                <Badge variant="outline" className="border-green-200 text-green-700">
                                  {user.status}
                                </Badge>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-sm">
                                <div>{user.email}</div>
                                <div className="text-gray-500">{user.phone}</div>
                              </div>
                            </TableCell>
                            <TableCell>{new Date(user.created_at).toLocaleDateString('en-IN')}</TableCell>
                            <TableCell className="text-center">{user.total_sessions}</TableCell>
                            <TableCell className="text-center">{user.total_leaves}</TableCell>
                            <TableCell>
                              {user.last_login 
                                ? new Date(user.last_login).toLocaleDateString('en-IN')
                                : 'Never'
                              }
                            </TableCell>
                            <TableCell>
                              <Button
                                onClick={() => fetchUserSessions(user.id)}
                                variant="outline"
                                size="sm"
                                data-testid={`view-user-${user.id}`}
                              >
                                View Sessions
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <UserCheck className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No users found</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sessions Tab */}
          <TabsContent value="sessions" className="space-y-6">
            {selectedUser ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    {selectedUser.name}'s Sessions
                  </CardTitle>
                  <p className="text-gray-600">{selectedUser.email}</p>
                  <Button
                    onClick={() => {setSelectedUser(null); setUserSessions([]);}}
                    variant="outline"
                    size="sm"
                    className="w-fit"
                  >
                    ← Back to Users
                  </Button>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="mt-2 text-gray-600">Loading sessions...</p>
                    </div>
                  ) : userSessions.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>Login</TableHead>
                            <TableHead>Logout</TableHead>
                            <TableHead>Effective Hours</TableHead>
                            <TableHead>Breaks</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Task</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {userSessions.map((session) => (
                            <TableRow key={session.id}>
                              <TableCell>{new Date(session.date).toLocaleDateString('en-IN')}</TableCell>
                              <TableCell>{session.login_time}</TableCell>
                              <TableCell>{session.logout_time}</TableCell>
                              <TableCell className="font-mono">{session.effective_hours}h</TableCell>
                              <TableCell className="text-center">{session.break_count}</TableCell>
                              <TableCell>
                                <Badge variant={session.day_type === 'Half Day' ? 'secondary' : 'default'}>
                                  {session.day_type}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="text-sm">
                                  <div className="font-medium">{session.task_id || 'N/A'}</div>
                                  <div className="text-gray-500 truncate max-w-xs">
                                    {session.work_description || 'No description'}
                                  </div>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No sessions found for this user</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <UserCheck className="h-16 w-16 mx-auto mb-4 opacity-50 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-600 mb-2">Select a User</h3>
                  <p className="text-gray-500">Go to the Users tab and click "View Sessions" to see detailed session history</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Organization Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <UserCheck className="h-6 w-6" />
                  Organization Settings
                </CardTitle>
                <p className="text-gray-600">Manage your organization details and branding</p>
              </CardHeader>
              <CardContent>
                {organizationSettings && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Company Information */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-gray-700">Company Information</h3>
                      <div>
                        <Label htmlFor="org-company-name">Company Name *</Label>
                        <Input
                          id="org-company-name"
                          value={orgSettingsData.company_name}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, company_name: e.target.value})}
                          placeholder="Enter company name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-establishment-date">Establishment Date</Label>
                        <Input
                          id="org-establishment-date"
                          type="date"
                          value={orgSettingsData.establishment_date}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, establishment_date: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-company-email">Company Email</Label>
                        <Input
                          id="org-company-email"
                          type="email"
                          value={orgSettingsData.company_email}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, company_email: e.target.value})}
                          placeholder="info@company.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-phone">Phone Number</Label>
                        <Input
                          id="org-phone"
                          value={orgSettingsData.phone}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, phone: e.target.value})}
                          placeholder="+1 (555) 123-4567"
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-website">Website</Label>
                        <Input
                          id="org-website"
                          value={orgSettingsData.website}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, website: e.target.value})}
                          placeholder="https://www.company.com"
                        />
                      </div>
                    </div>

                    {/* Founder & Contact Information */}
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-gray-700">Founder & Contact</h3>
                      <div>
                        <Label htmlFor="org-founder-name">Founder Name</Label>
                        <Input
                          id="org-founder-name"
                          value={orgSettingsData.founder_name}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, founder_name: e.target.value})}
                          placeholder="John Doe"
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-founder-email">Founder Email</Label>
                        <Input
                          id="org-founder-email"
                          type="email"
                          value={orgSettingsData.founder_email}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, founder_email: e.target.value})}
                          placeholder="founder@company.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="org-address">Company Address</Label>
                        <Textarea
                          id="org-address"
                          value={orgSettingsData.address}
                          onChange={(e) => setOrgSettingsData({...orgSettingsData, address: e.target.value})}
                          placeholder="123 Business Street, City, State 12345"
                          rows={3}
                        />
                      </div>
                      
                      {/* Company Logo Section */}
                      <div>
                        <Label>Company Logo</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                          {logoPreview || organizationSettings.company_logo ? (
                            <div className="space-y-2">
                              <img 
                                src={logoPreview || organizationSettings.company_logo} 
                                alt="Company Logo" 
                                className="mx-auto h-20 w-20 object-contain rounded-lg"
                              />
                              <p className="text-sm text-gray-600">
                                {logoPreview ? 'Preview' : 'Current Logo'}
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-2">
                              <div className="mx-auto h-20 w-20 bg-gray-100 rounded-lg flex items-center justify-center">
                                <UserCheck className="h-10 w-10 text-gray-400" />
                              </div>
                              <p className="text-sm text-gray-600">No logo uploaded</p>
                            </div>
                          )}
                          
                          <div className="flex flex-col space-y-2 mt-3">
                            {/* Upload Button */}
                            <div className="relative">
                              <input
                                type="file"
                                accept="image/png,image/jpeg,image/jpg"
                                onChange={handleLogoUpload}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                id="logo-upload"
                                disabled={logoUploading}
                              />
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="w-full"
                                disabled={logoUploading}
                                asChild
                              >
                                <label htmlFor="logo-upload" className="cursor-pointer">
                                  {logoUploading ? 'Uploading...' : 'Upload Logo'}
                                </label>
                              </Button>
                            </div>
                            
                            {/* Remove Button */}
                            {(organizationSettings.company_logo || logoPreview) && (
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={removeLogo}
                                disabled={logoUploading}
                              >
                                Remove Logo
                              </Button>
                            )}
                            
                            <p className="text-xs text-gray-500 mt-2">
                              PNG or JPEG, max 5MB
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex justify-end space-x-2 mt-6 pt-6 border-t">
                  <Button 
                    onClick={updateOrganizationSettings}
                    className="bg-blue-600 hover:bg-blue-700"
                    data-testid="update-org-settings"
                  >
                    Save Changes
                  </Button>
                  <Button 
                    onClick={() => setOrgSettingsData({
                      company_name: organizationSettings?.company_name || '',
                      establishment_date: organizationSettings?.establishment_date || '',
                      company_email: organizationSettings?.company_email || '',
                      founder_name: organizationSettings?.founder_name || '',
                      founder_email: organizationSettings?.founder_email || '',
                      address: organizationSettings?.address || '',
                      phone: organizationSettings?.phone || '',
                      website: organizationSettings?.website || ''
                    })}
                    variant="outline"
                  >
                    Reset
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Admin Users Management Page */}
      {showAdminUsersPage && (
        <div className="fixed inset-0 bg-slate-800 z-50 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Admin Users Management</h2>
                <p className="text-slate-300">Manage all admin users and their permissions</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowCreateAdminModal(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="add-admin-page-btn"
                >
                  Add New Admin
                </Button>
                <Button
                  onClick={() => setShowAdminUsersPage(false)}
                  variant="outline"
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  data-testid="close-admin-users-page"
                >
                  ← Back to Dashboard
                </Button>
              </div>
            </div>

            {/* Admin Users Table */}
            <Card className="bg-slate-700 border-slate-600">
              <CardHeader>
                <CardTitle className="text-white">All Admin Users ({adminUsers.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {adminUsers.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-600">
                          <TableHead className="text-slate-300">Name</TableHead>
                          <TableHead className="text-slate-300">Email</TableHead>
                          <TableHead className="text-slate-300">Created Date</TableHead>
                          <TableHead className="text-slate-300">Status</TableHead>
                          <TableHead className="text-slate-300">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {adminUsers.map((admin) => (
                          <TableRow key={admin.id} className="border-slate-600 hover:bg-slate-600">
                            <TableCell className="font-medium text-white">
                              <div className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                                  {admin.name.charAt(0).toUpperCase()}
                                </div>
                                <span>{admin.name}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-slate-300">{admin.email}</TableCell>
                            <TableCell className="text-slate-300">
                              {new Date(admin.created_at).toLocaleDateString('en-IN')}
                            </TableCell>
                            <TableCell>
                              <Badge className="bg-green-600 text-green-100">
                                {admin.status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-2">
                                <Button
                                  onClick={() => openEditAdmin(admin)}
                                  size="sm"
                                  variant="outline"
                                  className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                                  data-testid={`edit-admin-${admin.id}`}
                                >
                                  Edit
                                </Button>
                                {admin.id !== admin.id && (
                                  <Button
                                    onClick={() => deleteAdmin(admin.id)}
                                    size="sm"
                                    variant="outline"
                                    className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                                    data-testid={`delete-admin-${admin.id}`}
                                  >
                                    Delete
                                  </Button>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <UserCheck className="h-16 w-16 mx-auto mb-4 opacity-50 text-slate-400" />
                    <h3 className="text-lg font-medium text-slate-300 mb-2">No Admin Users</h3>
                    <p className="text-slate-400">Create your first admin user to get started</p>
                    <Button
                      onClick={() => setShowCreateAdminModal(true)}
                      className="mt-4 bg-blue-600 hover:bg-blue-700"
                    >
                      Add First Admin
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Holiday List Management Page */}
      {showHolidayListPage && (
        <div className="fixed inset-0 bg-slate-800 z-50 overflow-y-auto">
          <div className="max-w-6xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Holiday List Management</h2>
                <p className="text-slate-300">Manage all company holidays and their types</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowHolidayModal(true)}
                  className="bg-yellow-600 hover:bg-yellow-700"
                  data-testid="add-holiday-page-btn"
                >
                  Add New Holiday
                </Button>
                <Button
                  onClick={() => setShowHolidayListPage(false)}
                  variant="outline"
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  data-testid="close-holiday-list-page"
                >
                  ← Back to Dashboard
                </Button>
              </div>
            </div>

            {/* Holiday List Table */}
            <Card className="bg-slate-700 border-slate-600">
              <CardHeader>
                <CardTitle className="text-white">
                  All Holidays ({holidaysData ? holidaysData.total_holidays : 0})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {holidaysData && holidaysData.holidays.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-600">
                          <TableHead className="text-slate-300">Date</TableHead>
                          <TableHead className="text-slate-300">Description</TableHead>
                          <TableHead className="text-slate-300">Type</TableHead>
                          <TableHead className="text-slate-300">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {holidaysData.holidays.map((holiday) => (
                          <TableRow key={holiday.id} className="border-slate-600 hover:bg-slate-600">
                            <TableCell className="font-medium text-white">
                              <div className="flex items-center space-x-2">
                                <Calendar className="h-4 w-4 text-yellow-400" />
                                <span>{new Date(holiday.date).toLocaleDateString('en-IN', {
                                  weekday: 'short',
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric'
                                })}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-slate-300">
                              <div>
                                <div className="font-medium">{holiday.name}</div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge 
                                className={
                                  holiday.type === 'Mandatory' 
                                    ? 'bg-red-600 text-red-100' 
                                    : 'bg-blue-600 text-blue-100'
                                }
                              >
                                {holiday.type}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-2">
                                <Button
                                  onClick={() => openEditHoliday(holiday)}
                                  size="sm"
                                  variant="outline"
                                  className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                                  data-testid={`edit-holiday-${holiday.id}`}
                                >
                                  Edit
                                </Button>
                                <Button
                                  onClick={() => deleteHolidayById(holiday.id)}
                                  size="sm"
                                  variant="outline"
                                  className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                                  data-testid={`delete-holiday-${holiday.id}`}
                                >
                                  Delete
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Calendar className="h-16 w-16 mx-auto mb-4 opacity-50 text-slate-400" />
                    <h3 className="text-lg font-medium text-slate-300 mb-2">No Holidays</h3>
                    <p className="text-slate-400">Add your first company holiday to get started</p>
                    <Button
                      onClick={() => setShowHolidayModal(true)}
                      className="mt-4 bg-yellow-600 hover:bg-yellow-700"
                    >
                      Add First Holiday
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Employee Management Page */}
      {showEmployeePage && (
        <div className="fixed inset-0 bg-slate-800 z-50 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Employee Management</h2>
                <p className="text-slate-300">Manage all employee information and details</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowCreateEmployeeModal(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="add-employee-page-btn"
                >
                  Add New Employee
                </Button>
                <Button
                  onClick={() => setShowEmployeePage(false)}
                  variant="outline"
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  data-testid="close-employee-page"
                >
                  ← Back to Dashboard
                </Button>
              </div>
            </div>

            {/* Employee Table */}
            <Card className="bg-slate-700 border-slate-600">
              <CardHeader>
                <CardTitle className="text-white">
                  All Employees ({employees.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {employees.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-600">
                          <TableHead className="text-slate-300">Name</TableHead>
                          <TableHead className="text-slate-300">DOB</TableHead>
                          <TableHead className="text-slate-300">Phone No</TableHead>
                          <TableHead className="text-slate-300">Blood Group</TableHead>
                          <TableHead className="text-slate-300">Email</TableHead>
                          <TableHead className="text-slate-300">Emergency Contact</TableHead>
                          <TableHead className="text-slate-300">Address</TableHead>
                          <TableHead className="text-slate-300">Aadhar Card</TableHead>
                          <TableHead className="text-slate-300">Designation</TableHead>
                          <TableHead className="text-slate-300">Department</TableHead>
                          <TableHead className="text-slate-300">Joining Date</TableHead>
                          <TableHead className="text-slate-300">Release Date</TableHead>
                          <TableHead className="text-slate-300">Status</TableHead>
                          <TableHead className="text-slate-300">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {employees.map((employee) => (
                          <TableRow key={employee.id} className="border-slate-600 hover:bg-slate-600">
                            <TableCell className="font-medium text-white">
                              <div className="flex items-center space-x-2">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                                  {employee.name.charAt(0).toUpperCase()}
                                </div>
                                <span>{employee.name}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-slate-300">
                              {employee.dob ? new Date(employee.dob).toLocaleDateString('en-IN') : 'N/A'}
                            </TableCell>
                            <TableCell className="text-slate-300">{employee.phone || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">{employee.blood_group || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">{employee.email}</TableCell>
                            <TableCell className="text-slate-300">{employee.emergency_contact || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300 max-w-32 truncate">{employee.address || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">{employee.aadhar_card || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">{employee.designation || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">{employee.department || 'N/A'}</TableCell>
                            <TableCell className="text-slate-300">
                              {employee.joining_date ? new Date(employee.joining_date).toLocaleDateString('en-IN') : 'N/A'}
                            </TableCell>
                            <TableCell className="text-slate-300">
                              {employee.release_date ? new Date(employee.release_date).toLocaleDateString('en-IN') : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Badge 
                                className={
                                  employee.status === 'Active' 
                                    ? 'bg-green-600 text-green-100' 
                                    : 'bg-red-600 text-red-100'
                                }
                              >
                                {employee.status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex space-x-2">
                                <Button
                                  onClick={() => openEditEmployee(employee)}
                                  size="sm"
                                  variant="outline"
                                  className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                                  data-testid={`edit-employee-${employee.id}`}
                                >
                                  Edit
                                </Button>
                                <Button
                                  onClick={() => deleteEmployee(employee.id)}
                                  size="sm"
                                  variant="outline"
                                  className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white"
                                  data-testid={`delete-employee-${employee.id}`}
                                >
                                  Delete
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <UserCheck className="h-16 w-16 mx-auto mb-4 opacity-50 text-slate-400" />
                    <h3 className="text-lg font-medium text-slate-300 mb-2">No Employees</h3>
                    <p className="text-slate-400">Add your first employee to get started</p>
                    <Button
                      onClick={() => setShowCreateEmployeeModal(true)}
                      className="mt-4 bg-blue-600 hover:bg-blue-700"
                    >
                      Add First Employee
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Manager Assignment Page */}
      {showManagerAssignmentPage && (
        <div className="fixed inset-0 bg-slate-800 z-50 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Manager Assignments & Organization Tree</h2>
                <p className="text-slate-300">Manage departments, assign managers, create projects, and view organizational structure</p>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={() => setShowCreateDepartmentModal(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="create-department-btn"
                >
                  Add Department
                </Button>
                <Button
                  onClick={() => setShowCreateManagerModal(true)}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="create-manager-btn"
                >
                  Assign Manager
                </Button>
                <Button
                  onClick={() => setShowCreateProjectModal(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                  data-testid="create-project-btn"
                >
                  Create Project
                </Button>
                <Button
                  onClick={() => setShowManagerAssignmentPage(false)}
                  variant="outline"
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  data-testid="close-manager-page"
                >
                  ← Back to Dashboard
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Tree View */}
              <div className="lg:col-span-2">
                <Card className="bg-slate-700 border-slate-600">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded"></div>
                      Organization Tree Map
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {organizationTree && organizationTree.tree.length > 0 ? (
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {organizationTree.tree.map((department) => (
                          <TreeNode key={department.id} node={department} />
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="w-16 h-16 bg-slate-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                          <UserCheck className="h-8 w-8 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-300 mb-2">No Organization Structure</h3>
                        <p className="text-slate-400">Create departments and assign managers to build your organization tree</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Summary Cards */}
              <div className="space-y-4">
                {/* Summary Stats */}
                {organizationTree && (
                  <Card className="bg-slate-700 border-slate-600">
                    <CardHeader>
                      <CardTitle className="text-white">Organization Summary</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-300">Departments</span>
                        <Badge className="bg-blue-600 text-blue-100">{organizationTree.summary.departments}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-300">Managers</span>
                        <Badge className="bg-green-600 text-green-100">{organizationTree.summary.managers}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-300">Projects</span>
                        <Badge className="bg-purple-600 text-purple-100">{organizationTree.summary.projects}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-300">Employees</span>
                        <Badge className="bg-orange-600 text-orange-100">{organizationTree.summary.employees}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Quick Actions */}
                <Card className="bg-slate-700 border-slate-600">
                  <CardHeader>
                    <CardTitle className="text-white">Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button
                      onClick={() => setShowCreateDepartmentModal(true)}
                      variant="outline"
                      className="w-full border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white"
                    >
                      Add Department
                    </Button>
                    <Button
                      onClick={() => setShowCreateManagerModal(true)}
                      variant="outline"
                      className="w-full border-green-500 text-green-400 hover:bg-green-500 hover:text-white"
                    >
                      Assign Manager
                    </Button>
                    <Button
                      onClick={() => setShowCreateProjectModal(true)}
                      variant="outline"
                      className="w-full border-purple-500 text-purple-400 hover:bg-purple-500 hover:text-white"
                    >
                      Create Project
                    </Button>
                  </CardContent>
                </Card>

                {/* Legend */}
                <Card className="bg-slate-700 border-slate-600">
                  <CardHeader>
                    <CardTitle className="text-white">Legend</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-blue-500 rounded"></div>
                      <span className="text-slate-300 text-sm">Department</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-green-500 rounded"></div>
                      <span className="text-slate-300 text-sm">Manager</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-purple-500 rounded"></div>
                      <span className="text-slate-300 text-sm">Project</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-orange-500 rounded"></div>
                      <span className="text-slate-300 text-sm">Employee</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Admin Modal */}
      <Dialog open={showCreateAdminModal} onOpenChange={setShowCreateAdminModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Admin</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="admin-name">Full Name</Label>
              <Input
                id="admin-name"
                value={newAdminData.name}
                onChange={(e) => setNewAdminData({...newAdminData, name: e.target.value})}
                placeholder="Enter admin name"
              />
            </div>
            <div>
              <Label htmlFor="admin-email-create">Email</Label>
              <Input
                id="admin-email-create"
                type="email"
                value={newAdminData.email}
                onChange={(e) => setNewAdminData({...newAdminData, email: e.target.value})}
                placeholder="Enter admin email"
              />
            </div>
            <div>
              <Label htmlFor="admin-password-create">Password</Label>
              <Input
                id="admin-password-create"
                type="password"
                value={newAdminData.password}
                onChange={(e) => setNewAdminData({...newAdminData, password: e.target.value})}
                placeholder="Enter admin password"
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={createNewAdmin} className="flex-1" data-testid="create-admin-submit">
                Create Admin
              </Button>
              <Button onClick={() => setShowCreateAdminModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Holiday Modal */}
      <Dialog open={showHolidayModal} onOpenChange={setShowHolidayModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Holiday</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="holiday-name">Holiday Name</Label>
              <Input
                id="holiday-name"
                value={newHolidayData.name}
                onChange={(e) => setNewHolidayData({...newHolidayData, name: e.target.value})}
                placeholder="e.g., Christmas Day"
              />
            </div>
            <div>
              <Label htmlFor="holiday-date">Date</Label>
              <Input
                id="holiday-date"
                type="date"
                value={newHolidayData.date}
                onChange={(e) => setNewHolidayData({...newHolidayData, date: e.target.value})}
              />
            </div>
            <div>
              <Label htmlFor="holiday-type">Type</Label>
              <Select 
                value={newHolidayData.type} 
                onValueChange={(value) => setNewHolidayData({...newHolidayData, type: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Mandatory">Mandatory</SelectItem>
                  <SelectItem value="Optional">Optional</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex space-x-2">
              <Button onClick={addNewHoliday} className="flex-1" data-testid="add-holiday-submit">
                Add Holiday
              </Button>
              <Button onClick={() => setShowHolidayModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Admin Modal */}
      <Dialog open={showEditAdminModal} onOpenChange={setShowEditAdminModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Admin User</DialogTitle>
          </DialogHeader>
          {editingAdmin && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-admin-name">Full Name</Label>
                <Input
                  id="edit-admin-name"
                  value={editingAdmin.name}
                  onChange={(e) => setEditingAdmin({...editingAdmin, name: e.target.value})}
                  placeholder="Enter admin name"
                />
              </div>
              <div>
                <Label htmlFor="edit-admin-email">Email</Label>
                <Input
                  id="edit-admin-email"
                  type="email"
                  value={editingAdmin.email}
                  onChange={(e) => setEditingAdmin({...editingAdmin, email: e.target.value})}
                  placeholder="Enter admin email"
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={updateAdmin} className="flex-1" data-testid="update-admin-submit">
                  Update Admin
                </Button>
                <Button 
                  onClick={() => {
                    setShowEditAdminModal(false);
                    setEditingAdmin(null);
                  }} 
                  variant="outline" 
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      {/* Edit Holiday Modal */}
      <Dialog open={showEditHolidayModal} onOpenChange={setShowEditHolidayModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Holiday</DialogTitle>
          </DialogHeader>
          {editingHoliday && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-holiday-name">Holiday Name</Label>
                <Input
                  id="edit-holiday-name"
                  value={editingHoliday.name}
                  onChange={(e) => setEditingHoliday({...editingHoliday, name: e.target.value})}
                  placeholder="e.g., Christmas Day"
                />
              </div>
              <div>
                <Label htmlFor="edit-holiday-date">Date</Label>
                <Input
                  id="edit-holiday-date"
                  type="date"
                  value={editingHoliday.date}
                  onChange={(e) => setEditingHoliday({...editingHoliday, date: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit-holiday-type">Type</Label>
                <Select 
                  value={editingHoliday.type} 
                  onValueChange={(value) => setEditingHoliday({...editingHoliday, type: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Mandatory">Mandatory</SelectItem>
                    <SelectItem value="Optional">Optional</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex space-x-2">
                <Button onClick={updateHoliday} className="flex-1" data-testid="update-holiday-submit">
                  Update Holiday
                </Button>
                <Button 
                  onClick={() => {
                    setShowEditHolidayModal(false);
                    setEditingHoliday(null);
                  }} 
                  variant="outline" 
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Employee Modal */}
      <Dialog open={showCreateEmployeeModal} onOpenChange={setShowCreateEmployeeModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Employee</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-700">Basic Information</h3>
              <div>
                <Label htmlFor="emp-name">Full Name *</Label>
                <Input
                  id="emp-name"
                  value={newEmployeeData.name}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, name: e.target.value})}
                  placeholder="Enter full name"
                />
              </div>
              <div>
                <Label htmlFor="emp-email">Email *</Label>
                <Input
                  id="emp-email"
                  type="email"
                  value={newEmployeeData.email}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, email: e.target.value})}
                  placeholder="Enter email address"
                />
              </div>
              <div>
                <Label htmlFor="emp-phone">Phone Number *</Label>
                <Input
                  id="emp-phone"
                  value={newEmployeeData.phone}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, phone: e.target.value})}
                  placeholder="Enter phone number"
                />
              </div>
              <div>
                <Label htmlFor="emp-password">Password *</Label>
                <Input
                  id="emp-password"
                  type="password"
                  value={newEmployeeData.password}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, password: e.target.value})}
                  placeholder="Enter password"
                />
              </div>
              <div>
                <Label htmlFor="emp-dob">Date of Birth</Label>
                <Input
                  id="emp-dob"
                  type="date"
                  value={newEmployeeData.dob}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, dob: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="emp-blood-group">Blood Group</Label>
                <Input
                  id="emp-blood-group"
                  value={newEmployeeData.blood_group}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, blood_group: e.target.value})}
                  placeholder="e.g., A+, B-, O+"
                />
              </div>
              <div>
                <Label htmlFor="emp-emergency">Emergency Contact</Label>
                <Input
                  id="emp-emergency"
                  value={newEmployeeData.emergency_contact}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, emergency_contact: e.target.value})}
                  placeholder="Emergency contact number"
                />
              </div>
            </div>

            {/* Work Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-700">Work Information</h3>
              <div>
                <Label htmlFor="emp-address">Address</Label>
                <Textarea
                  id="emp-address"
                  value={newEmployeeData.address}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, address: e.target.value})}
                  placeholder="Enter full address"
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="emp-aadhar">Aadhar Card Number</Label>
                <Input
                  id="emp-aadhar"
                  value={newEmployeeData.aadhar_card}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, aadhar_card: e.target.value})}
                  placeholder="Enter 12-digit Aadhar number"
                />
              </div>
              <div>
                <Label htmlFor="emp-designation">Designation</Label>
                <Input
                  id="emp-designation"
                  value={newEmployeeData.designation}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, designation: e.target.value})}
                  placeholder="e.g., Software Developer"
                />
              </div>
              <div>
                <Label htmlFor="emp-department">Department</Label>
                <Input
                  id="emp-department"
                  value={newEmployeeData.department}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, department: e.target.value})}
                  placeholder="e.g., IT, HR, Finance"
                />
              </div>
              <div>
                <Label htmlFor="emp-joining">Joining Date</Label>
                <Input
                  id="emp-joining"
                  type="date"
                  value={newEmployeeData.joining_date}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, joining_date: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="emp-release">Release Date (Optional)</Label>
                <Input
                  id="emp-release"
                  type="date"
                  value={newEmployeeData.release_date}
                  onChange={(e) => setNewEmployeeData({...newEmployeeData, release_date: e.target.value})}
                />
              </div>
            </div>
          </div>
          <div className="flex space-x-2 mt-6">
            <Button onClick={createNewEmployee} className="flex-1" data-testid="create-employee-submit">
              Create Employee
            </Button>
            <Button 
              onClick={() => setShowCreateEmployeeModal(false)} 
              variant="outline" 
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Employee Modal */}
      <Dialog open={showEditEmployeeModal} onOpenChange={setShowEditEmployeeModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Employee</DialogTitle>
          </DialogHeader>
          {editingEmployee && (
            <div className="grid grid-cols-2 gap-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-700">Basic Information</h3>
                <div>
                  <Label htmlFor="edit-emp-name">Full Name *</Label>
                  <Input
                    id="edit-emp-name"
                    value={editingEmployee.name}
                    onChange={(e) => setEditingEmployee({...editingEmployee, name: e.target.value})}
                    placeholder="Enter full name"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-email">Email *</Label>
                  <Input
                    id="edit-emp-email"
                    type="email"
                    value={editingEmployee.email}
                    onChange={(e) => setEditingEmployee({...editingEmployee, email: e.target.value})}
                    placeholder="Enter email address"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-phone">Phone Number *</Label>
                  <Input
                    id="edit-emp-phone"
                    value={editingEmployee.phone}
                    onChange={(e) => setEditingEmployee({...editingEmployee, phone: e.target.value})}
                    placeholder="Enter phone number"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-dob">Date of Birth</Label>
                  <Input
                    id="edit-emp-dob"
                    type="date"
                    value={editingEmployee.dob}
                    onChange={(e) => setEditingEmployee({...editingEmployee, dob: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-blood-group">Blood Group</Label>
                  <Input
                    id="edit-emp-blood-group"
                    value={editingEmployee.blood_group}
                    onChange={(e) => setEditingEmployee({...editingEmployee, blood_group: e.target.value})}
                    placeholder="e.g., A+, B-, O+"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-emergency">Emergency Contact</Label>
                  <Input
                    id="edit-emp-emergency"
                    value={editingEmployee.emergency_contact}
                    onChange={(e) => setEditingEmployee({...editingEmployee, emergency_contact: e.target.value})}
                    placeholder="Emergency contact number"
                  />
                </div>
              </div>

              {/* Work Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-700">Work Information</h3>
                <div>
                  <Label htmlFor="edit-emp-address">Address</Label>
                  <Textarea
                    id="edit-emp-address"
                    value={editingEmployee.address}
                    onChange={(e) => setEditingEmployee({...editingEmployee, address: e.target.value})}
                    placeholder="Enter full address"
                    rows={2}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-aadhar">Aadhar Card Number</Label>
                  <Input
                    id="edit-emp-aadhar"
                    value={editingEmployee.aadhar_card}
                    onChange={(e) => setEditingEmployee({...editingEmployee, aadhar_card: e.target.value})}
                    placeholder="Enter 12-digit Aadhar number"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-designation">Designation</Label>
                  <Input
                    id="edit-emp-designation"
                    value={editingEmployee.designation}
                    onChange={(e) => setEditingEmployee({...editingEmployee, designation: e.target.value})}
                    placeholder="e.g., Software Developer"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-department">Department</Label>
                  <Input
                    id="edit-emp-department"
                    value={editingEmployee.department}
                    onChange={(e) => setEditingEmployee({...editingEmployee, department: e.target.value})}
                    placeholder="e.g., IT, HR, Finance"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-joining">Joining Date</Label>
                  <Input
                    id="edit-emp-joining"
                    type="date"
                    value={editingEmployee.joining_date}
                    onChange={(e) => setEditingEmployee({...editingEmployee, joining_date: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="edit-emp-release">Release Date (Optional)</Label>
                  <Input
                    id="edit-emp-release"
                    type="date"
                    value={editingEmployee.release_date}
                    onChange={(e) => setEditingEmployee({...editingEmployee, release_date: e.target.value})}
                  />
                </div>
              </div>
            </div>
          )}
          <div className="flex space-x-2 mt-6">
            <Button onClick={updateEmployee} className="flex-1" data-testid="update-employee-submit">
              Update Employee
            </Button>
            <Button 
              onClick={() => {
                setShowEditEmployeeModal(false);
                setEditingEmployee(null);
              }} 
              variant="outline" 
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Department Modal */}
      <Dialog open={showCreateDepartmentModal} onOpenChange={setShowCreateDepartmentModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create Department</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="dept-name">Department Name *</Label>
              <Input
                id="dept-name"
                value={newDepartmentData.name}
                onChange={(e) => setNewDepartmentData({...newDepartmentData, name: e.target.value})}
                placeholder="e.g., Engineering, HR, Finance"
              />
            </div>
            <div>
              <Label htmlFor="dept-description">Description</Label>
              <Textarea
                id="dept-description"
                value={newDepartmentData.description}
                onChange={(e) => setNewDepartmentData({...newDepartmentData, description: e.target.value})}
                placeholder="Department description..."
                rows={3}
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={createDepartment} className="flex-1" data-testid="create-department-submit">
                Create Department
              </Button>
              <Button onClick={() => setShowCreateDepartmentModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Manager Modal */}
      <Dialog open={showCreateManagerModal} onOpenChange={setShowCreateManagerModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Manager</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="manager-employee">Select Employee *</Label>
              <Select 
                value={newManagerData.employee_id} 
                onValueChange={(value) => setNewManagerData({...newManagerData, employee_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose an employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.filter(emp => !managers.some(m => m.employee_id === emp.id)).map(employee => (
                    <SelectItem key={employee.id} value={employee.id}>
                      {employee.name} ({employee.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="manager-department">Select Department *</Label>
              <Select 
                value={newManagerData.department_id} 
                onValueChange={(value) => setNewManagerData({...newManagerData, department_id: value})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map(dept => (
                    <SelectItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex space-x-2">
              <Button onClick={createManager} className="flex-1" data-testid="assign-manager-submit">
                Assign Manager
              </Button>
              <Button onClick={() => setShowCreateManagerModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Project Modal */}
      <Dialog open={showCreateProjectModal} onOpenChange={setShowCreateProjectModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Project</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            {/* Project Details */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-700">Project Details</h3>
              <div>
                <Label htmlFor="project-name">Project Name *</Label>
                <Input
                  id="project-name"
                  value={newProjectData.name}
                  onChange={(e) => setNewProjectData({...newProjectData, name: e.target.value})}
                  placeholder="Enter project name"
                />
              </div>
              <div>
                <Label htmlFor="project-description">Description</Label>
                <Textarea
                  id="project-description"
                  value={newProjectData.description}
                  onChange={(e) => setNewProjectData({...newProjectData, description: e.target.value})}
                  placeholder="Project description..."
                  rows={2}
                />
              </div>
              <div>
                <Label htmlFor="project-department">Department *</Label>
                <Select 
                  value={newProjectData.department_id} 
                  onValueChange={(value) => setNewProjectData({...newProjectData, department_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map(dept => (
                      <SelectItem key={dept.id} value={dept.id}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="project-manager">Manager *</Label>
                <Select 
                  value={newProjectData.manager_id} 
                  onValueChange={(value) => setNewProjectData({...newProjectData, manager_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose manager" />
                  </SelectTrigger>
                  <SelectContent>
                    {managers.filter(m => !newProjectData.department_id || m.department_id === newProjectData.department_id).map(manager => (
                      <SelectItem key={manager.id} value={manager.id}>
                        {manager.employee_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Project Timeline & Team */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-700">Timeline & Team</h3>
              <div>
                <Label htmlFor="project-start-date">Start Date</Label>
                <Input
                  id="project-start-date"
                  type="date"
                  value={newProjectData.start_date}
                  onChange={(e) => setNewProjectData({...newProjectData, start_date: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="project-end-date">End Date</Label>
                <Input
                  id="project-end-date"
                  type="date"
                  value={newProjectData.end_date}
                  onChange={(e) => setNewProjectData({...newProjectData, end_date: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="project-status">Status</Label>
                <Select 
                  value={newProjectData.status} 
                  onValueChange={(value) => setNewProjectData({...newProjectData, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Active">Active</SelectItem>
                    <SelectItem value="On Hold">On Hold</SelectItem>
                    <SelectItem value="Completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Assign Employees</Label>
                <div className="max-h-32 overflow-y-auto border rounded p-2 space-y-1">
                  {employees.map(employee => (
                    <label key={employee.id} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={selectedEmployeesForProject.includes(employee.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEmployeesForProject([...selectedEmployeesForProject, employee.id]);
                          } else {
                            setSelectedEmployeesForProject(selectedEmployeesForProject.filter(id => id !== employee.id));
                          }
                        }}
                      />
                      <span>{employee.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="flex space-x-2 mt-6">
            <Button onClick={createProject} className="flex-1" data-testid="create-project-submit">
              Create Project
            </Button>
            <Button onClick={() => setShowCreateProjectModal(false)} variant="outline" className="flex-1">
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// New Dashboard Cards Components
const AssociatedProjectsCard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/employee/projects`);
      setProjects(response.data);
    } catch (err) {
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <>
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setShowModal(true)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <BarChart3 className="mr-2 h-5 w-5 text-green-600" />
            Associated Projects
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-2xl font-bold text-green-600">
              {projects.length}
            </div>
            <p className="text-sm text-gray-600">
              {projects.length === 1 ? 'Project assigned' : 'Projects assigned'}
            </p>
            <Badge variant="outline" className="border-green-200 text-green-700">
              Click to view details
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>My Associated Projects</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {loading ? (
              <p>Loading projects...</p>
            ) : projects.length > 0 ? (
              projects.map(project => (
                <Card key={project.id} className="border">
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h3 className="font-semibold text-lg">{project.name}</h3>
                        <Badge className={project.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                          {project.status}
                        </Badge>
                      </div>
                      {project.description && (
                        <p className="text-gray-600">{project.description}</p>
                      )}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Manager:</span> {project.manager_name}
                        </div>
                        <div>
                          <span className="font-medium">Start Date:</span> {project.start_date || 'Not set'}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No projects assigned yet</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

const LeaveStatusCard = () => {
  const [leaveBalance, setLeaveBalance] = useState(null);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const fetchLeaveData = async () => {
    setLoading(true);
    try {
      const [balanceResponse, requestsResponse] = await Promise.all([
        axios.get(`${API}/employee/leave-balance`),
        axios.get(`${API}/employee/leave-requests`)
      ]);
      setLeaveBalance(balanceResponse.data);
      setLeaveRequests(requestsResponse.data);
    } catch (err) {
      console.error('Error fetching leave data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaveData();
  }, []);

  const totalAvailable = leaveBalance ? 
    leaveBalance.casual_leave.available + leaveBalance.sick_leave.available + leaveBalance.leave_without_pay.available : 0;

  return (
    <>
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setShowModal(true)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <Calendar className="mr-2 h-5 w-5 text-blue-600" />
            Leave Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-2xl font-bold text-blue-600">
              {totalAvailable}
            </div>
            <p className="text-sm text-gray-600">
              Days available
            </p>
            <Badge variant="outline" className="border-blue-200 text-blue-700">
              Q{leaveBalance?.quarter || 1} Balance
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Leave Status & History</DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            {loading ? (
              <p>Loading leave data...</p>
            ) : (
              <>
                {/* Leave Balance */}
                {leaveBalance && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Current Balance (Q{leaveBalance.quarter})</h3>
                    <div className="grid grid-cols-3 gap-4">
                      <Card>
                        <CardContent className="pt-4">
                          <div className="text-center space-y-2">
                            <h4 className="font-medium">Casual Leave</h4>
                            <div className="text-xl font-bold text-green-600">
                              {leaveBalance.casual_leave.available}
                            </div>
                            <p className="text-xs text-gray-500">
                              Used: {leaveBalance.casual_leave.used} / {leaveBalance.casual_leave.allocated}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4">
                          <div className="text-center space-y-2">
                            <h4 className="font-medium">Sick Leave</h4>
                            <div className="text-xl font-bold text-orange-600">
                              {leaveBalance.sick_leave.available}
                            </div>
                            <p className="text-xs text-gray-500">
                              Used: {leaveBalance.sick_leave.used} / {leaveBalance.sick_leave.allocated}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-4">
                          <div className="text-center space-y-2">
                            <h4 className="font-medium">Leave without Pay</h4>
                            <div className="text-xl font-bold text-purple-600">
                              {leaveBalance.leave_without_pay.available}
                            </div>
                            <p className="text-xs text-gray-500">
                              Used: {leaveBalance.leave_without_pay.used} / {leaveBalance.leave_without_pay.allocated}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  </div>
                )}

                {/* Leave History */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Leave Requests</h3>
                  <div className="max-h-64 overflow-y-auto space-y-3">
                    {leaveRequests.length > 0 ? (
                      leaveRequests.map(request => (
                        <Card key={request.id} className="border">
                          <CardContent className="pt-4">
                            <div className="flex justify-between items-start">
                              <div className="space-y-2">
                                <div className="font-medium">{request.leave_type}</div>
                                <div className="text-sm text-gray-600">
                                  {request.start_date} to {request.end_date} ({request.days_count} days)
                                </div>
                                <div className="text-sm">{request.reason}</div>
                                {request.manager_reason && request.status === 'rejected' && (
                                  <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                                    <span className="font-medium">Rejection Reason:</span> {request.manager_reason}
                                  </div>
                                )}
                              </div>
                              <Badge className={
                                request.status === 'approved' ? 'bg-green-100 text-green-800' :
                                request.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }>
                                {request.status}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    ) : (
                      <p className="text-gray-500 text-center py-4">No leave requests found</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

const ApplyLeaveCard = () => {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    leave_type: '',
    start_date: '',
    end_date: '',
    reason: '',
    days_count: 1
  });

  const calculateDays = () => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const diffTime = Math.abs(end - start);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      return diffDays;
    }
    return 1;
  };

  useEffect(() => {
    const days = calculateDays();
    setFormData(prev => ({ ...prev, days_count: days }));
  }, [formData.start_date, formData.end_date]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/employee/apply-leave`, formData);
      alert('Leave application submitted successfully!');
      setShowModal(false);
      setFormData({
        leave_type: '',
        start_date: '',
        end_date: '',
        reason: '',
        days_count: 1
      });
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to apply for leave');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setShowModal(true)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <UserCheck className="mr-2 h-5 w-5 text-purple-600" />
            Apply Leave
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-2xl font-bold text-purple-600">
              +
            </div>
            <p className="text-sm text-gray-600">
              Submit leave request
            </p>
            <Badge variant="outline" className="border-purple-200 text-purple-700">
              Click to apply
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Apply for Leave</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="leave_type">Leave Type</Label>
              <Select value={formData.leave_type} onValueChange={(value) => setFormData({...formData, leave_type: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select leave type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Casual Leave">Casual Leave</SelectItem>
                  <SelectItem value="Sick Leave">Sick Leave</SelectItem>
                  <SelectItem value="Leave without Pay">Leave without Pay</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="days_count">Days Count</Label>
              <Input
                id="days_count"
                type="number"
                value={formData.days_count}
                readOnly
                className="bg-gray-50"
              />
            </div>

            <div>
              <Label htmlFor="reason">Reason</Label>
              <Textarea
                id="reason"
                value={formData.reason}
                onChange={(e) => setFormData({...formData, reason: e.target.value})}
                placeholder="Please provide reason for leave"
                required
              />
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Submitting...' : 'Submit Application'}
              </Button>
              <Button type="button" onClick={() => setShowModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};

const RaiseITTicketCard = () => {
  const [showModal, setShowModal] = useState(false);
  const [showTicketsModal, setShowTicketsModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    priority: 'Medium'
  });

  const itCategories = [
    "Hardware Issues",
    "Software Issues", 
    "Network/Connectivity",
    "Account/Access",
    "Security",
    "General Support"
  ];

  const fetchTickets = async () => {
    try {
      const response = await axios.get(`${API}/employee/it-tickets`);
      setTickets(response.data);
    } catch (err) {
      console.error('Error fetching IT tickets:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/employee/it-tickets`, formData);
      alert('IT ticket created successfully!');
      setShowModal(false);
      setFormData({
        title: '',
        description: '',
        category: '',
        priority: 'Medium'
      });
      fetchTickets(); // Refresh tickets list
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create IT ticket');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Card className="cursor-pointer hover:shadow-md transition-shadow">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <Clock className="mr-2 h-5 w-5 text-red-600" />
            Raise IT Ticket
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-2xl font-bold text-red-600">
              ?
            </div>
            <p className="text-sm text-gray-600">
              Need IT support?
            </p>
            <div className="flex space-x-2">
              <Badge 
                variant="outline" 
                className="border-red-200 text-red-700 cursor-pointer"
                onClick={() => setShowModal(true)}
              >
                Create ticket
              </Badge>
              <Badge 
                variant="outline" 
                className="border-gray-200 text-gray-700 cursor-pointer"
                onClick={() => { fetchTickets(); setShowTicketsModal(true); }}
              >
                View tickets
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Ticket Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Raise IT Support Ticket</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="Brief description of the issue"
                required
              />
            </div>

            <div>
              <Label htmlFor="category">Category</Label>
              <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {itCategories.map(category => (
                    <SelectItem key={category} value={category}>{category}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select value={formData.priority} onValueChange={(value) => setFormData({...formData, priority: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Low">Low</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Provide detailed description of the issue"
                required
                rows={4}
              />
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? 'Creating...' : 'Create Ticket'}
              </Button>
              <Button type="button" onClick={() => setShowModal(false)} variant="outline" className="flex-1">
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Tickets Modal */}
      <Dialog open={showTicketsModal} onOpenChange={setShowTicketsModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>My IT Tickets</DialogTitle>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto space-y-3">
            {tickets.length > 0 ? (
              tickets.map(ticket => (
                <Card key={ticket.id} className="border">
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <h4 className="font-medium">{ticket.title}</h4>
                        <div className="flex space-x-2">
                          <Badge className={
                            ticket.priority === 'Critical' ? 'bg-red-100 text-red-800' :
                            ticket.priority === 'High' ? 'bg-orange-100 text-orange-800' :
                            ticket.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }>
                            {ticket.priority}
                          </Badge>
                          <Badge variant="outline">
                            {ticket.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-sm text-gray-600">
                        Category: {ticket.category}
                      </div>
                      <div className="text-sm text-gray-700">
                        {ticket.description}
                      </div>
                      <div className="text-xs text-gray-500">
                        Created: {new Date(ticket.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No IT tickets found</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

const Dashboard = ({ user, onLogout, orgBranding }) => {
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTimesheetModal, setShowTimesheetModal] = useState(false);
  const [timesheetData, setTimesheetData] = useState({
    task_id: '',
    work_description: '',
    status: 'Completed'
  });
  const [currentTime, setCurrentTime] = useState(new Date());
  const [sessionHistory, setSessionHistory] = useState([]);
  const [calendarData, setCalendarData] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('dashboard');
  const [canStartToday, setCanStartToday] = useState(null);
  const [isManager, setIsManager] = useState(false);
  const [managerInfo, setManagerInfo] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch active session
  const fetchActiveSession = async () => {
    try {
      const response = await axios.get(`${API}/sessions/active`);
      setActiveSession(response.data);
    } catch (err) {
      console.error('Error fetching active session:', err);
    }
  };

  // Timer effect
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch session history
  const fetchSessionHistory = async () => {
    try {
      const response = await axios.get(`${API}/sessions/history`);
      setSessionHistory(response.data);
    } catch (err) {
      console.error('Error fetching session history:', err);
    }
  };

  // Fetch calendar data
  const fetchCalendarData = async (year = new Date().getFullYear(), month = new Date().getMonth() + 1) => {
    try {
      const response = await axios.get(`${API}/calendar/month?year=${year}&month=${month}`);
      setCalendarData(response.data);
    } catch (err) {
      console.error('Error fetching calendar data:', err);
    }
  };

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats?year=${new Date().getFullYear()}`);
      setDashboardStats(response.data);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
    }
  };

  // Check if user can start session today
  const checkCanStartToday = async () => {
    try {
      const response = await axios.get(`${API}/sessions/can-start-today`);
      setCanStartToday(response.data);
    } catch (err) {
      console.error('Error checking session availability:', err);
    }
  };

  // Check if user is a manager
  const checkManagerStatus = async () => {
    try {
      const response = await axios.get(`${API}/employee/manager-status`);
      setIsManager(response.data.is_manager);
      if (response.data.is_manager) {
        setManagerInfo(response.data);
      }
    } catch (err) {
      console.error('Error checking manager status:', err);
    }
  };

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const [notificationsResponse, countResponse] = await Promise.all([
        axios.get(`${API}/employee/notifications`),
        axios.get(`${API}/employee/notifications/unread-count`)
      ]);
      setNotifications(notificationsResponse.data);
      setUnreadCount(countResponse.data.unread_count);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    }
  };

  // Mark notification as read
  const markNotificationRead = async (notificationId) => {
    try {
      await axios.put(`${API}/employee/notifications/${notificationId}/read`);
      // Refresh notifications
      fetchNotifications();
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  // Fetch session on mount and periodically
  useEffect(() => {
    fetchActiveSession();
    fetchSessionHistory();
    fetchCalendarData();
    fetchDashboardStats();
    checkCanStartToday();
    checkManagerStatus();
    fetchNotifications();
    
    const interval = setInterval(() => {
      fetchActiveSession();
      checkCanStartToday();
      fetchNotifications(); // Also refresh notifications
    }, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const startSession = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/sessions/start`);
      await fetchActiveSession();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start session');
    } finally {
      setLoading(false);
    }
  };

  const startBreak = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/breaks/start`);
      await fetchActiveSession();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start break');
    } finally {
      setLoading(false);
    }
  };

  const endBreak = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/breaks/end`);
      await fetchActiveSession();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to end break');
    } finally {
      setLoading(false);
    }
  };

  const applyHalfDay = async () => {
    if (!timesheetData.task_id || !timesheetData.work_description) {
      alert('Please fill in all timesheet fields');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API}/leaves/half-day`, timesheetData);
      setActiveSession(null);
      setShowTimesheetModal(false);
      setTimesheetData({ task_id: '', work_description: '', status: 'Completed' });
      
      // Refresh data after session ends
      await fetchSessionHistory();
      await fetchCalendarData();
      await fetchDashboardStats();
      await checkCanStartToday();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to apply half day');
    } finally {
      setLoading(false);
    }
  };

  const endSession = async () => {
    if (!timesheetData.task_id || !timesheetData.work_description) {
      alert('Please fill in all timesheet fields');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API}/sessions/end`, timesheetData);
      setActiveSession(null);
      setShowTimesheetModal(false);
      setTimesheetData({ task_id: '', work_description: '', status: 'Completed' });
      
      // Refresh data after session ends
      await fetchSessionHistory();
      await fetchCalendarData();
      await fetchDashboardStats();
      await checkCanStartToday();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to end session');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    onLogout();
  };

  const getCTAButton = () => {
    if (!activeSession) {
      // Check if user can start session today
      if (canStartToday && !canStartToday.can_start) {
        return (
          <div className="space-y-4">
            <Button
              disabled={true}
              className="w-full h-16 text-lg bg-gray-400 cursor-not-allowed"
              data-testid="session-blocked-btn"
            >
              <UserCheck className="mr-2 h-5 w-5" />
              Already Logged In Today
            </Button>
            <div className="text-center text-sm text-gray-600 bg-yellow-50 p-3 rounded-lg border border-yellow-200">
              <p className="font-medium text-yellow-800">One Login Per Day Policy</p>
              <p>You logged in today at {canStartToday.session_time} on {new Date(canStartToday.session_date).toLocaleDateString('en-IN')}</p>
              {canStartToday.is_completed ? (
                <p className="mt-1 text-green-700">✓ Session completed</p>
              ) : (
                <p className="mt-1 text-blue-700">Session is currently active</p>
              )}
            </div>
          </div>
        );
      }
      
      return (
        <Button
          onClick={startSession}
          disabled={loading}
          className="w-full h-16 text-lg bg-green-600 hover:bg-green-700"
          data-testid="start-session-btn"
        >
          <Play className="mr-2 h-5 w-5" />
          Login & Start Work
        </Button>
      );
    }

    if (activeSession.can_logout) {
      return (
        <Button
          onClick={() => setShowTimesheetModal(true)}
          disabled={loading}
          className="w-full h-16 text-lg bg-red-600 hover:bg-red-700"
          data-testid="logout-btn"
        >
          <LogOut className="mr-2 h-5 w-5" />
          Submit Timesheet & Logout
        </Button>
      );
    }

    return (
      <Button
        onClick={() => setShowTimesheetModal(true)}
        disabled={loading}
        className="w-full h-16 text-lg bg-orange-600 hover:bg-orange-700"
        data-testid="apply-half-day-btn"
      >
        <UserCheck className="mr-2 h-5 w-5" />
        Apply Half Day
      </Button>
    );
  };

  const getBreakButton = () => {
    if (!activeSession) return null;

    if (activeSession.active_break) {
      return (
        <Button
          onClick={endBreak}
          disabled={loading}
          variant="outline"
          className="w-full border-orange-300 text-orange-600 hover:bg-orange-50"
          data-testid="end-break-btn"
        >
          <Pause className="mr-2 h-4 w-4" />
          End Break
        </Button>
      );
    }

    return (
      <Button
        onClick={startBreak}
        disabled={loading}
        variant="outline"
        className="w-full border-blue-300 text-blue-600 hover:bg-blue-50"
        data-testid="start-break-btn"
      >
        <Coffee className="mr-2 h-4 w-4" />
        Start Break
      </Button>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            {orgBranding.company_logo && (
              <img 
                src={orgBranding.company_logo} 
                alt={orgBranding.company_name} 
                className="h-10 w-10 object-contain"
              />
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-800">{orgBranding.company_name}</h1>
              <p className="text-gray-600">Welcome back, {user.name}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm text-gray-600">
                {currentTime.toLocaleDateString('en-IN', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </div>
              <div className="text-lg font-mono">
                {currentTime.toLocaleTimeString('en-IN')}
              </div>
            </div>
            <Button 
              onClick={handleLogout} 
              variant="outline"
              data-testid="header-logout-btn"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4 space-y-6">
        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="dashboard" className="flex items-center gap-2" data-testid="dashboard-tab">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="calendar" className="flex items-center gap-2" data-testid="calendar-tab">
              <Calendar className="h-4 w-4" />
              Calendar
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2" data-testid="history-tab">
              <History className="h-4 w-4" />
              History
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center gap-2" data-testid="reports-tab">
              <BarChart3 className="h-4 w-4" />
              Reports
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Main CTA Card */}
            <Card className="shadow-lg border-0 bg-gradient-to-r from-white to-blue-50">
              <CardHeader className="text-center">
                <CardTitle className="text-3xl font-bold text-gray-800">
                  Today's Work Session
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Work Timer */}
                {activeSession && (
                  <div className="text-center space-y-4">
                    <div className="flex justify-center items-center space-x-8">
                      <div className="text-center">
                        <div className="text-sm text-gray-600 mb-1">Effective Work Time</div>
                        <div className="text-4xl font-mono font-bold text-blue-600" data-testid="work-timer">
                          {formatTime(activeSession.effective_seconds)}
                        </div>
                        <div className="text-sm text-gray-500">
                          Target: 09:00:00
                        </div>
                      </div>
                      
                      {activeSession.active_break && (
                        <div className="text-center">
                          <div className="text-sm text-gray-600 mb-1">Break Time</div>
                          <div className="text-2xl font-mono font-bold text-orange-500" data-testid="break-timer">
                            {formatTime(Math.floor((new Date() - new Date(activeSession.active_break.start_time)) / 1000))}
                          </div>
                          <Badge className="mt-1 bg-orange-100 text-orange-700">On Break</Badge>
                        </div>
                      )}
                    </div>
                    
                    {activeSession.eta_logout_utc && (
                      <div className="text-center">
                        <div className="text-sm text-gray-600">Estimated Logout Time</div>
                        <div className="text-lg font-mono text-green-600" data-testid="eta-logout">
                          {new Date(activeSession.eta_logout_utc).toLocaleTimeString('en-IN')}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* CTA Button */}
                <div className="max-w-md mx-auto">
                  {getCTAButton()}
                </div>
                
                {/* Break Control */}
                {activeSession && (
                  <div className="max-w-sm mx-auto">
                    {getBreakButton()}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center">
                    <Clock className="mr-2 h-5 w-5 text-blue-600" />
                    Session Status
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {activeSession ? (
                    <div className="space-y-2">
                      <p><span className="font-medium">Started:</span> {new Date(activeSession.session.start_time).toLocaleTimeString('en-IN')}</p>
                      <p><span className="font-medium">Duration:</span> {formatTime(Math.floor((new Date() - new Date(activeSession.session.start_time)) / 1000))}</p>
                      <Badge className={activeSession.can_logout ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}>
                        {activeSession.can_logout ? "Can Logout" : "Working"}
                      </Badge>
                    </div>
                  ) : (
                    <p className="text-gray-600">No active session</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Today's Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  {activeSession ? (
                    <div className="space-y-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{width: `${Math.min((activeSession.effective_seconds / (9 * 60 * 60)) * 100, 100)}%`}}
                        ></div>
                      </div>
                      <p className="text-sm text-gray-600">
                        {Math.round((activeSession.effective_seconds / (9 * 60 * 60)) * 100)}% Complete
                      </p>
                    </div>
                  ) : (
                    <p className="text-gray-600">Start your day!</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">Quick Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p><span className="font-medium">Role:</span> {user.role}</p>
                    <p><span className="font-medium">Email:</span> {user.email}</p>
                    <Badge variant="outline" className="border-green-200 text-green-700">Active Employee</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* New Employee Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
              {/* Associated Projects Card */}
              <AssociatedProjectsCard />
              
              {/* Leave Status Card */}
              <LeaveStatusCard />
              
              {/* Apply Leave Card */}
              <ApplyLeaveCard />
              
              {/* Raise IT Ticket Card */}
              <RaiseITTicketCard />
            </div>
          </TabsContent>

          {/* Calendar Tab */}
          <TabsContent value="calendar" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <Calendar className="h-6 w-6" />
                  Work Calendar
                </CardTitle>
                <p className="text-gray-600">View your work days, leaves, and holidays</p>
              </CardHeader>
              <CardContent>
                {calendarData && (
                  <div className="space-y-4">
                    {/* Calendar Header */}
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-semibold">
                        {new Date(calendarData.year, calendarData.month - 1).toLocaleDateString('en-US', { 
                          month: 'long', 
                          year: 'numeric' 
                        })}
                      </h3>
                      <div className="flex flex-wrap gap-4 text-sm">
                        <div className="flex items-center gap-1" title={calendarData.legend?.worked || "Full Day Worked"}>
                          <div className="w-3 h-3 bg-green-500 rounded"></div>
                          <span>✓ Worked</span>
                        </div>
                        <div className="flex items-center gap-1" title={calendarData.legend?.leave || "Full Day Leave"}>
                          <div className="w-3 h-3 bg-red-500 rounded"></div>
                          <span>✗ Leave</span>
                        </div>
                        <div className="flex items-center gap-1" title={calendarData.legend?.holiday || "Mandatory Holiday"}>
                          <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                          <span>🎉 Holiday</span>
                        </div>
                        <div className="flex items-center gap-1" title={calendarData.legend?.['half-day'] || "Half Day Worked/Leave"}>
                          <div className="w-3 h-3 bg-orange-500 rounded"></div>
                          <span>½ Half Day</span>
                        </div>
                        <div className="flex items-center gap-1" title={calendarData.legend?.available || "Available Day"}>
                          <div className="w-3 h-3 bg-gray-300 rounded"></div>
                          <span>Available</span>
                        </div>
                      </div>
                    </div>

                    {/* Calendar Grid */}
                    <div className="grid grid-cols-7 gap-2">
                      {/* Weekday headers */}
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="text-center font-medium text-gray-600 p-2">
                          {day}
                        </div>
                      ))}
                      
                      {/* Calendar days */}
                      {calendarData.days.map(day => {
                        let bgColor = 'bg-gray-50 hover:bg-gray-100';
                        let statusIcon = '';
                        let statusText = day.details?.status || 'Available';
                        
                        if (day.type === 'worked') {
                          bgColor = 'bg-green-100 hover:bg-green-200';
                          statusIcon = '✓';
                        } else if (day.type === 'leave') {
                          bgColor = 'bg-red-100 hover:bg-red-200';
                          statusIcon = '✗';
                        } else if (day.type === 'holiday') {
                          bgColor = 'bg-yellow-100 hover:bg-yellow-200';
                          statusIcon = '🎉';
                        } else if (day.type === 'half-day') {
                          bgColor = 'bg-orange-100 hover:bg-orange-200';
                          statusIcon = '½';
                        }
                        
                        return (
                          <div
                            key={day.date}
                            className={`p-3 text-center rounded-lg cursor-pointer transition-colors ${bgColor} relative group`}
                            data-testid={`calendar-day-${day.date}`}
                            title={statusText}
                          >
                            <span className="font-medium">{day.day}</span>
                            {statusIcon && (
                              <span className="text-xs absolute top-1 right-1 opacity-70">
                                {statusIcon}
                              </span>
                            )}
                            
                            {/* Tooltip with detailed information */}
                            {day.details && (
                              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10 whitespace-nowrap">
                                <div className="font-semibold">{statusText}</div>
                                {day.details.login_time && (
                                  <div>Login: {day.details.login_time}</div>
                                )}
                                {day.details.logout_time && (
                                  <div>Logout: {day.details.logout_time}</div>
                                )}
                                {day.details.effective_hours && (
                                  <div>Hours: {day.details.effective_hours}h</div>
                                )}
                                {day.details.holiday_name && (
                                  <div>{day.details.holiday_name}</div>
                                )}
                                {day.details.reason && (
                                  <div>Reason: {day.details.reason}</div>
                                )}
                                {/* Tooltip arrow */}
                                <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <History className="h-6 w-6" />
                  Work History
                </CardTitle>
                <p className="text-gray-600">View your login/logout history and work sessions</p>
              </CardHeader>
              <CardContent>
                {sessionHistory.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Login Time</TableHead>
                          <TableHead>Logout Time</TableHead>
                          <TableHead>Total Duration</TableHead>
                          <TableHead>Effective Work</TableHead>
                          <TableHead>Breaks</TableHead>
                          <TableHead>Day Type</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sessionHistory.map(session => (
                          <TableRow key={session.id} data-testid={`history-row-${session.id}`}>
                            <TableCell className="font-medium">
                              {new Date(session.date).toLocaleDateString('en-IN')}
                            </TableCell>
                            <TableCell>{session.login_time}</TableCell>
                            <TableCell>{session.logout_time}</TableCell>
                            <TableCell>{session.total_duration}</TableCell>
                            <TableCell className="font-mono">{session.effective_duration}</TableCell>
                            <TableCell>
                              {session.break_count} ({session.break_duration})
                            </TableCell>
                            <TableCell>
                              <Badge variant={session.day_type === 'Half Day' ? 'secondary' : 'default'}>
                                {session.day_type}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={session.timesheet_status === 'Submitted' ? 'default' : 'destructive'}>
                                {session.timesheet_status}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No work history found. Start your first session!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Reports Tab */}
          <TabsContent value="reports" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                  <BarChart3 className="h-6 w-6" />
                  Leave Reports
                </CardTitle>
                <p className="text-gray-600">Monthly leave statistics for {new Date().getFullYear()}</p>
              </CardHeader>
              <CardContent>
                {dashboardStats && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {dashboardStats.leaves_by_month.map(month => (
                        <Card key={month.month} className="p-4">
                          <div className="flex justify-between items-center">
                            <div>
                              <h4 className="font-medium">{month.month_name}</h4>
                              <p className="text-2xl font-bold text-blue-600">{month.leaves_count}</p>
                            </div>
                            <div className="text-gray-400">
                              <Calendar className="h-6 w-6" />
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Timesheet Modal */}
      <Dialog open={showTimesheetModal} onOpenChange={setShowTimesheetModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Submit Timesheet</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="task_id">Task ID</Label>
              <Input
                id="task_id"
                value={timesheetData.task_id}
                onChange={(e) => setTimesheetData({...timesheetData, task_id: e.target.value})}
                placeholder="e.g., TASK-123"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="work_description">Work Description</Label>
              <Textarea
                id="work_description"
                value={timesheetData.work_description}
                onChange={(e) => setTimesheetData({...timesheetData, work_description: e.target.value})}
                placeholder="Describe what you worked on today..."
                rows={3}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="status">Status</Label>
              <Select 
                value={timesheetData.status} 
                onValueChange={(value) => setTimesheetData({...timesheetData, status: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Ongoing">Ongoing</SelectItem>
                  <SelectItem value="Blocked">Blocked</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex space-x-2">
              {activeSession?.can_logout ? (
                <Button 
                  onClick={endSession} 
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-700"
                  data-testid="submit-timesheet-logout"
                >
                  Submit & Logout
                </Button>
              ) : (
                <Button 
                  onClick={applyHalfDay} 
                  disabled={loading}
                  className="flex-1 bg-orange-600 hover:bg-orange-700"
                  data-testid="submit-timesheet-halfday"
                >
                  Apply Half Day
                </Button>
              )}
              <Button 
                onClick={() => setShowTimesheetModal(false)} 
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [orgBranding, setOrgBranding] = useState({ company_name: 'Work Hours Tracker', company_logo: '' });

  useEffect(() => {
    // Fetch organization branding info first (public endpoint)
    const fetchOrgBranding = async () => {
      try {
        const response = await axios.get(`${API}/organization-info`);
        setOrgBranding(response.data);
      } catch (err) {
        console.error('Error fetching organization info:', err);
      }
    };

    fetchOrgBranding();

    // Check for regular user token
    const token = localStorage.getItem('token');
    const adminToken = localStorage.getItem('adminToken');
    
    if (adminToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${adminToken}`;
      // Verify admin token
      axios.get(`${API}/admin/auth/me`)
        .then(response => {
          setAdmin(response.data);
          setIsAdminAuthenticated(true);
        })
        .catch(() => {
          localStorage.removeItem('adminToken');
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Verify user token
      axios.get(`${API}/auth/me`)
        .then(response => {
          setUser(response.data);
          setIsAuthenticated(true);
        })
        .catch(() => {
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  const handleAdminLogin = (adminData) => {
    setAdmin(adminData);
    setIsAdminAuthenticated(true);
  };

  const handleAdminLogout = () => {
    setAdmin(null);
    setIsAdminAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route 
          path="/" 
          element={
            isAuthenticated && user ? 
              <Dashboard user={user} onLogout={handleLogout} orgBranding={orgBranding} /> :
              <AuthPage onLogin={handleLogin} orgBranding={orgBranding} />
          } 
        />
        <Route 
          path="/admin-login" 
          element={
            isAdminAuthenticated && admin ?
              <AdminDashboard admin={admin} onLogout={handleAdminLogout} orgBranding={orgBranding} /> :
              <AdminLoginPage onAdminLogin={handleAdminLogin} orgBranding={orgBranding} />
          } 
        />
        <Route 
          path="/admin" 
          element={
            isAdminAuthenticated && admin ?
              <AdminDashboard admin={admin} onLogout={handleAdminLogout} orgBranding={orgBranding} /> :
              <Navigate to="/admin-login" />
          } 
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;