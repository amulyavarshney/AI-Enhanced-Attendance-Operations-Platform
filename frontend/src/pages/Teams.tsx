
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Plus, Edit, Briefcase, Users, BarChart } from "lucide-react";
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
import { Employee, Team, TeamTrends } from "@/types";
import { 
  fetchEmployees, 
  fetchTeams, 
  fetchTeamTrends 
} from "@/services/mockData";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { getInitials } from "@/utils/formatters";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface TeamCardProps {
  team: Team;
  teamMembers: Employee[];
  teamTrends?: TeamTrends[];
}

const TeamCard: React.FC<TeamCardProps> = ({ team, teamMembers, teamTrends }) => {
  const managerCount = teamMembers.filter(e => e.role === "manager").length;
  const employeeCount = teamMembers.filter(e => e.role === "employee").length;
  
  // Calculate attendance rates based on team trends
  let presentRate = 0;
  let absentRate = 0;
  let wfhRate = 0;
  
  if (teamTrends && teamTrends.length > 0) {
    const totalPresent = teamTrends.reduce((sum, t) => sum + t.presentCount, 0);
    const totalWfh = teamTrends.reduce((sum, t) => sum + t.wfhCount, 0);
    const totalAbsent = teamTrends.reduce((sum, t) => sum + t.absentCount, 0);
    const totalLeave = teamTrends.reduce((sum, t) => sum + t.leaveCount, 0);
    const totalHalfDay = teamTrends.reduce((sum, t) => sum + t.halfDayCount, 0);
    
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
          <Button variant="ghost" size="icon" asChild>
            <Link to={`/teams/${team.id}`}>
              <Edit className="h-4 w-4" />
            </Link>
          </Button>
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
                      {getInitials(member.firstName, member.lastName)}
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
                    <span>{member.firstName} {member.lastName}</span>
                    <span className="text-muted-foreground text-xs">
                      {member.role === "manager" ? "Manager" : "Employee"}
                    </span>
                  </div>
                ))}
                
                {teamMembers.length > 3 && (
                  <Button variant="link" className="px-0 text-sm h-auto" asChild>
                    <Link to={`/teams/${team.id}`}>
                      View all members
                    </Link>
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
              
              <Button variant="outline" size="sm" className="w-full" asChild>
                <Link to={`/analytics?team=${team.id}`}>
                  <BarChart className="h-4 w-4 mr-2" />
                  View Analytics
                </Link>
              </Button>
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
  const [teamTrends, setTeamTrends] = useState<TeamTrends[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [teamsData, employeesData, teamTrendsData] = await Promise.all([
          fetchTeams(),
          fetchEmployees(),
          fetchTeamTrends()
        ]);
        
        setTeams(teamsData);
        setEmployees(employeesData);
        setTeamTrends(teamTrendsData);
      } catch (error) {
        console.error("Error fetching teams data:", error);
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
    return employees.filter(employee => employee.teamId === teamId);
  };
  
  // Get team trends for each team
  const getTeamTrends = (teamId: number) => {
    return teamTrends.filter(trend => trend.teamId === teamId);
  };
  
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Teams</h1>
        
        <Dialog>
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
            
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="team-name">Team Name</Label>
                <Input id="team-name" placeholder="Enter team name" />
              </div>
              
              <div className="grid gap-2">
                <Label>Initial Team Members</Label>
                <p className="text-sm text-muted-foreground">
                  You can add team members after creating the team.
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button type="submit">Create Team</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
      
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
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Teams;
