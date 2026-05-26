import React, { useState, useEffect } from 'react';
import { Newspaper, Send, MessageSquare, AlertTriangle, ShieldAlert, Cpu, CornerDownRight, ThumbsUp, ThumbsDown, RefreshCw, Pencil, Trash2, X, Check } from 'lucide-react';
import { feedService } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Feed() {
  const { user } = useAuth();
  const currentUserId = user?.id || 0;

  const [posts, setPosts] = useState([]);
  const [newPost, setNewPost] = useState('');
  const [commentsMap, setCommentsMap] = useState({}); // { postId: [comments] }
  const [newCommentsMap, setNewCommentsMap] = useState({}); // { postId: 'commentText' }
  const [expandedComments, setExpandedComments] = useState({}); // { postId: boolean }
  const [loading, setLoading] = useState(false);
  const [postLoadingMap, setPostLoadingMap] = useState({}); // { postId: boolean }
  
  // Moderation Warning Modal States
  const [showWarning, setShowWarning] = useState(false);
  const [warningData, setWarningData] = useState(null);

  // Editing States
  const [editingPostId, setEditingPostId] = useState(null);
  const [editPostContent, setEditPostContent] = useState('');
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editCommentContent, setEditCommentContent] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  useEffect(() => {
    fetchPosts();
    
    const interval = setInterval(() => {
      fetchPostsSilent();
      pollExpandedComments();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [expandedComments, commentsMap]);

  const fetchPosts = async () => {
    try {
      const data = await feedService.getPosts();
      setPosts(data);
    } catch (err) {
      console.error('Error fetching posts:', err);
    }
  };

  const fetchPostsSilent = async () => {
    try {
      const data = await feedService.getPosts();
      setPosts(prev => {
        if (prev.length === data.length) {
          const identical = prev.every((post, idx) => 
            post.Id === data[idx].Id && 
            post.Likes === data[idx].Likes && 
            post.Dislikes === data[idx].Dislikes && 
            post.ModerationStatus === data[idx].ModerationStatus &&
            post.PostContent === data[idx].PostContent &&
            post.Username === data[idx].Username
          );
          if (identical) return prev;
        }
        return data;
      });
    } catch (err) {
      console.error('Error polling posts:', err);
    }
  };

  const pollExpandedComments = async () => {
    const expandedPostIds = Object.keys(expandedComments).filter(postId => expandedComments[postId]);
    for (const postIdStr of expandedPostIds) {
      const postId = Number(postIdStr);
      try {
        const data = await feedService.getComments(postId);
        setCommentsMap(prev => {
          const prevComments = prev[postId] || [];
          if (prevComments.length === data.length) {
            const identical = prevComments.every((c, idx) => 
              c.Id === data[idx].Id && 
              c.Likes === data[idx].Likes && 
              c.Dislikes === data[idx].Dislikes && 
              c.ModerationStatus === data[idx].ModerationStatus &&
              c.CommentText === data[idx].CommentText &&
              c.Username === data[idx].Username
            );
            if (identical) return prev;
          }
          return { ...prev, [postId]: data };
        });
      } catch (err) {
        console.error(`Error polling comments for post ${postId}:`, err);
      }
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!newPost.trim()) return;
    setLoading(true);

    try {
      const data = await feedService.createPost(newPost);
      if (data.moderation_status === 'Blocked') {
        // Proactive Interception Block
        setWarningData({
          type: 'Post',
          text: newPost,
          verdict: data.verdict,
          message: data.message
        });
        setShowWarning(true);
      } else {
        // Post Approved
        setPosts([data.post, ...posts]);
        setNewPost('');
      }
    } catch (err) {
      console.error('Error creating post:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLikePost = async (postId) => {
    try {
      const data = await feedService.likePost(postId);
      setPosts(prevPosts => prevPosts.map(p => {
        if (p.Id === postId) {
          return { ...p, Likes: data.likes, Dislikes: data.dislikes };
        }
        return p;
      }));
    } catch (err) {
      console.error('Error liking post:', err);
    }
  };

  const handleDislikePost = async (postId) => {
    try {
      const data = await feedService.dislikePost(postId);
      setPosts(prevPosts => prevPosts.map(p => {
        if (p.Id === postId) {
          return { ...p, Likes: data.likes, Dislikes: data.dislikes };
        }
        return p;
      }));
    } catch (err) {
      console.error('Error disliking post:', err);
    }
  };

  const toggleComments = async (postId) => {
    const isExpanded = expandedComments[postId];
    setExpandedComments({ ...expandedComments, [postId]: !isExpanded });

    if (!isExpanded && !commentsMap[postId]) {
      fetchComments(postId);
    }
  };

  const fetchComments = async (postId) => {
    setPostLoadingMap((prev) => ({ ...prev, [postId]: true }));
    try {
      const data = await feedService.getComments(postId);
      setCommentsMap((prev) => ({ ...prev, [postId]: data }));
    } catch (err) {
      console.error('Error fetching comments:', err);
    } finally {
      setPostLoadingMap((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleCreateComment = async (e, postId) => {
    e.preventDefault();
    const commentText = newCommentsMap[postId] || '';
    if (!commentText.trim()) return;
    
    setPostLoadingMap((prev) => ({ ...prev, [postId]: true }));

    try {
      const data = await feedService.createComment(postId, commentText);
      if (data.moderation_status === 'Blocked') {
        // Proactive Interception Block
        setWarningData({
          type: 'Comment',
          text: commentText,
          verdict: data.verdict,
          message: data.message
        });
        setShowWarning(true);
      } else {
        // Comment Approved
        const postComments = commentsMap[postId] || [];
        setCommentsMap((prev) => ({
          ...prev,
          [postId]: [...postComments, data.comment]
        }));
        setNewCommentsMap((prev) => ({ ...prev, [postId]: '' }));
      }
    } catch (err) {
      console.error('Error posting comment:', err);
    } finally {
      setPostLoadingMap((prev) => ({ ...prev, [postId]: false }));
    }
  };

  const handleCommentTextChange = (postId, text) => {
    setNewCommentsMap((prev) => ({ ...prev, [postId]: text }));
  };

  const handleLikeComment = async (postId, commentId) => {
    try {
      const data = await feedService.likeComment(commentId);
      setCommentsMap(prev => ({
        ...prev,
        [postId]: prev[postId].map(c => {
          if (c.Id === commentId) {
            return { ...c, Likes: data.likes, Dislikes: data.dislikes };
          }
          return c;
        })
      }));
    } catch (err) {
      console.error('Error liking comment:', err);
    }
  };

  const handleDislikeComment = async (postId, commentId) => {
    try {
      const data = await feedService.dislikeComment(commentId);
      setCommentsMap(prev => ({
        ...prev,
        [postId]: prev[postId].map(c => {
          if (c.Id === commentId) {
            return { ...c, Likes: data.likes, Dislikes: data.dislikes };
          }
          return c;
        })
      }));
    } catch (err) {
      console.error('Error disliking comment:', err);
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm("Are you sure you want to delete this post? This will also delete all comments and reactions associated with it.")) return;
    try {
      await feedService.deletePost(postId);
      setPosts(prev => prev.filter(p => p.Id !== postId));
    } catch (err) {
      console.error('Error deleting post:', err);
      alert('Failed to delete post.');
    }
  };

  const handleStartEditPost = (post) => {
    setEditingPostId(post.Id);
    setEditPostContent(post.PostContent);
  };

  const handleCancelEditPost = () => {
    setEditingPostId(null);
    setEditPostContent('');
  };

  const handleSaveEditPost = async (postId) => {
    if (!editPostContent.trim()) return;
    setSavingEdit(true);
    try {
      const data = await feedService.updatePost(postId, editPostContent);
      if (data.moderation_status === 'Blocked') {
        setWarningData({
          type: 'Post Update',
          text: editPostContent,
          verdict: data.verdict,
          message: data.message
        });
        setShowWarning(true);
      } else {
        setPosts(prev => prev.map(p => {
          if (p.Id === postId) {
            return { 
              ...p, 
              PostContent: data.post.PostContent, 
              ModerationStatus: data.post.ModerationStatus,
              Likes: data.post.Likes,
              Dislikes: data.post.Dislikes
            };
          }
          return p;
        }));
        setEditingPostId(null);
        setEditPostContent('');
      }
    } catch (err) {
      console.error('Error saving post edit:', err);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteComment = async (postId, commentId) => {
    if (!window.confirm("Are you sure you want to delete this comment?")) return;
    try {
      await feedService.deleteComment(commentId);
      setCommentsMap(prev => ({
        ...prev,
        [postId]: prev[postId].filter(c => c.Id !== commentId)
      }));
    } catch (err) {
      console.error('Error deleting comment:', err);
      alert('Failed to delete comment.');
    }
  };

  const handleStartEditComment = (comment) => {
    setEditingCommentId(comment.Id);
    setEditCommentContent(comment.CommentText);
  };

  const handleCancelEditComment = () => {
    setEditingCommentId(null);
    setEditCommentContent('');
  };

  const handleSaveEditComment = async (postId, commentId) => {
    if (!editCommentContent.trim()) return;
    setSavingEdit(true);
    try {
      const data = await feedService.updateComment(commentId, editCommentContent);
      if (data.moderation_status === 'Blocked') {
        setWarningData({
          type: 'Comment Update',
          text: editCommentContent,
          verdict: data.verdict,
          message: data.message
        });
        setShowWarning(true);
      } else {
        setCommentsMap(prev => ({
          ...prev,
          [postId]: prev[postId].map(c => {
            if (c.Id === commentId) {
              return { 
                ...c, 
                CommentText: data.comment.CommentText, 
                ModerationStatus: data.comment.ModerationStatus,
                Likes: data.comment.Likes,
                Dislikes: data.comment.Dislikes
              };
            }
            return c;
          })
        }));
        setEditingCommentId(null);
        setEditCommentContent('');
      }
    } catch (err) {
      console.error('Error saving comment edit:', err);
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left Columns - Social Feed */}
      <div className="lg:col-span-2 space-y-6">
        {/* Create Post Section */}
        <div className="glass-panel rounded-3xl p-6 relative">
          <div className="flex items-center gap-2 mb-4">
            <Newspaper className="w-5 h-5 text-brand-500" />
            <h2 className="font-outfit font-bold text-lg text-dark-100">Create a Post</h2>
          </div>
          <form onSubmit={handleCreatePost} className="space-y-4">
            <textarea
              required
              rows="3"
              placeholder="What's on your mind? Share something correct... (Pidgin and English supported)"
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
              className="w-full glass-input resize-none"
              disabled={loading}
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading || !newPost.trim()}
                className="btn-primary flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Text...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 animate-spin-none" />
                    <span>Share Post</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Posts Feed Grid */}
        <div className="space-y-4">
          {posts.length === 0 ? (
            <div className="glass-panel rounded-3xl p-12 text-center text-dark-500">
              <p className="text-lg font-medium">No posts in the active feed yet.</p>
              <p className="text-sm mt-1">Be the first to share something positive!</p>
            </div>
          ) : (
            posts.map((post) => {
              const isBlocked = post.ModerationStatus === 'Blocked';
              return (
                <div key={post.Id} className={`glass-panel rounded-3xl p-6 relative transition-all duration-300 ${isBlocked ? 'border-red-500/25 bg-red-950/5' : 'hover:border-dark-800'}`}>
                  {/* Post Author & Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center font-outfit font-bold text-brand-400 capitalize">
                        {post.Username.substring(0, 2)}
                      </div>
                      <div>
                        <h4 className="font-outfit font-bold text-dark-100 capitalize">{post.Username}</h4>
                        <p className="text-xs text-dark-500">{new Date(post.Timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {post.UserId === currentUserId && editingPostId !== post.Id && (
                        <div className="flex items-center gap-1.5 mr-2">
                          <button
                            onClick={() => handleStartEditPost(post)}
                            className="p-1.5 rounded-lg text-dark-400 hover:text-brand-400 hover:bg-dark-900 transition-colors cursor-pointer"
                            title="Edit Post"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeletePost(post.Id)}
                            className="p-1.5 rounded-lg text-dark-400 hover:text-red-400 hover:bg-dark-900 transition-colors cursor-pointer"
                            title="Delete Post"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                      {isBlocked ? (
                        <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-red-500/10 text-red-500 border border-red-500/20">
                          Blocked Content
                        </span>
                      ) : (
                        <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-green-500/10 text-green-400 border border-green-500/20">
                          Safe (Approved)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Post Body / Editing Workspace */}
                  {editingPostId === post.Id ? (
                    <div className="mb-6 space-y-3 bg-dark-950/60 p-4 rounded-2xl border border-dark-800">
                      <textarea
                        rows="3"
                        value={editPostContent}
                        onChange={(e) => setEditPostContent(e.target.value)}
                        className="w-full glass-input resize-none text-sm text-dark-100"
                        disabled={savingEdit}
                      />
                      <div className="flex justify-end gap-2 text-xs">
                        <button
                          onClick={handleCancelEditPost}
                          disabled={savingEdit}
                          className="px-3 py-1.5 rounded-xl border border-dark-800 text-dark-300 hover:bg-dark-900 transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Cancel</span>
                        </button>
                        <button
                          onClick={() => handleSaveEditPost(post.Id)}
                          disabled={savingEdit || !editPostContent.trim()}
                          className="px-3 py-1.5 rounded-xl bg-brand-600 text-white hover:bg-brand-500 transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          {savingEdit ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Check className="w-3.5 h-3.5" />
                          )}
                          <span>Save Changes</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className={`text-base leading-relaxed mb-6 whitespace-pre-wrap ${isBlocked ? 'text-red-400/80 italic font-mono text-sm' : 'text-dark-100'}`}>{post.PostContent}</p>
                  )}

                  {/* Post Actions */}
                  <div className="flex items-center gap-6 border-t border-dark-850 pt-4 text-sm text-dark-400">
                    <button 
                      onClick={() => handleLikePost(post.Id)}
                      disabled={isBlocked || editingPostId === post.Id}
                      className="flex items-center gap-1.5 hover:text-brand-400 transition-colors cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ThumbsUp className="w-4 h-4" /> 
                      <span>Like ({post.Likes || 0})</span>
                    </button>
                    <button 
                      onClick={() => handleDislikePost(post.Id)}
                      disabled={isBlocked || editingPostId === post.Id}
                      className="flex items-center gap-1.5 hover:text-red-400 transition-colors cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
                    >
                      <ThumbsDown className="w-4 h-4" /> 
                      <span>Dislike ({post.Dislikes || 0})</span>
                    </button>
                    <button 
                      onClick={() => toggleComments(post.Id)}
                      className={`flex items-center gap-1.5 hover:text-brand-400 transition-colors cursor-pointer ${expandedComments[post.Id] ? 'text-brand-400' : ''}`}
                    >
                      <MessageSquare className="w-4 h-4" /> Comments
                    </button>
                  </div>

                  {/* Comment Section (Expands) */}
                  {expandedComments[post.Id] && (
                    <div className="mt-6 border-t border-dark-850 pt-6 space-y-4">
                      {/* List of Comments */}
                      <div className="space-y-3 pl-4 border-l-2 border-dark-800">
                        {commentsMap[post.Id]?.map((comment) => {
                          const isCommentBlocked = comment.ModerationStatus === 'Blocked';
                          return (
                            <div key={comment.Id} className={`bg-dark-950/40 rounded-2xl p-4 border transition-all duration-200 ${isCommentBlocked ? 'border-red-500/20 bg-red-950/5' : 'border-dark-900'}`}>
                              <div className="flex items-center justify-between mb-1.5">
                                <div className="flex items-center gap-2">
                                  <CornerDownRight className="w-3.5 h-3.5 text-dark-500" />
                                  <strong className="text-sm text-dark-100 capitalize">{comment.Username}</strong>
                                  {isCommentBlocked && (
                                    <span className="text-[9px] font-bold text-red-400 bg-red-500/10 border border-red-500/15 px-1.5 py-0.2 rounded-full ml-1">
                                      Blocked
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center gap-2">
                                  {comment.UserId === currentUserId && editingCommentId !== comment.Id && (
                                    <div className="flex items-center gap-1">
                                      <button
                                        onClick={() => handleStartEditComment(comment)}
                                        className="p-1 rounded-lg text-dark-400 hover:text-brand-400 hover:bg-dark-900 transition-colors cursor-pointer"
                                        title="Edit Comment"
                                      >
                                        <Pencil className="w-3 h-3" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteComment(post.Id, comment.Id)}
                                        className="p-1 rounded-lg text-dark-400 hover:text-red-400 hover:bg-dark-900 transition-colors cursor-pointer"
                                        title="Delete Comment"
                                      >
                                        <Trash2 className="w-3 h-3" />
                                      </button>
                                    </div>
                                  )}
                                  <span className="text-[10px] text-dark-500">{new Date(comment.Timestamp).toLocaleTimeString()}</span>
                                </div>
                              </div>

                              {/* Comment Body / Editing Workspace */}
                              {editingCommentId === comment.Id ? (
                                <div className="ml-5 mt-2 space-y-2 bg-dark-900/40 p-3 rounded-xl border border-dark-800">
                                  <textarea
                                    rows="2"
                                    value={editCommentContent}
                                    onChange={(e) => setEditCommentContent(e.target.value)}
                                    className="w-full glass-input resize-none text-xs text-dark-100 py-1.5 px-2"
                                    disabled={savingEdit}
                                  />
                                  <div className="flex justify-end gap-1.5 text-[10px]">
                                    <button
                                      onClick={handleCancelEditComment}
                                      disabled={savingEdit}
                                      className="px-2.5 py-1 rounded-lg border border-dark-800 text-dark-300 hover:bg-dark-900 transition-colors flex items-center gap-1 cursor-pointer"
                                    >
                                      <X className="w-3 h-3" />
                                      <span>Cancel</span>
                                    </button>
                                    <button
                                      onClick={() => handleSaveEditComment(post.Id, comment.Id)}
                                      disabled={savingEdit || !editCommentContent.trim()}
                                      className="px-2.5 py-1 rounded-lg bg-brand-600 text-white hover:bg-brand-500 transition-colors flex items-center gap-1 cursor-pointer"
                                    >
                                      {savingEdit ? (
                                        <RefreshCw className="w-3 h-3 animate-spin" />
                                      ) : (
                                        <Check className="w-3 h-3" />
                                      )}
                                      <span>Save</span>
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <p className={`text-sm leading-relaxed ml-5 ${isCommentBlocked ? 'text-red-400/80 italic font-mono text-xs' : 'text-dark-200'}`}>{comment.CommentText}</p>
                              )}
                              
                              {/* Comment Reactions */}
                              {!isCommentBlocked && editingCommentId !== comment.Id && (
                                <div className="flex items-center gap-4 ml-5 mt-2 text-xs text-dark-450 border-t border-dark-850/50 pt-2">
                                  <button 
                                    onClick={() => handleLikeComment(post.Id, comment.Id)}
                                    className="flex items-center gap-1 hover:text-brand-400 transition-colors cursor-pointer"
                                  >
                                    <ThumbsUp className="w-3.5 h-3.5" />
                                    <span>Like ({comment.Likes || 0})</span>
                                  </button>
                                  <button 
                                    onClick={() => handleDislikeComment(post.Id, comment.Id)}
                                    className="flex items-center gap-1 hover:text-red-400 transition-colors cursor-pointer"
                                  >
                                    <ThumbsDown className="w-3.5 h-3.5" />
                                    <span>Dislike ({comment.Dislikes || 0})</span>
                                  </button>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {/* Write Comment Form */}
                      <form onSubmit={(e) => handleCreateComment(e, post.Id)} className="flex gap-2">
                        <input
                          required
                          type="text"
                          placeholder="Write a correct reply..."
                          value={newCommentsMap[post.Id] || ''}
                          onChange={(e) => handleCommentTextChange(post.Id, e.target.value)}
                          className="flex-1 glass-input py-2 text-sm"
                          disabled={postLoadingMap[post.Id]}
                        />
                        <button
                          type="submit"
                          disabled={postLoadingMap[post.Id] || !(newCommentsMap[post.Id] || '').trim()}
                          className="bg-brand-600 hover:bg-brand-500 text-white rounded-xl px-4 flex items-center justify-center transition-all duration-200 cursor-pointer"
                        >
                          {postLoadingMap[post.Id] ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                        </button>
                      </form>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Column - Sidebar with Information */}
      <div className="space-y-6">
        {/* About SentryText Moderation Engine */}
        <div className="glass-panel rounded-3xl p-6 relative">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-5 h-5 text-brand-500" />
            <h3 className="font-outfit font-bold text-dark-100 text-lg">Moderation Engine</h3>
          </div>
          <div className="space-y-3 text-sm text-dark-300 leading-relaxed">
            <p>
              SentryText utilizes a **Dual-Model Proactive Engine** running parallel supervised classifiers:
            </p>
            <ul className="list-disc list-inside space-y-1 text-dark-400 pl-1">
              <li>Logistic Regression</li>
              <li>Support Vector Machine (SVM)</li>
            </ul>
            <p>
              Before any text is published, it is preprocessed (lowercased, tokenized, stop-words removed, stemmed) and classified.
            </p>
            <div className="p-3 bg-brand-950/20 border border-brand-500/10 rounded-2xl flex gap-2 text-brand-400 text-xs">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
              <span>Consensus Safety Policy: Content is blocked if EITHER algorithm flags it as harmful to prevent platform harassment.</span>
            </div>
          </div>
        </div>
      </div>

      {/* PROACTIVE MODERATION WARNING MODAL */}
      {showWarning && warningData && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="glass-panel w-full max-w-lg rounded-3xl p-6 relative shadow-2xl border-red-500/20 max-h-[90vh] overflow-y-auto">
            {/* Top red aesthetic bar */}
            <div className="absolute top-0 left-0 right-0 h-[3px] bg-red-500" />
            
            {/* Modal Header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/25 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-outfit font-extrabold text-xl text-dark-100">Harmful Text Intercepted</h3>
                <p className="text-sm text-dark-400 mt-1">{warningData.message}</p>
              </div>
            </div>

            {/* Blocked Text Preview */}
            <div className="bg-dark-950/80 rounded-2xl p-4 border border-dark-900 mb-6">
              <span className="text-[10px] uppercase font-bold text-dark-500 tracking-wider">Blocked {warningData.type} Content:</span>
              <p className="text-dark-200 text-sm mt-1.5 italic">"{warningData.text}"</p>
            </div>

            {/* Diagnostic Metrics */}
            <div className="space-y-4 mb-8">
              <h4 className="text-xs uppercase font-bold text-dark-400 tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-brand-500" /> Diagnostic Model Telemetry
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

            {/* Modal Controls */}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowWarning(false);
                  setWarningData(null);
                }}
                className="w-full sm:w-auto btn-secondary text-sm cursor-pointer"
              >
                Go Back & Edit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
