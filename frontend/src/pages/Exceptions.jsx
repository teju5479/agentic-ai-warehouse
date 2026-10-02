import React, { useState, useEffect } from 'react';
import { exceptionsApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';
import ApprovalPanel from '../components/ApprovalPanel';

const Exceptions = () => {
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resolvingId, setResolvingId] = useState(null);

  const fetchExceptions = async () => {
    try {
      const response = await exceptionsApi.list();
      setExceptions(response.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch exceptions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, []);

  const handleResolve = async (exceptionId) => {
    setResolvingId(exceptionId);
    try {
      const response = await exceptionsApi.resolve(exceptionId);
      const data = response.data;
      const outcome = data.outcome || 'COMPLETED';
      alert(`Exception Resolver executed successfully! Outcome: ${outcome}`);
      await fetchExceptions();
    } catch (err) {
      alert('Error resolving exception: ' + (err.response?.data?.detail || err.message));
    } finally {
      setResolvingId(null);
    }
  };

  const handleApprove = async (exceptionId) => {
    try {
      await exceptionsApi.approve(exceptionId);
      await fetchExceptions();
    } catch (err) {
      alert('Error approving exception: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleReject = async (exceptionId) => {
    try {
      await exceptionsApi.reject(exceptionId);
      await fetchExceptions();
    } catch (err) {
      alert('Error rejecting exception: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 p-4">{error}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Order Exceptions</h1>
      
      <div className="grid grid-cols-1 gap-6">
        {exceptions.map((exc) => {
          const excId = exc.exception_id || exc.id;
          return (
            <div key={excId} className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{exc.type}</h3>
                  <p className="text-sm text-gray-500 font-mono">Exception ID: {excId} | Order ID: {exc.order_id}</p>
                </div>
                <div className="flex space-x-2">
                  <StatusBadge status={exc.severity} />
                  <StatusBadge status={exc.status} />
                </div>
              </div>

              <p className="text-gray-700 mb-4">{exc.description}</p>

              {(exc.status === 'OPEN' || exc.status === 'INVESTIGATING') && (
                <button
                  onClick={() => handleResolve(excId)}
                  disabled={resolvingId === excId}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {resolvingId === excId ? 'Running Exception Resolver Agent...' : 'Run Exception Resolver'}
                </button>
              )}

              {exc.status === 'WAITING_FOR_APPROVAL' && (
                <ApprovalPanel
                  actionDetails={typeof exc.proposed_action === 'string' ? exc.proposed_action : JSON.stringify(exc.proposed_action)}
                  reason={exc.resolution || exc.description}
                  policy={exc.policy_reference || 'SOP-003'}
                  effect="Consequential state modification requires human approval."
                  onApprove={() => handleApprove(excId)}
                  onReject={() => handleReject(excId)}
                />
              )}

              {exc.resolution && exc.status !== 'WAITING_FOR_APPROVAL' && (
                <div className="mt-4 p-4 bg-gray-50 rounded-md border border-gray-200">
                  <h4 className="font-semibold text-gray-800 mb-2">Resolution Note</h4>
                  <p className="text-sm text-gray-700">{exc.resolution}</p>
                  
                  {exc.policy_reference && (
                    <div className="mt-2 text-sm text-blue-800">
                      <strong>Policy Cited:</strong> {exc.policy_reference}
                    </div>
                  )}

                  {exc.evidence && (
                    <div className="mt-2">
                      <strong className="text-xs text-gray-600 uppercase">Evidence Inspected:</strong>
                      <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto max-h-32">
                        {typeof exc.evidence === 'string' ? exc.evidence : JSON.stringify(exc.evidence, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        {exceptions.length === 0 && (
          <div className="text-gray-500 text-center py-8">No exceptions found.</div>
        )}
      </div>
    </div>
  );
};

export default Exceptions;
