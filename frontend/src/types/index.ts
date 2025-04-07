
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
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  role: Role;
  teamId: number;
  hireDate: string;
  createdAt: string;
  updatedAt: string;
  team?: Team;
}

export interface Team {
  id: number;
  name: string;
  createdAt: string;
  updatedAt: string;
  employees?: Employee[];
}

export interface Attendance {
  id: number;
  employeeId: number;
  date: string;
  status: AttendanceType;
  checkIn?: string;
  checkOut?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  employee?: Employee;
}

export interface TeamTrends {
  teamId: number;
  date: string;
  totalEmployees: number;
  presentCount: number;
  absentCount: number;
  wfhCount: number;
  halfDayCount: number;
  leaveCount: number;
  team?: Team;
}

export interface AIInsight {
  id: number;
  query: string;
  summary: string;
  details: Record<string, any>;
  generatedAt: string;
}

export interface EmployeeFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  role: Role;
  teamId: number;
  hireDate: string;
}

export interface AttendanceFormData {
  employeeId: number;
  status: AttendanceType;
  checkIn?: string;
  checkOut?: string;
  notes?: string;
}

export interface TeamFormData {
  name: string;
}
