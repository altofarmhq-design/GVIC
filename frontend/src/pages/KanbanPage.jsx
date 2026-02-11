import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { taskApi, categoryApi } from "@/lib/api";
import { TaskCard } from "@/components/TaskCard";
import { TaskModal } from "@/components/TaskModal";
import { toast } from "sonner";

const COLUMNS = [
  { id: "todo", title: "To Do", color: "bg-[#E3E2E0]" },
  { id: "in_progress", title: "In Progress", color: "bg-[#D3E5EF]" },
  { id: "done", title: "Done", color: "bg-[#DBEDDB]" },
];

export default function KanbanPage() {
  const [tasks, setTasks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [defaultStatus, setDefaultStatus] = useState("todo");
  const [draggedTask, setDraggedTask] = useState(null);

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

  const getTasksByStatus = (status) => tasks.filter(t => t.status === status);

  const handleTaskClick = (task) => {
    setSelectedTask(task);
    setModalOpen(true);
  };

  const handleNewTask = (status) => {
    setSelectedTask(null);
    setDefaultStatus(status);
    setModalOpen(true);
  };

  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", task.id);
    // Add dragging class
    e.target.classList.add("opacity-50", "rotate-2");
  };

  const handleDragEnd = (e) => {
    e.target.classList.remove("opacity-50", "rotate-2");
    setDraggedTask(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = async (e, newStatus) => {
    e.preventDefault();
    if (!draggedTask || draggedTask.status === newStatus) return;

    try {
      await taskApi.update(draggedTask.id, { status: newStatus });
      toast.success(`Task moved to ${COLUMNS.find(c => c.id === newStatus)?.title}`);
      fetchData();
    } catch (err) {
      toast.error("Failed to update task");
    }
  };

  return (
    <div className="space-y-6" data-testid="kanban-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight">
            Kanban Board
          </h1>
          <p className="text-muted-foreground mt-1">
            Drag and drop tasks to change their status
          </p>
        </div>
        <Button onClick={() => handleNewTask("todo")} className="gap-2" data-testid="kanban-new-task-btn">
          <Plus className="w-4 h-4" />
          New Task
        </Button>
      </div>

      {/* Kanban Board */}
      <div className="flex overflow-x-auto gap-6 pb-4 -mx-2 px-2">
        {COLUMNS.map((column) => {
          const columnTasks = getTasksByStatus(column.id);
          return (
            <div
              key={column.id}
              className="flex-shrink-0 w-80"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column.id)}
              data-testid={`kanban-column-${column.id}`}
            >
              {/* Column Header */}
              <div className="flex items-center gap-3 mb-4">
                <div className={cn("w-3 h-3 rounded-full", column.color)} />
                <h2 className="font-medium text-sm">{column.title}</h2>
                <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">
                  {columnTasks.length}
                </span>
              </div>

              {/* Column Content */}
              <div className={cn(
                "min-h-[500px] p-3 rounded-lg border border-border/50",
                "bg-[hsl(var(--sidebar))]",
                draggedTask && "ring-2 ring-primary/20"
              )}>
                <div className="space-y-3">
                  {columnTasks.map((task) => (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, task)}
                      onDragEnd={handleDragEnd}
                    >
                      <TaskCard
                        task={task}
                        category={getCategoryById(task.category_id)}
                        onClick={() => handleTaskClick(task)}
                        draggable
                      />
                    </div>
                  ))}

                  {columnTasks.length === 0 && (
                    <div className="py-12 text-center">
                      <p className="text-sm text-muted-foreground">
                        No tasks
                      </p>
                    </div>
                  )}
                </div>

                {/* Add task button */}
                <button
                  onClick={() => handleNewTask(column.id)}
                  className={cn(
                    "w-full mt-3 p-2 rounded-md border border-dashed border-border/60",
                    "text-sm text-muted-foreground",
                    "hover:border-border hover:bg-background/50",
                    "transition-colors duration-150 flex items-center justify-center gap-2"
                  )}
                  data-testid={`add-task-${column.id}`}
                >
                  <Plus className="w-4 h-4" />
                  Add task
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Task Modal */}
      <TaskModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        task={selectedTask || { status: defaultStatus }}
        onSuccess={fetchData}
      />
    </div>
  );
}
