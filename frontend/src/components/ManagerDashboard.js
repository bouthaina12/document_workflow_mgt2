import { useEffect, useState } from "react";
import axios from "axios";

function ManagerDashboard() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    axios
      .get("http://localhost:8000/users/api/manager-dashboard/", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((response) => setMessage(response.data.message))
      .catch((err) => setMessage(err.response?.data?.error || "Error"));
  }, []);

  return (
    <div>
      <h1>Manager Dashboard</h1>
      <p>{message}</p>
    </div>
  );
}

export default ManagerDashboard;
