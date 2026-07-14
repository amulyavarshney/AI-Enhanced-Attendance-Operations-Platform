import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Routes, Route } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Employees from "./pages/Employees";
import AttendancePage from "./pages/Attendance";
import Teams from "./pages/Teams";
import Analytics from "./pages/Analytics";
import AIInsights from "./pages/AIInsights";
import AuditLogs from "./pages/AuditLogs";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./context/AuthContext";

const queryClient = new QueryClient();

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const RoleRoute: React.FC<{
  children: React.ReactNode;
  allow: (auth: ReturnType<typeof useAuth>) => boolean;
}> = ({ children, allow }) => {
  const auth = useAuth();
  if (!allow(auth)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }
    >
      <Route index element={<Dashboard />} />
      <Route path="employees" element={<Employees />} />
      <Route path="attendance" element={<AttendancePage />} />
      <Route path="teams" element={<Teams />} />
      <Route path="analytics" element={
        <RoleRoute allow={(auth) => auth.canManage}>
          <Analytics />
        </RoleRoute>
      } />
      <Route
        path="ai-insights"
        element={
          <RoleRoute allow={(auth) => auth.canUseAI}>
            <AIInsights />
          </RoleRoute>
        }
      />
      <Route
        path="audit-logs"
        element={
          <RoleRoute allow={(auth) => auth.isAdmin}>
            <AuditLogs />
          </RoleRoute>
        }
      />
    </Route>
    <Route path="*" element={<NotFound />} />
  </Routes>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
