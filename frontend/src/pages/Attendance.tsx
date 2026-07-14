import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Calendar, Check, Clock, Pencil, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
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
import {
  Attendance,
  AttendanceType,
  Employee,
  Team,
  AttendanceFormData,
} from "@/types/models";
import { attendanceApi, employeeApi, teamApi } from "@/services/apiClient";
import {
  formatAttendanceStatus,
  formatTime,
  getAttendanceStatusClass,
} from "@/utils/formatters";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useForm, Controller } from "react-hook-form";

type AttendanceFormValues = {
  employeeId: string;
  date: Date;
  status: AttendanceType;
  checkIn: string;
  checkOut: string;
  notes: string;
};

const AttendancePage: React.FC = () => {
  const { canManage } = useAuth();
  // Data states
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);

  // UI states
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [updatingRecords, setUpdatingRecords] = useState<
    Record<number, boolean>
  >({});
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  // Form handling with react-hook-form
  const form = useForm<AttendanceFormValues>({
    defaultValues: {
      employeeId: "",
      date: new Date(),
      status: AttendanceType.PRESENT,
      checkIn: "",
      checkOut: "",
      notes: "",
    },
  });

  // Reset form to default values
  const resetForm = useCallback(() => {
    form.reset({
      employeeId: "",
      date: new Date(),
      status: AttendanceType.PRESENT,
      checkIn: "",
      checkOut: "",
      notes: "",
    });
    setIsEditing(false);
    setEditingId(null);
  }, [form]);

  // Open dialog for editing a record
  const openEditDialog = useCallback(
    (record: Attendance) => {
      const employee = employees.find((e) => e.id === record.employee_id);
      if (!employee) return;

      const recordDate = record.date ? new Date(record.date) : new Date();

      form.reset({
        employeeId: employee.id.toString(),
        date: recordDate,
        status: record.status,
        checkIn: record.check_in || "",
        checkOut: record.check_out || "",
        notes: record.notes || "",
      });

      setIsEditing(true);
      setEditingId(record.id);
      setDialogOpen(true);
    },
    [employees, form]
  );

  // Handle save attendance
  const handleSaveAttendance = useCallback(
    async (data: AttendanceFormValues) => {
      if (!data.employeeId) {
        alert("Please select an employee");
        return;
      }

      try {
        // Format the data for API
        const formattedDate = format(data.date, "yyyy-MM-dd");

        // Convert time strings to ISO format if they exist
        const formatTimeToISO = (timeString: string | undefined) => {
          if (!timeString) return undefined;

          // Create a date object with today's date and the time from the input
          const [hours, minutes] = timeString.split(":").map(Number);
          const dateObj = new Date();
          dateObj.setHours(hours, minutes, 0, 0);
          return dateObj.toISOString();
        };

        const attendanceData: Partial<Attendance> = {
          employee_id: parseInt(data.employeeId),
          status: data.status,
          check_in: data.checkIn ? formatTimeToISO(data.checkIn) : undefined,
          check_out: data.checkOut ? formatTimeToISO(data.checkOut) : undefined,
          notes: data.notes || undefined,
          date: formattedDate,
        };

        let updatedRecord: Attendance;

        if (isEditing && editingId) {
          // Update existing record
          updatedRecord = await attendanceApi.updateAttendance(
            editingId,
            attendanceData
          );

          // Update local state
          setAttendance((prev) =>
            prev.map((record) =>
              record.id === editingId ? updatedRecord : record
            )
          );
        } else {
          updatedRecord = await attendanceApi.createAttendance(
            attendanceData as Omit<Attendance, "id" | "createdAt" | "updatedAt">
          );

          // Add to the local state if it's the selected date
          if (formattedDate === format(selectedDate, "yyyy-MM-dd")) {
            setAttendance((prev) => [...prev, updatedRecord]);
          }
        }

        // Close dialog and reset form
        setDialogOpen(false);
        resetForm();
      } catch (error) {
        console.error("Error saving attendance:", error);
        alert("Failed to save attendance");
      }
    },
    [isEditing, editingId, selectedDate, resetForm]
  );

  // Handle check-out for an employee
  const handleCheckOut = useCallback(async (attendanceId: number) => {
    setUpdatingRecords((prev) => ({ ...prev, [attendanceId]: true }));

    try {
      const now = new Date();
      const isoTimeString = now.toISOString();

      const updatedRecord = await attendanceApi.updateAttendance(attendanceId, {
        check_out: isoTimeString,
      });

      setAttendance((prev) =>
        prev.map((record) =>
          record.id === attendanceId ? updatedRecord : record
        )
      );
    } catch (error) {
      console.error("Error updating check-out time:", error);
      alert("Failed to update check-out time");
    } finally {
      setUpdatingRecords((prev) => {
        const updated = { ...prev };
        delete updated[attendanceId];
        return updated;
      });
    }
  }, []);

  // Fetch employees and teams data once on mount
  useEffect(() => {
    const fetchMasterData = async () => {
      try {
        const [employeesData, teamsData] = await Promise.all([
          employeeApi.getEmployees(),
          teamApi.getTeams(),
        ]);

        setEmployees(employeesData);
        setTeams(teamsData);
      } catch (error) {
        console.error("Error fetching master data:", error);
      }
    };

    fetchMasterData();
  }, []);

  // Fetch attendance data when selected date changes
  useEffect(() => {
    const fetchAttendanceData = async () => {
      setLoading(true);
      try {
        const date = format(selectedDate, "yyyy-MM-dd");
        const attendanceData = await attendanceApi.getAttendance(date, date);
        setAttendance(attendanceData);
      } catch (error) {
        console.error("Error fetching attendance data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAttendanceData();
  }, [selectedDate]);

  // Memoized filtered attendance
  const filteredAttendance = useMemo(() => {
    return attendance.filter((record) => {
      // Filter by status
      const matchesStatus =
        statusFilter === "all" || record.status === statusFilter;

      // Filter by team
      const employee = employees.find((e) => e.id === record.employee_id);
      const matchesTeam =
        teamFilter === "all" ||
        (employee && employee.team_id === parseInt(teamFilter));

      // Filter by search
      const employeeName = employee
        ? `${employee.first_name} ${employee.last_name}`.toLowerCase()
        : "";
      const matchesSearch =
        searchQuery === "" || employeeName.includes(searchQuery.toLowerCase());

      return matchesStatus && matchesTeam && matchesSearch;
    });
  }, [attendance, statusFilter, teamFilter, searchQuery, employees]);

  // Utility functions to get employee and team information
  const getEmployeeName = useCallback(
    (employeeId: number) => {
      const employee = employees.find((e) => e.id === employeeId);
      return employee
        ? `${employee.first_name} ${employee.last_name}`
        : "Unknown Employee";
    },
    [employees]
  );

  const getTeamName = useCallback(
    (employeeId: number) => {
      const employee = employees.find((e) => e.id === employeeId);
      if (!employee) return "Unknown Team";

      const team = teams.find((t) => t.id === employee.team_id);
      return team ? team.name : "Unknown Team";
    },
    [employees, teams]
  );

  const getEmployeeInitials = useCallback(
    (employeeId: number) => {
      const employee = employees.find((e) => e.id === employeeId);
      return employee
        ? `${employee.first_name.charAt(0)}${employee.last_name.charAt(
            0
          )}`.toUpperCase()
        : "??";
    },
    [employees]
  );

  // Submit form handler that connects react-hook-form with our save function
  const onSubmit = form.handleSubmit(handleSaveAttendance);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attendance</h1>
          <p className="text-muted-foreground">
            View and manage daily attendance records for all employees.
          </p>
        </div>

        <div className="flex space-x-2">
          {canManage && (
          <Dialog
            open={dialogOpen}
            onOpenChange={(open) => {
              setDialogOpen(open);
              if (!open) resetForm();
            }}
          >
            <DialogTrigger asChild>
              <Button variant="outline">
                <Calendar className="mr-2 h-4 w-4" />
                Mark Attendance
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {isEditing ? "Edit Attendance" : "Mark Attendance"}
                </DialogTitle>
                <DialogDescription>
                  {isEditing
                    ? "Update attendance record"
                    : "Record attendance for an employee"}
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={onSubmit} className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="employee">Employee</Label>
                  <Controller
                    name="employeeId"
                    control={form.control}
                    render={({ field }) => (
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={isEditing}
                      >
                        <SelectTrigger id="employee">
                          <SelectValue placeholder="Select employee" />
                        </SelectTrigger>
                        <SelectContent>
                          {employees.map((employee) => (
                            <SelectItem
                              key={employee.id}
                              value={employee.id.toString()}
                            >
                              {employee.first_name} {employee.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="grid gap-2">
                  <Label>Date</Label>
                  <Controller
                    name="date"
                    control={form.control}
                    render={({ field }) => (
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button
                            type="button"
                            variant="outline"
                            className="justify-start text-left font-normal"
                            disabled={isEditing}
                          >
                            <Calendar className="mr-2 h-4 w-4" />
                            {format(field.value, "PPP")}
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <CalendarComponent
                            mode="single"
                            selected={field.value}
                            onSelect={(date) => date && field.onChange(date)}
                            initialFocus
                            className="pointer-events-auto"
                          />
                        </PopoverContent>
                      </Popover>
                    )}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="status">Status</Label>
                  <Controller
                    name="status"
                    control={form.control}
                    render={({ field }) => (
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger id="status">
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value={AttendanceType.PRESENT}>
                            {formatAttendanceStatus(AttendanceType.PRESENT)}
                          </SelectItem>
                          <SelectItem value={AttendanceType.ABSENT}>
                            {formatAttendanceStatus(AttendanceType.ABSENT)}
                          </SelectItem>
                          <SelectItem value={AttendanceType.WFH}>
                            {formatAttendanceStatus(AttendanceType.WFH)}
                          </SelectItem>
                          <SelectItem value={AttendanceType.HALF_DAY}>
                            {formatAttendanceStatus(AttendanceType.HALF_DAY)}
                          </SelectItem>
                          <SelectItem value={AttendanceType.LEAVE}>
                            {formatAttendanceStatus(AttendanceType.LEAVE)}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="check-in">Check In</Label>
                    <Controller
                      name="checkIn"
                      control={form.control}
                      render={({ field }) => (
                        <Input id="check-in" type="time" {...field} />
                      )}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="check-out">Check Out</Label>
                    <Controller
                      name="checkOut"
                      control={form.control}
                      render={({ field }) => (
                        <Input id="check-out" type="time" {...field} />
                      )}
                    />
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Controller
                    name="notes"
                    control={form.control}
                    render={({ field }) => (
                      <Textarea
                        id="notes"
                        placeholder="Add any additional notes..."
                        {...field}
                      />
                    )}
                  />
                </div>

                <DialogFooter className="mt-4 px-0 pb-0">
                  <Button type="submit">
                    {isEditing ? "Update Attendance" : "Save Attendance"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          {/* <CardTitle>Attendance Records</CardTitle>
          <CardDescription>
            View and manage daily attendance records for all employees.
          </CardDescription> */}
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
                  <SelectItem value={AttendanceType.PRESENT}>
                    {formatAttendanceStatus(AttendanceType.PRESENT)}
                  </SelectItem>
                  <SelectItem value={AttendanceType.ABSENT}>
                    {formatAttendanceStatus(AttendanceType.ABSENT)}
                  </SelectItem>
                  <SelectItem value={AttendanceType.WFH}>
                    {formatAttendanceStatus(AttendanceType.WFH)}
                  </SelectItem>
                  <SelectItem value={AttendanceType.HALF_DAY}>
                    {formatAttendanceStatus(AttendanceType.HALF_DAY)}
                  </SelectItem>
                  <SelectItem value={AttendanceType.LEAVE}>
                    {formatAttendanceStatus(AttendanceType.LEAVE)}
                  </SelectItem>
                </SelectContent>
              </Select>

              <Select value={teamFilter} onValueChange={setTeamFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by team" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Teams</SelectItem>
                  {teams.map((team) => (
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
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : filteredAttendance.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Calendar className="h-12 w-12 text-muted-foreground mb-3" />
              <h3 className="text-lg font-medium">
                No attendance records found
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                No records match your search criteria or filters for the
                selected date.
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
                  {filteredAttendance.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>
                        <div className="flex items-center">
                          <Avatar className="h-8 w-8 mr-2">
                            <AvatarFallback className="bg-primary text-primary-foreground">
                              {getEmployeeInitials(record.employee_id)}
                            </AvatarFallback>
                          </Avatar>
                          <span>{getEmployeeName(record.employee_id)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {getTeamName(record.employee_id)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={getAttendanceStatusClass(record.status)}
                        >
                          {formatAttendanceStatus(record.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {record.check_in ? (
                          <div className="flex items-center">
                            <Clock className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                            {formatTime(record.check_in)}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {record.check_out ? (
                          <div className="flex items-center">
                            <Clock className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                            {formatTime(record.check_out)}
                          </div>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div
                          className="max-w-[200px] truncate"
                          title={record.notes || ""}
                        >
                          {record.notes || (
                            <span className="text-muted-foreground">
                              No notes
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {canManage ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              disabled={updatingRecords[record.id]}
                            >
                              {updatingRecords[record.id] ? (
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                              ) : (
                                <Pencil className="h-4 w-4" />
                              )}
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => openEditDialog(record)}
                            >
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit record
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleCheckOut(record.id)}
                              disabled={!!record.check_out}
                            >
                              <Clock className="h-4 w-4 mr-2" />
                              Mark check-out
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                        ) : null}
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
