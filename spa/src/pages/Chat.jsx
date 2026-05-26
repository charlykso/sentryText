import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, User, ShieldAlert, AlertTriangle, Cpu, RefreshCw } from 'lucide-react';
import { chatService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Chat() {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const pollingInterval = useRef(null);
  
  // Moderation Warning Modal States
  const [showWarning, setShowWarning] = useState(false);
  const [warningData, setWarningData] = useState(null);

  useEffect(() => {
    fetchUsers();
    return () => clearInterval(pollingInterval.current);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchUsers = async () => {
    try {
      const data = await chatService.getUsers();
      setUsers(data);
    } catch (err) {
      console.error('Error fetching chat users:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const selectUserForChat = (user) => {
    setSelectedUser(user);
    setMessages([]);
    clearInterval(pollingInterval.current);
    
    // Fetch initial messages
    fetchMessages(user.Id);
    
    // Start polling every 3 seconds
    pollingInterval.current = setInterval(() => {
      fetchMessagesSilent(user.Id);
    }, 3000);
  };

  const fetchMessages = async (userId) => {
    setLoadingMessages(true);
    try {
      const data = await chatService.getMessages(userId);
      setMessages(data);
    } catch (err) {
      console.error('Error fetching messages:', err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const fetchMessagesSilent = async (userId) => {
    try {
      const data = await chatService.getMessages(userId);
      setMessages(prev => {
        if (prev.length === data.length) {
          const identical = prev.every((msg, idx) => 
            msg.Id === data[idx].Id && 
            msg.ModerationStatus === data[idx].ModerationStatus && 
            msg.MessageText === data[idx].MessageText
          );
          if (identical) return prev;
        }
        return data;
      });
    } catch (err) {
      console.error('Error polling messages:', err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedUser) return;
    setSending(true);

    try {
      const data = await chatService.sendMessage(selectedUser.Id, newMessage);
      if (data.moderation_status === 'Blocked') {
        // Proactive Interception Block
        setWarningData({
          type: 'Message',
          text: newMessage,
          verdict: data.verdict,
          message: data.message
        });
        setShowWarning(true);
      } else {
        // Message Approved
        setMessages([...messages, data.message]);
        setNewMessage('');
      }
    } catch (err) {
      console.error('Error sending message:', err);
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const { user } = useAuth();
  const currentUserId = user?.id || 0;

  return (
    <div className="glass-panel rounded-3xl overflow-hidden h-[75vh] flex grid grid-cols-1 md:grid-cols-4 border border-dark-800/80">
      {/* Left Sidebar - Chat Users List */}
      <div className="md:col-span-1 border-r border-dark-850 flex flex-col bg-dark-900/30">
        <div className="p-4 border-b border-dark-850 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-brand-500" />
          <h3 className="font-outfit font-bold text-dark-100 text-base">Conversations</h3>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loadingUsers ? (
            <div className="text-center py-6 text-dark-500 flex items-center justify-center gap-2 text-sm">
              <RefreshCw className="w-4 h-4 animate-spin text-brand-500" /> Loading users...
            </div>
          ) : users.length === 0 ? (
            <p className="text-center py-6 text-xs text-dark-500">No other users found on SentryText.</p>
          ) : (
            users.map((u) => (
              <button
                key={u.Id}
                onClick={() => selectUserForChat(u)}
                className={`w-full text-left p-3 rounded-2xl flex items-center gap-3 transition-all duration-200 ${selectedUser?.Id === u.Id ? 'bg-brand-600/10 border border-brand-500/20 text-brand-400' : 'text-dark-300 hover:bg-dark-900/60'}`}
              >
                <div className="w-9 h-9 rounded-xl bg-dark-950 flex items-center justify-center border border-dark-800 text-sm font-bold uppercase">
                  {u.Username.substring(0, 2)}
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-dark-100 capitalize">{u.Username}</h4>
                  <p className="text-xs text-dark-500">Click to chat</p>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right Column - Chat Room */}
      <div className="md:col-span-3 flex flex-col bg-dark-950/20 h-full">
        {selectedUser ? (
          <>
            {/* Active User Header */}
            <div className="p-4 border-b border-dark-850 flex items-center justify-between bg-dark-900/25">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center font-bold text-brand-400 capitalize">
                  {selectedUser.Username.substring(0, 2)}
                </div>
                <div>
                  <h4 className="font-outfit font-bold text-dark-100 capitalize">{selectedUser.Username}</h4>
                  <span className="text-[10px] text-green-400 font-semibold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Active Connection
                  </span>
                </div>
              </div>
            </div>

            {/* Conversation Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loadingMessages ? (
                <div className="h-full flex items-center justify-center text-sm text-dark-500 gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-brand-500" /> Fetching secure messages...
                </div>
              ) : messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-dark-500 p-8">
                  <div className="w-12 h-12 rounded-2xl bg-dark-900 border border-dark-800 flex items-center justify-center mb-3">
                    <MessageSquare className="w-5 h-5 text-dark-400" />
                  </div>
                  <p className="font-semibold">Start of Conversation</p>
                  <p className="text-xs mt-1 max-w-xs">Messages are screened dynamically to ensure safe, harassment-free interactions.</p>
                </div>
              ) : (
                messages.map((msg) => {
                  const isMe = msg.SenderId === currentUserId;
                  const isBlocked = msg.ModerationStatus === 'Blocked';
                  return (
                    <div 
                      key={msg.Id} 
                      className={`flex ${isMe ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                    >
                      <div className={`max-w-[70%] rounded-2xl p-3 border transition-all duration-200 ${
                        isBlocked
                          ? 'bg-red-500/10 border-red-500/20 text-red-400 italic font-mono text-xs rounded-2xl'
                          : isMe
                            ? 'bg-brand-600 border-transparent text-white rounded-tr-none'
                            : 'bg-dark-900 border-dark-800 text-dark-100 rounded-tl-none'
                      }`}>
                        <p className="text-sm leading-relaxed break-words">{msg.MessageText}</p>
                        <span className="text-[9px] text-dark-500 text-right block mt-1">
                          {new Date(msg.Timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input Form */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-dark-850 bg-dark-900/25 flex gap-2">
              <input
                required
                type="text"
                placeholder="Type your message securely..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1 glass-input py-2 text-sm"
                disabled={sending}
              />
              <button
                type="submit"
                disabled={sending || !newMessage.trim()}
                className="btn-primary px-4 py-2 flex items-center justify-center"
              >
                {sending ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </form>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center text-dark-500 p-8">
            <div className="w-16 h-16 rounded-3xl bg-dark-900 border border-dark-850 flex items-center justify-center mb-4">
              <MessageSquare className="w-8 h-8 text-dark-400" />
            </div>
            <h3 className="font-outfit font-bold text-lg text-dark-100">Private Chat Room</h3>
            <p className="text-sm mt-1 max-w-xs">Select a user from the conversations sidebar to begin private direct messaging.</p>
          </div>
        )}
      </div>

      {/* PROACTIVE MODERATION WARNING MODAL */}
      {showWarning && warningData && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="glass-panel w-full max-w-lg rounded-3xl p-6 relative shadow-2xl border-red-500/20 max-h-[90vh] overflow-y-auto">
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-red-500" />
            
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/25 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-outfit font-extrabold text-xl text-dark-100">Message Delivery Aborted</h3>
                <p className="text-sm text-dark-400 mt-1">{warningData.message}</p>
              </div>
            </div>

            <div className="bg-dark-950/80 rounded-2xl p-4 border border-dark-900 mb-6">
              <span className="text-[10px] uppercase font-bold text-dark-500 tracking-wider">Blocked Message Text:</span>
              <p className="text-dark-200 text-sm mt-1.5 italic">"{warningData.text}"</p>
            </div>

            {/* Diagnostic Metrics */}
            <div className="space-y-4 mb-8">
              <h4 className="text-xs uppercase font-bold text-dark-400 tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-brand-500" /> Proactive Interceptor Telemetry
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-dark-900/50 border border-dark-800 rounded-2xl p-4">
                  <span className="text-xs text-dark-400 block">Consensus Verdict</span>
                  <strong className="text-red-500 text-lg font-outfit block mt-0.5">Blocked (Harmful)</strong>
                </div>
                <div className="bg-dark-900/50 border border-dark-800 rounded-2xl p-4">
                  <span className="text-xs text-dark-400 block">Avg. Harmful Score</span>
                  <strong className="text-dark-100 text-lg font-outfit block mt-0.5">{warningData.verdict.confidence_score}%</strong>
                </div>
                <div className="bg-dark-900/50 border border-dark-800 rounded-2xl p-4 col-span-2 sm:col-span-1">
                  <span className="text-xs text-dark-400 block">Logistic Regression</span>
                  <span className={`text-sm font-semibold block mt-1 ${warningData.verdict.lr_classification === 'Harmful' ? 'text-red-400' : 'text-green-400'}`}>
                    {warningData.verdict.lr_classification} ({warningData.verdict.lr_confidence}%)
                  </span>
                </div>
                <div className="bg-dark-900/50 border border-dark-800 rounded-2xl p-4 col-span-2 sm:col-span-1">
                  <span className="text-xs text-dark-400 block">SVM Classifier</span>
                  <span className={`text-sm font-semibold block mt-1 ${warningData.verdict.svm_classification === 'Harmful' ? 'text-red-400' : 'text-green-400'}`}>
                    {warningData.verdict.svm_classification} ({warningData.verdict.svm_confidence}%)
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowWarning(false);
                  setWarningData(null);
                }}
                className="w-full sm:w-auto btn-secondary text-sm"
              >
                Go Back & Edit Message
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
