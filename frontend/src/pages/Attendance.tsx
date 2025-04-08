
import React, { useEffect, useState } from "react";
import { Calendar, Check, Clock, Pencil, Search, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Attendance, AttendanceType, Employee, Team } from "@/types/models";
import { fetchAttendance, fetchEmployees, fetchTeams } from "@/services/mockData";
import {
  formatAttendanceStatus,
  formatDate,
  formatTime,
  getAttendanceStatusClass
} from "@/utils/formatters";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const AttendancePage: React.FC = () => {
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [attendanceData, employeesData, teamsData] = await Promise.all([
          fetchAttendance(),
          fetchEmployees(),
          fetchTeams()
        ]);
        
        setAttendance(attendanceData);
        setEmployees(employeesData);
        setTeams(teamsData);
      } catch (error) {
        console.error("Error fetching attendance data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Filter attendance based on filters
  const filteredAttendance = attendance.filter(record => {
    // Filter by date
    const recordDate = record.date.split('T')[0];
    const filterDate = format(selectedDate, 'yyyy-MM-dd');
    const matchesDate = recordDate === filterDate;
    
    // Filter by status
    const matchesStatus = statusFilter === "all" || record.status === statusFilter;
    
    // Filter by team
    const employee = employees.find(e => e.id === record.employeeId);
    const matchesTeam = teamFilter === "all" || (employee && employee.teamId === parseInt(teamFilter));
    
    // Filter by search
    const employeeName = employee 
      ? `${employee.firstName} ${employee.lastName}`.toLowerCase()
      : "";
    const matchesSearch = searchQuery === "" || employeeName.includes(searchQuery.toLowerCase());
    
    return matchesDate && matchesStatus && matchesTeam && matchesSearch;
  });
  
  const getEmployeeName = (employeeId: number) => {
    const employee = employees.find(e => e.id === employeeId);
    return employee ? `${employee.firstName} ${employee.lastName}` : "Unknown Employee";
  };
  
  const getTeamName = (employeeId: number) => {
    const employee = employees.find(e => e.id === employeeId);
    if (!employee) return "Unknown Team";
    
    const team = teams.find(t => t.id === employee.teamId);
    return team ? team.name : "Unknown Team";
  };
  
  const getEmployeeInitials = (employeeId: number) => {
    const employee = employees.find(e => e.id === employeeId);
    return employee 
      ? `${employee.firstName.charAt(0)}${employee.lastName.charAt(0)}`.toUpperCase()
      : "??";
  };
  
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Attendance</h1>
        
        <div className="flex space-x-2">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Calendar className="mr-2 h-4 w-4" />
                Mark Attendance
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Mark Attendance</DialogTitle>
                <DialogDescription>
                  Record attendance for an employee
                </DialogDescription>
              </DialogHeader>
              
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="employee">Employee</Label>
                  <Select>
                    <SelectTrigger id="employee">
                      <SelectValue placeholder="Select employee" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map(employee => (
                        <SelectItem key={employee.id} value={employee.id.toString()}>
                          {employee.firstName} {employee.lastName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid gap-2">
                  <Label>Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="justify-start text-left font-normal"
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {format(new Date(), "PPP")}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <CalendarComponent
                        mode="single"
                        selected={new Date()}
                        onSelect={() => {}}
                        initialFocus
                        className="pointer-events-auto"
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="status">Status</Label>
                  <Select>
                    <SelectTrigger id="status">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={AttendanceType.PRESENT}>{formatAttendanceStatus(AttendanceType.PRESENT)}</SelectItem>
                      <SelectItem value={AttendanceType.ABSENT}>{formatAttendanceStatus(AttendanceType.ABSENT)}</SelectItem>
                      <SelectItem value={AttendanceType.WFH}>{formatAttendanceStatus(AttendanceType.WFH)}</SelectItem>
                      <SelectItem value={AttendanceType.HALF_DAY}>{formatAttendanceStatus(AttendanceType.HALF_DAY)}</SelectItem>
                      <SelectItem value={AttendanceType.LEAVE}>{formatAttendanceStatus(AttendanceType.LEAVE)}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="check-in">Check In</Label>
                    <Input
                      id="check-in"
                      type="time"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="check-out">Check Out</Label>
                    <Input
                      id="check-out"
                      type="time"
                    />
                  </div>
                </div>
                
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    placeholder="Add any additional notes..."
                  />
                </div>
              </div>
              
              <DialogFooter>
                <Button type="submit">Save Attendance</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          <Button>Check In Now</Button>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Attendance Records</CardTitle>
          <CardDescription>
            View and manage daily attendance records for all employees.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row justify-between space-y-4 md:space-y-0 md:space-x-4 mb-6">
            <div className="flex space-x-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="justify-start text-left font-normal"
                  >
                    <Calendar className="mr-2 h-4 w-4" />
                    {format(selectedDate, "PPP")}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <CalendarComponent
                    mode="single"
                    selected={selectedDate}
                    onSelect={(date) => date && setSelectedDate(date)}
                    initialFocus
                    className="pointer-events-auto"
                  />
                </PopoverContent>
              </Popover>
              
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name..."
                  className="pl-9 min-w-[200px]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            
            <div className="flex space-x-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value={AttendanceType.PRESENT}>{formatAttendanceStatus(AttendanceType.PRESENT)}</SelectItem>
                  <SelectItem value={AttendanceType.ABSENT}>{formatAttendanceStatus(AttendanceType.ABSENT)}</SelectItem>
                  <SelectItem value={AttendanceType.WFH}>{formatAttendanceStatus(AttendanceType.WFH)}</SelectItem>
                  <SelectItem value={AttendanceType.HALF_DAY}>{formatAttendanceStatus(AttendanceType.HALF_DAY)}</SelectItem>
                  <SelectItem value={AttendanceType.LEAVE}>{formatAttendanceStatus(AttendanceType.LEAVE)}</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={teamFilter} onValueChange={setTeamFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by team" />
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
            </div>
          </div>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <p className="text-muted-foreground">Loading attendance records...</p>
            </div>
          ) : filteredAttendance.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-3" />
              <h3 className="text-lg font-medium">No attendance records found</h3>
              <p className="text-sm text-muted-foreground mt-1">
                No records match your search criteria or filters for the selected date.
              </p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Team</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Check In</TableHead>
                    <TableHead>Check Out</TableHead>
                    <TableHead>Notes</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAttendance.map(record => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div className="flex items-center">
                          <Avatar className="h-8 w-8 mr-2">
                            <AvatarFallback className="bg-primary text-primary-foreground">
                              {getEmployeeInitials(record.employeeId)}
                            </AvatarFallback>
                          </Avatar>
                          <span>{getEmployeeName(record.employeeId)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{getTeamName(record.employeeId)}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getAttendanceStatusClass(record.status)}>
                          {formatAttendanceStatus(record.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {record.checkIn ? (
                          <div className="flex items-center">
                            <Clock className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                            {formatTime(record.checkIn)}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {record.checkOut ? (
                          <div className="flex items-center">
                            <Clock className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                            {formatTime(record.checkOut)}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="max-w-[200px] truncate">
                          {record.notes || <span className="text-muted-foreground">No notes</span>}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit record
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Clock className="h-4 w-4 mr-2" />
                              Mark check-out
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AttendancePage;
