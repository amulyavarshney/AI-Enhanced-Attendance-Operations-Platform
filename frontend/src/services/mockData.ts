
import { Employee, Team, Attendance, TeamTrends, AIInsight, Role, AttendanceType } from "@/types/models";

// Generate teams
export const teams: Team[] = [
  { id: 1, name: "Engineering", createdAt: "2023-01-01T00:00:00Z", updatedAt: "2023-01-01T00:00:00Z" },
  { id: 2, name: "Design", createdAt: "2023-01-01T00:00:00Z", updatedAt: "2023-01-01T00:00:00Z" },
  { id: 3, name: "Marketing", createdAt: "2023-01-01T00:00:00Z", updatedAt: "2023-01-01T00:00:00Z" },
  { id: 4, name: "HR", createdAt: "2023-01-01T00:00:00Z", updatedAt: "2023-01-01T00:00:00Z" },
  { id: 5, name: "Product", createdAt: "2023-01-01T00:00:00Z", updatedAt: "2023-01-01T00:00:00Z" },
];

// Generate employees
export const employees: Employee[] = [
  { 
    id: 1, 
    firstName: "John", 
    lastName: "Doe", 
    email: "john.doe@company.com", 
    phone: "123-456-7890", 
    role: Role.MANAGER, 
    teamId: 1, 
    hireDate: "2020-01-15", 
    createdAt: "2020-01-15T00:00:00Z",
    updatedAt: "2020-01-15T00:00:00Z"
  },
  { 
    id: 2, 
    firstName: "Jane", 
    lastName: "Smith", 
    email: "jane.smith@company.com", 
    phone: "123-456-7891", 
    role: Role.EMPLOYEE, 
    teamId: 1, 
    hireDate: "2020-02-20", 
    createdAt: "2020-02-20T00:00:00Z",
    updatedAt: "2020-02-20T00:00:00Z"
  },
  { 
    id: 3, 
    firstName: "Robert", 
    lastName: "Johnson", 
    email: "robert.johnson@company.com", 
    phone: "123-456-7892", 
    role: Role.EMPLOYEE, 
    teamId: 2, 
    hireDate: "2020-03-10", 
    createdAt: "2020-03-10T00:00:00Z",
    updatedAt: "2020-03-10T00:00:00Z"
  },
  { 
    id: 4, 
    firstName: "Emily", 
    lastName: "Davis", 
    email: "emily.davis@company.com", 
    phone: "123-456-7893", 
    role: Role.MANAGER, 
    teamId: 2, 
    hireDate: "2020-04-05", 
    createdAt: "2020-04-05T00:00:00Z",
    updatedAt: "2020-04-05T00:00:00Z"
  },
  { 
    id: 5, 
    firstName: "Michael", 
    lastName: "Brown", 
    email: "michael.brown@company.com", 
    phone: "123-456-7894", 
    role: Role.EMPLOYEE, 
    teamId: 3, 
    hireDate: "2020-05-12", 
    createdAt: "2020-05-12T00:00:00Z",
    updatedAt: "2020-05-12T00:00:00Z"
  },
  { 
    id: 6, 
    firstName: "Sarah", 
    lastName: "Wilson", 
    email: "sarah.wilson@company.com", 
    phone: "123-456-7895", 
    role: Role.MANAGER, 
    teamId: 3, 
    hireDate: "2020-06-18", 
    createdAt: "2020-06-18T00:00:00Z",
    updatedAt: "2020-06-18T00:00:00Z"
  },
  { 
    id: 7, 
    firstName: "David", 
    lastName: "Taylor", 
    email: "david.taylor@company.com", 
    phone: "123-456-7896", 
    role: Role.EMPLOYEE, 
    teamId: 4, 
    hireDate: "2020-07-22", 
    createdAt: "2020-07-22T00:00:00Z",
    updatedAt: "2020-07-22T00:00:00Z"
  },
  { 
    id: 8, 
    firstName: "Lisa", 
    lastName: "Anderson", 
    email: "lisa.anderson@company.com", 
    phone: "123-456-7897", 
    role: Role.MANAGER, 
    teamId: 4, 
    hireDate: "2020-08-30", 
    createdAt: "2020-08-30T00:00:00Z",
    updatedAt: "2020-08-30T00:00:00Z"
  },
  { 
    id: 9, 
    firstName: "James", 
    lastName: "Thomas", 
    email: "james.thomas@company.com", 
    phone: "123-456-7898", 
    role: Role.EMPLOYEE, 
    teamId: 5, 
    hireDate: "2020-09-14", 
    createdAt: "2020-09-14T00:00:00Z",
    updatedAt: "2020-09-14T00:00:00Z"
  },
  { 
    id: 10, 
    firstName: "Jessica", 
    lastName: "White", 
    email: "jessica.white@company.com", 
    phone: "123-456-7899", 
    role: Role.MANAGER, 
    teamId: 5, 
    hireDate: "2020-10-25", 
    createdAt: "2020-10-25T00:00:00Z",
    updatedAt: "2020-10-25T00:00:00Z"
  },
];

// Associate employees with teams
for (const team of teams) {
  team.employees = employees.filter(employee => employee.teamId === team.id);
}

// Generate attendance for each employee for the past 7 days
export const generateAttendance = (): Attendance[] => {
  const attendance: Attendance[] = [];
  const today = new Date();
  
  employees.forEach(employee => {
    for (let i = 0; i < 14; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      if (date.getDay() === 0 || date.getDay() === 6) {
        // Weekend - no attendance
        continue;
      }
      
      const statuses = [
        AttendanceType.PRESENT, 
        AttendanceType.ABSENT, 
        AttendanceType.HALF_DAY, 
        AttendanceType.WFH, 
        AttendanceType.LEAVE
      ];
      
      // Weighted probability for statuses
      const weights = [0.6, 0.1, 0.1, 0.15, 0.05];
      let random = Math.random();
      let statusIndex = 0;
      
      for (let j = 0; j < weights.length; j++) {
        if (random < weights[j]) {
          statusIndex = j;
          break;
        }
        random -= weights[j];
      }
      
      const status = statuses[statusIndex];
      
      let checkIn = null;
      let checkOut = null;
      
      if (status === AttendanceType.PRESENT || status === AttendanceType.HALF_DAY) {
        const checkInHour = status === AttendanceType.PRESENT ? 9 : 12;
        const checkInDate = new Date(date);
        checkInDate.setHours(checkInHour, Math.floor(Math.random() * 30));
        checkIn = checkInDate.toISOString();
        
        const checkOutHour = 17;
        const checkOutDate = new Date(date);
        checkOutDate.setHours(checkOutHour, 30 + Math.floor(Math.random() * 30));
        checkOut = checkOutDate.toISOString();
      } else if (status === AttendanceType.WFH) {
        const checkInDate = new Date(date);
        checkInDate.setHours(9, Math.floor(Math.random() * 60));
        checkIn = checkInDate.toISOString();
        
        const checkOutDate = new Date(date);
        checkOutDate.setHours(17, Math.floor(Math.random() * 60));
        checkOut = checkOutDate.toISOString();
      }
      
      const notes = status === AttendanceType.LEAVE 
        ? "Planned leave" 
        : status === AttendanceType.ABSENT 
          ? "Sick leave" 
          : "";
      
      attendance.push({
        id: attendance.length + 1,
        employeeId: employee.id,
        date: date.toISOString().split('T')[0],
        status,
        checkIn: checkIn,
        checkOut: checkOut,
        notes,
        createdAt: date.toISOString(),
        updatedAt: date.toISOString(),
        employee: employee
      });
    }
  });
  
  return attendance;
};

export const attendance: Attendance[] = generateAttendance();

// Generate team trends
export const generateTeamTrends = (): TeamTrends[] => {
  const trends: TeamTrends[] = [];
  const today = new Date();
  
  teams.forEach(team => {
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      // Skip weekends
      if (date.getDay() === 0 || date.getDay() === 6) {
        continue;
      }
      
      // Get employees in this team
      const teamEmployees = employees.filter(e => e.teamId === team.id);
      const totalEmployees = teamEmployees.length;
      
      // Get attendance for this team on this date
      const teamAttendance = attendance.filter(a => 
        teamEmployees.some(e => e.id === a.employeeId) && 
        a.date === dateStr
      );
      
      // Count attendance types
      const presentCount = teamAttendance.filter(a => a.status === AttendanceType.PRESENT).length;
      const absentCount = teamAttendance.filter(a => a.status === AttendanceType.ABSENT).length;
      const wfhCount = teamAttendance.filter(a => a.status === AttendanceType.WFH).length;
      const halfDayCount = teamAttendance.filter(a => a.status === AttendanceType.HALF_DAY).length;
      const leaveCount = teamAttendance.filter(a => a.status === AttendanceType.LEAVE).length;
      
      trends.push({
        teamId: team.id,
        date: dateStr,
        totalEmployees,
        presentCount,
        absentCount,
        wfhCount,
        halfDayCount,
        leaveCount,
        team
      });
    }
  });
  
  return trends;
};

export const teamTrends: TeamTrends[] = generateTeamTrends();

// Generate AI insights
export const aiInsights: AIInsight[] = [
  {
    id: 1,
    query: "Which team has the highest attendance rate?",
    summary: "The Engineering team consistently shows the highest attendance rate at 92%, followed by Product at 87%.",
    details: {
      teamRates: [
        { team: "Engineering", rate: 92 },
        { team: "Product", rate: 87 },
        { team: "Design", rate: 85 },
        { team: "Marketing", rate: 82 },
        { team: "HR", rate: 80 }
      ],
      trend: "improving"
    },
    generatedAt: "2023-04-01T14:32:10Z"
  },
  {
    id: 2,
    query: "Who has the most work from home days this month?",
    summary: "Michael Brown from Marketing leads with 7 WFH days this month, followed by Jane Smith with 6 days.",
    details: {
      topWfh: [
        { name: "Michael Brown", team: "Marketing", days: 7 },
        { name: "Jane Smith", team: "Engineering", days: 6 },
        { name: "Sarah Wilson", team: "Marketing", days: 5 },
        { name: "Robert Johnson", team: "Design", days: 4 },
        { name: "Jessica White", team: "Product", days: 4 }
      ]
    },
    generatedAt: "2023-04-02T09:15:42Z"
  },
  {
    id: 3,
    query: "Show me attendance trends for the past week",
    summary: "Overall attendance increased by 5% last week. WFH arrangements decreased slightly while in-office presence grew.",
    details: {
      weeklyTrend: {
        present: [65, 68, 70, 72, 75],
        wfh: [20, 18, 16, 15, 14],
        absent: [8, 7, 8, 6, 5],
        leave: [5, 5, 4, 5, 4],
        halfDay: [2, 2, 2, 2, 2]
      },
      insight: "The gradual return to office trend is continuing as seen in the 5% increase in physical presence."
    },
    generatedAt: "2023-04-03T11:22:35Z"
  },
  {
    id: 4,
    query: "Which day has the most absences?",
    summary: "Monday has the highest absence rate at 12%, followed by Friday at 10%. Mid-week days show significantly lower absence rates.",
    details: {
      absenceByDay: [
        { day: "Monday", rate: 12 },
        { day: "Tuesday", rate: 7 },
        { day: "Wednesday", rate: 5 },
        { day: "Thursday", rate: 6 },
        { day: "Friday", rate: 10 }
      ],
      insight: "Consider implementing engagement activities on Mondays to reduce the high absence rate."
    },
    generatedAt: "2023-04-04T16:48:19Z"
  },
  {
    id: 5,
    query: "What's the average check-in time for the Engineering team?",
    summary: "The Engineering team averages check-ins at 9:12 AM, with John Doe consistently being earliest at 8:45 AM on average.",
    details: {
      averageTime: "9:12 AM",
      earliestEmployee: { name: "John Doe", time: "8:45 AM" },
      latestEmployee: { name: "Jane Smith", time: "9:34 AM" },
      trend: "Check-in times have been stable over the past month with minimal variation."
    },
    generatedAt: "2023-04-05T10:03:27Z"
  }
];

// API mock services
export const fetchTeams = (): Promise<Team[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([...teams]);
    }, 300);
  });
};

export const fetchTeamById = (id: number): Promise<Team | undefined> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(teams.find(team => team.id === id));
    }, 300);
  });
};

export const fetchEmployees = (): Promise<Employee[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([...employees]);
    }, 300);
  });
};

export const fetchEmployeeById = (id: number): Promise<Employee | undefined> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(employees.find(employee => employee.id === id));
    }, 300);
  });
};

export const fetchEmployeesByTeam = (teamId: number): Promise<Employee[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(employees.filter(employee => employee.teamId === teamId));
    }, 300);
  });
};

export const fetchAttendance = (
  startDate?: string, 
  endDate?: string
): Promise<Attendance[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      let result = [...attendance];
      
      if (startDate) {
        result = result.filter(a => a.date >= startDate);
      }
      
      if (endDate) {
        result = result.filter(a => a.date <= endDate);
      }
      
      resolve(result);
    }, 300);
  });
};

export const fetchAttendanceById = (id: number): Promise<Attendance | undefined> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(attendance.find(a => a.id === id));
    }, 300);
  });
};

export const fetchAttendanceByEmployee = (
  employeeId: number, 
  startDate?: string, 
  endDate?: string
): Promise<Attendance[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      let result = attendance.filter(a => a.employeeId === employeeId);
      
      if (startDate) {
        result = result.filter(a => a.date >= startDate);
      }
      
      if (endDate) {
        result = result.filter(a => a.date <= endDate);
      }
      
      resolve(result);
    }, 300);
  });
};

export const fetchTeamTrends = (
  teamId?: number,
  startDate?: string,
  endDate?: string
): Promise<TeamTrends[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      let result = [...teamTrends];
      
      if (teamId) {
        result = result.filter(t => t.teamId === teamId);
      }
      
      if (startDate) {
        result = result.filter(t => t.date >= startDate);
      }
      
      if (endDate) {
        result = result.filter(t => t.date <= endDate);
      }
      
      resolve(result);
    }, 300);
  });
};

export const fetchAIInsights = (): Promise<AIInsight[]> => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([...aiInsights]);
    }, 300);
  });
};

export const generateAIInsight = (query: string): Promise<AIInsight> => {
  return new Promise(resolve => {
    setTimeout(() => {
      // For demo purposes, just return a random existing insight
      const randomInsight = {...aiInsights[Math.floor(Math.random() * aiInsights.length)]};
      randomInsight.query = query;
      randomInsight.generatedAt = new Date().toISOString();
      
      resolve(randomInsight);
    }, 1000);
  });
};
