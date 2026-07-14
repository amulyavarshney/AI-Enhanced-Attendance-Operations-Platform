import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { Employee, Role } from "@/types/models";
import { authApi, clearAuthToken, getAuthToken, setAuthToken } from "@/services/apiClient";

interface AuthContextValue {
  token: string | null;
  employee: Employee | null;
  isAuthenticated: boolean;
  role: Role | null;
  isAdmin: boolean;
  canManage: boolean;
  canUseAI: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const EMPLOYEE_STORAGE_KEY = "attendance_auth_employee";

function loadStoredEmployee(): Employee | null {
  try {
    const raw = localStorage.getItem(EMPLOYEE_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Employee) : null;
  } catch {
    return null;
  }
}

function normalizeRole(role: Employee["role"] | undefined | null): Role | null {
  if (!role) return null;
  const value = String(role).toLowerCase();
  if (value === Role.ADMIN) return Role.ADMIN;
  if (value === Role.MANAGER) return Role.MANAGER;
  if (value === Role.EMPLOYEE) return Role.EMPLOYEE;
  return null;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [employee, setEmployee] = useState<Employee | null>(() => loadStoredEmployee());

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setAuthToken(response.access_token);
    localStorage.setItem(EMPLOYEE_STORAGE_KEY, JSON.stringify(response.employee));
    setToken(response.access_token);
    setEmployee(response.employee);
  }, []);

  const logout = useCallback(() => {
    clearAuthToken();
    localStorage.removeItem(EMPLOYEE_STORAGE_KEY);
    setToken(null);
    setEmployee(null);
  }, []);

  const role = normalizeRole(employee?.role);
  const isAdmin = role === Role.ADMIN;
  const canManage = role === Role.ADMIN || role === Role.MANAGER;
  const canUseAI = canManage;

  const value = useMemo(
    () => ({
      token,
      employee,
      isAuthenticated: Boolean(token),
      role,
      isAdmin,
      canManage,
      canUseAI,
      login,
      logout,
    }),
    [token, employee, role, isAdmin, canManage, canUseAI, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
