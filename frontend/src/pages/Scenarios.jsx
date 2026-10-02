import React, { useState, useEffect } from 'react';
import { scenariosApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

const Scenarios = () => {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [runningId, setRunningId] = useState(null);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await scenariosApi.list();
      setScenarios(response.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch scenarios');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    try {
      await scenariosApi.reset();
      alert('Environment reset successfully.');
    } catch (err) {
      alert('Error resetting environment: ' + (err.response?.data?.detail || err.message));
    } finally {
      setResetting(false);
    }
  };

  const handleRunScenario = async (scenarioId) => {
    setRunningId(scenarioId);
    try {
      const response = await scenariosApi.run(scenarioId);
      const data = response.data;
      alert(`Scenario ${scenarioId} executed: ${data.message || data.status || 'Success'}`);
    } catch (err) {
      alert('Error running scenario: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunningId(null);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 p-4">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Reproducible Operational Scenarios</h1>
          <p className="text-sm text-gray-500 mt-1">Select a pre-configured scenario to simulate operational anomalies or replanning events.</p>
        </div>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none disabled:opacity-50"
        >
          {resetting ? 'Resetting...' : 'Reset Environment'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((scenario) => {
          const scenarioId = scenario.scenario_id || scenario.id;
          return (
            <div key={scenarioId} className="bg-white rounded-lg shadow p-6 flex flex-col border border-gray-100">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-bold text-gray-900">{scenario.name}</h3>
                <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-200">{scenarioId}</span>
              </div>
              <p className="text-gray-600 mb-4 flex-1 text-sm">{scenario.description}</p>
              
              <div className="bg-slate-50 p-3 rounded text-sm text-gray-700 mb-4 border border-slate-200">
                <strong className="text-slate-900">Expected Behavior:</strong> {scenario.expected_behavior}
              </div>

              <button
                onClick={() => handleRunScenario(scenarioId)}
                disabled={runningId === scenarioId}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none disabled:opacity-50"
              >
                {runningId === scenarioId ? 'Running Scenario...' : 'Run Scenario'}
              </button>
            </div>
          );
        })}
        {scenarios.length === 0 && (
          <div className="text-gray-500 col-span-2 text-center py-8">No scenarios available.</div>
        )}
      </div>
    </div>
  );
};

export default Scenarios;
