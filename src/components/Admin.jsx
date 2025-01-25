import React from 'react'
import { useNavigate } from 'react-router-dom'
import { RiDashboardLine, RiLogoutBoxLine, RiMessage2Line } from 'react-icons/ri'

function Admin() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    navigate('/admin');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="fixed w-64 h-full bg-gray-800">
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-center h-20 border-b border-gray-700">
            <h1 className="text-white text-2xl font-bold">Admin Dashboard</h1>
          </div>
          
          <nav className="flex-grow py-4">
            <a href="#" className="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700">
              <RiDashboardLine className="mr-3" />
              Dashboard
            </a>
            <a href="#" className="flex items-center px-6 py-3 text-gray-300 hover:bg-gray-700">
              <RiMessage2Line className="mr-3" />
              Chat History
            </a>
          </nav>

          <div className="p-4">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-2 text-gray-300 hover:bg-gray-700 rounded"
            >
              <RiLogoutBoxLine className="mr-3" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="ml-64 p-8">
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl text-white mb-4">Welcome, Admin</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-white text-lg mb-2">Total Chats</h3>
              <p className="text-blue-400 text-2xl font-bold">0</p>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-white text-lg mb-2">Active Users</h3>
              <p className="text-green-400 text-2xl font-bold">0</p>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-white text-lg mb-2">Total Messages</h3>
              <p className="text-purple-400 text-2xl font-bold">0</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Admin