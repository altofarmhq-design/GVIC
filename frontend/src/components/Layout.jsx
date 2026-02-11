import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Kanban, 
  List, 
  Settings,
  Menu,
  X,
  ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { CategoryManager } from "@/components/CategoryManager";

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/kanban", label: "Kanban Board", icon: Kanban },
  { path: "/list", label: "List View", icon: List },
];

export const Layout = ({ children }) => {
  const location = useLocation();
  const [showCategories, setShowCategories] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const NavContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-border/50">
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          TaskFlow
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">Organize your work</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium",
                "hover:bg-accent/80 active:scale-[0.98]",
                "transition-colors duration-150",
                isActive 
                  ? "bg-accent text-foreground" 
                  : "text-muted-foreground hover:text-foreground"
              )}
              data-testid={`nav-${item.path.replace("/", "") || "dashboard"}`}
            >
              <Icon className="w-4 h-4" strokeWidth={1.75} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Category Manager Toggle */}
      <div className="px-3 pb-4">
        <button
          onClick={() => setShowCategories(!showCategories)}
          className={cn(
            "w-full flex items-center justify-between px-3 py-2.5 rounded-md text-sm",
            "text-muted-foreground hover:text-foreground hover:bg-accent/80",
            "transition-colors duration-150"
          )}
          data-testid="toggle-categories"
        >
          <span className="flex items-center gap-3">
            <Settings className="w-4 h-4" strokeWidth={1.75} />
            Categories
          </span>
          <ChevronRight 
            className={cn(
              "w-4 h-4 transition-transform duration-200",
              showCategories && "rotate-90"
            )} 
          />
        </button>
        
        {showCategories && (
          <div className="mt-2 animate-fade-in">
            <CategoryManager />
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside 
        className="fixed left-0 top-0 h-screen w-64 bg-[hsl(var(--sidebar))] border-r border-border/50 hidden md:block"
        data-testid="desktop-sidebar"
      >
        <NavContent />
      </aside>

      {/* Mobile Header */}
      <header className="md:hidden fixed top-0 left-0 right-0 h-14 bg-background border-b border-border/50 flex items-center px-4 z-50">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" data-testid="mobile-menu-trigger">
              <Menu className="w-5 h-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0 bg-[hsl(var(--sidebar))]">
            <NavContent />
          </SheetContent>
        </Sheet>
        <h1 className="font-heading text-xl font-semibold ml-3">TaskFlow</h1>
      </header>

      {/* Main Content */}
      <main className="md:ml-64 min-h-screen pt-14 md:pt-0">
        <div className="p-6 md:p-8 lg:p-10">
          {children}
        </div>
      </main>
    </div>
  );
};
