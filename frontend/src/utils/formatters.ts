
import { AttendanceType, Role } from "@/types";

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export const formatTime = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatDateTime = (dateString?: string): string => {
  if (!dateString) return 'N/A';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatAttendanceStatus = (status: AttendanceType): string => {
  switch(status) {
    case AttendanceType.PRESENT:
      return 'Present';
    case AttendanceType.ABSENT:
      return 'Absent';
    case AttendanceType.HALF_DAY:
      return 'Half Day';
    case AttendanceType.WFH:
      return 'WFH';
    case AttendanceType.LEAVE:
      return 'Leave';
    default:
      return status;
  }
};

export const formatRole = (role: Role): string => {
  switch(role) {
    case Role.EMPLOYEE:
      return 'Employee';
    case Role.MANAGER:
      return 'Manager';
    case Role.ADMIN:
      return 'Admin';
    default:
      return role;
  }
};

export const getAttendanceStatusClass = (status: AttendanceType): string => {
  switch(status) {
    case AttendanceType.PRESENT:
      return 'attendance-present';
    case AttendanceType.ABSENT:
      return 'attendance-absent';
    case AttendanceType.HALF_DAY:
      return 'attendance-halfday';
    case AttendanceType.WFH:
      return 'attendance-wfh';
    case AttendanceType.LEAVE:
      return 'attendance-leave';
    default:
      return '';
  }
};

export const getInitials = (firstName: string, lastName: string): string => {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
};
