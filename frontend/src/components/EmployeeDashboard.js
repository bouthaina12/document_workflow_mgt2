import { useEffect, useState } from "react";
import axios from "axios";

function EmployeeDashboard() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    axios
      .get("http://localhost:8000/users/api/employee-dashboard/", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((response) => setMessage(response.data.message))
      .catch((err) => setMessage(err.response?.data?.error || "Error"));
  }, []);

  return (
    <div>
      <h1>Employee Dashboard</h1>
      <p>{message}</p>
    </div>
  );
}

export default EmployeeDashboard;
