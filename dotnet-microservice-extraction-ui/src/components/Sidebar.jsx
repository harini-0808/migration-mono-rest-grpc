import { Link, useNavigate } from "react-router-dom";
import { HiMenuAlt3, HiOutlineChartBar, HiOutlineDocumentText, HiOutlineLogin, HiOutlineUserAdd, HiOutlineLogout, HiOutlineInformationCircle } from "react-icons/hi";
import Logo from "../assets/ustlogo.png";

const Sidebar = ({ isOpen, setIsOpen }) => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem("jwt_token");

  const menuItems = isAuthenticated
    ? [
        { title: "Analysis", path: "/", icon: <HiOutlineChartBar size={20} /> },
        { title: "Results", path: "/result", icon: <HiOutlineDocumentText size={20} /> },
        { title: "Token Usage", path: "/token-usage", icon: <HiOutlineInformationCircle size={20} /> },
      ]
    : [
        { title: "Login", path: "/login", icon: <HiOutlineLogin size={20} /> },
        { title: "Register", path: "/register", icon: <HiOutlineUserAdd size={20} /> },
      ];


  const handleLogout = () => {
    localStorage.removeItem("jwt_token");
    navigate("/login");
  };

  return (
    <aside
      className={`
      fixed top-0 left-0 h-screen
      ${isOpen ? "w-64" : "w-16"}
      bg-gray-900 
      transition-all duration-300 ease-in-out
      shadow-xl
      z-50
    `}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-800">
        {isOpen && (
          <div className="flex items-center space-x-3">
            <img src={Logo} alt="Logo" className="h-8 w-auto" />
          </div>
        )}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
          aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
        >
          <HiMenuAlt3 size={20} className="text-gray-400 hover:text-white" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="mt-6 px-3 flex flex-col h-[calc(100%-4rem)]">
        <div className="space-y-1 flex-1">
          {menuItems.map((item, index) => (
            <Link
              key={index}
              to={item.path}
              className={`
                flex items-center group
                px-3 py-2.5 
                text-sm font-medium
                rounded-lg
                text-gray-300 hover:text-white
                hover:bg-gray-800
                transition-all duration-200
                relative
              `}
            >
              <span className="flex items-center justify-center w-5 h-5">
                {item.icon}
              </span>
              <span
                className={`
                  ml-3
                  transition-all duration-200
                  ${!isOpen && "opacity-0 translate-x-4 invisible"}
                `}
              >
                {item.title}
              </span>
              {!isOpen && (
                <div
                  className={`
                    absolute left-full ml-6
                    px-3 py-2
                    bg-gray-800 
                    rounded-lg
                    text-sm font-medium
                    text-white
                    shadow-lg
                    opacity-0 invisible
                    transform -translate-x-2
                    transition-all duration-200
                    group-hover:opacity-100 group-hover:visible group-hover:translate-x-0
                    whitespace-nowrap
                    z-50
                  `}
                >
                  {item.title}
                </div>
              )}
            </Link>
          ))}
        </div>

        {/* Logout Button (Authenticated Users Only) */}
        {isAuthenticated && (
          <div className="mt-auto pb-4">
            <button
              onClick={handleLogout}
              className={`
                flex items-center group
                px-3 py-2.5 w-full
                text-sm font-medium
                rounded-lg
                text-gray-300 hover:text-white
                hover:bg-gray-800
                transition-all duration-200
                relative
              `}
            >
              <span className="flex items-center justify-center w-5 h-5">
                <HiOutlineLogout size={20} />
              </span>
              <span
                className={`
                  ml-3
                  transition-all duration-200
                  ${!isOpen && "opacity-0 translate-x-4 invisible"}
                `}
              >
                Logout
              </span>
              {!isOpen && (
                <div
                  className={`
                    absolute left-full ml-6
                    px-3 py-2
                    bg-gray-800 
                    rounded-lg
                    text-sm font-medium
                    text-white
                    shadow-lg
                    opacity-0 invisible
                    transform -translate-x-2
                    transition-all duration-200
                    group-hover:opacity-100 group-hover:visible group-hover:translate-x-0
                    whitespace-nowrap
                    z-50
                  `}
                >
                  Logout
                </div>
              )}
            </button>
          </div>
        )}
      </nav>
    </aside>
  );
};

export default Sidebar;