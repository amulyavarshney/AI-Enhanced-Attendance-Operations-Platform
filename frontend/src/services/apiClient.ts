
import axios from 'axios';
import { 
  Employee, 
  Team, 
  Attendance, 
  AIInsight, 
  TeamTrend,
  DashboardStats, 
  ChartData,
  Notification,
  AuditLog
} from '@/types/models';

// Configure axios instance
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  
  createEmployee: async (employee: Omit<Employee, 'id'>): Promise<Employee> => {
    const response = await apiClient.post<Employee>('/employees', employee);
    return response.data;
  },
  
  updateEmployee: async (id: string, employee: Partial<Employee>): Promise<Employee> => {
    const response = await apiClient.put<Employee>(`/employees/${id}`, employee);
    return response.data;
  },
  
  deleteEmployee: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/employees/${id}`);
    return response.data;
  },

  getAttendanceByEmployeeId: async (employeeId: string, startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const response = await apiClient.get<Attendance[]>(`/employees/${employeeId}/attendance`, {
      params: { startDate, endDate }
    });
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
  
  updateTeam: async (id: string, team: Partial<Team>): Promise<Team> => {
    const response = await apiClient.put<Team>(`/teams/${id}`, team);
    return response.data;
  },
  
  deleteTeam: async (id: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/teams/${id}`);
    return response.data;
  },

  getEmployeeByTeamId: async (teamId: string): Promise<Employee[]> => {
    const response = await apiClient.get<Employee[]>(`/teams/${teamId}/employees`);
    return response.data;
  },

  getAttendanceByTeamId: async (teamId: string, startDate?: string, endDate?: string): Promise<Attendance[]> => {
    const response = await apiClient.get<Attendance[]>(`/teams/${teamId}/attendance`, {
      params: { startDate, endDate }
    });
    return response.data;
  },

  getAttendenceTrendsByTeamId: async (teamId: string, startDate?: string, endDate?: string): Promise<TeamTrend[]> => {
    const response = await apiClient.get<TeamTrend[]>(`/teams/${teamId}/attendance/trends`, {
      params: { startDate, endDate }
    });
    return response.data;
  },
};

// Attendance API
export const attendanceApi = {
  getAttendance: async (date?: string): Promise<Attendance[]> => {
    const url = date ? `/attendance?date=${date}` : '/attendance';
    const response = await apiClient.get<Attendance[]>(url);
    return response.data;
  },
  
  getAttendanceById: async (id: string, startDate?: string, endDate?: string): Promise<Attendance> => {
    const response = await apiClient.get<Attendance>(`/attendance/${id}`, {
      params: { startDate, endDate }
    });
    return response.data;
  },
  
  createAttendance: async (attendance: Omit<Attendance, 'id'>): Promise<Attendance> => {
    const response = await apiClient.post<Attendance>('/attendance', attendance);
    return response.data;
  },
  
  updateAttendance: async (id: string, attendance: Partial<Attendance>): Promise<Attendance> => {
    const response = await apiClient.put<Attendance>(`/attendance/${id}`, attendance);
    return response.data;
  },
};

// AI Insights API
export const insightApi = {
  getAIInsights: async (limit: number = 10): Promise<AIInsight[]> => {
    const response = await apiClient.get<AIInsight[]>(`/ai/insights/history`, {
      params: { limit }
    });
    return response.data;
  },
  
  getInsight: async (query: string): Promise<AIInsight> => {
    const response = await apiClient.get<AIInsight>(`/ai/insights`, {
      params: { query }
    });
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
