'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { sessionAPI, SessionResponse, ReceiptItem, UserResponse } from '../../../../lib/api';

export default function GuestSession() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<SessionResponse | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [userName, setUserName] = useState('');
  const [userId, setUserId] = useState<number | null>(null);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [itemSplits, setItemSplits] = useState<Record<string, number>>({}); // item_id -> split_count
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [joined, setJoined] = useState(false);

  useEffect(() => {
    if (sessionId) {
      fetchSession();
    }
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const data = await sessionAPI.get(sessionId);
      setSession(data);
    } catch (err) {
      setError('Failed to load session');
      console.error(err);
    }
  };

  const handleJoin = async () => {
    if (!userName.trim()) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await sessionAPI.join(sessionId, { name: userName });
      setUserId(response.user_id);
      setJoined(true);
    } catch (err) {
      setError('Failed to join session');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleItemToggle = (itemId: string) => {
    setSelectedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleSelectItems = async () => {
    if (selectedItems.length === 0) {
      setError('Please select at least one item');
      return;
    }

    if (!userId) return;

    setLoading(true);
    setError('');

    try {
      // Convert selectedItems to item_splits format
      const item_splits = selectedItems.map(itemId => ({
        item_id: itemId,
        split_count: itemSplits[itemId] || 1, // Default to 1 if not set
      }));

      const userData = await sessionAPI.selectItems(sessionId, userId, {
        item_splits: item_splits,
      });
      setUser(userData);
      // Refresh session to update claimed_items
      await fetchSession();
    } catch (err: any) {
      // Extract error message from API response
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to update selections';
      setError(errorMessage);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkPaid = async () => {
    if (!userId) return;

    setLoading(true);
    setError('');

    try {
      await sessionAPI.markPaid(sessionId, userId);
      await fetchSession();
      if (user) {
        setUser({ ...user, paid: true });
      }
    } catch (err) {
      setError('Failed to mark as paid');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePayWithVenmo = (username: string, amount: number) => {
    // Venmo deep link format: venmo://paycharge?txn=pay&recipients=USERNAME&amount=AMOUNT&note=MESSAGE
    const venmoUsername = username.replace('@', '');
    const formattedAmount = amount.toFixed(2);
    const note = encodeURIComponent(`Split bill payment`);
    const venmoLink = `venmo://paycharge?txn=pay&recipients=${venmoUsername}&amount=${formattedAmount}&note=${note}`;
    
    // Try to open Venmo app
    window.location.href = venmoLink;
    
    // Set a timeout to check if Venmo opened (fallback after 2 seconds)
    setTimeout(() => {
      window.open(`https://venmo.com/${venmoUsername}?txn=pay&amount=${formattedAmount}&note=${note}`, '_blank');
    }, 2000);
  };

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!joined) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
        <main className="container mx-auto px-4 py-16">
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">Join Session</h1>
              <p className="text-gray-600 mb-6">
                Split the bill for {session.host_name}'s session
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Name
                  </label>
                  <input
                    type="text"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-gray-900"
                  />
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                  </div>
                )}

                <button
                  onClick={handleJoin}
                  disabled={loading}
                  className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 disabled:bg-gray-400"
                >
                  {loading ? 'Joining...' : 'Join Session'}
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h2 className="text-2xl font-bold mb-4 text-gray-900">Select Your Items</h2>
              <p className="text-gray-900 mb-6 font-semibold">Choose which items you ordered</p>

              <div className="space-y-3 mb-6">
                {session.receipt_items.map((item: ReceiptItem) => {
                  const quantity = item.quantity || 1;
                  const itemPrice = item.price * quantity;
                  
                  // Calculate how much of this item has been split
                  const itemSplits = session.item_splits && session.item_splits[item.id] 
                    ? session.item_splits[item.id] 
                    : [];
                  
                  // Calculate total amount already split (excluding current user)
                  const claimedAmount = itemSplits
                    .filter((split: any) => split.user_id !== userId)
                    .reduce((sum: number, split: any) => sum + (split.share || 0), 0);
                  
                  const remainingAmount = itemPrice - claimedAmount;
                  const isFullyClaimed = remainingAmount <= 0;
                  const isPartiallyClaimed = claimedAmount > 0;
                  
                  return (
                    <div
                      key={item.id}
                      className={`p-4 border-2 rounded-lg ${
                        isFullyClaimed 
                          ? 'border-red-300 bg-red-50 opacity-60' 
                          : 'border-gray-200 hover:border-purple-500'
                      }`}
                    >
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedItems.includes(item.id)}
                          onChange={() => !isFullyClaimed && handleItemToggle(item.id)}
                          disabled={isFullyClaimed}
                          className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500 disabled:cursor-not-allowed"
                        />
                        <div className="ml-3 flex-1">
                          <div className="font-medium text-gray-900">
                            {item.name}
                            {quantity > 1 && (
                              <span className="ml-2 text-sm text-gray-500">(×{quantity})</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-900">
                            ${item.price.toFixed(2)}
                            {isFullyClaimed && (
                              <span className="ml-2 text-red-600 font-semibold">• Fully claimed</span>
                            )}
                            {isPartiallyClaimed && !isFullyClaimed && (
                              <span className="ml-2 text-orange-600 font-semibold">
                                • ${remainingAmount.toFixed(2)} remaining
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      {selectedItems.includes(item.id) && !isFullyClaimed && (
                        <div className="mt-3 ml-8 flex items-center gap-2">
                          <label className="text-sm text-gray-700">Split among:</label>
                          <input
                            key={`split-${item.id}`}
                            id={`split-${item.id}`}
                            type="number"
                            min="1"
                            max={session.number_of_guests || 10}
                            step="1"
                            value={itemSplits[item.id] ?? 1}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val === '' || val === null || val === undefined) {
                                return;
                              }
                              const count = Math.max(1, Math.min(parseInt(val) || 1, session.number_of_guests || 10));
                              setItemSplits(prev => {
                                const updated = { ...prev, [item.id]: count };
                                return updated;
                              });
                            }}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-gray-900 text-center"
                          />
                          <span className="text-sm text-gray-500">
                            {itemSplits[item.id] === 1 ? 'person' : 'people'}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>



              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                  {error}
                </div>
              )}

              <button
                onClick={handleSelectItems}
                disabled={loading || selectedItems.length === 0}
                className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400"
              >
                {loading ? 'Calculating...' : 'Calculate Total'}
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100">
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">
              {user.paid ? 'Payment Received!' : 'Your Total'}
            </h2>

            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <div className="space-y-2 text-gray-900">
                <div className="flex justify-between">
                  <span className="font-semibold">Subtotal:</span>
                  <span className="font-semibold">${user.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Tax:</span>
                  <span className="font-semibold">${user.tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Tip:</span>
                  <span className="font-semibold">${user.tip.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-2xl font-bold pt-2 border-t border-gray-300">
                  <span>Total:</span>
                  <span>${user.total.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {!user.paid ? (
              <>
                {user.host_payment_handle && (
                  <div className="space-y-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-800 mb-2">
                        Send ${user.total.toFixed(2)} to: <strong>{user.host_payment_handle}</strong>
                      </p>
                      <p className="text-xs text-blue-600 italic">
                        After completing payment in Venmo, return here and confirm
                      </p>
                    </div>
                    
                    <button
                      onClick={() => user.host_payment_handle && handlePayWithVenmo(user.host_payment_handle, user.total)}
                      disabled={loading || !user.host_payment_handle}
                      className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
                    >
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19.5 3.5L18 2l-1.5 1.5L15 2l-1.5 1.5L12 2l-1.5 1.5L9 2 7.5 3.5 6 2v14H3v3c0 1.66 1.34 3 3 3h12c1.66 0 3-1.34 3-3V2l-1.5 1.5zM19 19c0 .55-.45 1-1 1s-1-.45-1-1v-3H8V5h11v14z"/>
                      </svg>
                      {loading ? 'Processing...' : 'Pay with Venmo'}
                    </button>
                    
                    <div className="border-t border-gray-200 pt-3">
                      <p className="text-xs text-gray-500 text-center mb-2">
                        Already sent the payment?
                      </p>
                      <button
                        onClick={handleMarkPaid}
                        disabled={loading}
                        className="w-full bg-gray-500 text-white py-2 px-4 rounded-lg font-semibold hover:bg-gray-600 disabled:bg-gray-400 text-sm"
                      >
                        {loading ? 'Processing...' : 'Confirm Payment Sent'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <p className="text-green-800 font-semibold">
                  ✓ Payment confirmed! Thank you!
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
