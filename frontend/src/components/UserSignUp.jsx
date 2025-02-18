import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { FaUserGraduate } from "react-icons/fa";
import GradientText from "./ui/GradientText";

function UserSignUp() {
  const [userData, setUserData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!userData.username || !userData.email || !userData.password || !userData.confirmPassword) {
      setError("Please fill in all fields");
      return;
    }

    if (userData.password !== userData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const response = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: userData.username,
          email: userData.email,
          password: userData.password,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        navigate("/login");
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="flex flex-col items-center">
          <FaUserGraduate className="text-8xl text-indigo-500" />
          <GradientText className="mt-6 text-center text-3xl font-extrabold">
            Create Account
          </GradientText>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 mt-8">
          {error && (
            <div className="text-red-500 text-center text-sm">{error}</div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="text"
                placeholder="Username"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={userData.username}
                onChange={(e) =>
                  setUserData({ ...userData, username: e.target.value })
                }
              />
            </div>
            <div>
              <input
                type="email"
                placeholder="Email"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={userData.email}
                onChange={(e) =>
                  setUserData({ ...userData, email: e.target.value })
                }
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={userData.password}
                onChange={(e) =>
                  setUserData({ ...userData, password: e.target.value })
                }
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Confirm Password"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-700 placeholder-gray-500 text-white bg-gray-800 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                value={userData.confirmPassword}
                onChange={(e) =>
                  setUserData({ ...userData, confirmPassword: e.target.value })
                }
              />
            </div>
          </div>
          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
            >
              Sign Up
            </button>
          </div>
          <div className="text-center text-sm">
            <span className="text-gray-500">Already have an account? </span>
            <Link to="/login" className="text-indigo-500 hover:text-indigo-400">
              Sign in
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UserSignUp;
