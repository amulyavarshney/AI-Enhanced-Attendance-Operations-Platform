
import React, { useEffect, useState } from "react";
import { Bot, ChevronUp, MessageSquare, Search, Send, Sparkles, Star } from "lucide-react";
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
import { AIInsight } from "@/types";
import { fetchAIInsights, generateAIInsight } from "@/services/mockData";
import { formatDateTime } from "@/utils/formatters";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { toast } from "@/hooks/use-toast";

const AIInsightsPage: React.FC = () => {
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [query, setQuery] = useState("");
  const [conversation, setConversation] = useState<{ role: "user" | "ai"; content: string }[]>([]);
  
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const insightsData = await fetchAIInsights();
        setInsights(insightsData);
        
        // Add AI welcome message
        setConversation([
          { 
            role: "ai", 
            content: "Hello! I'm your AI Attendance Analyst. I can help you understand attendance patterns, trends, and provide insights about your organization. What would you like to know?" 
          }
        ]);
      } catch (error) {
        console.error("Error fetching AI insights:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleGenerateInsight = async () => {
    if (!query.trim()) return;
    
    // Add user query to conversation
    setConversation(prev => [...prev, { role: "user", content: query }]);
    
    setGenerating(true);
    try {
      // Add temporary loading message
      setConversation(prev => [...prev, { role: "ai", content: "Analyzing attendance data..." }]);
      
      const insight = await generateAIInsight(query);
      
      // Replace loading message with actual response
      setConversation(prev => prev.slice(0, -1).concat({ role: "ai", content: insight.summary }));
      
      // Add to insights list if not already present
      setInsights(prev => {
        if (!prev.some(i => i.id === insight.id)) {
          return [insight, ...prev];
        }
        return prev;
      });
      
      setQuery("");
    } catch (error) {
      console.error("Error generating AI insight:", error);
      // Replace loading message with error
      setConversation(prev => prev.slice(0, -1).concat({ 
        role: "ai", 
        content: "I'm sorry, I encountered an error while analyzing the data. Please try again." 
      }));
      
      toast({
        title: "Error",
        description: "Failed to generate AI insight. Please try again.",
        variant: "destructive"
      });
    } finally {
      setGenerating(false);
    }
  };
  
  const popularQueries = [
    "Who has the best attendance record this month?",
    "Which team has the highest absence rate?",
    "What days have the most WFH employees?",
    "Show me the trend of late check-ins",
    "Compare attendance between Engineering and Design teams"
  ];
  
  return (
    <div className="space-y-6 animate-fade-in">
      <h1 className="text-3xl font-bold tracking-tight">AI Insights</h1>
      
      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bot className="mr-2 h-5 w-5" />
                AI Attendance Analyst
              </CardTitle>
              <CardDescription>
                Ask questions about attendance patterns and trends
              </CardDescription>
            </CardHeader>
            
            <CardContent className="flex-1 overflow-y-auto">
              <div className="space-y-4">
                {conversation.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
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
                      <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse"></div>
                      <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse"></div>
                      <div className="h-2 w-2 bg-foreground/70 rounded-full animate-pulse"></div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            
            <CardFooter className="pt-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleGenerateInsight();
                }}
                className="grid w-full gap-2"
              >
                <Textarea
                  placeholder="Ask about attendance patterns, trends, or specific insights..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="min-h-[80px]"
                />
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={generating || !query.trim()}
                >
                  <Send className="mr-2 h-4 w-4" />
                  Generate Insight
                </Button>
              </form>
            </CardFooter>
          </Card>
        </div>
        
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Popular Queries</CardTitle>
              <CardDescription>
                Try these sample questions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {popularQueries.map((q, i) => (
                  <Button 
                    key={i} 
                    variant="outline" 
                    className="w-full justify-start text-left h-auto py-2"
                    onClick={() => {
                      setQuery(q);
                    }}
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
              <CardTitle>Recent Insights</CardTitle>
              <CardDescription>
                Previously generated insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="py-4 text-center">
                  <p className="text-sm text-muted-foreground">Loading insights...</p>
                </div>
              ) : insights.length === 0 ? (
                <div className="py-4 text-center">
                  <p className="text-sm text-muted-foreground">No insights yet</p>
                </div>
              ) : (
                <Accordion type="single" collapsible className="w-full">
                  {insights.slice(0, 5).map((insight, index) => (
                    <AccordionItem key={insight.id} value={`item-${index}`}>
                      <AccordionTrigger className="text-left">
                        <div className="truncate pr-2">
                          {insight.query}
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="space-y-2">
                          <p>{insight.summary}</p>
                          <p className="text-xs text-muted-foreground">
                            Generated on {formatDateTime(insight.generatedAt)}
                          </p>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      
      <h2 className="text-2xl font-bold mt-8">Featured Insights</h2>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {insights.slice(0, 3).map(insight => (
          <Card key={insight.id} className="card-hover">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <CardTitle className="text-lg">{insight.query}</CardTitle>
                <Sparkles className="h-5 w-5 text-amber-500" />
              </div>
            </CardHeader>
            <CardContent>
              <p>{insight.summary}</p>
            </CardContent>
            <CardFooter className="flex justify-between pt-2">
              <Button variant="ghost" size="sm">
                <Star className="h-4 w-4 mr-1" />
                Save
              </Button>
              <p className="text-xs text-muted-foreground">
                {formatDateTime(insight.generatedAt)}
              </p>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default AIInsightsPage;
