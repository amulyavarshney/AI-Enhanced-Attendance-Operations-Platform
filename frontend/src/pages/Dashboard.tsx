
import React, { useEffect, useState } from "react";
import { ArrowUp, ArrowDown, Calendar, CheckCircle2, Users, UserCog, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { 
  fetchAttendance, 
  fetchEmployees, 
  fetchTeams, 
  fetchTeamTrends 
} from "@/services/mockData";
import { formatDate } from "@/utils/formatters";
import { Employee, Attendance, Team, TeamTrends, AttendanceType } from "@/types/models";

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
        const [employeesData, teamsData, attendanceData, teamTrendsData] = await Promise.all([
          fetchEmployees(),
          fetchTeams(),
          fetchAttendance(),
          fetchTeamTrends()
        ]);
        
        setEmployees(employeesData);
        setTeams(teamsData);
        setAttendance(attendanceData);
        setTeamTrends(teamTrendsData);
        
        // Get today's attendance
        const today = new Date().toISOString().split('T')[0];
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
      existingDay.present += trend.presentCount;
      existingDay.wfh += trend.wfhCount;
      existingDay.absent += trend.absentCount;
      existingDay.leave += trend.leaveCount;
      existingDay.halfDay += trend.halfDayCount;
      existingDay.total += trend.totalEmployees;
    } else {
      acc.push({
        date,
        present: trend.presentCount,
        wfh: trend.wfhCount,
        absent: trend.absentCount,
        leave: trend.leaveCount,
        halfDay: trend.halfDayCount,
        total: trend.totalEmployees
      });
    }
    
    return acc;
  }, [] as any[]).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  // Team comparison data
  const teamComparisonData = teams.map(team => {
    const teamEmployeeCount = employees.filter(e => e.teamId === team.id).length;
    const teamTrendsData = teamTrends.filter(t => t.teamId === team.id);
    
    const avgPresent = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.presentCount, 0) / teamTrendsData.length
      : 0;
    
    const avgWfh = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.wfhCount, 0) / teamTrendsData.length
      : 0;
    
    const avgAbsent = teamTrendsData.length > 0
      ? teamTrendsData.reduce((sum, t) => sum + t.absentCount, 0) / teamTrendsData.length
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
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium">3 employees have missed check-in</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Lisa Anderson, David Taylor, James Thomas
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium">Engineering team absence rate above threshold</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    15% absence rate (threshold: 10%)
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium">High WFH percentage in Design team</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    65% of Design team is working from home today
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
