'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { sessionAPI, SessionResponse, UserResponse } from '../../../../lib/api';
import { QRCodeSVG } from 'qrcode.react';

export default function HostView() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const router = useRouter();
  
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (sessionId) {
      fetchSessionStatus();
      // Refresh every 5 seconds
      const interval = setInterval(fetchSessionStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [sessionId]);

  const fetchSessionStatus = async () => {
    try {
      const data = await sessionAPI.getStatus(sessionId);
      setSession(data.session);
      setUsers(data.users);
      setError('');
    } catch (err) {
      setError('Failed to load session');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Use network IP instead of localhost for mobile access, include port
  const shareLink = typeof window !== 'undefined' 
    ? `${window.location.origin}/session/${sessionId}` 
    : '';

  const copyToClipboard = () => {
    // Try modern clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(shareLink).then(() => {
        alert('Link copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy:', err);
        fallbackCopyToClipboard(shareLink);
      });
    } else {
      // Fallback for older browsers or non-secure contexts
      fallbackCopyToClipboard(shareLink);
    }
  };

  const fallbackCopyToClipboard = (text: string) => {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      alert('Link copied to clipboard!');
    } catch (err) {
      console.error('Fallback copy failed:', err);
      alert('Failed to copy link. Please copy manually.');
    }
    document.body.removeChild(textArea);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-red-600">{error || 'Session not found'}</div>
      </div>
    );
  }

  // Calculate totals correctly:
  // Total Owed = The original receipt total (session.total) - this is what the host paid
  // Collected = Sum of all user payments (from users who have marked as paid)
  // Pending = Total Owed - Collected
  const totalAmount = session.total; // This is the receipt total the host paid
  const paidAmount = users.filter(u => u.paid && u.total > 0).reduce((sum, user) => sum + user.total, 0);
  const remainingAmount = totalAmount - paidAmount;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Host View</h1>
                <p className="text-gray-600">Session: {session.host_name}</p>
              </div>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                New Session
              </button>
            </div>

            {/* Payment Summary */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm font-semibold text-gray-900">Total Owed</div>
                <div className="text-2xl font-bold text-blue-600">${totalAmount.toFixed(2)}</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm font-semibold text-gray-900">Collected</div>
                <div className="text-2xl font-bold text-green-600">${paidAmount.toFixed(2)}</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-sm font-semibold text-gray-900">Pending</div>
                <div className="text-2xl font-bold text-orange-600">${remainingAmount.toFixed(2)}</div>
              </div>
            </div>
          </div>

          {/* QR Code and Share */}
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Share Session</h2>
            <div className="flex flex-col md:flex-row gap-6 items-center">
              <div className="p-4 bg-white rounded-lg border-2 border-gray-200">
                <QRCodeSVG value={shareLink} size={200} />
              </div>
              <div className="flex-1">
                <p className="text-gray-900 font-semibold mb-3">Share this link with your friends:</p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={shareLink}
                    readOnly
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm text-gray-900"
                  />
                  <button
                    onClick={copyToClipboard}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Users List */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900">
              Participants ({users.filter(u => u.selected_items && u.selected_items.length > 0).length})
            </h2>
            
            {users.length === 0 || users.filter(u => u.selected_items && u.selected_items.length > 0).length === 0 ? (
              <div className="text-center py-8 text-gray-900">
                No one has selected items yet. Share the link above!
              </div>
            ) : (
              <div className="space-y-4">
                {users.filter(u => u.selected_items && u.selected_items.length > 0).map((user) => (
                  <div
                    key={user.id}
                    className={`border-2 rounded-lg p-4 ${
                      user.paid
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900">{user.name}</h3>
                        {user.payment_method && (
                          <span className="text-xs text-gray-900">
                            Payment: {user.payment_method}
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900">${user.total.toFixed(2)}</div>
                        <div className="text-xs text-gray-600 font-semibold">
                          Sub: ${user.subtotal.toFixed(2)} + Tax: ${user.tax.toFixed(2)} + Tip: ${user.tip.toFixed(2)}
                        </div>
                        {user.paid ? (
                          <span className="text-xs text-green-600 font-semibold">✓ Paid</span>
                        ) : (
                          <span className="text-xs text-orange-600 font-semibold">Pending</span>
                        )}
                      </div>
                    </div>
                    
                    {user.selected_items && user.selected_items.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-semibold text-gray-900 mb-2">Selected Items:</p>
                        <div className="grid grid-cols-2 gap-2">
                          {user.selected_items.map((itemId: string) => {
                            const item = session.receipt_items.find((i: any) => i.id === itemId);
                            if (!item) return null;
                            const quantity = item.quantity || 1;
                            return (
                              <div key={itemId} className="text-xs text-gray-700 bg-white px-2 py-1 rounded border">
                                <span className="font-medium">{item.name}</span>
                                {quantity > 1 && <span className="text-gray-500"> (×{quantity})</span>}
                                <div className="text-gray-600">${item.price.toFixed(2)}</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    
                    <div className="text-sm text-gray-900 space-y-1 mt-3 pt-3 border-t border-gray-200">
                      <div className="flex justify-between">
                        <span>Subtotal:</span>
                        <span>${user.subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tax:</span>
                        <span>${user.tax.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tip:</span>
                        <span>${user.tip.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
