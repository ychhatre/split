'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { receiptAPI, sessionAPI, ReceiptData } from '../../lib/api';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [hostName, setHostName] = useState('');
  const [hostPaymentHandle, setHostPaymentHandle] = useState('');
  const [venmoValidationError, setVenmoValidationError] = useState('');
  const [numberOfGuests, setNumberOfGuests] = useState<number>(1);
  const [guestInputValue, setGuestInputValue] = useState<string>('1');
  const [receiptData, setReceiptData] = useState<ReceiptData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  // Validate Venmo username format (required)
  const validateVenmoUsername = (username: string): { isValid: boolean; error: string } => {
    if (!username) {
      return { isValid: false, error: 'Venmo username is required' };
    }

    // Remove @ if present at the start
    const cleanUsername = username.startsWith('@') ? username.slice(1) : username;

    // Venmo username rules:
    // - 5-30 characters
    // - Letters, numbers, hyphens, underscores only
    const venmoUsernameRegex = /^[a-zA-Z0-9_-]{5,30}$/;

    if (cleanUsername.length < 5) {
      return { isValid: false, error: 'Username must be at least 5 characters' };
    }

    if (cleanUsername.length > 30) {
      return { isValid: false, error: 'Username must be 30 characters or less' };
    }

    if (!venmoUsernameRegex.test(cleanUsername)) {
      return { isValid: false, error: 'Username can only contain letters, numbers, hyphens, and underscores' };
    }

    return { isValid: true, error: '' };
  };

  // Format Venmo username for display (add @ if not present)
  const formatVenmoUsername = (username: string): string => {
    if (!username) return '';
    return username.startsWith('@') ? username : `@${username}`;
  };

  const handlePaymentHandleChange = (value: string) => {
    setHostPaymentHandle(value);
    const validation = validateVenmoUsername(value);
    setVenmoValidationError(validation.error);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUploadReceipt = async () => {
    if (!file) {
      setError('Please select a receipt image');
      return;
    }

    if (!hostName) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data = await receiptAPI.upload(file);
      setReceiptData(data);
    } catch (err: any) {
      console.error('Receipt upload error:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to parse receipt. Please try again.';
      setError(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async () => {
    if (!receiptData) return;

    setLoading(true);
    setError('');

    try {
      const session = await sessionAPI.create({
        host_name: hostName,
        receipt_data: receiptData,
        receipt_image_url: receiptData.image_url,
        session_id: receiptData.session_id,
        host_payment_handle: hostPaymentHandle,
        number_of_guests: numberOfGuests,
      });

      router.push(`/host/${session.id}`);
    } catch (err: any) {
      console.error('Session creation error:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to create session. Please try again.';
      setError(`Error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveItem = (index: number) => {
    if (!receiptData) return;

    const newItems = receiptData.items.filter((_, i) => i !== index);
    const newSubtotal = newItems.reduce((sum, i) => sum + i.price * (i.quantity || 1), 0);
    const newTotal = newSubtotal + receiptData.tax + receiptData.tip;
    
    setReceiptData({ 
      ...receiptData, 
      items: newItems,
      subtotal: newSubtotal,
      total: newTotal
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Cheque
            </h1>
            <p className="text-gray-600 mb-8">
              Split restaurant bills easily. Scan your receipt and let everyone pay their share.
            </p>

            {!receiptData ? (
              <>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Your Name
                    </label>
                    <input
                      type="text"
                      value={hostName}
                      onChange={(e) => setHostName(e.target.value)}
                      placeholder="Enter your name"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Number of Guests
                    </label>
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={guestInputValue}
                      onChange={(e) => {
                        const value = e.target.value;
                        // Allow empty string while typing
                        if (value === '') {
                          setGuestInputValue('');
                          return;
                        }
                        // Only allow digits
                        if (/^\d+$/.test(value)) {
                          const num = parseInt(value, 10);
                          if (num >= 1 && num <= 99) {
                            setGuestInputValue(value);
                            setNumberOfGuests(num);
                          }
                        }
                      }}
                      onBlur={(e) => {
                        // Ensure valid value on blur
                        const value = e.target.value;
                        if (value === '' || parseInt(value, 10) < 1) {
                          setNumberOfGuests(1);
                          setGuestInputValue('1');
                        }
                      }}
                      placeholder="Enter number of guests"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Enter a number between 1 and 99
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Venmo Username
                    </label>
                    <input
                      type="text"
                      value={hostPaymentHandle}
                      onChange={(e) => handlePaymentHandleChange(e.target.value)}
                      placeholder="e.g., @yourvenmo or yourvenmo"
                      className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:border-transparent text-gray-900 ${
                        venmoValidationError 
                          ? 'border-red-500 focus:ring-red-500' 
                          : 'border-gray-300 focus:ring-indigo-500'
                      }`}
                    />
                    {venmoValidationError ? (
                      <p className="text-xs text-red-600 mt-1 font-semibold">
                        ⚠ {venmoValidationError}
                      </p>
                    ) : hostPaymentHandle && !venmoValidationError ? (
                      <p className="text-xs text-green-600 mt-1 font-semibold">
                        ✓ Valid Venmo username
                      </p>
                    ) : (
                      <p className="text-xs text-gray-500 mt-1">
                        Guests will send payments to this Venmo account
                      </p>
                    )}
                  </div>

                  {/* Venmo Preview */}
                  {hostPaymentHandle && !venmoValidationError && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm font-semibold text-blue-900 mb-2">
                        Preview: Payment Link
                      </p>
                      <div className="bg-white rounded p-3 border border-blue-300">
                        <p className="text-xs text-gray-600 mb-1">Guests will see:</p>
                        <p className="text-sm text-gray-900">
                          Send payment to: <span className="font-bold text-blue-600">{formatVenmoUsername(hostPaymentHandle)}</span>
                        </p>
                        <p className="text-xs text-blue-600 mt-2 italic">
                          Clicking "Pay with Venmo" will open their Venmo app with your username pre-filled
                        </p>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        ⚠️ Important: Make sure this username is correct. We cannot verify if it exists on Venmo.
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Upload Receipt
                    </label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="cursor-pointer flex flex-col items-center"
                      >
                        <svg
                          className="w-12 h-12 text-gray-400 mb-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                          />
                        </svg>
                        <span className="text-gray-600">
                          {file ? file.name : 'Click to upload receipt'}
                        </span>
                      </label>
                    </div>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleUploadReceipt}
                    disabled={loading || !file || !hostName || !!venmoValidationError || !hostPaymentHandle}
                    className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Processing...' : 'Upload Receipt'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="space-y-4 mb-6">
                  <div className="flex justify-between items-center">
                    <h2 className="text-2xl font-semibold text-gray-900">Receipt Preview</h2>
                    <button
                      onClick={() => setReceiptData(null)}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
                    >
                      Upload New Receipt
                    </button>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-semibold mb-3 text-gray-900">Items</h3>
                    <div className="space-y-2">
                      {receiptData.items.map((item, index) => (
                        <div key={item.id} className="flex justify-between items-center text-sm text-gray-900 bg-white p-2 rounded border border-gray-200 gap-2">
                          <input
                            type="text"
                            value={item.name}
                            onChange={(e) => {
                              const newItems = [...receiptData.items];
                              newItems[index] = { ...newItems[index], name: e.target.value };
                              setReceiptData({ ...receiptData, items: newItems });
                            }}
                            className="flex-1 px-2 py-1 border border-gray-300 rounded text-gray-900"
                          />
                          <span>$</span>
                          <input
                            type="number"
                            step="0.01"
                            value={item.price.toFixed(2)}
                            onChange={(e) => {
                              const newItems = [...receiptData.items];
                              newItems[index] = { ...newItems[index], price: Math.round((parseFloat(e.target.value) || 0) * 100) / 100 };
                              // Recalculate subtotal, but keep tax and tip as user-entered values
                              const newSubtotal = newItems.reduce((sum, i) => sum + i.price * (i.quantity || 1), 0);
                              const newTotal = newSubtotal + receiptData.tax + receiptData.tip;
                              setReceiptData({ 
                                ...receiptData, 
                                items: newItems,
                                subtotal: newSubtotal,
                                total: newTotal
                              });
                            }}
                            className="w-20 px-2 py-1 border border-gray-300 rounded text-gray-900 text-right"
                          />
                          {item.quantity > 1 && (
                            <span className="text-gray-500 text-xs">(×{item.quantity})</span>
                          )}
                          <button
                            onClick={() => handleRemoveItem(index)}
                            className="ml-2 px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs font-semibold"
                            title="Remove item"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-300 space-y-2 text-sm text-gray-900">
                      <div className="flex justify-between items-center">
                        <span>Subtotal</span>
                        <span>${receiptData.subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Tax</span>
                        <input
                          type="number"
                          step="0.01"
                          value={receiptData.tax.toFixed(2)}
                          onChange={(e) => {
                            const newTax = Math.round((parseFloat(e.target.value) || 0) * 100) / 100;
                            setReceiptData({
                              ...receiptData,
                              tax: newTax,
                              total: receiptData.subtotal + newTax + receiptData.tip
                            });
                          }}
                          className="w-24 px-2 py-1 border border-gray-300 rounded text-gray-900 text-right"
                        />
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Tip</span>
                        <input
                          type="number"
                          step="0.01"
                          value={receiptData.tip.toFixed(2)}
                          onChange={(e) => {
                            const newTip = Math.round((parseFloat(e.target.value) || 0) * 100) / 100;
                            setReceiptData({
                              ...receiptData,
                              tip: newTip,
                              total: receiptData.subtotal + receiptData.tax + newTip
                            });
                          }}
                          className="w-24 px-2 py-1 border border-gray-300 rounded text-gray-900 text-right"
                        />
                      </div>
                      <div className="flex justify-between font-semibold text-base pt-2 border-t border-gray-300">
                        <span>Total</span>
                        <span>${receiptData.total.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleCreateSession}
                  disabled={loading || !!venmoValidationError || !hostPaymentHandle}
                  className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Creating Session...' : 'Create Session & Share'}
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
