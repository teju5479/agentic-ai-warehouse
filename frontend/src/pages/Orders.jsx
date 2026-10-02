import React, { useState, useEffect } from 'react';
import { ordersApi } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatusBadge from '../components/StatusBadge';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedOrderId, setSelectedOrderId] = useState(null);
  const [orderDetail, setOrderDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await ordersApi.list();
      setOrders(response.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch orders');
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = async (orderId) => {
    setSelectedOrderId(orderId);
    setDetailLoading(true);
    try {
      const response = await ordersApi.get(orderId);
      setOrderDetail(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 p-4">{error}</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Orders</h1>
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Deadline</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Destination</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {orders.map((order) => (
              <tr 
                key={order.order_id} 
                onClick={() => handleRowClick(order.order_id)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-blue-600">{order.order_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><StatusBadge status={order.status} /></td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"><StatusBadge status={order.priority} /></td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.deadline ? new Date(order.deadline).toLocaleString() : 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{order.destination}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedOrderId && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex justify-center items-center z-50" onClick={() => setSelectedOrderId(null)}>
          <div className="bg-white p-8 rounded-lg shadow-xl w-3/4 max-w-4xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Order Details: {selectedOrderId}</h2>
              <button onClick={() => setSelectedOrderId(null)} className="text-gray-500 hover:text-gray-700 text-lg font-bold">✕</button>
            </div>
            
            {detailLoading ? (
              <LoadingSpinner />
            ) : orderDetail ? (
              <div>
                <div className="grid grid-cols-2 gap-4 mb-6 bg-slate-50 p-4 rounded-md">
                  <div><span className="font-semibold text-gray-700">Status:</span> <StatusBadge status={orderDetail.status} /></div>
                  <div><span className="font-semibold text-gray-700">Priority:</span> <StatusBadge status={orderDetail.priority} /></div>
                  <div><span className="font-semibold text-gray-700">Deadline:</span> {orderDetail.deadline ? new Date(orderDetail.deadline).toLocaleString() : 'N/A'}</div>
                  <div><span className="font-semibold text-gray-700">Destination:</span> {orderDetail.destination}</div>
                  {orderDetail.held_reason && (
                    <div className="col-span-2"><span className="font-semibold text-red-600">Reason / Hold Note:</span> {orderDetail.held_reason}</div>
                  )}
                </div>
                
                <h3 className="text-lg font-semibold mb-2">Order Lines</h3>
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requested Qty</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Picked Qty</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {orderDetail.order_lines?.map((line, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{line.sku}</td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">{line.requested_qty}</td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">{line.picked_qty}</td>
                        <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500"><StatusBadge status={line.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>Failed to load details.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;
