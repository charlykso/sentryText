import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Response interceptor to handle authorization failures
api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export const authService = {
  register: async (username, email, password, gender) => {
    const response = await api.post('/auth/register', { Username: username, Email: email, Password: password, Gender: gender });
    return response.data;
  },
  login: async (email, password) => {
    const response = await api.post('/auth/login', { Email: email, Password: password });
    return response.data;
  },
  adminLogin: async (email, password) => {
    const response = await api.post('/auth/admin/login', { Email: email, Password: password });
    return response.data;
  },
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

export const feedService = {
  getPosts: async () => {
    const response = await api.get('/feed/posts');
    return response.data;
  },
  createPost: async (postContent) => {
    const response = await api.post('/feed/posts', { PostContent: postContent });
    return response.data;
  },
  getComments: async (postId) => {
    const response = await api.get(`/feed/posts/${postId}/comments`);
    return response.data;
  },
  createComment: async (postId, commentText) => {
    const response = await api.post(`/feed/posts/${postId}/comments`, { CommentText: commentText });
    return response.data;
  },
  getSafetyHistory: async () => {
    const response = await api.get('/feed/safety-history');
    return response.data;
  },
  likePost: async (postId) => {
    const response = await api.post(`/feed/posts/${postId}/like`);
    return response.data;
  },
  dislikePost: async (postId) => {
    const response = await api.post(`/feed/posts/${postId}/dislike`);
    return response.data;
  },
  likeComment: async (commentId) => {
    const response = await api.post(`/feed/comments/${commentId}/like`);
    return response.data;
  },
  dislikeComment: async (commentId) => {
    const response = await api.post(`/feed/comments/${commentId}/dislike`);
    return response.data;
  }
};

export const chatService = {
  getUsers: async () => {
    const response = await api.get('/chat/users');
    return response.data;
  },
  getMessages: async (receiverId) => {
    const response = await api.get(`/chat/messages/${receiverId}`);
    return response.data;
  },
  sendMessage: async (receiverId, messageText) => {
    const response = await api.post('/chat/messages', { ReceiverId: receiverId, MessageText: messageText });
    return response.data;
  }
};

export const auditorService = {
  analyzeText: async (text) => {
    const response = await api.post('/auditor/analyze', { Text: text });
    return response.data;
  }
};

export const adminService = {
  getTelemetry: async () => {
    const response = await api.get('/admin/telemetry');
    return response.data;
  },
  getLogs: async () => {
    const response = await api.get('/admin/logs');
    return response.data;
  },
  getUsers: async () => {
    const response = await api.get('/admin/users');
    return response.data;
  },
  deleteUser: async (userId) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  }
};

export default api;
