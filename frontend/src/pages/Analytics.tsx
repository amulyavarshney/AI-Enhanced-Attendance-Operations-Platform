import React, { useEffect, useState } from "react";
import { BarChart3, CalendarRange, PieChart, TrendingUp, Users, Download } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Attendance, Team, TeamTrends } from "@/types/models";
import { teamApi, attendanceApi, dashboardApi } from "@/services/apiClient";
import { formatDate } from "@/utils/formatters";
import { DateRangePicker } from "@/components/ui/date-range-picker";
import { Button } from "@/components/ui/button";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { useToast } from "@/hooks/use-toast";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPlot,
  Pie,
  Cell,
  Legend
} from "recharts";

const Analytics: React.FC = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [teamTrends, setTeamTrends] = useState<TeamTrends[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>("all");
  const [selectedPeriod, setSelectedPeriod] = useState<string>("7days");
  
  // Add state for date range
  const [startDate, setStartDate] = useState<Date>(() => {
    const date = new Date();
    date.setDate(date.getDate() - 7); // Default to 7 days ago
    return date;
  });
  const [endDate, setEndDate] = useState<Date>(new Date()); // Default to today
  
  // Date range state for the picker
  const [dateRange, setDateRange] = useState<DateRange | undefined>({
    from: startDate,
    to: endDate
  });
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [teamsData] = await Promise.all([
          teamApi.getTeams(),
        ]);
        
        setTeams(teamsData);
      } catch (error) {
        console.error("Error fetching teams data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Update dates whenever period changes
  useEffect(() => {
    const today = new Date();
    let newStartDate = new Date();
    
    if (selectedPeriod !== "custom") {
      switch (selectedPeriod) {
        case "7days":
          newStartDate.setDate(today.getDate() - 7);
          break;
        case "30days":
          newStartDate.setDate(today.getDate() - 30);
          break;
        case "90days":
          newStartDate.setDate(today.getDate() - 90);
          break;
        default:
          newStartDate.setDate(today.getDate() - 7);
      }
      setStartDate(newStartDate);
      setEndDate(today);
      
      // Update the date range picker
      setDateRange({
        from: newStartDate,
        to: today
      });
    }
  }, [selectedPeriod]);
  
  // Update startDate and endDate when dateRange changes
  useEffect(() => {
    if (dateRange?.from) {
      setStartDate(dateRange.from);
    }
    if (dateRange?.to) {
      setEndDate(dateRange.to);
    }
  }, [dateRange]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const startDateStr = format(startDate, "yyyy-MM-dd");
        const endDateStr = format(endDate, "yyyy-MM-dd");
        
        const [attendanceData, teamTrendsData] = await Promise.all([
          attendanceApi.getAttendance(startDateStr, endDateStr),
          dashboardApi.getTrends(startDateStr, endDateStr)
        ]);
        
        setAttendance(attendanceData);
        setTeamTrends(teamTrendsData);
      } catch (error) {
        console.error("Error fetching analytics data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [startDate, endDate]);
  
  // Filter data based on selections
  const filterDataByTeam = (data: TeamTrends[]) => {
    if (selectedTeam === "all") return data;
    return data.filter(item => item.team_id === parseInt(selectedTeam));
  };
  
  // Filter data based on selected period
  const filterDataByPeriod = <T extends { date: string }>(data: T[]) => {
    const startDateString = format(startDate, "yyyy-MM-dd");
    const endDateString = format(endDate, "yyyy-MM-dd");
    
    return data.filter(item => {
      const itemDate = item.date ? item.date.split('T')[0] : "";
      return itemDate >= startDateString && itemDate <= endDateString;
    });
  };
  
  // Handle custom date range changes
  const applyCustomDateRange = () => {
    // This will trigger the useEffect hook to fetch new data
    setSelectedPeriod("custom");
  };

  const handleExportCsv = async () => {
    setExporting(true);
    try {
      const startDateStr = format(startDate, "yyyy-MM-dd");
      const endDateStr = format(endDate, "yyyy-MM-dd");
      const blob = await attendanceApi.exportCsv(startDateStr, endDateStr);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `attendance_${startDateStr}_to_${endDateStr}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast({ title: "Export ready", description: "Attendance CSV downloaded." });
    } catch {
      toast({
        title: "Export failed",
        description: "Could not download attendance CSV.",
        variant: "destructive",
      });
    } finally {
      setExporting(false);
    }
  };
  
  // Prepare data for attendance status pie chart
  const getAttendanceStatusData = () => {
    const filteredAttendance = filterDataByPeriod(
      attendance
    );
    
    const statusCounts: Record<string, number> = {
      present: 0,
      absent: 0,
      wfh: 0,
      half_day: 0,
      leave: 0
    };
    
    filteredAttendance.forEach(record => {
      statusCounts[record.status] = (statusCounts[record.status] || 0) + 1;
    });
    
    return [
      { name: 'Present', value: statusCounts.present, color: '#10B981' },
      { name: 'Absent', value: statusCounts.absent, color: '#EF4444' },
      { name: 'WFH', value: statusCounts.wfh, color: '#6366F1' },
      { name: 'Half Day', value: statusCounts.half_day, color: '#F59E0B' },
      { name: 'Leave', value: statusCounts.leave, color: '#8B5CF6' }
    ];
  };
  
  // Prepare data for attendance trends chart
  const getAttendanceTrendsData = () => {
    const filteredTrends = filterDataByPeriod(
      filterDataByTeam(teamTrends)
    );
    
    const trendsData: Record<string, any> = {};
    
    filteredTrends.forEach(trend => {
      const date = formatDate(trend.date);
      
      if (!trendsData[date]) {
        trendsData[date] = {
          date,
          present: 0,
          absent: 0,
          wfh: 0,
          halfDay: 0,
          leave: 0
        };
      }
      
      trendsData[date].present += trend.present_count;
      trendsData[date].absent += trend.absent_count;
      trendsData[date].wfh += trend.wfh_count;
      trendsData[date].halfDay += trend.half_day_count;
      trendsData[date].leave += trend.leave_count;
    });
    
    return Object.values(trendsData).sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  };
  
  // Prepare data for team comparison chart
  const getTeamComparisonData = () => {
    const filteredTrends = filterDataByPeriod(teamTrends);
    
    const teamData: Record<string, any> = {};
    
    teams.forEach(team => {
      teamData[team.id] = {
        name: team.name,
        presentRate: 0,
        absentRate: 0,
        wfhRate: 0,
        count: 0
      };
    });
    
    filteredTrends.forEach(trend => {
      const team = teamData[trend.team_id];
      if (team) {
        const total = trend.present_count + trend.absent_count + trend.wfh_count + trend.leave_count + trend.half_day_count;
        
        if (total > 0) {
          team.presentRate += (trend.present_count / total) * 100;
          team.absentRate += ((trend.absent_count + trend.leave_count) / total) * 100;
          team.wfhRate += (trend.wfh_count / total) * 100;
          team.count += 1;
        }
      }
    });
    
    // Calculate averages
    Object.values(teamData).forEach(team => {
      if (team.count > 0) {
        team.presentRate = Math.round(team.presentRate / team.count);
        team.absentRate = Math.round(team.absentRate / team.count);
        team.wfhRate = Math.round(team.wfhRate / team.count);
      }
    });
    
    return Object.values(teamData);
  };
  
  // Attendance status data
  const attendanceStatusData = getAttendanceStatusData();
  
  // Attendance trends data
  const attendanceTrendsData = getAttendanceTrendsData();
  
  // Team comparison data
  const teamComparisonData = getTeamComparisonData();
  
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-lg text-muted-foreground">Loading analytics data...</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        
        <div className="flex space-x-2">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7days">Last 7 Days</SelectItem>
              <SelectItem value="30days">Last 30 Days</SelectItem>
              <SelectItem value="90days">Last 90 Days</SelectItem>
              <SelectItem value="custom">Custom Range</SelectItem>
            </SelectContent>
          </Select>
           
          {selectedPeriod === "custom" && (
            <div className="flex items-center space-x-2">
              <DateRangePicker 
                dateRange={dateRange}
                onDateRangeChange={setDateRange}
                className="w-[300px]"
              />
              <Button onClick={applyCustomDateRange} variant="outline" size="sm">
                Apply
              </Button>
            </div>
          )}
          <Button onClick={handleExportCsv} variant="outline" size="sm" disabled={exporting}>
            <Download className="h-4 w-4 mr-2" />
            {exporting ? "Exporting..." : "Export CSV"}
          </Button>
        </div>
      </div>
      
      <Tabs defaultValue="attendance">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="attendance" className="flex items-center">
            <PieChart className="h-4 w-4 mr-2" />
            Attendance Status
          </TabsTrigger>
          <TabsTrigger value="trends" className="flex items-center">
            <TrendingUp className="h-4 w-4 mr-2" />
            Attendance Trends
          </TabsTrigger>
          <TabsTrigger value="team" className="flex items-center">
            <Users className="h-4 w-4 mr-2" />
            Team Comparison
          </TabsTrigger>
          <TabsTrigger value="calendar" className="flex items-center">
            <CalendarRange className="h-4 w-4 mr-2" />
            Calendar View
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="attendance" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Attendance Status Distribution</CardTitle>
              <CardDescription>
                Breakdown of attendance status across {selectedTeam === "all" ? "all teams" : teams.find(t => t.id.toString() === selectedTeam)?.name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPlot>
                    <Pie
                      data={attendanceStatusData}
                      cx="50%"
                      cy="50%"
                      outerRadius={150}
                      dataKey="value"
                      nameKey="name"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {attendanceStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </RechartsPlot>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="trends" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Attendance Trends Over Time</CardTitle>
                <CardDescription>
                View how attendance patterns change over the selected period
                </CardDescription>
              </div>
              <Select value={selectedTeam} onValueChange={setSelectedTeam}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select team" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Teams</SelectItem>
                  {teams.map(team => (
                    <SelectItem key={team.id} value={team.id.toString()}>
                      {team.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={attendanceTrendsData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="present" 
                      name="Present" 
                      stackId="1"
                      stroke="#10B981" 
                      fill="#10B981" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="wfh" 
                      name="WFH" 
                      stackId="1"
                      stroke="#6366F1" 
                      fill="#6366F1" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="halfDay" 
                      name="Half Day" 
                      stackId="1"
                      stroke="#F59E0B" 
                      fill="#F59E0B" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="absent" 
                      name="Absent" 
                      stackId="1"
                      stroke="#EF4444" 
                      fill="#EF4444" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="leave" 
                      name="Leave" 
                      stackId="1"
                      stroke="#8B5CF6" 
                      fill="#8B5CF6" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="team" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Team Attendance Comparison</CardTitle>
              <CardDescription>
                Compare attendance patterns across different teams
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={teamComparisonData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="presentRate" name="Present %" fill="#10B981" />
                    <Bar dataKey="wfhRate" name="WFH %" fill="#6366F1" />
                    <Bar dataKey="absentRate" name="Absent/Leave %" fill="#EF4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="calendar" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Attendance Calendar View</CardTitle>
              <CardDescription>
                Calendar heat map view coming soon
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[400px] flex items-center justify-center">
              <div className="text-center">
                <CalendarRange className="h-16 w-16 mx-auto text-muted-foreground" />
                <h3 className="text-xl font-medium mt-4">Coming Soon</h3>
                <p className="text-muted-foreground mt-2 max-w-md">
                  Calendar heat map visualization for attendance patterns is under development.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Analytics;
