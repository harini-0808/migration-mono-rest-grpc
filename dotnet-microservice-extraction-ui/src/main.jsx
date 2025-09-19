import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import Analysis from "./pages/Analysis.jsx";
import AnalysisResult from "./pages/AnalysisResult.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import TokenUsage from "./components/TokenUsage.jsx";

createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />}>
        <Route index element={<Analysis />} />
        <Route path="result" element={<AnalysisResult />} />
        <Route path="token-usage" element={<TokenUsage />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
      </Route>
    </Routes>
  </BrowserRouter>
);