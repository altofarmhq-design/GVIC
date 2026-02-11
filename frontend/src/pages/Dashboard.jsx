import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { format, parseISO, isBefore, addDays } from "date-fns";
import { 
  CheckCircle2, 
  Clock, 
  ListTodo, 
  AlertTriangle,
  Plus,
  TrendingUp,
  Calendar
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { taskApi, categoryApi } from "@/lib/api";
import { TaskCard } from "@/components/TaskCard";
import { TaskModal } from "@/components/TaskModal";

const StatCard = ({ title, value, icon: Icon, trend, className }) => (
  <Card className={cn("border-border/50", className)}>
    <CardContent className="p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-semibold mt-1 font-heading">{value}</p>
          {trend && (
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </div>
        <div className="p-3 bg-secondary rounded-lg">
          <Icon className="w-5 h-5 text-muted-foreground" strokeWidth={1.75} />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const [stats, setStats] = useState({ total: 0, todo: 0, in_progress: 0, done: 0, overdue: 0, due_soon: 0 });
  const [tasks, setTasks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const fetchData = async () => {
    try {
      const [statsRes, tasksRes, catsRes] = await Promise.all([
        taskApi.getStats(),
        taskApi.getAll(),
        categoryApi.getAll(),
      ]);
      setStats(statsRes.data);
      setTasks(tasksRes.data);
      setCategories(catsRes.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getCategoryById = (id) => categories.find(c => c.id === id);

  const completionRate = stats.total > 0 
    ? Math.round((stats.done / stats.total) * 100) 
    : 0;

  const upcomingTasks = tasks
    .filter(t => t.status !== "done" && t.due_date)
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .slice(0, 5);

  const recentTasks = [...tasks]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  const handleTaskClick = (task) => {
    setSelectedTask(task);
    setModalOpen(true);
  };

  const handleNewTask = () => {
    setSelectedTask(null);
    setModalOpen(true);
  };

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight">
            Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            {format(new Date(), "EEEE, MMMM d")}
          </p>
        </div>
        <Button onClick={handleNewTask} className="gap-2" data-testid="new-task-btn">
          <Plus className="w-4 h-4" />
          New Task
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Tasks" 
          value={stats.total} 
          icon={ListTodo}
        />
        <StatCard 
          title="In Progress" 
          value={stats.in_progress} 
          icon={Clock}
        />
        <StatCard 
          title="Completed" 
          value={stats.done} 
          icon={CheckCircle2}
        />
        <StatCard 
          title="Overdue" 
          value={stats.overdue} 
          icon={AlertTriangle}
          className={stats.overdue > 0 ? "border-[#FFE2DD]" : ""}
        />
      </div>

      {/* Progress Section */}
      <Card className="border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="font-heading text-xl font-medium">
            Overall Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Progress value={completionRate} className="h-2 flex-1" />
            <span className="text-2xl font-semibold font-heading w-16 text-right">
              {completionRate}%
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            {stats.done} of {stats.total} tasks completed
          </p>
        </CardContent>
      </Card>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Tasks */}
        <Card className="border-border/50">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="font-heading text-xl font-medium flex items-center gap-2">
              <Calendar className="w-5 h-5 text-muted-foreground" />
              Due Soon
            </CardTitle>
            {stats.due_soon > 0 && (
              <span className="text-xs px-2 py-1 bg-[#FADEC9] text-[#49290E] rounded-full font-medium">
                {stats.due_soon} tasks
              </span>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            {upcomingTasks.length > 0 ? (
              upcomingTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  category={getCategoryById(task.category_id)}
                  onClick={() => handleTaskClick(task)}
                />
              ))
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No upcoming tasks
              </p>
            )}
          </CardContent>
        </Card>

        {/* Recent Tasks */}
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="font-heading text-xl font-medium flex items-center gap-2">
              <Clock className="w-5 h-5 text-muted-foreground" />
              Recently Added
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recentTasks.length > 0 ? (
              recentTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  category={getCategoryById(task.category_id)}
                  onClick={() => handleTaskClick(task)}
                />
              ))
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No tasks yet. Create your first task!
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Task Modal */}
      <TaskModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask}
        onSuccess={fetchData}
      />
    </div>
  );
}
