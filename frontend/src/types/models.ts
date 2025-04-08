export enum AttendanceType {
  PRESENT = "present",
  ABSENT = "absent",
  HALF_DAY = "half_day",
  WFH = "wfh",
  LEAVE = "leave"
}

export enum Role {
  EMPLOYEE = "employee",
  MANAGER = "manager",
  ADMIN = "admin"
}

export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role: Role;
  team_id: number;
  hire_date: string;
  created_at: string;
  updated_at: string;
  team?: Team;
}

export interface Team {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  employees?: Employee[];
}

export interface Attendance {
  id: number;
  employee_id: number;
  date: string;
  status: AttendanceType;
  check_in?: string;
  check_out?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  employee?: Employee;
}

export interface TeamTrends {
  team_id: number;
  date: string;
  total_employees: number;
  present_count: number;
  absent_count: number;
  wfh_count: number;
  half_day_count: number;
  leave_count: number;
  team?: Team;
}

export interface AIInsight {
  id: number;
  query: string;
  summary: string;
  details: Record<string, any>;
  generated_at: string;
}

export interface EmployeeFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role: Role;
  team_id: number;
  hire_date: string;
}

export interface AttendanceFormData {
  employee_id: number;
  status: AttendanceType;
  check_in?: string;
  check_out?: string;
  notes?: string;
}

export interface TeamFormData {
  name: string;
}
