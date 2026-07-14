
import React, { useEffect, useState } from "react";
import { ArrowUp, ArrowDown, Calendar, CheckCircle2, Users, UserCog, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { employeeApi, teamApi, attendanceApi, dashboardApi } from "@/services/apiClient";
import { formatDate } from "@/utils/formatters";
import { Employee, Attendance, Team, TeamTrends, AttendanceType } from "@/types/models";
import { format, subDays } from "date-fns";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  trendLabel?: string;
  className?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ 
  title, 
  value, 
  icon, 
  trend, 
  trendLabel,
  className
}) => {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <h3 className="text-2xl font-bold mt-1">{value}</h3>
            
            {trend !== undefined && (
              <div className="flex items-center mt-2">
                {trend > 0 ? (
                  <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
                ) : (
                  <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
                )}
                <span className={`text-sm font-medium ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {Math.abs(trend)}% {trendLabel || (trend > 0 ? 'increase' : 'decrease')}
                </span>
              </div>
            )}
          </div>
          
          <div className="rounded-full p-2 bg-primary/10 text-primary">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [teamTrends, setTeamTrends] = useState<TeamTrends[]>([]);
  const [todayAttendance, setTodayAttendance] = useState<Attendance[]>([]);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const end = new Date();
        const start = subDays(end, 30);
        const startDate = format(start, "yyyy-MM-dd");
        const endDate = format(end, "yyyy-MM-dd");
        const today = format(end, "yyyy-MM-dd");

        const [employeesData, teamsData, attendanceData, teamTrendsData] = await Promise.all([
          employeeApi.getEmployees(),
          teamApi.getTeams(),
          attendanceApi.getAttendance(startDate, endDate),
          dashboardApi.getTrends(startDate, endDate),
        ]);
        
        setEmployees(employeesData);
        setTeams(teamsData);
        setAttendance(attendanceData);
        setTeamTrends(teamTrendsData);
        setTodayAttendance(attendanceData.filter(a => a.date === today));
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Calculate statistics
  const totalEmployees = employees.length;
  const totalTeams = teams.length;
  
  // Today's attendance stats
  const presentCount = todayAttendance.filter(a => a.status === AttendanceType.PRESENT).length;
  const absentCount = todayAttendance.filter(a => a.status === AttendanceType.ABSENT).length;
  const wfhCount = todayAttendance.filter(a => a.status === AttendanceType.WFH).length;
  const leaveCount = todayAttendance.filter(a => a.status === AttendanceType.LEAVE).length;
  const halfDayCount = todayAttendance.filter(a => a.status === AttendanceType.HALF_DAY).length;
  
  const presentPercentage = totalEmployees > 0 
    ? Math.round((presentCount / totalEmployees) * 100) 
    : 0;
  
  const wfhPercentage = totalEmployees > 0 
    ? Math.round((wfhCount / totalEmployees) * 100) 
    : 0;
  
  const absentPercentage = totalEmployees > 0 
    ? Math.round(((absentCount + leaveCount) / totalEmployees) * 100) 
    : 0;
  
  // Attendance trend data for chart
  const attendanceTrendData = teamTrends.reduce((acc, trend) => {
    const date = formatDate(trend.date);
    const existingDay = acc.find(d => d.date === date);
    
    if (existingDay) {
      existingDay.present += trend.present_count;
      existingDay.wfh += trend.wfh_count;
      existingDay.absent += trend.absent_count;
      existingDay.leave += trend.leave_count;
      existingDay.halfDay += trend.half_day_count;
      existingDay.total += trend.total_employees;
    } else {
      acc.push({
        date,
        present: trend.present_count,
        wfh: trend.wfh_count,
        absent: trend.absent_count,
        leave: trend.leave_count,
        halfDay: trend.half_day_count,
        total: trend.total_employees
      });
    }
    
    return acc;
  }, [] as any[]).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  // Team comparison data
  const teamComparisonData = teams.map(team => {
    const teamEmployeeCount = employees.filter(e => e.team_id === team.id).length;
    const teamTrendsData = teamTrends.filter(t => t.team_id === team.id);
    
    const avgPresent = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.present_count, 0) / teamTrendsData.length
      : 0;
    
    const avgWfh = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.wfh_count, 0) / teamTrendsData.length
      : 0;
    
    const avgAbsent = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.absent_count, 0) / teamTrendsData.length
      : 0;
    
    const totalAvg = avgPresent + avgWfh + avgAbsent;
    
    return {
      name: team.name,
      employees: teamEmployeeCount,
      presentRate: totalAvg > 0 ? Math.round((avgPresent / totalAvg) * 100) : 0,
      wfhRate: totalAvg > 0 ? Math.round((avgWfh / totalAvg) * 100) : 0,
      absentRate: totalAvg > 0 ? Math.round((avgAbsent / totalAvg) * 100) : 0
    };
  });
  
  // Today's attendance breakdown for pie chart
  const attendanceBreakdown = [
    { name: 'Present', value: presentCount, color: '#10B981' },
    { name: 'WFH', value: wfhCount, color: '#6366F1' },
    { name: 'Half Day', value: halfDayCount, color: '#F59E0B' },
    { name: 'Absent', value: absentCount, color: '#EF4444' },
    { name: 'Leave', value: leaveCount, color: '#8B5CF6' }
  ];
  
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading dashboard data...</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard 
          title="Total Employees" 
          value={totalEmployees} 
          icon={<Users className="h-6 w-6" />}
          trend={2.5}
          trendLabel="from last month"
        />
        <StatsCard 
          title="Today's Attendance" 
          value={`${presentPercentage}%`} 
          icon={<CheckCircle2 className="h-6 w-6" />}
          trend={1.2}
          trendLabel="from yesterday"
        />
        <StatsCard 
          title="WFH Today" 
          value={`${wfhPercentage}%`} 
          icon={<Calendar className="h-6 w-6" />}
          trend={-0.8}
          trendLabel="from yesterday"
        />
        <StatsCard 
          title="Teams" 
          value={totalTeams} 
          icon={<UserCog className="h-6 w-6" />}
        />
      </div>
      
      <Tabs defaultValue="attendance">
        <TabsList>
          <TabsTrigger value="attendance">Attendance Trends</TabsTrigger>
          <TabsTrigger value="teams">Team Comparison</TabsTrigger>
        </TabsList>
        
        <TabsContent value="attendance" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Attendance Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={attendanceTrendData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="date" stroke="#94A3B8" />
                    <YAxis stroke="#94A3B8" />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="present" 
                      stackId="1"
                      stroke="#10B981" 
                      fill="#10B981" 
                      name="Present"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="wfh" 
                      stackId="1"
                      stroke="#6366F1" 
                      fill="#6366F1" 
                      name="WFH"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="halfDay" 
                      stackId="1"
                      stroke="#F59E0B" 
                      fill="#F59E0B" 
                      name="Half Day"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="absent" 
                      stackId="1"
                      stroke="#EF4444" 
                      fill="#EF4444" 
                      name="Absent"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="leave" 
                      stackId="1"
                      stroke="#8B5CF6" 
                      fill="#8B5CF6" 
                      name="Leave"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="teams" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={teamComparisonData}
                    layout="vertical"
                    margin={{ top: 10, right: 30, left: 70, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis type="number" stroke="#94A3B8" />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      scale="band" 
                      stroke="#94A3B8" 
                    />
                    <Tooltip />
                    <Legend />
                    <Bar 
                      dataKey="presentRate" 
                      fill="#10B981" 
                      name="Present %" 
                      barSize={20}
                    />
                    <Bar 
                      dataKey="wfhRate" 
                      fill="#6366F1" 
                      name="WFH %" 
                      barSize={20}
                    />
                    <Bar 
                      dataKey="absentRate" 
                      fill="#EF4444" 
                      name="Absent %" 
                      barSize={20}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Today's Attendance Status</CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <div className="h-[250px] w-full max-w-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={attendanceBreakdown}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {attendanceBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Attendance Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(() => {
                const missingCheckIn = employees.filter((emp) => {
                  const record = todayAttendance.find((a) => a.employee_id === emp.id);
                  return !record || !record.check_in;
                });
                const absentToday = todayAttendance.filter(
                  (a) => a.status === AttendanceType.ABSENT || a.status === AttendanceType.LEAVE
                );
                const highWfhTeams = teamComparisonData.filter((t) => t.wfhRate >= 50);

                if (
                  missingCheckIn.length === 0 &&
                  absentToday.length === 0 &&
                  highWfhTeams.length === 0
                ) {
                  return (
                    <p className="text-sm text-muted-foreground">
                      No attendance alerts for the visible scope today.
                    </p>
                  );
                }

                return (
                  <>
                    {missingCheckIn.length > 0 && (
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-medium">
                            {missingCheckIn.length} employee{missingCheckIn.length === 1 ? "" : "s"} missing check-in
                          </h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {missingCheckIn
                              .slice(0, 5)
                              .map((e) => `${e.first_name} ${e.last_name}`)
                              .join(", ")}
                            {missingCheckIn.length > 5 ? "…" : ""}
                          </p>
                        </div>
                      </div>
                    )}
                    {absentToday.length > 0 && (
                      <div className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-medium">
                            {absentToday.length} absent/leave record{absentToday.length === 1 ? "" : "s"} today
                          </h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            Absence rate about {absentPercentage}% of visible headcount
                          </p>
                        </div>
                      </div>
                    )}
                    {highWfhTeams.map((team) => (
                      <div key={team.name} className="flex items-start space-x-3">
                        <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-medium">High WFH in {team.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {team.wfhRate}% remote in recent trend window
                          </p>
                        </div>
                      </div>
                    ))}
                  </>
                );
              })()}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
