import axios from 'axios';
import { 
  Employee, 
  Team, 
  Attendance, 
  AIInsight, 
  TeamTrends,
} from '@/types/models';

// Configure axios instance
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_DEV_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const buildQueryParams = (params: Record<string, number | string | undefined>): string => {
  const validParams = Object.entries(params)
    .filter(([_, value]) => value !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');
  
  return validParams ? `?${validParams}` : '';
};

// Employee API
export const employeeApi = {
  getEmployees: async (): Promise<Employee[]> => {
    const response = await apiClient.get<Employee[]>('/employees');
    return response.data;
  },
  
  getEmployeeById: async (id: string): Promise<Employee> => {
    const response = await apiClient.get<Employee>(`/employees/${id}`);
    return response.data;
  },
  
  createEmployee: async (employee: Omit<Employee, 'id' | 'createdAt' | 'updatedAt'>): Promise<Employee> => {
    const response = await apiClient.post<Employee>('/employees', employee);
    return response.data;
  },
  
  updateEmployee: async (id: string, employee: Partial<Omit<Employee, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Employee> => {
    const response = await apiClient.put<Employee>(`/employees/${id}`, employee);
    return response.data;
  },
  
  deleteEmployee: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/employees/${id}`);
    return response.data;
  },

  getAttendanceByEmployeeId: async (employeeId: string, startDate?: string, endDate?: string): Promise<Attendance[]> => {
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
  
  getTeamById: async (id: string): Promise<Team> => {
    const response = await apiClient.get<Team>(`/teams/${id}`);
    return response.data;
  },
  
  createTeam: async (team: Omit<Team, 'id' | 'createdAt' | 'updatedAt'>): Promise<Team> => {
    const response = await apiClient.post<Team>('/teams', team);
    return response.data;
  },
  
  updateTeam: async (id: string, team: Partial<Omit<Team, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Team> => {
    const response = await apiClient.put<Team>(`/teams/${id}`, team);
    return response.data;
  },
  
  deleteTeam: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/teams/${id}`);
    return response.data;
  },

  getEmployeesByTeamId: async (teamId: string): Promise<Employee[]> => {
    const response = await apiClient.get<Employee[]>(`/teams/${teamId}/employees`);
    return response.data;
  },

  getAttendanceByTeamId: async (teamId: string, startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const endpoint = `/teams/${teamId}/attendance` + buildQueryParams(params);
    const response = await apiClient.get<Attendance[]>(endpoint);
    return response.data;
  },

  getAttendenceTrendsByTeamId: async (teamId: string, startDate?: string, endDate?: string): Promise<TeamTrends[]> => {
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
  
  getAttendanceById: async (id: string): Promise<Attendance> => {
    const response = await apiClient.get<Attendance>(`/attendance/${id}`);
    return response.data;
  },
  
  createAttendance: async (attendance: Omit<Attendance, 'id' | 'createdAt' | 'updatedAt'>): Promise<Attendance> => {
    const response = await apiClient.post<Attendance>('/attendance', attendance);
    return response.data;
  },
  
  updateAttendance: async (id: string, attendance: Partial<Omit<Attendance, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Attendance> => {
    const response = await apiClient.put<Attendance>(`/attendance/${id}`, attendance);
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

// // Dashboard API
// export const dashboardApi = {
//   getDashboardStats: async (): Promise<DashboardStats> => {
//     const response = await apiClient.get<DashboardStats>('/dashboard/stats');
//     return response.data;
//   },
  
//   getAttendanceTrendChartData: async (): Promise<ChartData> => {
//     const response = await apiClient.get<ChartData>('/dashboard/charts/attendance-trend');
//     return response.data;
//   },
  
//   getTodayAttendancePieChartData: async (): Promise<ChartData> => {
//     const response = await apiClient.get<ChartData>('/dashboard/charts/today-attendance');
//     return response.data;
//   },
  
//   getTeamComparisonChartData: async (): Promise<ChartData> => {
//     const response = await apiClient.get<ChartData>('/dashboard/charts/team-comparison');
//     return response.data;
//   }
// };

// // Notification API
// export const notificationApi = {
//   getNotifications: async (userId: string): Promise<Notification[]> => {
//     const response = await apiClient.get<Notification[]>(`/notifications?userId=${userId}`);
//     return response.data;
//   },
  
//   markAsRead: async (notificationId: string): Promise<Notification> => {
//     const response = await apiClient.put<Notification>(`/notifications/${notificationId}/read`);
//     return response.data;
//   },
  
//   markAllAsRead: async (userId: string): Promise<{ message: string }> => {
//     const response = await apiClient.put<{ message: string }>(`/notifications/read-all?userId=${userId}`);
//     return response.data;
//   },
  
//   deleteNotification: async (notificationId: string): Promise<{ message: string }> => {
//     const response = await apiClient.delete<{ message: string }>(`/notifications/${notificationId}`);
//     return response.data;
//   }
// };

// // Audit Log API
// export const auditApi = {
//   getAuditLogs: async (limit: number = 50, skip: number = 0): Promise<AuditLog[]> => {
//     const response = await apiClient.get<AuditLog[]>(`/audit-logs?limit=${limit}&skip=${skip}`);
//     return response.data;
//   },
  
//   getUserAuditLogs: async (userId: string): Promise<AuditLog[]> => {
//     const response = await apiClient.get<AuditLog[]>(`/audit-logs?userId=${userId}`);
//     return response.data;
//   }
// };

// // Error handling interceptor
// apiClient.interceptors.response.use(
//   response => response,
//   error => {
//     if (axios.isAxiosError(error) && error.response) {
//       // Extract the detail message from the API error response
//       const errorMessage = error.response.data?.message || 'An error occurred';
//       return Promise.reject(new Error(errorMessage));
//     }
//     return Promise.reject(error);
//   }
// );

export default apiClient;
