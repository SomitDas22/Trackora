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

const AuthPage = ({ onLogin }) => {
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
          <CardTitle className="text-2xl font-bold text-gray-800">
            {isLogin ? 'Welcome Back' : 'Join Our Team'}
          </CardTitle>
          <p className="text-gray-600">Work Hours Tracker</p>
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

const AdminLoginPage = ({ onAdminLogin }) => {
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
          <CardTitle className="text-2xl font-bold text-gray-800">
            Admin Login
          </CardTitle>
          <p className="text-gray-600">Work Hours Tracker - Admin Panel</p>
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

const AdminDashboard = ({ admin, onLogout }) => {
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
  const [newHolidayData, setNewHolidayData] = useState({ date: '', name: '' });

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
    if (!newHolidayData.date || !newHolidayData.name) {
      alert('Please fill all fields');
      return;
    }

    try {
      await axios.post(`${API}/admin/add-holiday`, newHolidayData);
      setShowHolidayModal(false);
      setNewHolidayData({ date: '', name: '' });
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Admin Header */}
      <div className="bg-slate-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
            <p className="text-slate-300">Work Hours Tracker Administration</p>
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
          <TabsList className="grid w-full grid-cols-3 mb-6">
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
                          <p className="text-purple-100">Sessions This Month</p>
                          <p className="text-3xl font-bold">{adminStats.sessions_this_month}</p>
                        </div>
                        <Calendar className="h-8 w-8 text-purple-200" />
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
        </Tabs>
      </div>
    </div>
  );
};

const Dashboard = ({ user, onLogout }) => {
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

  // Fetch session on mount and periodically
  useEffect(() => {
    fetchActiveSession();
    fetchSessionHistory();
    fetchCalendarData();
    fetchDashboardStats();
    checkCanStartToday();
    
    const interval = setInterval(() => {
      fetchActiveSession();
      checkCanStartToday();
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
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Work Hours Tracker</h1>
            <p className="text-gray-600">Welcome back, {user.name}</p>
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
                      <div className="flex gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-green-500 rounded"></div>
                          <span>Worked</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-red-500 rounded"></div>
                          <span>Leave</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                          <span>Holiday</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className="w-3 h-3 bg-orange-500 rounded"></div>
                          <span>Half Day</span>
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
                        if (day.type === 'worked') bgColor = 'bg-green-100 hover:bg-green-200';
                        else if (day.type === 'leave') bgColor = 'bg-red-100 hover:bg-red-200';
                        else if (day.type === 'holiday') bgColor = 'bg-yellow-100 hover:bg-yellow-200';
                        else if (day.type === 'half-day') bgColor = 'bg-orange-100 hover:bg-orange-200';
                        
                        return (
                          <div
                            key={day.date}
                            className={`p-3 text-center rounded-lg cursor-pointer transition-colors ${bgColor}`}
                            data-testid={`calendar-day-${day.date}`}
                          >
                            <span className="font-medium">{day.day}</span>
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

  useEffect(() => {
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
              <Dashboard user={user} onLogout={handleLogout} /> :
              <AuthPage onLogin={handleLogin} />
          } 
        />
        <Route 
          path="/admin-login" 
          element={
            isAdminAuthenticated && admin ?
              <AdminDashboard admin={admin} onLogout={handleAdminLogout} /> :
              <AdminLoginPage onAdminLogin={handleAdminLogin} />
          } 
        />
        <Route 
          path="/admin" 
          element={
            isAdminAuthenticated && admin ?
              <AdminDashboard admin={admin} onLogout={handleAdminLogout} /> :
              <Navigate to="/admin-login" />
          } 
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;