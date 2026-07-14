import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, Building, CheckCircle2, HomeIcon, Trophy, User, LogOut, Bell, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi, employeeApi, teamApi, attendanceApi, notificationApi, NotificationItem } from "@/services/apiClient";
import { format } from "date-fns";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/hooks/use-toast";

interface InsightsData {
  totalUsers: number;
  totalTeams: number;
  attendanceRate: number;
  remoteWorkRate: number;
  topTeam: string;
  loading: boolean;
}

const Topbar: React.FC = () => {
  const { employee, logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
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
        const today = new Date();
        const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        const startDate = format(firstDayOfMonth, "yyyy-MM-dd");
        const endDate = format(today, "yyyy-MM-dd");

        const [employees, teams, attendanceData, recentNotifications] = await Promise.all([
          employeeApi.getEmployees(),
          teamApi.getTeams(),
          attendanceApi.getAttendance(startDate, endDate),
          notificationApi.getNotifications(8).catch(() => [] as NotificationItem[]),
        ]);

        setNotifications(recentNotifications);

        const totalRecords = attendanceData.length || 1;
        const presentCount = attendanceData.filter(record => record.status === "present").length;
        const wfhCount = attendanceData.filter(record => record.status === "wfh").length;
        const attendanceRate = Math.round(((presentCount + wfhCount) / totalRecords) * 100);
        const remoteWorkRate = Math.round((wfhCount / totalRecords) * 100);

        const teamAttendance: Record<string, { total: number; present: number; name: string }> = {};
        teams.forEach(team => {
          teamAttendance[team.id] = { total: 0, present: 0, name: team.name };
        });

        attendanceData.forEach(record => {
          const matched = employees.find(emp => emp.id === record.employee_id);
          if (matched && matched.team_id) {
            const teamId = matched.team_id.toString();
            if (teamAttendance[teamId]) {
              teamAttendance[teamId].total += 1;
              if (record.status === "present" || record.status === "wfh") {
                teamAttendance[teamId].present += 1;
              }
            }
          }
        });

        let topTeam = "N/A";
        let highestRate = -1;
        Object.values(teamAttendance).forEach(team => {
          if (team.total > 0) {
            const rate = team.present / team.total;
            if (rate > highestRate) {
              highestRate = rate;
              topTeam = team.name;
            }
          }
        });

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

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const resetPasswordForm = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const handleChangePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    if (newPassword.length < 8) {
      toast({
        title: "Invalid password",
        description: "New password must be at least 8 characters.",
        variant: "destructive",
      });
      return;
    }
    if (newPassword !== confirmPassword) {
      toast({
        title: "Passwords do not match",
        description: "Confirm password must match the new password.",
        variant: "destructive",
      });
      return;
    }

    setChangingPassword(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast({
        title: "Password updated",
        description: "Your password has been changed successfully.",
      });
      setPasswordDialogOpen(false);
      resetPasswordForm();
    } catch {
      toast({
        title: "Unable to change password",
        description: "Check your current password and try again.",
        variant: "destructive",
      });
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <header className="bg-background border-b border-border h-16 flex items-center justify-between px-6 py-2">
      <div className="flex items-center space-x-4 w-full">
        <div className="flex items-center space-x-2 bg-muted/50 p-2 rounded-lg">
          <div className="flex flex-col">
            <span className="text-xs text-muted-foreground">Attendance Insights</span>
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

      <div className="flex items-center space-x-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative">
              <Bell size={18} />
              {notifications.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 h-4 min-w-4 rounded-full bg-primary px-1 text-[10px] text-primary-foreground flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Recent activity</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {notifications.length === 0 && (
              <DropdownMenuItem disabled>No recent notifications</DropdownMenuItem>
            )}
            {notifications.map((item) => (
              <DropdownMenuItem key={item.id} className="flex flex-col items-start gap-1 py-2">
                <span className="text-sm font-medium">{item.title}</span>
                <span className="text-xs text-muted-foreground">{item.message}</span>
                <span className="text-[10px] text-muted-foreground">
                  {item.created_at ? format(new Date(item.created_at), "MMM d, HH:mm") : ""}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

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
            <DropdownMenuLabel>
              {employee ? `${employee.first_name} ${employee.last_name}` : "Account"}
            </DropdownMenuLabel>
            {employee && (
              <DropdownMenuItem disabled className="text-xs text-muted-foreground">
                {employee.email} · {employee.role}
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setPasswordDialogOpen(true)}>
              <KeyRound size={14} className="mr-2" />
              Change password
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut size={14} className="mr-2" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Dialog
        open={passwordDialogOpen}
        onOpenChange={(open) => {
          setPasswordDialogOpen(open);
          if (!open) resetPasswordForm();
        }}
      >
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Change password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one (min 8 characters).
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm new password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>
            <DialogFooter>
              <Button type="submit" disabled={changingPassword}>
                {changingPassword ? "Updating..." : "Update password"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </header>
  );
};

export default Topbar;
