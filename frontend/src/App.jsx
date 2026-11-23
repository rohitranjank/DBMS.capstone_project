import { createContext, useContext, useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import api, { resetCsrf } from "./api";
import { Spinner } from "./ui.jsx";
import { Landing, Login, Register } from "./pages.jsx";
import { StudentDashboard, Submit, MyComplaints } from "./student.jsx";
import { AdminDashboard, AdminComplaints, Departments } from "./admin.jsx";
import Detail from "./Detail.jsx";
import Profile from "./Profile.jsx";

const Auth = createContext(null);
export const useAuth = () => useContext(Auth);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null), [loading, setLoading] = useState(true);
  useEffect(() => { api.get("/auth/me").then((r) => setUser(r.data.data)).catch(() => setUser(null)).finally(() => setLoading(false)); }, []);
  const logout = async () => { await api.post("/auth/logout").catch(() => {}); resetCsrf(); setUser(null); };
  return <Auth.Provider value={{ user, setUser, logout, loading }}>{children}</Auth.Provider>;
}

// Route guard for usability only - the server enforces real authorization.
function Guard({ role }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to={role === "admin" ? "/admin/login" : "/login"} replace />;
  if (user.role !== role) return <Navigate to={user.role === "admin" ? "/admin" : "/student"} replace />;
  return <Shell role={role} />;
}

function Shell({ role }) {
  const { user, logout } = useAuth(), nav = useNavigate();
  const links = role === "admin" ? [["/admin", "Dashboard"], ["/admin/complaints", "Complaints"], ["/admin/departments", "Departments"], ["/admin/profile", "Profile"]]
    : [["/student", "Dashboard"], ["/student/submit", "Submit complaint"], ["/student/complaints", "My complaints"], ["/student/profile", "Profile"]];
  return <div className="shell"><aside><div className="brand"><img className="logo" src="/krmu-logo.png" alt="" /><h1>KRMU Campus Care</h1></div><nav>{links.map(([to, t]) => <NavLink key={to} to={to} end={to.split("/").length === 2}>{t}</NavLink>)}</nav>
    <div className="who"><small>{user.name}</small><button className="btn ghost light" onClick={async () => { await logout(); nav("/"); }}>Log out</button></div></aside>
    <main><Outlet /></main></div>;
}

export default function App() {
  return <AuthProvider><Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/login" element={<Login role="student" />} />
    <Route path="/register" element={<Register />} />
    <Route path="/admin/login" element={<Login role="admin" />} />
    <Route path="/student" element={<Guard role="student" />}>
      <Route index element={<StudentDashboard />} /><Route path="submit" element={<Submit />} />
      <Route path="complaints" element={<MyComplaints />} /><Route path="complaints/:id" element={<Detail />} /><Route path="profile" element={<Profile />} /></Route>
    <Route path="/admin" element={<Guard role="admin" />}>
      <Route index element={<AdminDashboard />} /><Route path="complaints" element={<AdminComplaints />} />
      <Route path="complaints/:id" element={<Detail admin />} /><Route path="departments" element={<Departments />} /><Route path="profile" element={<Profile />} /></Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></AuthProvider>;
}
