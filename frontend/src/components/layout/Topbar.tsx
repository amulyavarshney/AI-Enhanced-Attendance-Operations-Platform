import React, { useEffect, useState } from "react";
import { Bell, Search, User, Users, Building, CheckCircle2, HomeIcon, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { employeeApi, teamApi, attendanceApi } from "@/services/apiClient";
import { format } from "date-fns";

// Interface for our insights data
interface InsightsData {
  totalUsers: number;
  totalTeams: number;
  attendanceRate: number;
  remoteWorkRate: number;
  topTeam: string;
  loading: boolean;
}

const Topbar: React.FC = () => {
  const [insights, setInsights] = useState<InsightsData>({
    totalUsers: 0,
    totalTeams: 0,
    attendanceRate: 0,
    remoteWorkRate: 0,
    topTeam: "",
    loading: true
  });

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        // Get the current date
        const today = new Date();
        const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        
        // Format dates for API calls
        const startDate = format(firstDayOfMonth, 'yyyy-MM-dd');
        const endDate = format(today, 'yyyy-MM-dd');
        
        // Fetch data in parallel
        const [employees, teams, attendanceData] = await Promise.all([
          employeeApi.getEmployees(),
          teamApi.getTeams(),
          attendanceApi.getAttendance(startDate, endDate)
        ]);
        
        // Calculate attendance rate - no need to filter by date since the API will do that
        const totalRecords = attendanceData.length || 1; // Avoid division by zero
        const presentCount = attendanceData.filter(record => record.status === 'present').length;
        const wfhCount = attendanceData.filter(record => record.status === 'wfh').length;
        
        // Calculate rates
        const attendanceRate = Math.round(((presentCount + wfhCount) / totalRecords) * 100);
        const remoteWorkRate = Math.round((wfhCount / totalRecords) * 100);
        
        // Find top team (team with highest attendance)
        let teamAttendance: Record<string, { total: number; present: number; name: string }> = {};
        
        // Initialize team attendance records
        teams.forEach(team => {
          teamAttendance[team.id] = { total: 0, present: 0, name: team.name };
        });
        
        // Calculate attendance by team
        attendanceData.forEach(record => {
          const employee = employees.find(emp => emp.id === record.employee_id);
          if (employee && employee.team_id) {
            const teamId = employee.team_id.toString();
            if (teamAttendance[teamId]) {
              teamAttendance[teamId].total += 1;
              if (record.status === 'present' || record.status === 'wfh') {
                teamAttendance[teamId].present += 1;
              }
            }
          }
        });
        
        // Find team with highest attendance rate
        let topTeamId = "";
        let topAttendanceRate = 0;
        
        Object.entries(teamAttendance).forEach(([teamId, data]) => {
          if (data.total > 0) {
            const rate = data.present / data.total;
            if (rate > topAttendanceRate) {
              topAttendanceRate = rate;
              topTeamId = teamId;
            }
          }
        });
        
        const topTeam = topTeamId ? teamAttendance[topTeamId].name : "N/A";
        
        // Update insights
        setInsights({
          totalUsers: employees.length,
          totalTeams: teams.length,
          attendanceRate,
          remoteWorkRate,
          topTeam,
          loading: false
        });
        
      } catch (error) {
        console.error("Error fetching insights:", error);
        setInsights(prev => ({ ...prev, loading: false }));
      }
    };
    
    fetchInsights();
  }, []);

  return (
    <header className="bg-background border-b border-border h-16 flex items-center justify-between px-6 py-2">
      <div className="flex items-center space-x-4 w-full">
        <div className="flex items-center space-x-2 bg-muted/50 p-2 rounded-lg">
          <div className="flex flex-col">
            <span className="text-xs text-muted-foreground">Attendance Insights</span>
            {/* <span className="text-sm font-medium">Team Performance</span> */}
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <Users size={16} className="text-blue-500" />
            <span className="text-sm">Users: {insights.loading ? "..." : insights.totalUsers}</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <Building size={16} className="text-purple-500" />
            <span className="text-sm">Teams: {insights.loading ? "..." : insights.totalTeams}</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <CheckCircle2 size={16} className="text-green-500" />
            <span className="text-sm">Attendance: {insights.loading ? "..." : `${insights.attendanceRate}%`}</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <HomeIcon size={16} className="text-indigo-500" />
            <span className="text-sm">Remote: {insights.loading ? "..." : `${insights.remoteWorkRate}%`}</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <Trophy size={16} className="text-amber-500" />
            <span className="text-sm">Top Team: {insights.loading ? "..." : insights.topTeam}</span>
          </div>
        </div>
      </div>
      
      {/* <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon">
          <Bell size={20} />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              className="relative rounded-full h-8 w-8 flex items-center justify-center"
            >
              <User size={20} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Logout</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div> */}
    </header>
  );
};

export default Topbar;
