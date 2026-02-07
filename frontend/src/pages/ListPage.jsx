import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { format, parseISO } from "date-fns";
import { 
  Plus, 
  Search, 
  Filter, 
  Calendar, 
  Flag, 
  MoreHorizontal,
  CheckCircle2,
  Circle,
  Clock,
  Trash2,
  Edit2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { taskApi, categoryApi } from "@/lib/api";
import { TaskModal } from "@/components/TaskModal";
import { getColorClasses } from "@/components/CategoryManager";
import { toast } from "sonner";

const STATUS_CONFIG = {
  todo: { label: "To Do", icon: Circle, color: "text-muted-foreground" },
  in_progress: { label: "In Progress", icon: Clock, color: "text-[#183347]" },
  done: { label: "Done", icon: CheckCircle2, color: "text-[#1C3829]" },
};

const PRIORITY_CONFIG = {
  low: { label: "Low", color: "text-[#1C3829]", bg: "bg-[#DBEDDB]" },
  medium: { label: "Medium", color: "text-[#183347]", bg: "bg-[#D3E5EF]" },
  high: { label: "High", color: "text-[#49290E]", bg: "bg-[#FADEC9]" },
  urgent: { label: "Urgent", color: "text-[#5D1715]", bg: "bg-[#FFE2DD]" },
};

export default function ListPage() {
  const [tasks, setTasks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");

  const fetchData = useCallback(async () => {
    try {
      const [tasksRes, catsRes] = await Promise.all([
        taskApi.getAll(),
        categoryApi.getAll(),
      ]);
      setTasks(tasksRes.data);
      setCategories(catsRes.data);
    } catch (err) {
      console.error("Failed to fetch data", err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getCategoryById = (id) => categories.find(c => c.id === id);

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || task.status === statusFilter;
    const matchesPriority = priorityFilter === "all" || task.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const handleTaskClick = (task) => {
    setSelectedTask(task);
    setModalOpen(true);
  };

  const handleNewTask = () => {
    setSelectedTask(null);
    setModalOpen(true);
  };

  const handleStatusToggle = async (task) => {
    const newStatus = task.status === "done" ? "todo" : "done";
    try {
      await taskApi.update(task.id, { status: newStatus });
      toast.success(newStatus === "done" ? "Task completed!" : "Task reopened");
      fetchData();
    } catch (err) {
      toast.error("Failed to update task");
    }
  };

  const handleDelete = async (task) => {
    try {
      await taskApi.delete(task.id);
      toast.success("Task deleted");
      fetchData();
    } catch (err) {
      toast.error("Failed to delete task");
    }
  };

  return (
    <div className="space-y-6" data-testid="list-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight">
            All Tasks
          </h1>
          <p className="text-muted-foreground mt-1">
            {filteredTasks.length} of {tasks.length} tasks
          </p>
        </div>
        <Button onClick={handleNewTask} className="gap-2" data-testid="list-new-task-btn">
          <Plus className="w-4 h-4" />
          New Task
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tasks..."
            className="pl-10"
            data-testid="search-input"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40" data-testid="status-filter">
            <Filter className="w-4 h-4 mr-2 text-muted-foreground" />
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="todo">To Do</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="done">Done</SelectItem>
          </SelectContent>
        </Select>

        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-40" data-testid="priority-filter">
            <Flag className="w-4 h-4 mr-2 text-muted-foreground" />
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="border border-border/50 rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-[hsl(var(--sidebar))] hover:bg-[hsl(var(--sidebar))]">
              <TableHead className="w-12"></TableHead>
              <TableHead>Task</TableHead>
              <TableHead className="w-32">Status</TableHead>
              <TableHead className="w-32">Priority</TableHead>
              <TableHead className="w-32">Category</TableHead>
              <TableHead className="w-32">Due Date</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTasks.length > 0 ? (
              filteredTasks.map((task) => {
                const statusConfig = STATUS_CONFIG[task.status];
                const priorityConfig = PRIORITY_CONFIG[task.priority];
                const category = getCategoryById(task.category_id);
                const categoryColors = category ? getColorClasses(category.color) : null;
                const StatusIcon = statusConfig.icon;

                return (
                  <TableRow 
                    key={task.id} 
                    className="group"
                    data-testid={`task-row-${task.id}`}
                  >
                    <TableCell>
                      <Checkbox
                        checked={task.status === "done"}
                        onCheckedChange={() => handleStatusToggle(task)}
                        className="data-[state=checked]:bg-[#1C3829] data-[state=checked]:border-[#1C3829]"
                        data-testid={`task-checkbox-${task.id}`}
                      />
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => handleTaskClick(task)}
                        className="text-left w-full"
                      >
                        <p className={cn(
                          "font-medium text-sm",
                          task.status === "done" && "line-through text-muted-foreground"
                        )}>
                          {task.title}
                        </p>
                        {task.description && (
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                            {task.description}
                          </p>
                        )}
                      </button>
                    </TableCell>
                    <TableCell>
                      <span className={cn(
                        "inline-flex items-center gap-1.5 text-xs font-medium",
                        statusConfig.color
                      )}>
                        <StatusIcon className="w-3.5 h-3.5" />
                        {statusConfig.label}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium",
                        priorityConfig.bg, priorityConfig.color
                      )}>
                        {priorityConfig.label}
                      </span>
                    </TableCell>
                    <TableCell>
                      {category ? (
                        <span className={cn(
                          "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                          categoryColors.bg, categoryColors.text
                        )}>
                          {category.name}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {task.due_date ? (
                        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Calendar className="w-3.5 h-3.5" />
                          {format(parseISO(task.due_date), "MMM d, yyyy")}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
                            data-testid={`task-menu-${task.id}`}
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleTaskClick(task)}>
                            <Edit2 className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(task)}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center">
                  <p className="text-muted-foreground">No tasks found</p>
                  <Button
                    variant="link"
                    onClick={handleNewTask}
                    className="mt-2"
                  >
                    Create your first task
                  </Button>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
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
