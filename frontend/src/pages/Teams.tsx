import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Edit, Trash2, Briefcase, Users, BarChart, UserRound, PieChart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Employee, Team, TeamTrends, TeamFormData } from "@/types/models";
import { 
  employeeApi, 
  teamApi 
} from "@/services/apiClient";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getInitials } from "@/utils/formatters";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/components/ui/use-toast";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ScrollArea,
} from "@/components/ui/scroll-area";

// Form validation schema
const teamFormSchema = z.object({
  name: z.string().min(2, { message: "Team name must be at least 2 characters" })
});

type TeamFormValues = z.infer<typeof teamFormSchema>;

interface TeamCardProps {
  team: Team;
  teamMembers: Employee[];
  teamTrends?: TeamTrends[];
  onEdit?: (team: Team) => void;
  onDelete?: (teamId: number) => void;
  onViewAllMembers?: (team: Team) => void;
  onViewAnalytics?: (team: Team) => void;
}

const TeamCard: React.FC<TeamCardProps> = ({ 
  team, 
  teamMembers, 
  teamTrends = [], 
  onEdit, 
  onDelete,
  onViewAllMembers,
  onViewAnalytics
}) => {
  const managerCount = teamMembers.filter(e => e.role === "manager").length;
  const employeeCount = teamMembers.filter(e => e.role === "employee").length;
  
  // Calculate attendance rates based on team trends
  let presentRate = 0;
  let absentRate = 0;
  let wfhRate = 0;
  
  if (teamTrends.length > 0) {
    const totalPresent = teamTrends.reduce((sum, t) => sum + t.present_count, 0);
    const totalWfh = teamTrends.reduce((sum, t) => sum + t.wfh_count, 0);
    const totalAbsent = teamTrends.reduce((sum, t) => sum + t.absent_count, 0);
    const totalLeave = teamTrends.reduce((sum, t) => sum + t.leave_count, 0);
    const totalHalfDay = teamTrends.reduce((sum, t) => sum + t.half_day_count, 0);
    
    const total = totalPresent + totalWfh + totalAbsent + totalLeave + totalHalfDay;
    
    if (total > 0) {
      presentRate = Math.round((totalPresent / total) * 100);
      absentRate = Math.round(((totalAbsent + totalLeave) / total) * 100);
      wfhRate = Math.round((totalWfh / total) * 100);
    }
  }
  
  return (
    <Card className="card-hover overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-primary/10 to-background pb-2">
        <div className="flex justify-between items-center">
          <CardTitle>{team.name}</CardTitle>
          <div className="flex gap-1">
            {onEdit && (
              <Button variant="ghost" size="icon" onClick={() => onEdit(team)}>
                <Edit className="h-4 w-4" />
              </Button>
            )}
            {onDelete && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete the "{team.name}" team and remove all team associations.
                      This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => onDelete(team.id)}>
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
        <CardDescription>
          {teamMembers.length} members • {managerCount} managers
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6">
        <Tabs defaultValue="members">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="members">Members</TabsTrigger>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="members" className="pt-4">
            <div className="space-y-4">
              <div className="flex -space-x-2 overflow-hidden">
                {teamMembers.slice(0, 5).map(member => (
                  <Avatar key={member.id} className="border-2 border-background">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      {getInitials(member.first_name, member.last_name)}
                    </AvatarFallback>
                  </Avatar>
                ))}
                
                {teamMembers.length > 5 && (
                  <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-background bg-muted text-muted-foreground text-xs font-medium">
                    +{teamMembers.length - 5}
                  </div>
                )}
              </div>
              
              <div className="space-y-2">
                {teamMembers.slice(0, 3).map(member => (
                  <div key={member.id} className="flex items-center justify-between text-sm">
                    <span>{member.first_name} {member.last_name}</span>
                    <span className="text-muted-foreground text-xs">
                      {member.role === "manager" ? "Manager" : "Employee"}
                    </span>
                  </div>
                ))}
                
                {teamMembers.length > 3 && onViewAllMembers && (
                  <Button 
                    variant="link" 
                    className="px-0 text-sm h-auto"
                    onClick={() => onViewAllMembers(team)}
                  >
                    View all members
                  </Button>
                )}
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="stats" className="pt-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>Present Rate</span>
                  <span className="font-medium">{presentRate}%</span>
                </div>
                <Progress value={presentRate} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>WFH Rate</span>
                  <span className="font-medium">{wfhRate}%</span>
                </div>
                <Progress value={wfhRate} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span>Absence Rate</span>
                  <span className="font-medium">{absentRate}%</span>
                </div>
                <Progress value={absentRate} className="h-2" />
              </div>
              
              {onViewAnalytics && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full"
                  onClick={() => onViewAnalytics(team)}
                >
                  <BarChart className="h-4 w-4 mr-2" />
                  View Analytics
                </Button>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

const Teams: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [teamTrends, setTeamTrends] = useState<{ [key: number]: TeamTrends[] }>({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [currentTeam, setCurrentTeam] = useState<Team | null>(null);
  const [isMembersDialogOpen, setIsMembersDialogOpen] = useState(false);
  const [isAnalyticsDialogOpen, setIsAnalyticsDialogOpen] = useState(false);
  
  // Form setup for adding/editing teams
  const form = useForm<TeamFormValues>({
    resolver: zodResolver(teamFormSchema),
    defaultValues: {
      name: "",
    },
  });
  
  useEffect(() => {
    // Reset form when currentTeam changes
    if (currentTeam) {
      form.reset({
        name: currentTeam.name,
      });
    } else {
      form.reset({
        name: "",
      });
    }
  }, [currentTeam, form]);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [teamsData, employeesData] = await Promise.all([
          teamApi.getTeams(),
          employeeApi.getEmployees()
        ]);
        
        setTeams(teamsData);
        setEmployees(employeesData);
        
        // Fetch team trends for each team
        const trendsObj: { [key: number]: TeamTrends[] } = {};
        
        // Load trends for each team
        await Promise.all(
          teamsData.map(async (team) => {
            try {
              const trendsData = await teamApi.getAttendenceTrendsByTeamId(team.id.toString());
              trendsObj[team.id] = trendsData;
            } catch (error) {
              console.error(`Error fetching trends for team ${team.id}:`, error);
              trendsObj[team.id] = [];
            }
          })
        );
        
        setTeamTrends(trendsObj);
      } catch (error) {
        console.error("Error fetching teams data:", error);
        toast({
          title: "Error",
          description: "Failed to load teams data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Filter teams based on search query
  const filteredTeams = teams.filter(team => {
    return searchQuery === "" || team.name.toLowerCase().includes(searchQuery.toLowerCase());
  });
  
  // Get team members for each team
  const getTeamMembers = (teamId: number) => {
    return employees.filter(employee => employee.team_id === teamId);
  };
  
  // Get team trends for a team from the pre-loaded data
  const getTeamTrends = (teamId: number) => {
    return teamTrends[teamId] || [];
  };

  // Handler for adding a new team
  const handleAddTeam = async (data: TeamFormValues) => {
    try {
      // Team data
      const teamData: TeamFormData = {
        name: data.name,
      };

      // Make API call to create team
      const response = await (teamApi.createTeam as any)(teamData);
      
      if (response) {
        // Add the new team to the state
        setTeams([...teams, response]);
        setIsAddDialogOpen(false);
        form.reset();
        toast({
          title: "Success",
          description: "Team added successfully",
        });
      }
    } catch (error) {
      console.error("Error adding team:", error);
      toast({
        title: "Error",
        description: "Failed to add team",
        variant: "destructive",
      });
    }
  };

  // Handler for editing a team
  const handleEditTeam = async (data: TeamFormValues) => {
    if (!currentTeam) return;
    
    try {
      // Team data
      const teamData: TeamFormData = {
        name: data.name,
      };

      // Make API call to update team
      const response = await (teamApi.updateTeam as any)(currentTeam.id.toString(), teamData);
      
      if (response) {
        // Update the team in the state
        const updatedTeams = teams.map(team => 
          team.id === currentTeam.id ? response : team
        );
        
        setTeams(updatedTeams);
        setIsEditDialogOpen(false);
        setCurrentTeam(null);
        toast({
          title: "Success",
          description: "Team updated successfully",
        });
      }
    } catch (error) {
      console.error("Error updating team:", error);
      toast({
        title: "Error",
        description: "Failed to update team",
        variant: "destructive",
      });
    }
  };

  // Handler for deleting a team
  const handleDeleteTeam = async (teamId: number) => {
    try {
      // Check if team has members
      const teamMembers = getTeamMembers(teamId);
      if (teamMembers.length > 0) {
        toast({
          title: "Warning",
          description: "Cannot delete team with members. Reassign members first.",
          variant: "destructive",
        });
        return;
      }
      
      // Make API call to delete team
      await (teamApi.deleteTeam as any)(teamId.toString());
      
      // Remove the team from the state
      const updatedTeams = teams.filter(team => team.id !== teamId);
      setTeams(updatedTeams);
      toast({
        title: "Success",
        description: "Team deleted successfully",
      });
    } catch (error) {
      console.error("Error deleting team:", error);
      toast({
        title: "Error",
        description: "Failed to delete team",
        variant: "destructive",
      });
    }
  };

  const openEditDialog = (team: Team) => {
    setCurrentTeam(team);
    setIsEditDialogOpen(true);
  };

  const openMembersDialog = (team: Team) => {
    setCurrentTeam(team);
    setIsMembersDialogOpen(true);
  };

  const openAnalyticsDialog = (team: Team) => {
    setCurrentTeam(team);
    setIsAnalyticsDialogOpen(true);
  };
  
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Teams</h1>
        
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Team
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Team</DialogTitle>
              <DialogDescription>
                Add a new team to your organization.
              </DialogDescription>
            </DialogHeader>
            
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleAddTeam)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Team Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Engineering" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <div className="mt-2">
                  <p className="text-sm text-muted-foreground">
                    You can add team members after creating the team.
                  </p>
                </div>
                
                <DialogFooter>
                  <Button type="submit">Create Team</Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Edit Team Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Team</DialogTitle>
            <DialogDescription>
              Update team information. Click save when you're done.
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleEditTeam)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Team Name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="submit">Save Changes</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
      
      <div className="max-w-md">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search teams..."
            className="pl-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>
      
      {loading ? (
        <div className="flex justify-center py-8">
          <p className="text-muted-foreground">Loading teams...</p>
        </div>
      ) : filteredTeams.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Briefcase className="h-12 w-12 text-muted-foreground mb-3" />
          <h3 className="text-lg font-medium">No teams found</h3>
          <p className="text-sm text-muted-foreground mt-1">
            No teams match your search criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTeams.map(team => (
            <TeamCard 
              key={team.id} 
              team={team} 
              teamMembers={getTeamMembers(team.id)}
              teamTrends={getTeamTrends(team.id)}
              onEdit={openEditDialog}
              onDelete={handleDeleteTeam}
              onViewAllMembers={openMembersDialog}
              onViewAnalytics={openAnalyticsDialog}
            />
          ))}
        </div>
      )}

      {/* View Team Members Dialog */}
      <Dialog open={isMembersDialogOpen} onOpenChange={setIsMembersDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <UserRound className="h-5 w-5" />
                {currentTeam?.name} - Team Members
              </div>
            </DialogTitle>
            <DialogDescription>
              View all members of this team and their roles.
            </DialogDescription>
          </DialogHeader>
          
          {currentTeam && (
            <ScrollArea className="h-[400px] pr-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Email</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {getTeamMembers(currentTeam.id).map(member => (
                    <TableRow key={member.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                              {getInitials(member.first_name, member.last_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            {member.first_name} {member.last_name}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                      </TableCell>
                      <TableCell>{member.email}</TableCell>
                    </TableRow>
                  ))}
                  {getTeamMembers(currentTeam.id).length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center py-6 text-muted-foreground">
                        No members in this team yet.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>

      {/* View Team Analytics Dialog */}
      <Dialog open={isAnalyticsDialogOpen} onOpenChange={setIsAnalyticsDialogOpen}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <BarChart className="h-5 w-5" />
                {currentTeam?.name} - Team Analytics
              </div>
            </DialogTitle>
            <DialogDescription>
              Detailed attendance analytics for this team.
            </DialogDescription>
          </DialogHeader>
          
          {currentTeam && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium mb-2">Attendance Overview</h3>
                
                {getTeamTrends(currentTeam.id).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Present Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="text-2xl font-bold">
                            {Math.round(getTeamTrends(currentTeam.id).reduce((sum, t) => sum + t.present_count, 0) / 
                              getTeamTrends(currentTeam.id).length)}%
                          </div>
                          <div className="p-2 bg-green-100 text-green-800 rounded-full">
                            <UserRound className="h-4 w-4" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">WFH Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="text-2xl font-bold">
                            {Math.round(getTeamTrends(currentTeam.id).reduce((sum, t) => sum + t.wfh_count, 0) / 
                              getTeamTrends(currentTeam.id).length)}%
                          </div>
                          <div className="p-2 bg-blue-100 text-blue-800 rounded-full">
                            <Users className="h-4 w-4" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Absence Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center justify-between">
                          <div className="text-2xl font-bold">
                            {Math.round((getTeamTrends(currentTeam.id).reduce((sum, t) => sum + t.absent_count, 0) +
                              getTeamTrends(currentTeam.id).reduce((sum, t) => sum + t.leave_count, 0)) / 
                              getTeamTrends(currentTeam.id).length)}%
                          </div>
                          <div className="p-2 bg-amber-100 text-amber-800 rounded-full">
                            <PieChart className="h-4 w-4" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    No analytics data available for this team.
                  </div>
                )}
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Team Composition</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Managers</span>
                    <span className="font-medium">
                      {getTeamMembers(currentTeam.id).filter(m => m.role === "manager").length}
                    </span>
                  </div>
                  <Progress 
                    value={getTeamMembers(currentTeam.id).filter(m => m.role === "manager").length / 
                      Math.max(1, getTeamMembers(currentTeam.id).length) * 100} 
                    className="h-2" 
                  />
                  
                  <div className="flex items-center justify-between">
                    <span>Employees</span>
                    <span className="font-medium">
                      {getTeamMembers(currentTeam.id).filter(m => m.role === "employee").length}
                    </span>
                  </div>
                  <Progress 
                    value={getTeamMembers(currentTeam.id).filter(m => m.role === "employee").length / 
                      Math.max(1, getTeamMembers(currentTeam.id).length) * 100} 
                    className="h-2" 
                  />
                </div>
              </div>
              
              <Button variant="outline" className="w-full">
                Export Team Report
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Teams;
