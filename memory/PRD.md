# TaskFlow - Notion Style Task Manager

## Original Problem Statement
Build a Notion-style task manager where users can add, edit, complete, and delete tasks. Include categories or priorities, due dates, and a dashboard showing tasks by status.

## User Choices
- No authentication (single user)
- Basic features: title, description, status, due date, priority
- Both Kanban board and List views
- User-customizable categories

## Architecture

### Backend (FastAPI + MongoDB)
- **server.py**: Main API server with CRUD endpoints
- **Collections**: tasks, categories
- **Endpoints**: /api/tasks, /api/categories, /api/tasks/stats/overview

### Frontend (React + Tailwind + Shadcn/UI)
- **Dashboard**: Task stats, progress, upcoming tasks
- **Kanban Board**: Drag & drop columns (To Do, In Progress, Done)
- **List View**: Sortable table with filters
- **Task Modal**: Create/edit tasks with calendar picker
- **Category Manager**: Custom categories with colors

## What's Been Implemented (Feb 7, 2026)

### Core Features ✅
- [x] Task CRUD operations (create, read, update, delete)
- [x] Task status management (To Do, In Progress, Done)
- [x] Priority levels (Low, Medium, High, Urgent)
- [x] Due date with calendar picker
- [x] Custom categories with color selection
- [x] Dashboard with task statistics
- [x] Kanban board with drag & drop
- [x] List view with search and filters
- [x] Responsive design (desktop + mobile)
- [x] Notion-style UI (Newsreader + Inter fonts)

### API Endpoints
- GET/POST /api/tasks - List/Create tasks
- GET/PUT/DELETE /api/tasks/{id} - Task operations
- GET /api/tasks/stats/overview - Dashboard statistics
- GET/POST /api/categories - List/Create categories
- PUT/DELETE /api/categories/{id} - Category operations

## Prioritized Backlog

### P0 (Critical) - Done ✅
- Task CRUD
- Kanban board
- List view
- Category management

### P1 (Important)
- [ ] Subtasks support
- [ ] Task comments
- [ ] Due date reminders/notifications
- [ ] Keyboard shortcuts

### P2 (Nice to Have)
- [ ] Dark mode toggle
- [ ] Task archiving
- [ ] Export tasks to CSV
- [ ] Recurring tasks
- [ ] Tags system
- [ ] Activity log

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, lucide-react
- **Backend**: FastAPI, Motor (async MongoDB driver)
- **Database**: MongoDB
- **Fonts**: Newsreader (headings), Inter (body)
