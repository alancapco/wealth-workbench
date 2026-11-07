'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface Message {
  message_id: string;
  workflow_id: string;
  content: string;
  status: 'draft' | 'pending_review' | 'approved' | 'sent';
  created_at: string;
  updated_at: string;
  approved_by?: string;
  approved_at?: string;
}

export default function MessageComposerPage() {
  const params = useParams();
  const workflowId = params?.workflowId as string;

  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    if (workflowId) {
      loadMessages();
    }
  }, [workflowId]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<Message[]>(`/workflows/${workflowId}/messages`);
      setMessages(response.data);
      if (response.data.length > 0 && !selectedMessage) {
        setSelectedMessage(response.data[0]);
      }
    } catch (err: any) {
      console.error('Error loading messages:', err);
      setError(err.message || 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (messageId: string) => {
    try {
      await apiClient.post(`/workflows/${workflowId}/messages/${messageId}/approve`, {
        approved_by: 'current_user',
      });
      await loadMessages();
      alert('Message approved successfully');
    } catch (err: any) {
      console.error('Error approving message:', err);
      alert('Failed to approve message');
    }
  };

  const handleSend = async (messageId: string) => {
    try {
      await apiClient.post(`/workflows/${workflowId}/messages/${messageId}/send`);
      await loadMessages();
      alert('Message sent successfully');
    } catch (err: any) {
      console.error('Error sending message:', err);
      alert('Failed to send message');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'pending_review':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'sent':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-gray-300 border-t-black rounded-full animate-spin" />
              <span className="text-sm text-gray-600">Loading messages...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-4">
            <Link href={`/workflows/${workflowId}`} className="text-blue-600 hover:text-blue-800">
              ← Back to Workflow
            </Link>
          </div>
          <div className="bg-red-50 border border-red-300 rounded p-6">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadMessages}
              className="mt-2 text-sm text-red-800 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link href={`/workflows/${workflowId}`} className="text-blue-600 hover:text-blue-800">
            ← Back to Workflow
          </Link>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Message Composer</h1>
          <p className="text-gray-600">Draft, preview, and approve messages for this workflow</p>
        </div>

        {messages.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-gray-500">No messages found for this workflow</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Message List */}
            <div className="lg:col-span-1 bg-white border border-gray-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4">Messages</h2>
              <div className="space-y-2">
                {messages.map((message) => (
                  <button
                    key={message.message_id}
                    onClick={() => setSelectedMessage(message)}
                    className={`w-full text-left p-3 rounded border transition-all ${
                      selectedMessage?.message_id === message.message_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-mono text-gray-600">
                        {message.message_id.slice(0, 8)}
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(message.status)}`}>
                        {message.status}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(message.created_at).toLocaleString()}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Message Preview/Edit */}
            <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6">
              {selectedMessage ? (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold">
                      {previewMode ? 'Preview' : 'Edit Message'}
                    </h2>
                    <button
                      onClick={() => setPreviewMode(!previewMode)}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                      {previewMode ? 'Edit' : 'Preview'}
                    </button>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-4">
                      <span className={`px-3 py-1 text-sm font-medium rounded ${getStatusColor(selectedMessage.status)}`}>
                        {selectedMessage.status}
                      </span>
                      <span className="text-sm text-gray-500">
                        Created: {new Date(selectedMessage.created_at).toLocaleString()}
                      </span>
                    </div>

                    {selectedMessage.approved_by && (
                      <div className="text-sm text-green-700 mb-4">
                        Approved by {selectedMessage.approved_by} on{' '}
                        {selectedMessage.approved_at && new Date(selectedMessage.approved_at).toLocaleString()}
                      </div>
                    )}
                  </div>

                  {previewMode ? (
                    <div className="border border-gray-300 rounded p-6 bg-gray-50 min-h-[400px] whitespace-pre-wrap">
                      {selectedMessage.content}
                    </div>
                  ) : (
                    <textarea
                      value={selectedMessage.content}
                      onChange={(e) =>
                        setSelectedMessage({ ...selectedMessage, content: e.target.value })
                      }
                      className="w-full min-h-[400px] p-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder="Message content..."
                    />
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-3 mt-6">
                    {selectedMessage.status === 'draft' && (
                      <button
                        onClick={() => handleApprove(selectedMessage.message_id)}
                        className="px-4 py-2 bg-green-600 text-white font-medium rounded hover:bg-green-700 transition-colors"
                      >
                        Approve
                      </button>
                    )}
                    {selectedMessage.status === 'approved' && (
                      <button
                        onClick={() => handleSend(selectedMessage.message_id)}
                        className="px-4 py-2 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 transition-colors"
                      >
                        Send
                      </button>
                    )}
                    <button
                      onClick={loadMessages}
                      className="px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded hover:bg-gray-300 transition-colors"
                    >
                      Refresh
                    </button>
                  </div>
                </>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  Select a message to view or edit
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
