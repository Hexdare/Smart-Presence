import React, { useState, useEffect, useRef } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { QrCode, Users, Calendar, LogOut, Camera, CheckCircle, Clock, User, Megaphone, Plus, Edit, Trash2, Eye, AlertTriangle, Menu, Shield, X, ZoomIn, ZoomOut } from "lucide-react";
import QrScanner from 'qr-scanner';
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, '') || "";
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem("token");
      }
    }
    setLoading(false);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Routes>
          <Route path="/login" element={!user ? <Login setUser={setUser} setError={setError} error={error} /> : <Navigate to="/" />} />
          <Route path="/register" element={!user ? <Register setError={setError} error={error} /> : <Navigate to="/" />} />
          <Route path="/" element={user ? <Dashboard user={user} logout={logout} /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
};

const Login = ({ setUser, setError, error }) => {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      const { access_token } = response.data;
      
      localStorage.setItem("token", access_token);
      
      const userResponse = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      
      setUser(userResponse.data);
    } catch (error) {
      setError(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center">
            <Users className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">Smart Attendance</CardTitle>
          <p className="text-gray-600">Sign in to your account</p>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                data-testid="username-input"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                data-testid="password-input"
                className="mt-1"
              />
            </div>
            <Button 
              type="submit" 
              className="w-full bg-indigo-600 hover:bg-indigo-700" 
              disabled={loading}
              data-testid="login-button"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{" "}
              <a href="/register" className="text-indigo-600 hover:text-indigo-700 font-medium">
                Register here
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const Register = ({ setError, error }) => {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    role: "",
    student_id: "",
    class_section: "",
    subjects: [],
    full_name: ""
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await axios.post(`${API}/auth/register`, formData);
      setSuccess(true);
    } catch (error) {
      setError(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="pt-6 text-center">
            <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Registration Successful!</h2>
            <p className="text-gray-600 mb-6">Your account has been created successfully.</p>
            <a href="/login">
              <Button className="w-full bg-indigo-600 hover:bg-indigo-700">Go to Login</Button>
            </a>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">Create Account</CardTitle>
          <p className="text-gray-600">Register for Smart Attendance</p>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
                data-testid="fullname-input"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
                data-testid="reg-username-input"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                data-testid="reg-password-input"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                <SelectTrigger className="mt-1" data-testid="role-select">
                  <SelectValue placeholder="Select your role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="student">Student</SelectItem>
                  <SelectItem value="teacher">Teacher</SelectItem>
                  <SelectItem value="principal">Principal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.role === "student" && (
              <>
                <div>
                  <Label htmlFor="student_id">Student ID</Label>
                  <Input
                    id="student_id"
                    type="text"
                    value={formData.student_id}
                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                    required
                    data-testid="student-id-input"
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="class_section">Class Section</Label>
                  <Select value={formData.class_section} onValueChange={(value) => setFormData({ ...formData, class_section: value })}>
                    <SelectTrigger className="mt-1" data-testid="class-section-select">
                      <SelectValue placeholder="Select class section" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="A5">A5</SelectItem>
                      <SelectItem value="A6">A6</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
            {formData.role === "teacher" && (
              <div>
                <Label>Subjects (Select multiple)</Label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {[
                    "Mathematics", "Physics", "English", "Basic Electrical Engineering",
                    "Integrated Circuits", "CAD Lab", "Communication Lab", "Physics Lab",
                    "BEE Lab", "Production and Manufacturing Engineering"
                  ].map((subject) => (
                    <div key={subject} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`subject-${subject}`}
                        checked={formData.subjects.includes(subject)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, subjects: [...formData.subjects, subject] });
                          } else {
                            setFormData({ ...formData, subjects: formData.subjects.filter(s => s !== subject) });
                          }
                        }}
                        className="rounded border-gray-300"
                        data-testid={`subject-${subject.replace(/\s+/g, '-').toLowerCase()}`}
                      />
                      <Label htmlFor={`subject-${subject}`} className="text-sm font-normal">
                        {subject}
                      </Label>
                    </div>
                  ))}
                </div>
                {formData.subjects.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">Selected: {formData.subjects.join(", ")}</p>
                  </div>
                )}
              </div>
            )}
            {formData.role === "principal" && (
              <div>
                <Label>Subjects (Optional - Select if you teach any subjects)</Label>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {[
                    "Mathematics", "Physics", "English", "Basic Electrical Engineering",
                    "Integrated Circuits", "CAD Lab", "Communication Lab", "Physics Lab",
                    "BEE Lab", "Production and Manufacturing Engineering"
                  ].map((subject) => (
                    <div key={subject} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`principal-subject-${subject}`}
                        checked={formData.subjects.includes(subject)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, subjects: [...formData.subjects, subject] });
                          } else {
                            setFormData({ ...formData, subjects: formData.subjects.filter(s => s !== subject) });
                          }
                        }}
                        className="rounded border-gray-300"
                        data-testid={`principal-subject-${subject.replace(/\s+/g, '-').toLowerCase()}`}
                      />
                      <Label htmlFor={`principal-subject-${subject}`} className="text-sm font-normal">
                        {subject}
                      </Label>
                    </div>
                  ))}
                </div>
                {formData.subjects.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">Selected: {formData.subjects.join(", ")}</p>
                  </div>
                )}
                <div className="mt-2 p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-800">
                    <strong>Principal Account:</strong> You'll have full access to all features including 
                    QR code generation, attendance management, timetable editing, and announcements.
                  </p>
                </div>
              </div>
            )}
            <Button 
              type="submit" 
              className="w-full bg-indigo-600 hover:bg-indigo-700" 
              disabled={loading}
              data-testid="register-button"
            >
              {loading ? "Creating Account..." : "Create Account"}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{" "}
              <a href="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
                Sign in here
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const Dashboard = ({ user, logout }) => {
  return (
    <div className="min-h-screen">
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-indigo-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Smart Attendance</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Welcome, {user.full_name} ({user.role})
              </span>
              <Button 
                variant="outline" 
                onClick={logout}
                data-testid="logout-button"
                className="flex items-center"
              >
                <LogOut className="w-4 h-4 mr-1" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {user.role === "teacher" ? (
          <TeacherDashboard user={user} />
        ) : user.role === "principal" ? (
          <PrincipalDashboard user={user} />
        ) : (
          <StudentDashboard user={user} />
        )}
      </main>
    </div>
  );
};

const TeacherDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState("announcements");
  const [qrSessions, setQrSessions] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [announcements, setAnnouncements] = useState([]);
  const [showAlertsHistory, setShowAlertsHistory] = useState(false);

  useEffect(() => {
    fetchQrSessions();
    fetchAttendanceRecords();
    fetchTimetable();
    fetchAnnouncements();
  }, []);

  const fetchQrSessions = async () => {
    try {
      const response = await axios.get(`${API}/qr/sessions`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setQrSessions(response.data);
    } catch (error) {
      console.error("Error fetching QR sessions:", error);
    }
  };

  const fetchAttendanceRecords = async () => {
    try {
      const response = await axios.get(`${API}/attendance/records`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAttendanceRecords(response.data);
    } catch (error) {
      console.error("Error fetching attendance records:", error);
    }
  };

  const fetchTimetable = async () => {
    try {
      const response = await axios.get(`${API}/timetable`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setTimetable(response.data);
    } catch (error) {
      console.error("Error fetching timetable:", error);
    }
  };

  const fetchAnnouncements = async () => {
    try {
      const response = await axios.get(`${API}/announcements`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAnnouncements(response.data);
    } catch (error) {
      console.error("Error fetching announcements:", error);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Emergency Alerts Menu Button */}
      <div className="fixed top-20 right-4 z-50">
        <Button
          onClick={() => setShowAlertsHistory(true)}
          className="w-12 h-12 rounded-full bg-red-500/90 backdrop-blur-sm hover:bg-red-600/95 shadow-lg border border-red-400/30"
          data-testid="teacher-alerts-button"
        >
          <Shield className="w-6 h-6 text-white" />
        </Button>
      </div>

      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h2>
        <p className="mt-2 text-gray-600">Manage your classes and track attendance</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-white/60 backdrop-blur-sm">
          <TabsTrigger value="announcements" data-testid="teacher-announcements-tab">
            <Megaphone className="w-4 h-4 mr-2" />
            Announcements
          </TabsTrigger>
          <TabsTrigger value="generate" data-testid="generate-tab">
            <QrCode className="w-4 h-4 mr-2" />
            Generate QR
          </TabsTrigger>
          <TabsTrigger value="sessions" data-testid="sessions-tab">
            <Clock className="w-4 h-4 mr-2" />
            Sessions
          </TabsTrigger>
          <TabsTrigger value="attendance" data-testid="attendance-tab">
            <Users className="w-4 h-4 mr-2" />
            Attendance
          </TabsTrigger>
          <TabsTrigger value="timetable" data-testid="timetable-tab">
            <Calendar className="w-4 h-4 mr-2" />
            Timetable
          </TabsTrigger>
        </TabsList>

        <TabsContent value="announcements">
          <AnnouncementSection 
            announcements={announcements} 
            onAnnouncementCreated={fetchAnnouncements}
            userRole={user.role}
          />
        </TabsContent>

        <TabsContent value="generate">
          <GenerateQRCard onQrGenerated={fetchQrSessions} />
        </TabsContent>

        <TabsContent value="sessions">
          <QRSessionsList sessions={qrSessions} />
        </TabsContent>

        <TabsContent value="attendance">
          <AttendanceList records={attendanceRecords} />
        </TabsContent>

        <TabsContent value="timetable">
          <TimetableView timetable={timetable} />
        </TabsContent>
      </Tabs>

      {/* Emergency Alerts History Modal */}
      {showAlertsHistory && (
        <EmergencyAlertsHistory 
          onClose={() => setShowAlertsHistory(false)}
          user={user}
        />
      )}
    </div>
  );
};

const PrincipalDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState("announcements");
  const [qrSessions, setQrSessions] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [announcements, setAnnouncements] = useState([]);
  const [showAlertsHistory, setShowAlertsHistory] = useState(false);

  useEffect(() => {
    fetchQrSessions();
    fetchAttendanceRecords();
    fetchTimetable();
    fetchAnnouncements();
  }, []);

  const fetchQrSessions = async () => {
    try {
      const response = await axios.get(`${API}/qr/sessions`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setQrSessions(response.data);
    } catch (error) {
      console.error("Error fetching QR sessions:", error);
    }
  };

  const fetchAttendanceRecords = async () => {
    try {
      const response = await axios.get(`${API}/attendance/records`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAttendanceRecords(response.data);
    } catch (error) {
      console.error("Error fetching attendance records:", error);
    }
  };

  const fetchTimetable = async () => {
    try {
      const response = await axios.get(`${API}/timetable`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setTimetable(response.data);
    } catch (error) {
      console.error("Error fetching timetable:", error);
    }
  };

  const fetchAnnouncements = async () => {
    try {
      const response = await axios.get(`${API}/announcements`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAnnouncements(response.data);
    } catch (error) {
      console.error("Error fetching announcements:", error);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Emergency Alerts Menu Button - Principal has prominent access */}
      <div className="fixed top-20 right-4 z-50">
        <Button
          onClick={() => setShowAlertsHistory(true)}
          className="w-14 h-14 rounded-full bg-red-600/90 backdrop-blur-sm hover:bg-red-700/95 shadow-xl border-2 border-red-400/30 animate-pulse"
          data-testid="principal-alerts-button"
        >
          <Shield className="w-7 h-7 text-white" />
        </Button>
      </div>

      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Principal Dashboard</h2>
        <p className="mt-2 text-gray-600">Manage school operations and communications</p>
        <Badge className="mt-2 bg-green-600">Principal</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 bg-white/60 backdrop-blur-sm">
          <TabsTrigger value="announcements" data-testid="announcements-tab">
            <Megaphone className="w-4 h-4 mr-2" />
            Announcements
          </TabsTrigger>
          <TabsTrigger value="generate" data-testid="principal-generate-tab">
            <QrCode className="w-4 h-4 mr-2" />
            Generate QR
          </TabsTrigger>
          <TabsTrigger value="attendance" data-testid="principal-attendance-tab">
            <Users className="w-4 h-4 mr-2" />
            Attendance
          </TabsTrigger>
          <TabsTrigger value="timetable" data-testid="principal-timetable-tab">
            <Calendar className="w-4 h-4 mr-2" />
            Timetable
          </TabsTrigger>
          <TabsTrigger value="sessions" data-testid="principal-sessions-tab">
            <Clock className="w-4 h-4 mr-2" />
            Sessions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="announcements">
          <AnnouncementSection 
            announcements={announcements} 
            onAnnouncementCreated={fetchAnnouncements}
            userRole={user.role}
          />
        </TabsContent>

        <TabsContent value="generate">
          <GenerateQRCard onQrGenerated={fetchQrSessions} />
        </TabsContent>

        <TabsContent value="attendance">
          <AttendanceList records={attendanceRecords} />
        </TabsContent>

        <TabsContent value="timetable">
          <TimetableManagement timetable={timetable} onTimetableUpdate={fetchTimetable} />
        </TabsContent>

        <TabsContent value="sessions">
          <QRSessionsList sessions={qrSessions} />
        </TabsContent>
      </Tabs>

      {/* Emergency Alerts History Modal */}
      {showAlertsHistory && (
        <EmergencyAlertsHistory 
          onClose={() => setShowAlertsHistory(false)}
          user={user}
        />
      )}
    </div>
  );
};

const GenerateQRCard = ({ onQrGenerated }) => {
  const [formData, setFormData] = useState({
    class_section: "",
    subject: "",
    class_code: "",
    time_slot: ""
  });
  const [loading, setLoading] = useState(false);
  const [qrResult, setQrResult] = useState(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(`${API}/qr/generate`, formData, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setQrResult(response.data);
      onQrGenerated();
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to generate QR code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center">
          <QrCode className="w-5 h-5 mr-2" />
          Generate QR Code for Attendance
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50">
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {qrResult ? (
          <div className="text-center space-y-4">
            <div className="bg-white p-4 rounded-lg inline-block shadow-md">
              <img 
                src={`data:image/png;base64,${qrResult.qr_image}`} 
                alt="QR Code" 
                className="mx-auto"
                data-testid="generated-qr-code"
              />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Session Details:</p>
              <Badge variant="outline">{qrResult.class_section}</Badge>
              <Badge variant="outline">{qrResult.subject}</Badge>
              <Badge variant="outline">{qrResult.time_slot}</Badge>
            </div>
            <p className="text-sm text-gray-600">
              Expires: {new Date(qrResult.expires_at).toLocaleString()}
            </p>
            <Button 
              onClick={() => setQrResult(null)}
              variant="outline"
              data-testid="generate-new-qr-button"
            >
              Generate New QR Code
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="class_section">Class Section</Label>
              <Select 
                value={formData.class_section} 
                onValueChange={(value) => setFormData({ ...formData, class_section: value })}
              >
                <SelectTrigger data-testid="qr-class-section-select">
                  <SelectValue placeholder="Select class section" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="A5">A5</SelectItem>
                  <SelectItem value="A6">A6</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                placeholder="e.g., Mathematics, Physics"
                required
                data-testid="qr-subject-input"
              />
            </div>

            <div>
              <Label htmlFor="class_code">Class Code</Label>
              <Input
                id="class_code"
                type="text"
                value={formData.class_code}
                onChange={(e) => setFormData({ ...formData, class_code: e.target.value })}
                placeholder="e.g., MC, PHY, ENG"
                required
                data-testid="qr-class-code-input"
              />
            </div>

            <div>
              <Label htmlFor="time_slot">Time Slot</Label>
              <Input
                id="time_slot"
                type="text"
                value={formData.time_slot}
                onChange={(e) => setFormData({ ...formData, time_slot: e.target.value })}
                placeholder="e.g., 09:30-10:30"
                required
                data-testid="qr-time-slot-input"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full bg-indigo-600 hover:bg-indigo-700" 
              disabled={loading}
              data-testid="generate-qr-submit-button"
            >
              {loading ? "Generating..." : "Generate QR Code"}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
};

const StudentDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState("announcements");
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [announcements, setAnnouncements] = useState([]);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [showAlertsHistory, setShowAlertsHistory] = useState(false);

  useEffect(() => {
    fetchAttendanceRecords();
    fetchTimetable();
    fetchAnnouncements();
  }, []);

  const fetchAttendanceRecords = async () => {
    try {
      const response = await axios.get(`${API}/attendance/records`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAttendanceRecords(response.data);
    } catch (error) {
      console.error("Error fetching attendance records:", error);
    }
  };

  const fetchTimetable = async () => {
    try {
      const response = await axios.get(`${API}/timetable`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setTimetable(response.data);
    } catch (error) {
      console.error("Error fetching timetable:", error);
    }
  };

  const fetchAnnouncements = async () => {
    try {
      const response = await axios.get(`${API}/announcements`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAnnouncements(response.data);
    } catch (error) {
      console.error("Error fetching announcements:", error);
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* Hamburger Menu - Floating Button */}
      <div className="fixed top-20 left-4 z-50">
        <Button
          onClick={() => setShowAlertsHistory(true)}
          className="w-12 h-12 rounded-full bg-white/90 backdrop-blur-sm hover:bg-white/95 shadow-lg border border-gray-200"
          variant="outline"
          data-testid="hamburger-menu-button"
        >
          <Menu className="w-6 h-6 text-gray-700" />
        </Button>
      </div>

      {/* Emergency Alert Button - Translucent Red Squircle */}
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setShowEmergencyModal(true)}
          className="w-16 h-16 rounded-3xl bg-red-500/60 backdrop-blur-sm hover:bg-red-600/70 shadow-2xl border border-red-400/30 transition-all duration-300 animate-pulse"
          data-testid="emergency-alert-button"
        >
          <AlertTriangle className="w-8 h-8 text-white" />
        </Button>
      </div>

      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Student Dashboard</h2>
        <p className="mt-2 text-gray-600">Scan QR codes to mark your attendance</p>
        <Badge className="mt-2 bg-indigo-600">{user.class_section}</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-white/60 backdrop-blur-sm">
          <TabsTrigger value="announcements" data-testid="student-announcements-tab">
            <Megaphone className="w-4 h-4 mr-2" />
            Announcements
          </TabsTrigger>
          <TabsTrigger value="scan" data-testid="scan-tab">
            <Camera className="w-4 h-4 mr-2" />
            Scan QR
          </TabsTrigger>
          <TabsTrigger value="attendance" data-testid="student-attendance-tab">
            <Users className="w-4 h-4 mr-2" />
            My Attendance
          </TabsTrigger>
          <TabsTrigger value="timetable" data-testid="student-timetable-tab">
            <Calendar className="w-4 h-4 mr-2" />
            Timetable
          </TabsTrigger>
        </TabsList>

        <TabsContent value="announcements">
          <AnnouncementSection 
            announcements={announcements} 
            onAnnouncementCreated={fetchAnnouncements}
            userRole={user.role}
          />
        </TabsContent>

        <TabsContent value="scan">
          <QRScannerCard onAttendanceMarked={fetchAttendanceRecords} />
        </TabsContent>

        <TabsContent value="attendance">
          <AttendanceList records={attendanceRecords} />
        </TabsContent>

        <TabsContent value="timetable">
          <TimetableView timetable={timetable} />
        </TabsContent>
      </Tabs>

      {/* Emergency Alert Modal */}
      {showEmergencyModal && (
        <EmergencyAlertModal 
          onClose={() => setShowEmergencyModal(false)} 
          user={user}
        />
      )}

      {/* Emergency Alerts History Modal */}
      {showAlertsHistory && (
        <EmergencyAlertsHistory 
          onClose={() => setShowAlertsHistory(false)}
          user={user}
        />
      )}
    </div>
  );
};

const QRScannerCard = ({ onAttendanceMarked }) => {
  const [showScanner, setShowScanner] = useState(false);
  const [qrInput, setQrInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [cameraError, setCameraError] = useState(false);
  const [showTextFallback, setShowTextFallback] = useState(false);

  const markAttendance = async (qrData) => {
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await axios.post(`${API}/attendance/mark`, { qr_data: qrData }, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setSuccess("Attendance marked successfully!");
      setQrInput("");
      setShowScanner(false);
      onAttendanceMarked();
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to mark attendance");
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    await markAttendance(qrInput);
  };

  const handleScanSuccess = async (result) => {
    if (result) {
      await markAttendance(result);
    }
  };

  const handleCameraError = () => {
    setCameraError(true);
    setShowScanner(false);
    setShowTextFallback(true);
    setError("Camera access failed. Please use the text input option below or check camera permissions.");
  };

  const startScanning = () => {
    setCameraError(false);
    setError("");
    setSuccess("");
    setShowScanner(true);
    setShowTextFallback(false);
  };

  return (
    <>
      {/* Fullscreen QR Scanner Modal */}
      {showScanner && (
        <QRCameraScanner 
          onScanSuccess={handleScanSuccess}
          onClose={() => setShowScanner(false)}
          onError={handleCameraError}
        />
      )}

      <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Camera className="w-5 h-5 mr-2" />
            Scan QR Code for Attendance
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <AlertDescription className="text-green-800">{success}</AlertDescription>
            </Alert>
          )}

          {/* Main Camera Scanner Button */}
          {!showTextFallback && (
            <div className="space-y-4">
              <Button 
                onClick={startScanning}
                className="w-full bg-blue-600 hover:bg-blue-700 py-6 text-lg"
                disabled={loading}
                data-testid="camera-scanner-button"
              >
                <Camera className="w-6 h-6 mr-3" />
                Open Camera Scanner
              </Button>
              
              {!cameraError && (
                <div className="text-center">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => setShowTextFallback(true)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    Having trouble? Use text input instead
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Text Input Fallback */}
          {showTextFallback && (
            <div className="space-y-4">
              {cameraError && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>Camera unavailable:</strong> Please make sure camera permissions are enabled or use the text input below.
                  </p>
                </div>
              )}
              
              <form onSubmit={handleTextSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="qr_input">QR Code Data</Label>
                  <Input
                    id="qr_input"
                    type="text"
                    value={qrInput}
                    onChange={(e) => setQrInput(e.target.value)}
                    placeholder="Paste QR code data here"
                    required
                    data-testid="qr-input-field"
                    className="mt-1"
                  />
                </div>

                <div className="flex space-x-2">
                  <Button 
                    type="submit" 
                    className="flex-1 bg-green-600 hover:bg-green-700" 
                    disabled={loading}
                    data-testid="mark-attendance-button"
                  >
                    {loading ? "Marking Attendance..." : "Mark Attendance"}
                  </Button>
                  
                  {!cameraError && (
                    <Button 
                      type="button"
                      variant="outline" 
                      onClick={() => setShowTextFallback(false)}
                      disabled={loading}
                    >
                      Back to Camera
                    </Button>
                  )}
                </div>
              </form>
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>How to use:</strong> Tap "Open Camera Scanner" to scan QR codes directly with your camera. 
              Position the QR code within the square outline for automatic detection.
            </p>
          </div>
        </CardContent>
      </Card>
    </>
  );
};

// Full-screen QR Camera Scanner Component
const QRCameraScanner = ({ onScanSuccess, onClose, onError }) => {
  const videoRef = useRef(null);
  const scannerRef = useRef(null);
  const [isScanning, setIsScanning] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [hasFlash, setHasFlash] = useState(false);

  useEffect(() => {
    let scanner = null;
    
    const startScanner = async () => {
      if (!videoRef.current) return;

      try {
        // Check if QrScanner is supported
        const hasCamera = await QrScanner.hasCamera();
        if (!hasCamera) {
          throw new Error("No camera found");
        }

        scanner = new QrScanner(
          videoRef.current,
          (result) => {
            if (result && result.data) {
              setIsScanning(false);
              onScanSuccess(result.data);
            }
          },
          {
            returnDetailedScanResult: true,
            highlightScanRegion: true,
            highlightCodeOutline: true,
            preferredCamera: 'environment', // Use back camera
            maxScansPerSecond: 5,
          }
        );

        await scanner.start();
        setIsScanning(true);
        scannerRef.current = scanner;

        // Check if flash is available
        if (scanner._qrEnginePromise) {
          try {
            const capabilities = await scanner._getCameraStream().getVideoTracks()[0].getCapabilities?.();
            setHasFlash(capabilities?.torch === true);
          } catch (e) {
            // Flash not available
          }
        }

      } catch (error) {
        console.error("Scanner error:", error);
        onError();
      }
    };

    startScanner();

    return () => {
      if (scanner) {
        scanner.stop();
        scanner.destroy();
      }
    };
  }, [onScanSuccess, onError]);

  const handleZoomChange = (newZoom) => {
    setZoomLevel(newZoom);
    if (scannerRef.current) {
      try {
        const stream = scannerRef.current._getCameraStream();
        const track = stream.getVideoTracks()[0];
        const capabilities = track.getCapabilities();
        
        if (capabilities.zoom) {
          track.applyConstraints({
            advanced: [{ zoom: newZoom }]
          });
        }
      } catch (error) {
        console.warn("Zoom not supported:", error);
      }
    }
  };

  const handleClose = () => {
    if (scannerRef.current) {
      scannerRef.current.stop();
      scannerRef.current.destroy();
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black">
      {/* Video Element */}
      <video 
        ref={videoRef}
        className="w-full h-full object-cover"
        playsInline
        muted
      />
      
      {/* Overlay with scanning area */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top overlay */}
        <div className="absolute top-0 left-0 right-0 bg-black bg-opacity-50 h-1/4"></div>
        
        {/* Bottom overlay */}
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 h-1/4"></div>
        
        {/* Left overlay */}
        <div className="absolute top-1/4 bottom-1/4 left-0 bg-black bg-opacity-50 w-1/8"></div>
        
        {/* Right overlay */}
        <div className="absolute top-1/4 bottom-1/4 right-0 bg-black bg-opacity-50 w-1/8"></div>
        
        {/* Center scanning square outline */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 border-4 border-white rounded-lg pointer-events-none">
          <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-blue-500 rounded-tl-lg"></div>
          <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-blue-500 rounded-tr-lg"></div>
          <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-blue-500 rounded-bl-lg"></div>
          <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-blue-500 rounded-br-lg"></div>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-center pointer-events-auto">
        <Button
          onClick={handleClose}
          variant="ghost"
          size="sm"
          className="text-white bg-black bg-opacity-50 hover:bg-opacity-70 rounded-full p-2"
        >
          <X className="w-6 h-6" />
        </Button>
        
        <div className="text-white bg-black bg-opacity-50 px-3 py-1 rounded-full text-sm">
          {isScanning ? "Scanning..." : "Starting camera..."}
        </div>
      </div>

      {/* Bottom Controls */}
      <div className="absolute bottom-4 left-4 right-4 pointer-events-auto">
        <div className="flex justify-center items-center space-x-4">
          {/* Zoom Controls */}
          <div className="flex items-center space-x-2 bg-black bg-opacity-50 rounded-full px-4 py-2">
            <Button
              onClick={() => handleZoomChange(1)}
              variant="ghost"
              size="sm"
              className={`text-white px-3 py-1 rounded-full ${zoomLevel === 1 ? 'bg-blue-600' : ''}`}
            >
              1x
            </Button>
            <Button
              onClick={() => handleZoomChange(2)}
              variant="ghost"
              size="sm"
              className={`text-white px-3 py-1 rounded-full ${zoomLevel === 2 ? 'bg-blue-600' : ''}`}
            >
              2x
            </Button>
            <Button
              onClick={() => handleZoomChange(3)}
              variant="ghost"
              size="sm"
              className={`text-white px-3 py-1 rounded-full ${zoomLevel === 3 ? 'bg-blue-600' : ''}`}
            >
              3x
            </Button>
          </div>
        </div>
        
        <div className="text-center mt-4">
          <p className="text-white text-sm bg-black bg-opacity-50 inline-block px-3 py-1 rounded-full">
            Position QR code within the square to scan
          </p>
        </div>
      </div>
    </div>
  );
};

const QRSessionsList = ({ sessions }) => {
  return (
    <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
      <CardHeader>
        <CardTitle>Active QR Sessions</CardTitle>
      </CardHeader>
      <CardContent>
        {sessions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No QR sessions found.</p>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.id} className="border rounded-lg p-4 bg-white/50">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-medium">{session.subject}</h3>
                    <p className="text-sm text-gray-600">
                      {session.class_section} • {session.time_slot}
                    </p>
                  </div>
                  <Badge variant={session.is_active ? "default" : "secondary"}>
                    {session.is_active ? "Active" : "Expired"}
                  </Badge>
                </div>
                <p className="text-xs text-gray-500">
                  Created: {new Date(session.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const AttendanceList = ({ records }) => {
  return (
    <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
      <CardHeader>
        <CardTitle>Attendance Records</CardTitle>
      </CardHeader>
      <CardContent>
        {records.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No attendance records found.</p>
        ) : (
          <div className="space-y-4">
            {records.map((record) => (
              <div key={record.id} className="border rounded-lg p-4 bg-white/50">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">{record.subject}</h3>
                    <p className="text-sm text-gray-600">
                      Student: {record.student_name} ({record.student_id})
                    </p>
                    <p className="text-sm text-gray-600">
                      {record.class_section} • {record.time_slot}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge className="bg-green-600">Present</Badge>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(record.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const TimetableView = ({ timetable }) => {
  // Ensure timetable is an object and not null/undefined
  const safeTimatable = timetable || {};
  const days = Object.keys(safeTimatable);

  return (
    <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
      <CardHeader>
        <CardTitle>Weekly Timetable</CardTitle>
      </CardHeader>
      <CardContent>
        {days.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No timetable data available.</p>
        ) : (
          <div className="space-y-6">
            {days.map((day) => {
              // Ensure timetable[day] is an array before mapping
              const daySchedule = Array.isArray(safeTimatable[day]) ? safeTimatable[day] : [];
              
              return (
                <div key={day} className="border rounded-lg p-4 bg-white/50">
                  <h3 className="font-bold text-lg mb-3 text-indigo-700">{day}</h3>
                  <div className="grid gap-2">
                    {daySchedule.length === 0 ? (
                      <p className="text-gray-400 text-sm">No classes scheduled</p>
                    ) : (
                      daySchedule.map((period, index) => (
                        <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="font-medium text-sm">{period.time || 'N/A'}</span>
                          <span className="text-sm text-gray-600">{period.subject || 'N/A'}</span>
                          <div className="flex space-x-1">
                            {period.class && (
                              <Badge variant="outline" className="text-xs">
                                {period.class}
                              </Badge>
                            )}
                            {period.section && (
                              <Badge className="text-xs bg-indigo-600">
                                {period.section}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Role Tag Component
const RoleTag = ({ role }) => {
  const tagStyles = {
    teacher: "bg-blue-500/20 text-blue-800 border-blue-300",
    principal: "bg-green-500/20 text-green-800 border-green-300",
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${tagStyles[role] || 'bg-gray-500/20 text-gray-800 border-gray-300'}`}>
      {role}
    </span>
  );
};

// Announcement Section Component
const AnnouncementSection = ({ announcements, onAnnouncementCreated, userRole }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);

  return (
    <div className="space-y-6">
      {(userRole === "teacher" || userRole === "principal") && (
        <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Manage Announcements</CardTitle>
              <Button 
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Announcement
              </Button>
            </div>
          </CardHeader>
          {showCreateForm && (
            <CardContent>
              <CreateAnnouncementForm 
                onAnnouncementCreated={() => {
                  onAnnouncementCreated();
                  setShowCreateForm(false);
                }}
                onCancel={() => setShowCreateForm(false)}
              />
            </CardContent>
          )}
        </Card>
      )}

      <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Megaphone className="w-5 h-5 mr-2" />
            Announcements
          </CardTitle>
        </CardHeader>
        <CardContent>
          {announcements.length === 0 ? (
            <div className="text-center py-8">
              <Megaphone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No announcements yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {announcements.map((announcement) => (
                <AnnouncementCard key={announcement.id} announcement={announcement} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Create Announcement Form Component
const CreateAnnouncementForm = ({ onAnnouncementCreated, onCancel }) => {
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    target_audience: "all",
    image_data: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        // Convert to base64 (remove data:image/...;base64, prefix)
        const base64String = reader.result.split(',')[1];
        setFormData({ ...formData, image_data: base64String });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await axios.post(`${API}/announcements`, formData, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      onAnnouncementCreated();
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to create announcement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
            className="mt-1"
            placeholder="Enter announcement title"
          />
        </div>

        <div>
          <Label htmlFor="content">Content</Label>
          <textarea
            id="content"
            rows="4"
            className="w-full mt-1 p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            required
            placeholder="Write your announcement here..."
          />
        </div>

        <div>
          <Label htmlFor="target_audience">Target Audience</Label>
          <Select 
            value={formData.target_audience} 
            onValueChange={(value) => setFormData({ ...formData, target_audience: value })}
          >
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select target audience" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Users</SelectItem>
              <SelectItem value="students">Students Only</SelectItem>
              <SelectItem value="teachers">Teachers Only</SelectItem>
              <SelectItem value="A5">Class A5 Only</SelectItem>
              <SelectItem value="A6">Class A6 Only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="image">Image (Optional)</Label>
          <Input
            id="image"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="mt-1"
          />
          {formData.image_data && (
            <div className="mt-2">
              <p className="text-sm text-green-600">✓ Image selected</p>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-3">
          <Button 
            type="button" 
            variant="outline" 
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            className="bg-indigo-600 hover:bg-indigo-700" 
            disabled={loading}
          >
            {loading ? "Creating..." : "Create Announcement"}
          </Button>
        </div>
      </form>
    </div>
  );
};

// Announcement Card Component
const AnnouncementCard = ({ announcement }) => {
  return (
    <div className="border rounded-lg p-6 bg-white/50 hover:bg-white/70 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-semibold text-gray-900">{announcement.title}</h3>
        </div>
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <span>{new Date(announcement.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="mb-3">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>by</span>
          <span className="font-medium">{announcement.author_name}</span>
          <RoleTag role={announcement.author_role} />
        </div>
      </div>

      <div className="prose prose-sm max-w-none mb-4">
        <p className="text-gray-700 whitespace-pre-wrap">{announcement.content}</p>
      </div>

      {announcement.image_data && (
        <div className="mb-4">
          <img
            src={`data:image/jpeg;base64,${announcement.image_data}`}
            alt="Announcement"
            className="max-w-full h-auto rounded-lg shadow-md"
            style={{ maxHeight: '300px' }}
          />
        </div>
      )}

      <div className="flex justify-between items-center text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-xs">
            Target: {announcement.target_audience}
          </Badge>
        </div>
        <div>
          {announcement.updated_at !== announcement.created_at && (
            <span>Updated {new Date(announcement.updated_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>
    </div>
  );
};

// Timetable Management Component for Principals
const TimetableManagement = ({ timetable, onTimetableUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editableTimetable, setEditableTimetable] = useState(timetable);

  useEffect(() => {
    setEditableTimetable(timetable);
  }, [timetable]);

  return (
    <Card className="bg-white/80 backdrop-blur-sm shadow-lg">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Timetable Management</CardTitle>
          <Button
            onClick={() => setIsEditing(!isEditing)}
            variant={isEditing ? "destructive" : "default"}
            className={isEditing ? "" : "bg-indigo-600 hover:bg-indigo-700"}
          >
            <Edit className="w-4 h-4 mr-2" />
            {isEditing ? "Cancel" : "Edit Timetable"}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isEditing ? (
          <div className="space-y-4">
            <Alert className="border-orange-200 bg-orange-50">
              <AlertDescription className="text-orange-800">
                <strong>Note:</strong> Timetable editing is a complex feature that would require a comprehensive form. 
                For now, this shows the structure. In a full implementation, you would have detailed forms for each day/section/period.
              </AlertDescription>
            </Alert>
            <div className="flex space-x-3">
              <Button 
                onClick={() => {
                  // Here you would save the timetable changes
                  setIsEditing(false);
                  onTimetableUpdate();
                }} 
                className="bg-green-600 hover:bg-green-700"
              >
                Save Changes
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : null}
        <TimetableView timetable={timetable} />
      </CardContent>
    </Card>
  );
};

// Emergency Alert Modal Component
const EmergencyAlertModal = ({ onClose, user }) => {
  const [alertType, setAlertType] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await axios.post(`${API}/emergency-alerts`, {
        alert_type: alertType,
        description: description || null
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      
      setSuccess("Emergency alert sent successfully!");
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to send emergency alert");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4 shadow-2xl border-red-200">
        <CardHeader className="bg-red-50 border-b border-red-200">
          <CardTitle className="text-red-800 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Emergency Alert
          </CardTitle>
          <p className="text-sm text-red-600">This will notify all teachers and the principal immediately</p>
        </CardHeader>
        <CardContent className="p-6">
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <AlertDescription className="text-green-800">{success}</AlertDescription>
            </Alert>
          )}

          {!success && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label className="text-sm font-semibold text-gray-700">Emergency Type</Label>
                <div className="mt-2 space-y-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="fire"
                      value="fire"
                      checked={alertType === "fire"}
                      onChange={(e) => setAlertType(e.target.value)}
                      className="text-red-600"
                      required
                    />
                    <Label htmlFor="fire" className="font-normal">🔥 Fire Emergency</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="unauthorized_access"
                      value="unauthorized_access"
                      checked={alertType === "unauthorized_access"}
                      onChange={(e) => setAlertType(e.target.value)}
                      className="text-red-600"
                      required
                    />
                    <Label htmlFor="unauthorized_access" className="font-normal">🚨 Unauthorized Access</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id="other"
                      value="other"
                      checked={alertType === "other"}
                      onChange={(e) => setAlertType(e.target.value)}
                      className="text-red-600"
                      required
                    />
                    <Label htmlFor="other" className="font-normal">⚠️ Other Emergency</Label>
                  </div>
                </div>
              </div>

              {alertType === "other" && (
                <div>
                  <Label htmlFor="description">Description*</Label>
                  <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Please describe the emergency..."
                    className="w-full mt-1 p-3 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
                    rows="3"
                    required={alertType === "other"}
                  />
                </div>
              )}

              <div className="flex space-x-3 pt-4">
                <Button 
                  type="submit" 
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold" 
                  disabled={loading}
                  data-testid="send-alert-button"
                >
                  {loading ? "Sending..." : "Send Alert"}
                </Button>
                <Button 
                  type="button" 
                  onClick={onClose}
                  variant="outline"
                  className="flex-1"
                  data-testid="cancel-alert-button"
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Emergency Alerts History Component
const EmergencyAlertsHistory = ({ onClose, user }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/emergency-alerts`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setAlerts(response.data);
    } catch (error) {
      setError("Failed to fetch emergency alerts");
    } finally {
      setLoading(false);
    }
  };

  const updateAlertStatus = async (alertId, status) => {
    try {
      await axios.put(`${API}/emergency-alerts/${alertId}/status`, {
        status: status
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      
      // Refresh alerts
      fetchAlerts();
    } catch (error) {
      console.error("Failed to update alert status:", error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "pending": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "acknowledged": return "bg-blue-100 text-blue-800 border-blue-200";
      case "resolved": return "bg-green-100 text-green-800 border-green-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getAlertTypeIcon = (alertType) => {
    switch (alertType) {
      case "fire": return "🔥";
      case "unauthorized_access": return "🚨";
      case "other": return "⚠️";
      default: return "❗";
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl max-h-[80vh] mx-4 shadow-2xl">
        <CardHeader className="bg-gray-50 border-b">
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center text-gray-800">
              <Shield className="w-5 h-5 mr-2" />
              Emergency Alerts History
            </CardTitle>
            <Button
              onClick={onClose}
              variant="outline"
              size="sm"
              data-testid="close-alerts-history"
            >
              ✕
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-y-auto max-h-[60vh]">
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <span className="ml-2">Loading alerts...</span>
              </div>
            ) : error ? (
              <div className="p-6">
                <Alert className="border-red-200 bg-red-50">
                  <AlertDescription className="text-red-800">{error}</AlertDescription>
                </Alert>
              </div>
            ) : alerts.length === 0 ? (
              <div className="text-center p-8 text-gray-500">
                <Shield className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No emergency alerts found</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {alerts.map((alert) => (
                  <div key={alert.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-2xl">{getAlertTypeIcon(alert.alert_type)}</span>
                          <div>
                            <h4 className="font-semibold text-gray-900 capitalize">
                              {alert.alert_type.replace('_', ' ')} Emergency
                            </h4>
                            <p className="text-sm text-gray-600">
                              By {alert.student_name} ({alert.class_section})
                            </p>
                          </div>
                        </div>
                        
                        {alert.description && (
                          <p className="text-sm text-gray-700 mb-2 pl-11">
                            {alert.description}
                          </p>
                        )}
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-500 pl-11">
                          <span>Created: {new Date(alert.created_at).toLocaleString()}</span>
                          {alert.resolved_at && (
                            <span>Resolved by: {alert.resolver_name}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end space-y-2">
                        <Badge className={`${getStatusColor(alert.status)} text-xs px-2 py-1`}>
                          {alert.status.toUpperCase()}
                        </Badge>
                        
                        {user.role === "principal" && alert.status !== "resolved" && (
                          <div className="flex space-x-1">
                            {alert.status === "pending" && (
                              <Button
                                onClick={() => updateAlertStatus(alert.id, "acknowledged")}
                                size="sm"
                                variant="outline"
                                className="text-xs px-2 py-1 h-6"
                              >
                                Acknowledge
                              </Button>
                            )}
                            <Button
                              onClick={() => updateAlertStatus(alert.id, "resolved")}
                              size="sm"
                              className="text-xs px-2 py-1 h-6 bg-green-600 hover:bg-green-700"
                            >
                              Resolve
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default App;
