'use client';

/**
 * Dashboard Component
 * 
 * Main dashboard view showing learning progress, stats, and quick actions.
 */

import { useEffect } from 'react';
import { useAppStore, useAuthStore } from '@/lib/stores';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  BookOpen, 
  Flame, 
  Clock, 
  Target, 
  TrendingUp,
  GraduationCap,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export function Dashboard() {
  const { user } = useAuthStore();
  const { 
    dashboard, 
    progress, 
    loadDashboard, 
    loadProgress,
    dashboardLoading,
    setCurrentView,
  } = useAppStore();
  
  useEffect(() => {
    loadDashboard();
    loadProgress();
  }, [loadDashboard, loadProgress]);
  
  if (dashboardLoading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-6 bg-muted rounded w-1/3" />
            </CardHeader>
            <CardContent>
              <div className="h-20 bg-muted rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  
  const stats = [
    {
      label: 'Words Learned',
      value: progress?.vocabulary.mastered || 0,
      total: progress?.vocabulary.total || 0,
      icon: BookOpen,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Current Streak',
      value: progress?.streaks.current || 0,
      suffix: 'days',
      icon: Flame,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
    },
    {
      label: 'Time Spent',
      value: Math.round(progress?.total_time_spent || 0),
      suffix: 'min',
      icon: Clock,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Grammar Rules',
      value: progress?.grammar.mastered || 0,
      total: progress?.grammar.total || 0,
      icon: Target,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
    },
  ];
  
  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back, {user?.username}! 👋
          </h1>
          <p className="text-muted-foreground mt-1">
            Ready to continue your learning journey?
          </p>
        </div>
        <Button onClick={() => setCurrentView('vocabulary')}>
          <Sparkles className="w-4 h-4 mr-2" />
          Start Learning
        </Button>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">
                    {stat.value}
                    {stat.suffix && <span className="text-sm font-normal ml-1">{stat.suffix}</span>}
                  </p>
                  {stat.total !== undefined && stat.total > 0 && (
                    <p className="text-xs text-muted-foreground">of {stat.total}</p>
                  )}
                </div>
              </div>
              {stat.total !== undefined && stat.total > 0 && (
                <Progress 
                  value={(stat.value / stat.total) * 100} 
                  className="mt-3 h-1.5"
                />
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Due Items Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vocabulary Due */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-lg">Vocabulary Due</CardTitle>
              <CardDescription>
                Words ready for review
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-lg">
              {dashboard?.due_vocabulary || 0}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-2">
                  Review your vocabulary to strengthen memory retention using spaced repetition.
                </p>
                <Button 
                  onClick={() => setCurrentView('vocabulary')}
                  disabled={!dashboard?.due_vocabulary}
                >
                  Review Now
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
              <div className="hidden md:block">
                <BookOpen className="w-16 h-16 text-muted-foreground/30" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Progress Overview */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Learning Progress</CardTitle>
            <CardDescription>
              Your vocabulary proficiency breakdown
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <ProgressItem 
                label="Mastered" 
                value={progress?.vocabulary.mastered || 0}
                total={progress?.vocabulary.total || 1}
                color="bg-green-500"
              />
              <ProgressItem 
                label="Proficient" 
                value={progress?.vocabulary.learning || 0}
                total={progress?.vocabulary.total || 1}
                color="bg-blue-500"
              />
              <ProgressItem 
                label="Learning" 
                value={progress?.vocabulary.new || 0}
                total={progress?.vocabulary.total || 1}
                color="bg-yellow-500"
              />
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Recommended Actions */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary" />
            Recommended Next
          </CardTitle>
          <CardDescription>
            Personalized suggestions based on your progress
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {dashboard?.recommended_next?.map((item, index) => (
              <Button
                key={item}
                variant="outline"
                className="h-auto py-4 justify-start"
                onClick={() => setCurrentView(item as 'vocabulary' | 'grammar' | 'reading' | 'writing')}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    {index === 0 && <BookOpen className="w-5 h-5 text-primary" />}
                    {index === 1 && <Target className="w-5 h-5 text-primary" />}
                    {index === 2 && <GraduationCap className="w-5 h-5 text-primary" />}
                  </div>
                  <div className="text-left">
                    <p className="font-medium capitalize">{item}</p>
                    <p className="text-xs text-muted-foreground">Continue learning</p>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper component for progress items
function ProgressItem({ 
  label, 
  value, 
  total, 
  color 
}: { 
  label: string; 
  value: number; 
  total: number; 
  color: string;
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  
  return (
    <div className="flex items-center gap-3">
      <div className="w-20 text-sm text-muted-foreground">{label}</div>
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="w-12 text-sm text-right">{value}</div>
    </div>
  );
}
