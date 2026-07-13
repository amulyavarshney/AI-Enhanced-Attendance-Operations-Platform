import axios from 'axios';
import { 
  Employee, 
  Team, 
  Attendance, 
  AIInsight, 
  TeamTrends,
} from '@/types/models';

const TOKEN_STORAGE_KEY = 'attendance_auth_token';

export const getAuthToken = (): string | null => localStorage.getItem(TOKEN_STORAGE_KEY);

export const setAuthToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

export const clearAuthToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

// Configure axios instance
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthToken();
      localStorage.removeItem('attendance_auth_employee');
      if (window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  }
);

const buildQueryParams = (params: Record<string, number | string | undefined | null>): string => {
  const validParams = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
  
  return validParams ? `?${validParams}` : '';
};

export interface TokenResponse {
  access_token: string;
  token_type: string;
  employee: Employee;
}

export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    return response.data;
  },
  me: async (): Promise<{ employee: Employee }> => {
    const response = await apiClient.get<{ employee: Employee }>('/auth/me');
    return response.data;
  },
};

// Employee API
export const employeeApi = {
  getEmployees: async (): Promise<Employee[]> => {
    const response = await apiClient.get<Employee[]>('/employees');
    return response.data;
  },
  
  getEmployeeById: async (id: number): Promise<Employee> => {
    const response = await apiClient.get<Employee>(`/employees/${id}`);
    return response.data;
  },
  
  createEmployee: async (employee: Omit<Employee, 'id' | 'createdAt' | 'updatedAt'>): Promise<Employee> => {
    const response = await apiClient.post<Employee>('/employees', employee);
    return response.data;
  },
  
  updateEmployee: async (id: number, employee: Partial<Omit<Employee, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Employee> => {
    const response = await apiClient.put<Employee>(`/employees/${id}`, employee);
    return response.data;
  },
  
  deleteEmployee: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/employees/${id}`);
    return response.data;
  },

  getAttendanceByEmployeeId: async (employeeId: number, startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const endpoint = `/employees/${employeeId}/attendance` + buildQueryParams(params);
    const response = await apiClient.get<Attendance[]>(endpoint);
    return response.data;
  }
};

// Team API
export const teamApi = {
  getTeams: async (): Promise<Team[]> => {
    const response = await apiClient.get<Team[]>('/teams');
    return response.data;
  },
  
  getTeamById: async (id: number): Promise<Team> => {
    const response = await apiClient.get<Team>(`/teams/${id}`);
    return response.data;
  },
  
  createTeam: async (team: Omit<Team, 'id' | 'createdAt' | 'updatedAt'>): Promise<Team> => {
    const response = await apiClient.post<Team>('/teams', team);
    return response.data;
  },
  
  updateTeam: async (id: number, team: Partial<Omit<Team, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Team> => {
    const response = await apiClient.put<Team>(`/teams/${id}`, team);
    return response.data;
  },
  
  deleteTeam: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/teams/${id}`);
    return response.data;
  },

  getEmployeesByTeamId: async (teamId: number): Promise<Employee[]> => {
    const response = await apiClient.get<Employee[]>(`/teams/${teamId}/employees`);
    return response.data;
  },

  getAttendanceByTeamId: async (teamId: number, startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const endpoint = `/teams/${teamId}/attendance` + buildQueryParams(params);
    const response = await apiClient.get<Attendance[]>(endpoint);
    return response.data;
  },

  getAttendenceTrendsByTeamId: async (teamId: number, startDate?: string, endDate?: string): Promise<TeamTrends[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const endpoint = `/teams/${teamId}/attendance/trends` + buildQueryParams(params);
    const response = await apiClient.get<TeamTrends[]>(endpoint);
    return response.data;
  },
};

// Attendance API
export const attendanceApi = {
  getAttendance: async (startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const endpoint = '/attendance' + buildQueryParams(params);
    const response = await apiClient.get<Attendance[]>(endpoint);
    return response.data;
  },
  
  getAttendanceById: async (id: number): Promise<Attendance> => {
    const response = await apiClient.get<Attendance>(`/attendance/${id}`);
    return response.data;
  },
  
  createAttendance: async (attendance: Omit<Attendance, 'id' | 'createdAt' | 'updatedAt'>): Promise<Attendance> => {
    const response = await apiClient.post<Attendance>('/attendance', attendance);
    return response.data;
  },
  
  updateAttendance: async (id: number, attendance: Partial<Omit<Attendance, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Attendance> => {
    const response = await apiClient.put<Attendance>(`/attendance/${id}`, attendance);
    return response.data;
  },

  deleteAttendance: async (id: number): Promise<void> => {
    await apiClient.delete(`/attendance/${id}`);
  },

  exportCsv: async (startDate?: string, endDate?: string, employeeId?: number): Promise<Blob> => {
    const params = { start_date: startDate, end_date: endDate, employee_id: employeeId };
    const response = await apiClient.get('/attendance/export' + buildQueryParams(params), {
      responseType: 'blob',
    });
    return response.data;
  },
};

// AI Insights API
export const insightApi = {
  getInsight: async (query: string): Promise<AIInsight> => {
    const params = { query: query };
    const endpoint = `/ai/insights` + buildQueryParams(params);
    const response = await apiClient.get<AIInsight>(endpoint);
    return response.data;
  },

  getAIInsights: async (limit: number = 10): Promise<AIInsight[]> => {
    const params = { limit: limit };
    const endpoint = `/ai/insights/history` + buildQueryParams(params);
    const response = await apiClient.get<AIInsight[]>(endpoint);
    return response.data;
  },
};

export interface DashboardStats {
  date: string;
  total_employees: number;
  total_teams: number;
  present_count: number;
  absent_count: number;
  wfh_count: number;
  half_day_count: number;
  leave_count: number;
  present_percentage: number;
  wfh_percentage: number;
  absent_percentage: number;
  records_today: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
  getTrends: async (startDate?: string, endDate?: string, teamId?: number): Promise<TeamTrends[]> => {
    const params = { start_date: startDate, end_date: endDate, team_id: teamId };
    const endpoint = '/dashboard/trends' + buildQueryParams(params);
    const response = await apiClient.get<TeamTrends[]>(endpoint);
    return response.data;
  },
};

export interface AuditLog {
  id: number;
  actor_id?: number | null;
  actor_email?: string | null;
  method: string;
  path: string;
  status_code: number;
  action: string;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export const auditApi = {
  getAuditLogs: async (limit = 50, skip = 0): Promise<AuditLog[]> => {
    const response = await apiClient.get<AuditLog[]>(
      '/audit-logs' + buildQueryParams({ limit, skip })
    );
    return response.data;
  },
};

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  created_at: string;
  source: string;
}

export const notificationApi = {
  getNotifications: async (limit = 20): Promise<NotificationItem[]> => {
    const response = await apiClient.get<NotificationItem[]>(
      '/notifications' + buildQueryParams({ limit })
    );
    return response.data;
  },
};

export const pagedApi = {
  getEmployees: async (skip = 0, limit = 50, teamId?: number, search?: string): Promise<PaginatedResponse<Employee>> => {
    const params = { skip, limit, team_id: teamId, search };
    const response = await apiClient.get<PaginatedResponse<Employee>>('/employees/page' + buildQueryParams(params));
    return response.data;
  },
  getTeams: async (skip = 0, limit = 50, search?: string): Promise<PaginatedResponse<Team>> => {
    const params = { skip, limit, search };
    const response = await apiClient.get<PaginatedResponse<Team>>('/teams/page' + buildQueryParams(params));
    return response.data;
  },
  getAttendance: async (
    skip = 0,
    limit = 50,
    startDate?: string,
    endDate?: string,
    employeeId?: number,
  ): Promise<PaginatedResponse<Attendance>> => {
    const params = { skip, limit, start_date: startDate, end_date: endDate, employee_id: employeeId };
    const response = await apiClient.get<PaginatedResponse<Attendance>>('/attendance/page' + buildQueryParams(params));
    return response.data;
  },
};

export default apiClient;
