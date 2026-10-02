import React, { useState, useEffect } from 'react';
import { plannerApi, pickersApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';

const Planner = () => {
  const [plans, setPlans] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [pickers, setPickers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningPlanner, setRunningPlanner] = useState(false);
  const [replanning, setReplanning] = useState(false);
  const [selectedPickerId, setSelectedPickerId] = useState('');

  const fetchData = async () => {
    try {
      const [plansRes, pickersRes] = await Promise.all([
        plannerApi.listPlans(),
        pickersApi.list()
      ]);
      setPlans(plansRes.data);
      if (plansRes.data.length > 0) {
        const firstPlanId = plansRes.data[0].plan_id || plansRes.data[0].id;
        fetchPlanDetail(firstPlanId);
      } else {
        setLoading(false);
      }
      setPickers(pickersRes.data);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  const fetchPlanDetail = async (planId) => {
    try {
      const response = await plannerApi.getPlan(planId);
      setCurrentPlan(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunPlanner = async () => {
    setRunningPlanner(true);
    try {
      await plannerApi.run();
      await fetchData();
    } catch (error) {
      alert('Error running planner: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRunningPlanner(false);
    }
  };

  const handleMakePickerUnavailable = async () => {
    if (!selectedPickerId) return;
    setReplanning(true);
    try {
      await plannerApi.replan({
        change_type: 'picker_unavailable',
        change_details: { picker_id: selectedPickerId }
      });
      await fetchData();
    } catch (error) {
      alert('Error replanning: ' + (error.response?.data?.detail || error.message));
    } finally {
      setReplanning(false);
    }
  };

  const handleAddUrgentOrder = async () => {
    setReplanning(true);
    try {
      await plannerApi.replan({
        change_type: 'urgent_order',
        change_details: {}
      });
      await fetchData();
    } catch (error) {
      alert('Error replanning: ' + (error.response?.data?.detail || error.message));
    } finally {
      setReplanning(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  const planId = currentPlan ? (currentPlan.plan_id || currentPlan.id) : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Shift Task Planner</h1>
          <p className="text-sm text-gray-500 mt-1">Multi-order task assignment & capacity-based shift planning.</p>
        </div>
        <button
          onClick={handleRunPlanner}
          disabled={runningPlanner}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none disabled:opacity-50"
        >
          {runningPlanner ? 'Running Planner...' : 'Run Shift Planner'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Replanning Events</h2>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[250px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Make Picker Unavailable</label>
            <div className="flex space-x-2">
              <select
                value={selectedPickerId}
                onChange={(e) => setSelectedPickerId(e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md border"
              >
                <option value="">Select Picker</option>
                {pickers.map(p => {
                  const pId = p.picker_id || p.id;
                  const pStatus = p.availability || p.status;
                  return <option key={pId} value={pId}>{p.name} ({pStatus})</option>;
                })}
              </select>
              <button
                onClick={handleMakePickerUnavailable}
                disabled={replanning || !selectedPickerId}
                className="mt-1 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium disabled:opacity-50"
              >
                {replanning ? 'Replanning...' : 'Replan'}
              </button>
            </div>
          </div>
          <div>
            <button
              onClick={handleAddUrgentOrder}
              disabled={replanning}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium disabled:opacity-50 h-[38px]"
            >
              Add Urgent Order & Replan
            </button>
          </div>
        </div>
      </div>

      {currentPlan ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold text-gray-800">Plan ID: {planId}</h2>
              <p className="text-xs text-gray-500 font-mono">Version: {currentPlan.version || 1} | Created by: {currentPlan.created_by}</p>
            </div>
            <StatusBadge status={currentPlan.status} />
          </div>
          
          <div className="p-4">
            <h3 className="font-semibold text-gray-700 mb-2">Shift Assignments</h3>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sequence</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Assigned Picker</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Workload</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {currentPlan.assignments?.map((assignment, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm text-gray-900 font-mono">{assignment.sequence || idx + 1}</td>
                    <td className="px-4 py-2 text-sm font-bold text-blue-600">{assignment.order_id}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{assignment.picker_id || <span className="text-red-500 italic">Unassigned</span>}</td>
                    <td className="px-4 py-2 text-sm text-gray-700">{assignment.workload || '-'}</td>
                    <td className="px-4 py-2 text-sm"><StatusBadge status={assignment.status} /></td>
                  </tr>
                ))}
                {(!currentPlan.assignments || currentPlan.assignments.length === 0) && (
                  <tr><td colSpan="5" className="px-4 py-2 text-sm text-gray-500 text-center">No assignments in this plan.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
          No active shift plans available. Click "Run Shift Planner" above to create one.
        </div>
      )}
    </div>
  );
};

export default Planner;
