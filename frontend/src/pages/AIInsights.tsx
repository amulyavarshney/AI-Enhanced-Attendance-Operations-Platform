import React, { useEffect, useState } from "react";
import {
  Bot,
  LineChart,
  BarChart2,
  Search,
  Send,
  Settings,
  Users,
  Clock,
  Calendar,
  MessageSquare,
  TrendingUp,
  ChevronRight,
  BookmarkPlus,
  Clipboard,
  CalendarClock,
  Building,
  Star,
} from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";
import { AIInsight } from "@/types/models";
import { insightApi } from "@/services/apiClient";
import { formatDateTime } from "@/utils/formatters";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/ui/use-toast";
import { Progress } from "@/components/ui/progress";
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

// Types for insights categorization
type InsightCategory =
  | "attendance"
  | "performance"
  | "trends"
  | "team"
  | "general";

interface EnhancedInsight extends AIInsight {
  category: InsightCategory;
  tags: string[];
  starred?: boolean;
}

// Type for live insight widgets
interface LiveWidget {
  id: string;
  title: string;
  query: string;
  value: string | number;
  delta?: number;
  icon: React.ReactNode;
  color: string;
}

const AIInsightsPage: React.FC = () => {
  const [insights, setInsights] = useState<EnhancedInsight[]>([]);
  const [liveWidgets, setLiveWidgets] = useState<LiveWidget[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [query, setQuery] = useState("");
  const [conversation, setConversation] = useState<
    { role: "user" | "ai"; content: string }[]
  >([]);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Categories for filtering insights
  const categories = [
    { id: "all", name: "All Insights" },
    { id: "attendance", name: "Attendance" },
    { id: "team", name: "Team Analysis" },
    { id: "trends", name: "Trends" },
    { id: "performance", name: "Performance" },
    { id: "general", name: "General" },
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch insights
        const insightsData = await insightApi.getAIInsights();

        // Enhance with categories and tags
        const enhancedInsights = insightsData.map((insight) => {
          // Automatically categorize based on query content
          let category: InsightCategory = "general";
          const tags: string[] = [];

          const query = insight.query.toLowerCase();

          if (
            query.includes("attend") ||
            query.includes("absence") ||
            query.includes("present")
          ) {
            category = "attendance";
            tags.push("attendance");
          }

          if (
            query.includes("team") ||
            query.includes("department") ||
            query.includes("group")
          ) {
            category = "team";
            tags.push("team");
          }

          if (
            query.includes("trend") ||
            query.includes("pattern") ||
            query.includes("over time")
          ) {
            category = "trends";
            tags.push("trends");
          }

          if (
            query.includes("perform") ||
            query.includes("productivity") ||
            query.includes("efficient")
          ) {
            category = "performance";
            tags.push("performance");
          }

          // Add more tags based on content
          if (
            query.includes("wfh") ||
            query.includes("remote") ||
            query.includes("work from home")
          ) {
            tags.push("work from home");
          }

          if (
            query.includes("month") ||
            query.includes("week") ||
            query.includes("day")
          ) {
            tags.push("time period");
          }

          return {
            ...insight,
            category,
            tags,
            starred: Math.random() > 0.7, // Randomly star some insights for demo
          };
        });

        setInsights(enhancedInsights);

        // Create live widgets based on key metrics
        setLiveWidgets([
          {
            id: "attendance-rate",
            title: "Overall Attendance",
            query:
              "What's the current attendance rate? (last 30 days): Answer in percentage",
            value: "94.2%",
            delta: 1.5,
            icon: <Users className="h-4 w-4" />,
            color: "bg-green-500",
          },
          {
            id: "remote-work",
            title: "Remote Work",
            query:
              "How many people are working from home today?: Answer in percentage",
            value: "27%",
            delta: -3.2,
            icon: <Building className="h-4 w-4" />,
            color: "bg-blue-500",
          },
          {
            id: "attendance-trend",
            title: "Attendance Trend",
            query:
              "Show me attendance trends this month (last 30 days): Positive or Negative",
            value: "Positive",
            delta: 2.8,
            icon: <TrendingUp className="h-4 w-4" />,
            color: "bg-purple-500",
          },
          {
            id: "team-performance",
            title: "Top Team",
            query:
              "Which team has the best attendance? (last 30 days): Name the team",
            value: "Engineering",
            icon: <Star className="h-4 w-4" />,
            color: "bg-amber-500",
          },
        ]);

        // Add AI welcome message
        setConversation([
          {
            role: "ai",
            content:
              "Hello! I'm your AI Attendance Analyst. I can help you understand attendance patterns, trends, and provide insights about your organization. What would you like to know?",
          },
        ]);
      } catch (error) {
        console.error("Error fetching AI insights:", error);
        toast({
          title: "Error",
          description: "Failed to load insights. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleGenerateInsight = async () => {
    if (!query.trim()) return;

    // Add user query to conversation
    setConversation((prev) => [...prev, { role: "user", content: query }]);

    setGenerating(true);
    try {
      // Add temporary loading message
      setConversation((prev) => [
        ...prev,
        { role: "ai", content: "Analyzing attendance data..." },
      ]);

      const insight = await insightApi.getInsight(query);

      // Replace loading message with actual response
      setConversation((prev) =>
        prev.slice(0, -1).concat({ role: "ai", content: insight.summary })
      );

      // Categorize the new insight
      let category: InsightCategory = "general";
      const tags: string[] = [];

      const lowerQuery = query.toLowerCase();

      if (
        lowerQuery.includes("attend") ||
        lowerQuery.includes("absent") ||
        lowerQuery.includes("present")
      ) {
        category = "attendance";
        tags.push("attendance");
      }

      if (lowerQuery.includes("team") || lowerQuery.includes("department")) {
        category = "team";
        tags.push("team");
      }

      if (lowerQuery.includes("trend") || lowerQuery.includes("pattern")) {
        category = "trends";
        tags.push("trends");
      }

      if (
        lowerQuery.includes("perform") ||
        lowerQuery.includes("productivity")
      ) {
        category = "performance";
        tags.push("performance");
      }

      // Add to insights list if not already present
      setInsights((prev) => {
        if (!prev.some((i) => i.id === insight.id)) {
          return [
            {
              ...insight,
              category,
              tags,
              starred: false,
            },
            ...prev,
          ];
        }
        return prev;
      });

      setQuery("");
    } catch (error) {
      console.error("Error generating AI insight:", error);
      // Replace loading message with error
      setConversation((prev) =>
        prev.slice(0, -1).concat({
          role: "ai",
          content:
            "I'm sorry, I encountered an error while analyzing the data. Please try again.",
        })
      );

      toast({
        title: "Error",
        description: "Failed to generate AI insight. Please try again.",
        variant: "destructive",
      });
    } finally {
      setGenerating(false);
    }
  };

  const toggleStarInsight = (insightId: number) => {
    setInsights((prev) =>
      prev.map((insight) =>
        insight.id === insightId
          ? { ...insight, starred: !insight.starred }
          : insight
      )
    );
  };

  const filteredInsights = insights.filter((insight) => {
    // Filter by category
    const matchesCategory =
      activeCategory === "all" || insight.category === activeCategory;

    // Filter by search query
    const matchesSearch =
      searchQuery === "" ||
      insight.query.toLowerCase().includes(searchQuery.toLowerCase()) ||
      insight.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      insight.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );

    return matchesCategory && matchesSearch;
  });

  const popularQueries = [
    "Who has the best attendance record this month?",
    "Which team has the highest absence rate?",
    "What days have the most WFH employees?",
    "Show me the trend of late check-ins",
    "Compare attendance between Engineering and Design teams",
    "When do most employees check in?",
    "What's the average time employees spend at work?",
  ];

  const runSampleQuery = (question: string) => {
    setQuery(question);
    handleGenerateInsight();
  };

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Insights</h1>
          <p className="text-muted-foreground">
            Analyze attendance patterns and get intelligent recommendations
          </p>
        </div>

        <div className="flex gap-2">
          <div className="relative w-full md:w-auto">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search insights..."
              className="pl-9 w-full md:w-[200px]"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Select defaultValue="today">
            <SelectTrigger className="w-[130px]">
              <CalendarClock className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Live Widgets Dashboard */}
      {/* <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {liveWidgets.map(widget => (
          <Card key={widget.id} className="card-hover">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {widget.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold">{widget.value}</div>
                  {widget.delta && (
                    <div className={`text-xs ${widget.delta > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {widget.delta > 0 ? `+${widget.delta}%` : `${widget.delta}%`} from last week
                    </div>
                  )}
                </div>
                <div className={`p-2 rounded-full ${widget.color} text-white`}>
                  {widget.icon}
                </div>
              </div>
            </CardContent>
            <CardFooter className="pt-0">
              <Button 
                variant="ghost" 
                size="sm" 
                className="text-xs w-full justify-start p-0 h-auto"
                onClick={() => runSampleQuery(widget.query)}
              >
                <MessageSquare className="h-3 w-3 mr-1" />
                Query details
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div> */}

      <Tabs defaultValue="insights" className="mt-6">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-3 lg:w-auto">
          <TabsTrigger value="insights">
            <BarChart2 className="h-4 w-4 mr-2" />
            Insights Dashboard
          </TabsTrigger>
          <TabsTrigger value="chat">
            <Bot className="h-4 w-4 mr-2" />
            AI Assistant
          </TabsTrigger>
          <TabsTrigger value="history">
            <Clock className="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        {/* Insights Dashboard Tab */}
        <TabsContent value="insights" className="pt-4">
          <div className="flex gap-2 overflow-auto pb-2 mb-4">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={activeCategory === category.id ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveCategory(category.id)}
              >
                {category.name}
              </Button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Featured Insights</CardTitle>
                  <CardDescription>
                    AI-powered analysis of your organization's attendance
                    patterns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="grid grid-cols-1 gap-4">
                      {[1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className="h-20 bg-muted animate-pulse rounded-md"
                        ></div>
                      ))}
                    </div>
                  ) : filteredInsights.filter((i) => i.starred).length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-muted-foreground">
                        No featured insights available
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {filteredInsights
                        .filter((i) => i.starred)
                        .slice(0, 3)
                        .map((insight) => (
                          <Card
                            key={insight.id}
                            className="relative overflow-hidden"
                          >
                            <div
                              className={`absolute top-0 left-0 w-1 h-full ${
                                insight.category === "attendance"
                                  ? "bg-green-500"
                                  : insight.category === "team"
                                  ? "bg-blue-500"
                                  : insight.category === "trends"
                                  ? "bg-purple-500"
                                  : insight.category === "performance"
                                  ? "bg-amber-500"
                                  : "bg-slate-500"
                              }`}
                            ></div>
                            <CardContent className="p-4">
                              <div className="flex justify-between mb-2">
                                <h3 className="font-medium truncate">
                                  {insight.query}
                                </h3>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6"
                                  onClick={() => toggleStarInsight(insight.id)}
                                >
                                  <Star
                                    className={`h-4 w-4 ${
                                      insight.starred
                                        ? "fill-yellow-400 text-yellow-400"
                                        : ""
                                    }`}
                                  />
                                </Button>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {insight.summary}
                              </p>
                              <div className="flex justify-between items-center mt-2">
                                <div className="flex gap-1">
                                  {insight.tags.map((tag) => (
                                    <Badge
                                      key={tag}
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                                <span className="text-xs text-muted-foreground">
                                  {formatDateTime(insight.generated_at)}
                                </span>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Insights</CardTitle>
                  <CardDescription>
                    The latest attendance analysis and patterns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="h-40 bg-muted animate-pulse rounded-md"></div>
                  ) : filteredInsights.length === 0 ? (
                    <div className="text-center py-10">
                      <p className="text-muted-foreground">
                        No insights available for the selected filters
                      </p>
                    </div>
                  ) : (
                    <ScrollArea className="h-[400px] pr-4">
                      <div className="space-y-4">
                        {filteredInsights.map((insight) => (
                          <Card
                            key={insight.id}
                            className="relative overflow-hidden"
                          >
                            <div
                              className={`absolute top-0 left-0 w-1 h-full ${
                                insight.category === "attendance"
                                  ? "bg-green-500"
                                  : insight.category === "team"
                                  ? "bg-blue-500"
                                  : insight.category === "trends"
                                  ? "bg-purple-500"
                                  : insight.category === "performance"
                                  ? "bg-amber-500"
                                  : "bg-slate-500"
                              }`}
                            ></div>
                            <CardContent className="p-4">
                              <div className="flex justify-between mb-1">
                                <h3 className="font-medium truncate mr-2">
                                  {insight.query}
                                </h3>
                                <div className="flex items-center gap-1">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6"
                                    onClick={() =>
                                      toggleStarInsight(insight.id)
                                    }
                                  >
                                    <Star
                                      className={`h-4 w-4 ${
                                        insight.starred
                                          ? "fill-yellow-400 text-yellow-400"
                                          : ""
                                      }`}
                                    />
                                  </Button>
                                  <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-6 w-6"
                                      >
                                        <Settings className="h-4 w-4" />
                                      </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                      <DropdownMenuItem>
                                        <BookmarkPlus className="mr-2 h-4 w-4" />
                                        Save to collection
                                      </DropdownMenuItem>
                                      <DropdownMenuItem>
                                        <LineChart className="mr-2 h-4 w-4" />
                                        View in depth
                                      </DropdownMenuItem>
                                      <DropdownMenuItem>
                                        <Clipboard className="mr-2 h-4 w-4" />
                                        Copy to clipboard
                                      </DropdownMenuItem>
                                    </DropdownMenuContent>
                                  </DropdownMenu>
                                </div>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {insight.summary}
                              </p>
                              <div className="flex justify-between items-center mt-2">
                                <div className="flex gap-1">
                                  {insight.tags.map((tag) => (
                                    <Badge
                                      key={tag}
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      {tag}
                                    </Badge>
                                  ))}
                                </div>
                                <span className="text-xs text-muted-foreground">
                                  {formatDateTime(insight.generated_at)}
                                </span>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Popular Questions</CardTitle>
                  <CardDescription>
                    Try these questions to get started
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {popularQueries.map((q, i) => (
                      <Button
                        key={i}
                        variant="outline"
                        className="w-full justify-start text-left h-auto py-2"
                        onClick={() => setQuery(q)}
                      >
                        <MessageSquare className="mr-2 h-4 w-4 shrink-0" />
                        <span className="truncate">{q}</span>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Top Trends</CardTitle>
                  <CardDescription>Current attendance patterns</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1 text-sm">
                      <span>Present Rate</span>
                      <span className="font-medium">92%</span>
                    </div>
                    <Progress value={92} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1 text-sm">
                      <span>WFH Rate</span>
                      <span className="font-medium">27%</span>
                    </div>
                    <Progress value={27} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1 text-sm">
                      <span>Absence Rate</span>
                      <span className="font-medium">8%</span>
                    </div>
                    <Progress value={8} className="h-2" />
                  </div>

                  <div>
                    <div className="flex justify-between mb-1 text-sm">
                      <span>On-Time Rate</span>
                      <span className="font-medium">86%</span>
                    </div>
                    <Progress value={86} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* AI Assistant Chat Tab */}
        <TabsContent value="chat" className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <Card className="h-[600px] flex flex-col">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-lg">
                    <Bot className="mr-2 h-5 w-5" />
                    AI Attendance Analyst
                  </CardTitle>
                  <CardDescription>
                    Ask questions about attendance patterns and get intelligent
                    insights
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1 overflow-hidden p-4">
                  <ScrollArea className="h-full pr-4">
                    <div className="space-y-4">
                      {conversation.map((message, index) => (
                        <div
                          key={index}
                          className={`flex ${
                            message.role === "user"
                              ? "justify-end"
                              : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg px-4 py-2 ${
                              message.role === "user"
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted"
                            }`}
                          >
                            {message.content}
                          </div>
                        </div>
                      ))}

                      {generating && (
                        <div className="flex justify-start">
                          <div className="flex items-center space-x-2 bg-muted max-w-[80%] rounded-lg px-4 py-2">
                            <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse delay-0"></div>
                            <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse delay-150"></div>
                            <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse delay-300"></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>

                <CardFooter className="p-4 pt-2">
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleGenerateInsight();
                    }}
                    className="w-full"
                  >
                    <div className="flex gap-2">
                      <Textarea
                        placeholder="Ask about attendance patterns, trends, or specific insights..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="min-h-[60px] flex-1 resize-none"
                      />
                      <Button
                        type="submit"
                        className="h-auto"
                        disabled={generating || !query.trim()}
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </form>
                </CardFooter>
              </Card>
            </div>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Questions</CardTitle>
                  <CardDescription>Common attendance queries</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {popularQueries.slice(0, 5).map((q, i) => (
                      <Button
                        key={i}
                        variant="outline"
                        className="w-full justify-start text-left h-auto py-2"
                        onClick={() => runSampleQuery(q)}
                      >
                        <ChevronRight className="mr-2 h-4 w-4 shrink-0" />
                        <span className="truncate">{q}</span>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Conversations</CardTitle>
                  <CardDescription>Your recent AI interactions</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {insights.slice(0, 5).map((insight) => (
                      <Button
                        key={insight.id}
                        variant="outline"
                        className="w-full justify-start text-left h-auto py-2"
                        onClick={() => runSampleQuery(insight.query)}
                      >
                        <MessageSquare className="mr-2 h-4 w-4 shrink-0" />
                        <span className="truncate">{insight.query}</span>
                      </Button>
                    ))}

                    {insights.length === 0 && (
                      <div className="text-center py-4">
                        <p className="text-sm text-muted-foreground">
                          No recent conversations
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="pt-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
                <div>
                  <CardTitle>Insight History</CardTitle>
                  <CardDescription>
                    Comprehensive record of all generated insights
                  </CardDescription>
                </div>

                <div className="flex gap-2">
                  <Select defaultValue="all">
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="attendance">Attendance</SelectItem>
                      <SelectItem value="team">Team Analysis</SelectItem>
                      <SelectItem value="trends">Trends</SelectItem>
                      <SelectItem value="performance">Performance</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select defaultValue="latest">
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Sort By" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="latest">Latest First</SelectItem>
                      <SelectItem value="oldest">Oldest First</SelectItem>
                      <SelectItem value="alphabetical">Alphabetical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <>
                      {[1, 2, 3, 4, 5].map((i) => (
                        <TableRow key={i}>
                          <TableCell colSpan={4}>
                            <div className="h-8 bg-muted animate-pulse rounded-md"></div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </>
                  ) : filteredInsights.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="h-24 text-center">
                        No insights found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredInsights.map((insight) => (
                      <TableRow key={insight.id}>
                        <TableCell className="font-medium">
                          <div className="max-w-[300px] truncate">
                            {insight.query}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={
                              insight.category === "attendance"
                                ? "bg-green-50 text-green-700 border-green-200"
                                : insight.category === "team"
                                ? "bg-blue-50 text-blue-700 border-blue-200"
                                : insight.category === "trends"
                                ? "bg-purple-50 text-purple-700 border-purple-200"
                                : insight.category === "performance"
                                ? "bg-amber-50 text-amber-700 border-amber-200"
                                : "bg-slate-50 text-slate-700 border-slate-200"
                            }
                          >
                            {insight.category.charAt(0).toUpperCase() +
                              insight.category.slice(1)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {formatDateTime(insight.generated_at)}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => runSampleQuery(insight.query)}
                            >
                              <MessageSquare className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => toggleStarInsight(insight.id)}
                            >
                              <Star
                                className={`h-4 w-4 ${
                                  insight.starred
                                    ? "fill-yellow-400 text-yellow-400"
                                    : ""
                                }`}
                              />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIInsightsPage;
