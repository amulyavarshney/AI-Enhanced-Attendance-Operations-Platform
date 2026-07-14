
import React from "react";
import { NavLink } from "react-router-dom";
import { 
  Home, 
  Users, 
  CalendarCheck2, 
  Briefcase, 
  BarChart3, 
  MessageSquare,
  Menu,
  Shield
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";

const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = React.useState(false);
  const { isAdmin, canUseAI } = useAuth();

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  return (
    <aside 
      className={cn(
        "bg-primary text-primary-foreground flex flex-col transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-primary-foreground/10">
        {!collapsed && (
          <h1 className="font-bold text-xl">Attendance AI</h1>
        )}
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar} 
          className="text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground"
        >
          <Menu size={20} />
        </Button>
      </div>
      
      <nav className="flex-1 py-4">
        <ul className="space-y-1 px-2">
          <NavItem 
            to="/" 
            icon={<Home size={20} />} 
            label="Dashboard" 
            collapsed={collapsed} 
          />
          <NavItem 
            to="/employees" 
            icon={<Users size={20} />} 
            label="Employees" 
            collapsed={collapsed} 
          />
          <NavItem 
            to="/attendance" 
            icon={<CalendarCheck2 size={20} />} 
            label="Attendance" 
            collapsed={collapsed} 
          />
          <NavItem 
            to="/teams" 
            icon={<Briefcase size={20} />} 
            label="Teams" 
            collapsed={collapsed} 
          />
          <NavItem 
            to="/analytics" 
            icon={<BarChart3 size={20} />} 
            label="Analytics" 
            collapsed={collapsed} 
          />
          {canUseAI && (
            <NavItem 
              to="/ai-insights" 
              icon={<MessageSquare size={20} />} 
              label="AI Insights" 
              collapsed={collapsed} 
            />
          )}
          {isAdmin && (
            <NavItem 
              to="/audit-logs" 
              icon={<Shield size={20} />} 
              label="Audit Logs" 
              collapsed={collapsed} 
            />
          )}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-primary-foreground/10">
        {!collapsed && (
          <div className="text-xs text-primary-foreground/70">
            <p>Attendance AI © 2025</p>
            <p>Developed by <a href="https://github.com/amulyavarshney" target="_blank" rel="noopener noreferrer">Amulya Varshney</a></p>
          </div>
        )}
      </div>
    </aside>
  );
};

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, collapsed }) => {
  return (
    <li>
      <NavLink
        to={to}
        className={({ isActive }) =>
          cn(
            "flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors",
            isActive 
              ? "bg-white/10 text-white" 
              : "text-primary-foreground/80 hover:text-white hover:bg-white/5",
            collapsed ? "justify-center" : "justify-start"
          )
        }
      >
        <span className="flex items-center justify-center">
          {icon}
        </span>
        {!collapsed && <span className="ml-3">{label}</span>}
      </NavLink>
    </li>
  );
};

export default Sidebar;
