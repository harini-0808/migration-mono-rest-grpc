import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";


function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Hide sidebar for login and register pages
  const hideSidebar = ["/login", "/register"].includes(location.pathname);

  useEffect(() => {
    const token = localStorage.getItem("jwt_token");
    const publicRoutes = ["/login", "/register"];
    const currentPath = location.pathname;

    if (!token && !publicRoutes.includes(currentPath)) {
      navigate("/login");
    }
  }, [navigate, location.pathname]);

  return (
    <div className="min-h-screen flex">
      {!hideSidebar && (
        <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />
      )}
      <main
        className={`transition-all duration-300 flex-1 bg-gray-50 ${
          !hideSidebar && isSidebarOpen ? "ml-64" : !hideSidebar ? "ml-16" : ""
        }`}
      >
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default App;