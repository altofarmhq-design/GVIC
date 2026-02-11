import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { Layout } from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import KanbanPage from "@/pages/KanbanPage";
import ListPage from "@/pages/ListPage";
import "@/App.css";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kanban" element={<KanbanPage />} />
          <Route path="/list" element={<ListPage />} />
        </Routes>
      </Layout>
      <Toaster position="bottom-right" />
    </BrowserRouter>
  );
}

export default App;
