
import React from "react";
import { Bell, Search, User } from "lucide-react";
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

const Topbar: React.FC = () => {
  return (
    <header className="bg-background border-b border-border h-16 flex items-center justify-between px-6 py-2">
      <div className="flex items-center w-1/3">
        <div className="flex items-center space-x-2 bg-muted/50 p-2 rounded-lg">
          <div className="flex flex-col">
            <span className="text-xs text-muted-foreground">AI Insight</span>
            <span className="text-sm font-medium">Team Performance</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm">Active Teams: 8</span>
          </div>
          <div className="h-8 w-px bg-border mx-2" />
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-sm">Avg. Attendance: 92%</span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
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
      </div>
    </header>
  );
};

export default Topbar;
