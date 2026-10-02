import React, { useState } from 'react';

const ApprovalPanel = ({ onApprove, onReject, actionDetails, reason, policy, effect }) => {
  const [loading, setLoading] = useState(false);

  const handleAction = async (action) => {
    setLoading(true);
    try {
      if (action === 'approve') {
        await onApprove();
      } else {
        await onReject();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mt-4">
      <h3 className="text-lg font-medium text-yellow-800 mb-2">Confirmation Required</h3>
      
      <div className="space-y-2 mb-4 text-sm text-yellow-900">
        <p><strong>Action Details:</strong> {actionDetails}</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p><strong>Policy:</strong> {policy}</p>
        <p><strong>Effect:</strong> {effect}</p>
      </div>

      <div className="flex space-x-3">
        <button
          onClick={() => handleAction('approve')}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Approve'}
        </button>
        <button
          onClick={() => handleAction('reject')}
          disabled={loading}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded shadow-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Reject'}
        </button>
      </div>
    </div>
  );
};

export default ApprovalPanel;
