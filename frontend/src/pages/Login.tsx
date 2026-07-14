import React, { useEffect, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Bot, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

const DEMO_MODE =
  import.meta.env.DEV ||
  import.meta.env.VITE_DEMO_MODE === "true" ||
  import.meta.env.VITE_DEMO_MODE === "1";

const DEMO_ACCOUNTS = [
  { role: "Admin", email: "admin@example.com", password: "Admin123!" },
  { role: "Manager", email: "john.doe@example.com", password: "Admin123!" },
] as const;

const Login: React.FC = () => {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const [email, setEmail] = useState(DEMO_MODE ? "admin@example.com" : "");
  const [password, setPassword] = useState(DEMO_MODE ? "Admin123!" : "");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get("reason") !== "expired") return;
    toast({
      title: "Session expired",
      description: "Please sign in again to continue.",
      variant: "destructive",
    });
    const next = new URLSearchParams(searchParams);
    next.delete("reason");
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams, toast]);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast({ title: "Signed in", description: "Welcome back." });
      navigate("/", { replace: true });
    } catch {
      toast({
        title: "Sign in failed",
        description: DEMO_MODE
          ? "Is the API running? Try docker compose up, then use a seeded demo account."
          : "Check your email and password, then try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-[radial-gradient(ellipse_at_top,_#e8eef8_0%,_#f8fafc_45%,_#eef2f7_100%)]">
      <div className="absolute inset-0 opacity-[0.35] pointer-events-none bg-[linear-gradient(to_right,#94a3b833_1px,transparent_1px),linear-gradient(to_bottom,#94a3b833_1px,transparent_1px)] bg-[size:28px_28px]" />

      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col justify-center gap-10 px-4 py-12 lg:flex-row lg:items-center lg:gap-16">
        <section className="flex-1 space-y-6 max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/70 px-3 py-1 text-xs font-medium text-slate-600 backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-sky-600" />
            AI-Enhanced Attendance Operations
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
            Attendance AI
          </h1>
          <p className="text-lg text-slate-600 leading-relaxed">
            Track attendance, manage teams, and ask natural-language questions across
            your org — with JWT auth, role scoping, audit logs, and Azure OpenAI insights.
          </p>
          <ul className="space-y-3 text-sm text-slate-600">
            <li className="flex items-start gap-2">
              <ShieldCheck className="mt-0.5 h-4 w-4 text-emerald-600" />
              Role-based access for employee, manager, and admin
            </li>
            <li className="flex items-start gap-2">
              <Bot className="mt-0.5 h-4 w-4 text-sky-600" />
              Safe AI SQL insights with rate limits and circuit breaker
            </li>
          </ul>
        </section>

        <section className="w-full max-w-md">
          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-2xl border border-slate-200/80 bg-white/90 p-6 shadow-xl shadow-slate-200/60 backdrop-blur"
          >
            <div className="space-y-1">
              <h2 className="text-xl font-semibold text-slate-900">Sign in</h2>
              <p className="text-sm text-slate-500">Use your account or a seeded demo user.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>

            {DEMO_MODE && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
                <p className="text-xs font-medium text-slate-700">Demo accounts</p>
                {DEMO_ACCOUNTS.map((account) => (
                  <button
                    key={account.email}
                    type="button"
                    className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs hover:border-sky-300 hover:bg-sky-50/60 transition"
                    onClick={() => {
                      setEmail(account.email);
                      setPassword(account.password);
                    }}
                  >
                    <span className="font-medium text-slate-800">{account.role}</span>
                    <span className="text-slate-500">{account.email}</span>
                  </button>
                ))}
                <p className="text-[11px] text-slate-500">
                  Password for seeded users: <code className="font-mono">Admin123!</code>
                </p>
              </div>
            )}
          </form>
        </section>
      </div>
    </div>
  );
};

export default Login;
