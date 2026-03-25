'use client';

/**
 * Self-Improvement Metrics Dashboard (SI-006)
 * 
 * Displays real-time metrics for the RPA self-improvement system:
 * - System health status
 * - Cycle statistics
 * - Pattern mutation history
 * - Gap closure progress
 * - Confidence trends
 */

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Activity,
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  Zap,
  Target,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  BarChart3,
  Layers,
  GitBranch,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Types for API responses
interface SystemHealth {
  status: string;
  total_patterns: number;
  strong_patterns: number;
  weak_patterns: number;
  deprecated_patterns: number;
  avg_pattern_strength: number;
  avg_confidence: number;
  pending_mutations: number;
  open_gaps: number;
  recent_success_rate: number;
  learning_velocity: number;
  last_cycle_time: string | null;
}

interface CycleStats {
  total_cycles: number;
  total_patterns_evaluated: number;
  total_patterns_reinforced: number;
  total_patterns_decayed: number;
  total_patterns_mutated: number;
  total_successful_mutations: number;
  total_gaps_detected: number;
  total_gaps_closed: number;
  avg_cycle_duration: number;
}

interface MutationStats {
  total_mutations: number;
  successful_mutations: number;
  by_type: Record<string, number>;
  patterns_versioned: number;
  patterns_deprecated: number;
  patterns_restored: number;
}

interface GapStats {
  total_gaps_detected: number;
  total_goals_created: number;
  total_goals_completed: number;
  pending_goals: number;
  in_progress_goals: number;
  completed_goals: number;
  success_rate: number;
}

interface TrendDataPoint {
  timestamp: string;
  success_rate: number;
  patterns_evaluated: number;
  patterns_reinforced: number;
  patterns_mutated: number;
  gaps_detected: number;
  gaps_closed: number;
}

interface ConfidenceTrends {
  period_days: number;
  data_points: TrendDataPoint[];
  trend_direction: 'improving' | 'declining' | 'stable';
  avg_change_per_day: number;
}

interface DashboardSummary {
  timestamp: string;
  health: SystemHealth;
  cycle_stats: CycleStats;
  recent_cycles: Array<{
    cycle_id: string;
    patterns_evaluated: number;
    patterns_reinforced: number;
    patterns_mutated: number;
    gaps_detected: number;
    gaps_closed: number;
    duration_seconds: number;
  }>;
  mutation_stats: MutationStats;
  gap_stats: GapStats;
  trends: ConfidenceTrends;
  learning_velocity: {
    patterns_per_hour: number;
    mutations_per_hour: number;
    gap_closures_per_hour: number;
    improvement_rate: number;
  };
}

// Metric Card Component
function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  color = 'default',
}: {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'stable';
  color?: 'default' | 'success' | 'warning' | 'destructive';
}) {
  const colorClasses = {
    default: 'text-primary',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    destructive: 'text-red-600',
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={cn('h-4 w-4', colorClasses[color])} />
      </CardHeader>
      <CardContent>
        <div className={cn('text-2xl font-bold', colorClasses[color])}>{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2">
            {trend === 'up' && <TrendingUp className="h-3 w-3 text-green-600 mr-1" />}
            {trend === 'down' && <TrendingDown className="h-3 w-3 text-red-600 mr-1" />}
            {trend === 'stable' && <Minus className="h-3 w-3 text-yellow-600 mr-1" />}
            <span className={cn(
              'text-xs',
              trend === 'up' && 'text-green-600',
              trend === 'down' && 'text-red-600',
              trend === 'stable' && 'text-yellow-600'
            )}>
              {trend === 'up' ? 'Improving' : trend === 'down' ? 'Declining' : 'Stable'}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Progress Bar with Label
function LabeledProgress({
  label,
  value,
  max,
  showPercentage = true,
}: {
  label: string;
  value: number;
  max: number;
  showPercentage?: boolean;
}) {
  const percentage = max > 0 ? Math.round((value / max) * 100) : 0;
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        {showPercentage && (
          <span className="text-muted-foreground">{percentage}%</span>
        )}
      </div>
      <Progress value={percentage} className="h-2" />
    </div>
  );
}

// Status Badge
function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'success' | 'warning' | 'destructive'> = {
    healthy: 'success',
    degraded: 'warning',
    error: 'destructive',
    unknown: 'default',
  };

  const icons: Record<string, React.ElementType> = {
    healthy: CheckCircle2,
    degraded: AlertCircle,
    error: AlertCircle,
    unknown: AlertCircle,
  };

  const Icon = icons[status] || AlertCircle;

  return (
    <Badge variant={variants[status] || 'default'} className="gap-1">
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

// Trend Chart (Simple Bar Visualization)
function TrendChart({ data }: { data: TrendDataPoint[] }) {
  if (data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-muted-foreground">
        No trend data available
      </div>
    );
  }

  const maxRate = Math.max(...data.map(d => d.success_rate), 1);

  return (
    <div className="h-32 flex items-end gap-1">
      {data.slice(-20).map((point, i) => {
        const height = (point.success_rate / maxRate) * 100;
        return (
          <div
            key={i}
            className="flex-1 bg-primary/20 hover:bg-primary/40 rounded-t transition-colors"
            style={{ height: `${height}%`, minHeight: '4px' }}
            title={`${new Date(point.timestamp).toLocaleTimeString()}: ${(point.success_rate * 100).toFixed(1)}%`}
          />
        );
      })}
    </div>
  );
}

export function SIDashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  // Fetch dashboard data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/si/dashboard');
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      console.error('Error fetching SI dashboard:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  // Trigger improvement cycle
  const triggerCycle = async () => {
    try {
      setTriggering(true);
      const response = await fetch('/api/si/trigger', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Failed to trigger cycle');
      }
      // Refresh data after trigger
      setTimeout(fetchData, 1000);
    } catch (err) {
      console.error('Error triggering cycle:', err);
    } finally {
      setTriggering(false);
    }
  };

  // Initial fetch and polling
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  // Loading state
  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Error Loading Dashboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{error}</p>
          <Button onClick={fetchData} variant="outline" className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  // No data state
  if (!data) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const { health, cycle_stats, mutation_stats, gap_stats, trends, learning_velocity, recent_cycles } = data;

  return (
    <ScrollArea className="h-full">
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              Self-Improvement Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">
              Monitor the RPA autonomous learning system
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={health.status} />
            <Button onClick={fetchData} variant="outline" size="sm">
              <RefreshCw className={cn('h-4 w-4 mr-2', loading && 'animate-spin')} />
              Refresh
            </Button>
            <Button onClick={triggerCycle} disabled={triggering} size="sm">
              <Zap className="h-4 w-4 mr-2" />
              Run Cycle
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Patterns"
            value={health.total_patterns.toLocaleString()}
            description={`${health.strong_patterns} strong, ${health.weak_patterns} weak`}
            icon={Layers}
            color={health.weak_patterns > health.strong_patterns ? 'warning' : 'success'}
          />
          <MetricCard
            title="Avg Confidence"
            value={`${(health.avg_confidence * 100).toFixed(1)}%`}
            description="Pattern confidence score"
            icon={Target}
            trend={trends.trend_direction === 'improving' ? 'up' : trends.trend_direction === 'declining' ? 'down' : 'stable'}
            color={health.avg_confidence > 0.7 ? 'success' : health.avg_confidence > 0.4 ? 'warning' : 'destructive'}
          />
          <MetricCard
            title="Learning Velocity"
            value={`${learning_velocity.patterns_per_hour.toFixed(1)}/hr`}
            description="Patterns improved per hour"
            icon={Activity}
            color={learning_velocity.patterns_per_hour > 5 ? 'success' : 'default'}
          />
          <MetricCard
            title="Success Rate"
            value={`${(health.recent_success_rate * 100).toFixed(1)}%`}
            description="Recent pattern success"
            icon={CheckCircle2}
            color={health.recent_success_rate > 0.7 ? 'success' : health.recent_success_rate > 0.5 ? 'warning' : 'destructive'}
          />
        </div>

        {/* Charts Row */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Confidence Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Confidence Trend
              </CardTitle>
              <CardDescription>
                Last {trends.period_days} days ({trends.data_points.length} data points)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <TrendChart data={trends.data_points} />
              <div className="mt-4 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Direction:</span>
                <Badge variant={
                  trends.trend_direction === 'improving' ? 'default' :
                  trends.trend_direction === 'declining' ? 'destructive' : 'secondary'
                }>
                  {trends.trend_direction === 'improving' && <TrendingUp className="h-3 w-3 mr-1" />}
                  {trends.trend_direction === 'declining' && <TrendingDown className="h-3 w-3 mr-1" />}
                  {trends.trend_direction === 'stable' && <Minus className="h-3 w-3 mr-1" />}
                  {trends.trend_direction.charAt(0).toUpperCase() + trends.trend_direction.slice(1)}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Cycle Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Cycle Activity
              </CardTitle>
              <CardDescription>
                {cycle_stats.total_cycles} total cycles completed
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <LabeledProgress
                label="Patterns Reinforced"
                value={cycle_stats.total_patterns_reinforced}
                max={cycle_stats.total_patterns_evaluated || 1}
              />
              <LabeledProgress
                label="Successful Mutations"
                value={cycle_stats.total_successful_mutations}
                max={cycle_stats.total_patterns_mutated || 1}
              />
              <LabeledProgress
                label="Gaps Closed"
                value={cycle_stats.total_gaps_closed}
                max={cycle_stats.total_gaps_detected || 1}
              />
              <Separator />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Avg Duration</span>
                  <p className="font-medium">{cycle_stats.avg_cycle_duration.toFixed(2)}s</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Decayed</span>
                  <p className="font-medium">{cycle_stats.total_patterns_decayed}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Stats */}
        <div className="grid gap-4 md:grid-cols-3">
          {/* Mutation Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Mutations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Mutations</span>
                <span className="font-medium">{mutation_stats.total_mutations}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Successful</span>
                <span className="font-medium text-green-600">{mutation_stats.successful_mutations}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Patterns Versioned</span>
                <span className="font-medium">{mutation_stats.patterns_versioned}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Deprecated</span>
                <span className="font-medium text-red-600">{mutation_stats.patterns_deprecated}</span>
              </div>
              <Separator />
              <div className="text-sm text-muted-foreground">
                <p className="font-medium mb-2">By Type:</p>
                <div className="grid grid-cols-2 gap-1">
                  {Object.entries(mutation_stats.by_type).map(([type, count]) => (
                    <div key={type} className="flex justify-between">
                      <span className="capitalize">{type}:</span>
                      <span>{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Gap Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Gap Closure
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Detected</span>
                <span className="font-medium">{gap_stats.total_gaps_detected}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Goals Created</span>
                <span className="font-medium">{gap_stats.total_goals_created}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Goals Completed</span>
                <span className="font-medium text-green-600">{gap_stats.total_goals_completed}</span>
              </div>
              <Separator />
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div>
                  <p className="text-yellow-600 font-medium">{gap_stats.pending_goals}</p>
                  <p className="text-muted-foreground text-xs">Pending</p>
                </div>
                <div>
                  <p className="text-blue-600 font-medium">{gap_stats.in_progress_goals}</p>
                  <p className="text-muted-foreground text-xs">In Progress</p>
                </div>
                <div>
                  <p className="text-green-600 font-medium">{gap_stats.completed_goals}</p>
                  <p className="text-muted-foreground text-xs">Completed</p>
                </div>
              </div>
              <div className="mt-2">
                <LabeledProgress
                  label="Success Rate"
                  value={gap_stats.success_rate * 100}
                  max={100}
                />
              </div>
            </CardContent>
          </Card>

          {/* Velocity Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Learning Velocity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Patterns/Hour</span>
                <span className="font-medium">{learning_velocity.patterns_per_hour.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mutations/Hour</span>
                <span className="font-medium">{learning_velocity.mutations_per_hour.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Gap Closures/Hour</span>
                <span className="font-medium">{learning_velocity.gap_closures_per_hour.toFixed(1)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Improvement Rate</span>
                <span className="font-medium">{learning_velocity.improvement_rate.toFixed(1)}/hr</span>
              </div>
              <Separator />
              <div className="text-sm text-muted-foreground">
                <p className="font-medium mb-1">System State:</p>
                <div className="flex justify-between">
                  <span>Pending Mutations:</span>
                  <span>{health.pending_mutations}</span>
                </div>
                <div className="flex justify-between">
                  <span>Open Gaps:</span>
                  <span>{health.open_gaps}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Cycles */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Cycles
            </CardTitle>
            <CardDescription>
              Last {recent_cycles.length} improvement cycles
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48">
              {recent_cycles.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">No cycles recorded</p>
              ) : (
                <div className="space-y-2">
                  {recent_cycles.map((cycle, i) => (
                    <div key={cycle.cycle_id || i} className="flex items-center justify-between p-2 rounded bg-muted/50">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {cycle.cycle_id?.slice(-8) || `cycle-${i}`}
                        </Badge>
                        <span className="text-sm">
                          {cycle.patterns_evaluated} evaluated, {cycle.patterns_reinforced} reinforced
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{cycle.patterns_mutated} mutated</span>
                        <span>{cycle.gaps_closed} gaps closed</span>
                        <span>{cycle.duration_seconds.toFixed(2)}s</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Last Update */}
        <div className="text-center text-sm text-muted-foreground">
          Last updated: {new Date(data.timestamp).toLocaleString()}
          {health.last_cycle_time && (
            <span className="ml-4">
              Last cycle: {new Date(health.last_cycle_time).toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}
