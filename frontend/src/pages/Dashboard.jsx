import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await dashboardApi.get();
        setData(response.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 p-4">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-blue-500">
          <h3 className="text-slate-500 text-sm font-medium">Total Orders</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.total_orders}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-yellow-500">
          <h3 className="text-slate-500 text-sm font-medium">Pending Orders</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.pending_orders}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-red-500">
          <h3 className="text-slate-500 text-sm font-medium">Blocked Orders</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.blocked_orders}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-orange-500">
          <h3 className="text-slate-500 text-sm font-medium">Held Orders</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.held_orders}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-red-600">
          <h3 className="text-slate-500 text-sm font-medium">Open Exceptions</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.open_exceptions}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-green-500">
          <h3 className="text-slate-500 text-sm font-medium">Available Pickers</h3>
          <p className="text-3xl font-bold text-slate-800 mt-2">{data.available_pickers} / {data.total_pickers}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mt-8">
        <h2 className="text-xl font-bold text-slate-800 mb-4">Current Plan</h2>
        {data.current_plan ? (
          <div className="space-y-2">
            <p><strong>Plan ID:</strong> <span className="font-mono text-blue-600 font-bold">{data.current_plan.plan_id || data.current_plan.id}</span></p>
            <p><strong>Version:</strong> {data.current_plan.version || 1}</p>
            <p><strong>Status:</strong> {data.current_plan.status}</p>
          </div>
        ) : (
          <p className="text-slate-500">No active plan.</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
