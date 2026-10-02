import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, AlertTriangle, Calendar, FileText, Play } from 'lucide-react';

import Dashboard from './pages/Dashboard';
import Orders from './pages/Orders';
import Exceptions from './pages/Exceptions';
import Planner from './pages/Planner';
import Audit from './pages/Audit';
import Scenarios from './pages/Scenarios';

function App() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/orders', label: 'Orders', icon: Package },
    { path: '/exceptions', label: 'Exceptions', icon: AlertTriangle },
    { path: '/planner', label: 'Planner', icon: Calendar },
    { path: '/audit', label: 'Audit', icon: FileText },
    { path: '/scenarios', label: 'Scenarios', icon: Play },
  ];

  return (
    <div className="flex h-screen bg-slate-100">
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 text-xl font-bold border-b border-slate-800">
          Warehouse Agent
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/exceptions" element={<Exceptions />} />
            <Route path="/planner" element={<Planner />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="/scenarios" element={<Scenarios />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App;
