import React, { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import { auditApi, AuditLog } from "@/services/apiClient";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { format } from "date-fns";

const AuditLogs: React.FC = () => {
  const { isAdmin } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await auditApi.getAuditLogs(100, 0);
        setLogs(data);
      } catch {
        setError("Unable to load audit logs. Admin access is required.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [isAdmin]);

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Shield className="h-7 w-7 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
          <p className="text-muted-foreground">Recent mutating API activity across the platform</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-muted-foreground">Loading audit logs...</p>}
          {error && <p className="text-destructive">{error}</p>}
          {!loading && !error && logs.length === 0 && (
            <p className="text-muted-foreground">No audit events yet.</p>
          )}
          {!loading && !error && logs.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>When</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="whitespace-nowrap">
                      {log.created_at
                        ? format(new Date(log.created_at), "yyyy-MM-dd HH:mm")
                        : "—"}
                    </TableCell>
                    <TableCell>{log.actor_email || (log.actor_id ? `#${log.actor_id}` : "system")}</TableCell>
                    <TableCell className="font-mono text-xs">{log.action}</TableCell>
                    <TableCell>{log.status_code}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AuditLogs;
