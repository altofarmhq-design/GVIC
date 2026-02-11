import { useState, useEffect } from "react";
import { categoryApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Plus, Trash2, Edit2, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

const TAG_COLORS = [
  { value: "gray", label: "Gray", bg: "bg-[#E3E2E0]", text: "text-[#32302C]" },
  { value: "brown", label: "Brown", bg: "bg-[#EEE0DA]", text: "text-[#442A1E]" },
  { value: "orange", label: "Orange", bg: "bg-[#FADEC9]", text: "text-[#49290E]" },
  { value: "yellow", label: "Yellow", bg: "bg-[#FDECC8]", text: "text-[#402C1B]" },
  { value: "green", label: "Green", bg: "bg-[#DBEDDB]", text: "text-[#1C3829]" },
  { value: "blue", label: "Blue", bg: "bg-[#D3E5EF]", text: "text-[#183347]" },
  { value: "purple", label: "Purple", bg: "bg-[#E8DEEE]", text: "text-[#412454]" },
  { value: "pink", label: "Pink", bg: "bg-[#F5E0E9]", text: "text-[#4C2337]" },
  { value: "red", label: "Red", bg: "bg-[#FFE2DD]", text: "text-[#5D1715]" },
];

export const getColorClasses = (color) => {
  return TAG_COLORS.find(c => c.value === color) || TAG_COLORS[0];
};

export const CategoryManager = ({ onUpdate }) => {
  const [categories, setCategories] = useState([]);
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState("gray");
  const [editName, setEditName] = useState("");
  const [editColor, setEditColor] = useState("");

  const fetchCategories = async () => {
    try {
      const res = await categoryApi.getAll();
      setCategories(res.data);
    } catch (err) {
      console.error("Failed to fetch categories", err);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    try {
      await categoryApi.create({ name: newName.trim(), color: newColor });
      toast.success("Category created");
      setNewName("");
      setNewColor("gray");
      setIsAdding(false);
      fetchCategories();
      onUpdate?.();
    } catch (err) {
      toast.error("Failed to create category");
    }
  };

  const handleUpdate = async (id) => {
    if (!editName.trim()) return;
    try {
      await categoryApi.update(id, { name: editName.trim(), color: editColor });
      toast.success("Category updated");
      setEditingId(null);
      fetchCategories();
      onUpdate?.();
    } catch (err) {
      toast.error("Failed to update category");
    }
  };

  const handleDelete = async (id) => {
    try {
      await categoryApi.delete(id);
      toast.success("Category deleted");
      fetchCategories();
      onUpdate?.();
    } catch (err) {
      toast.error("Failed to delete category");
    }
  };

  const startEdit = (cat) => {
    setEditingId(cat.id);
    setEditName(cat.name);
    setEditColor(cat.color);
  };

  return (
    <div className="space-y-2 px-1">
      {categories.map((cat) => {
        const colorClass = getColorClasses(cat.color);
        if (editingId === cat.id) {
          return (
            <div key={cat.id} className="flex items-center gap-1.5">
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="h-7 text-xs flex-1"
                autoFocus
              />
              <Select value={editColor} onValueChange={setEditColor}>
                <SelectTrigger className="w-16 h-7">
                  <div className={cn("w-3 h-3 rounded", colorClass.bg)} />
                </SelectTrigger>
                <SelectContent>
                  {TAG_COLORS.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      <div className="flex items-center gap-2">
                        <div className={cn("w-3 h-3 rounded", c.bg)} />
                        <span className="text-xs">{c.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => handleUpdate(cat.id)}
              >
                <Check className="w-3.5 h-3.5" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7"
                onClick={() => setEditingId(null)}
              >
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>
          );
        }

        return (
          <div
            key={cat.id}
            className="flex items-center gap-2 group px-2 py-1.5 rounded hover:bg-accent/50"
            data-testid={`category-${cat.id}`}
          >
            <div className={cn("w-3 h-3 rounded", colorClass.bg)} />
            <span className="text-sm flex-1 truncate">{cat.name}</span>
            <div className="opacity-0 group-hover:opacity-100 flex gap-0.5 transition-opacity duration-150">
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6"
                onClick={() => startEdit(cat)}
              >
                <Edit2 className="w-3 h-3" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-6 w-6 text-destructive hover:text-destructive"
                onClick={() => handleDelete(cat.id)}
              >
                <Trash2 className="w-3 h-3" />
              </Button>
            </div>
          </div>
        );
      })}

      {isAdding ? (
        <div className="flex items-center gap-1.5 mt-2">
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Category name"
            className="h-7 text-xs flex-1"
            autoFocus
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <Select value={newColor} onValueChange={setNewColor}>
            <SelectTrigger className="w-16 h-7">
              <div className={cn("w-3 h-3 rounded", getColorClasses(newColor).bg)} />
            </SelectTrigger>
            <SelectContent>
              {TAG_COLORS.map((c) => (
                <SelectItem key={c.value} value={c.value}>
                  <div className="flex items-center gap-2">
                    <div className={cn("w-3 h-3 rounded", c.bg)} />
                    <span className="text-xs">{c.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={handleAdd}
          >
            <Check className="w-3.5 h-3.5" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setIsAdding(false)}
          >
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
      ) : (
        <button
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground px-2 py-1.5 w-full rounded hover:bg-accent/50 transition-colors duration-150"
          data-testid="add-category-btn"
        >
          <Plus className="w-3.5 h-3.5" />
          Add category
        </button>
      )}
    </div>
  );
};
