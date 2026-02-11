import { cn } from "@/lib/utils";
import { format, parseISO, isAfter, isBefore, addDays } from "date-fns";
import { Calendar, Flag, GripVertical } from "lucide-react";
import { getColorClasses } from "@/components/CategoryManager";

const PRIORITY_CONFIG = {
  low: { label: "Low", color: "text-[#1C3829]", bg: "bg-[#DBEDDB]" },
  medium: { label: "Medium", color: "text-[#183347]", bg: "bg-[#D3E5EF]" },
  high: { label: "High", color: "text-[#49290E]", bg: "bg-[#FADEC9]" },
  urgent: { label: "Urgent", color: "text-[#5D1715]", bg: "bg-[#FFE2DD]" },
};

export const TaskCard = ({ task, category, onClick, draggable = false }) => {
  const priorityConfig = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
  const categoryColors = category ? getColorClasses(category.color) : null;
  
  const isOverdue = task.due_date && 
    task.status !== "done" && 
    isBefore(parseISO(task.due_date), new Date());
  
  const isDueSoon = task.due_date && 
    task.status !== "done" && 
    !isOverdue &&
    isBefore(parseISO(task.due_date), addDays(new Date(), 3));

  return (
    <div
      className={cn(
        "group p-3 bg-white border border-border/60 rounded-md",
        "shadow-sm hover:shadow-md hover:border-border",
        "transition-shadow duration-200 cursor-pointer",
        draggable && "cursor-grab active:cursor-grabbing"
      )}
      onClick={onClick}
      data-testid={`task-card-${task.id}`}
    >
      {draggable && (
        <div className="absolute left-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-50 transition-opacity duration-150">
          <GripVertical className="w-4 h-4 text-muted-foreground" />
        </div>
      )}
      
      {/* Title */}
      <h4 className={cn(
        "font-medium text-sm text-foreground line-clamp-2",
        task.status === "done" && "line-through text-muted-foreground"
      )}>
        {task.title}
      </h4>
      
      {/* Description preview */}
      {task.description && (
        <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
          {task.description}
        </p>
      )}
      
      {/* Meta info */}
      <div className="flex items-center gap-2 mt-3 flex-wrap">
        {/* Priority badge */}
        <span className={cn(
          "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium",
          priorityConfig.bg, priorityConfig.color
        )}>
          <Flag className="w-3 h-3" />
          {priorityConfig.label}
        </span>
        
        {/* Category badge */}
        {category && (
          <span className={cn(
            "inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium",
            categoryColors.bg, categoryColors.text
          )}>
            {category.name}
          </span>
        )}
        
        {/* Due date */}
        {task.due_date && (
          <span className={cn(
            "inline-flex items-center gap-1 text-xs",
            isOverdue && "text-[#5D1715] font-medium",
            isDueSoon && !isOverdue && "text-[#49290E] font-medium",
            !isOverdue && !isDueSoon && "text-muted-foreground"
          )}>
            <Calendar className="w-3 h-3" />
            {format(parseISO(task.due_date), "MMM d")}
            {isOverdue && " (Overdue)"}
          </span>
        )}
      </div>
    </div>
  );
};

export const getPriorityConfig = () => PRIORITY_CONFIG;
