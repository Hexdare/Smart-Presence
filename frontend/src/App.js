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
import { QrCode, Users, Calendar, LogOut, Camera, CheckCircle, Clock, User, Megaphone, Plus, Edit, Trash2, Eye } from "lucide-react";
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
    <div className="space-y-6">
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
    </div>
  );
};

const PrincipalDashboard = ({ user }) => {
  const [activeTab, setActiveTab] = useState("announcements");
  const [qrSessions, setQrSessions] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [timetable, setTimetable] = useState({});
  const [announcements, setAnnouncements] = useState([]);

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
    <div className="space-y-6">
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
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Student Dashboard</h2>
        <p className="mt-2 text-gray-600">Scan QR codes to mark your attendance</p>
        <Badge className="mt-2 bg-indigo-600">{user.class_section}</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-white/60 backdrop-blur-sm">
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
    </div>
  );
};

const QRScannerCard = ({ onAttendanceMarked }) => {
  const [qrInput, setQrInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await axios.post(`${API}/attendance/mark`, { qr_data: qrInput }, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setSuccess("Attendance marked successfully!");
      setQrInput("");
      onAttendanceMarked();
    } catch (error) {
      setError(error.response?.data?.detail || "Failed to mark attendance");
    } finally {
      setLoading(false);
    }
  };

  return (
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

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="qr_input">QR Code Data</Label>
            <Input
              id="qr_input"
              type="text"
              value={qrInput}
              onChange={(e) => setQrInput(e.target.value)}
              placeholder="Paste QR code data here or scan with camera"
              required
              data-testid="qr-input-field"
              className="mt-1"
            />
          </div>

          <Button 
            type="submit" 
            className="w-full bg-green-600 hover:bg-green-700" 
            disabled={loading}
            data-testid="mark-attendance-button"
          >
            {loading ? "Marking Attendance..." : "Mark Attendance"}
          </Button>
        </form>

        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>How to use:</strong> Ask your teacher to show the QR code, then copy the QR data and paste it above. 
            In future versions, you'll be able to use your camera to scan directly.
          </p>
        </div>
      </CardContent>
    </Card>
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

export default App;
