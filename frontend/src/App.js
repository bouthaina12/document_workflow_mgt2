import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import LoginForm from "./components/LoginForm";
import AdminDashboard from "./components/AdminDashboard";
import ManagerDashboard from "./components/ManagerDashboard";
import EmployeeDashboard from "./components/EmployeeDashboard";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginForm />} />
        <Route path="/AdminDashboard" element={<AdminDashboard />} />
        <Route path="/ManagerDashboard " element={<ManagerDashboard />} />
        <Route path="/EmployeeDashboard" element={<EmployeeDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
