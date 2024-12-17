import { useEffect, useState } from "react";
import axios from "axios";

function AdminDashboard() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    axios
      .get("http://localhost:8000/users/api/admin-page/", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((response) => setMessage(response.data.message))
      .catch((err) => setMessage(err.response?.data?.error || "Error"));
  }, []);

  return (
    <div>
      <h1>Admin Dashboard</h1>
      <p>{message}</p>
    </div>
  );
}

export default AdminDashboard;
