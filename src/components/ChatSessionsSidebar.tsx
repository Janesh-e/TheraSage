import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Plus,
  MessageSquare,
  MoreHorizontal,
  Edit2,
  Trash2,
  Check,
  X,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
  last_message_at?: string;
  total_messages?: number;
  created_at?: string;
  updated_at?: string;
}

interface ChatSessionsSidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

const ChatSessionsSidebar = ({
  currentSessionId,
  onSessionSelect,
  onNewSession,
}: ChatSessionsSidebarProps) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const [error, setError] = useState<string | null>(null);

  // Load sessions when component mounts
  useEffect(() => {
    loadSessions();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  };

  const getUserId = () => {
    return localStorage.getItem('user_id');
  };

  // Helper function to safely parse dates
  const safeParseDate = (dateString: string | undefined | null): Date => {
    if (!dateString) return new Date();
    try {
      const parsed = new Date(dateString);
      return isNaN(parsed.getTime()) ? new Date() : parsed;
    } catch {
      return new Date();
    }
  };

  // Helper function to transform backend response to frontend format
  const transformSessionData = (backendSession: any): ChatSession => {
    return {
      id: backendSession.id,
      title: backendSession.title || `Chat Session ${backendSession.session_number || ''}`,
      lastMessage: "Continue your conversation...", // Default since backend doesn't provide this
      timestamp: safeParseDate(backendSession.last_message_at || backendSession.updated_at || backendSession.created_at),
      messageCount: backendSession.total_messages || 0,
      // Keep original properties for reference
      last_message_at: backendSession.last_message_at,
      total_messages: backendSession.total_messages,
      created_at: backendSession.created_at,
      updated_at: backendSession.updated_at,
    };
  };

  const loadSessions = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const userId = getUserId();
      if (!userId) {
        setError('User ID not found. Please log in again.');
        return;
      }

      const response = await fetch(`http://localhost:8000/sessions/user/${userId}?limit=50&skip=0&include_archived=false`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const transformedSessions = Array.isArray(data) 
        ? data.map(transformSessionData)
        : [];
      setSessions(transformedSessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
      setError('Failed to load chat sessions');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (date: Date) => {
    // Additional safety check
    if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
      return "Recently";
    }

    try {
      const now = new Date();
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

      if (diffInHours < 1) return "Just now";
      if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
      if (diffInHours < 48) return "Yesterday";
      return date.toLocaleDateString();
    } catch (error) {
      console.error('Error formatting timestamp:', error);
      return "Recently";
    }
  };

  const handleRename = (sessionId: string, currentTitle: string) => {
    setEditingId(sessionId);
    setEditTitle(currentTitle);
  };

  const saveRename = async (sessionId: string) => {
    const newTitle = editTitle.trim();
    if (!newTitle) {
      cancelRename();
      return;
    }

    try {
      const userId = getUserId();
      if (!userId) return;
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}/rename`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ new_title: newTitle, user_id: userId }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const updatedSession = await response.json();
      
      setSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? { ...session, title: updatedSession.title }
            : session
        )
      );
    } catch (error) {
      console.error('Error renaming session:', error);
      setError('Failed to rename session');
    }

    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleDelete = async (sessionId: string) => {
    if (!window.confirm('Are you sure you want to delete this chat session? This action cannot be undone.')) {
      return;
    }

    try {
      const userId = getUserId();
      if (!userId) return;

      const response = await fetch(`http://localhost:8000/sessions/${sessionId}?user_id=${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSessions((prev) => prev.filter((session) => session.id !== sessionId));
      
      // If we deleted the current session, trigger new session creation
      if (currentSessionId === sessionId) {
        onNewSession();
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      setError('Failed to delete session');
    }
  };

  const handleNewSession = async () => {
    try {
      const userId = localStorage.getItem('user_id');
    console.log('Creating new session for user:', userId); // Debug log
    
    const response = await fetch(`http://localhost:8000/sessions/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ 
        user_id: userId,
        title: null
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Server error:', errorData); // Debug log
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const newSession = await response.json();
    console.log('New session created:', newSession); // Debug log

     // Transform the new session data
      const transformedNewSession = transformSessionData(newSession);
      
      // Add new session to the top of the list
      setSessions((prev) => [transformedNewSession, ...prev]);
    
    // Select the new session
    console.log('Selecting new session:', newSession.id); // Debug log
    onSessionSelect(newSession.id);
    } catch (error) {
      console.error('Error creating new session:', error);
      setError('Failed to create new session');
    }
  };

    const handleSessionSelect = (sessionId: string) => {
    // Validate UUID format before selecting
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(sessionId)) {
      console.error('Invalid session ID format:', sessionId);
      setError('Invalid session ID');
      return;
    }
    
    onSessionSelect(sessionId);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="w-80 h-full bg-card border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <Button
            onClick={handleNewSession}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Chat
          </Button>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-sm text-muted-foreground">Loading sessions...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-80 h-full bg-card border-r border-border flex flex-col">
        <div className="p-4 border-b border-border">
          <Button
            onClick={handleNewSession}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Chat
          </Button>
        </div>
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="text-center">
            <div className="text-sm text-red-600 mb-2">{error}</div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => {
                setError(null);
                loadSessions();
              }}
            >
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 h-full bg-card border-r border-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <Button
          onClick={handleNewSession}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {sessions.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No chat sessions yet</p>
              <p className="text-xs text-muted-foreground">Start a new conversation!</p>
            </div>
          ) : (
            sessions.map((session) => {
              const isSelected = currentSessionId === session.id;

              return (
                <div
                  key={session.id}
                  className={cn(
                    "group relative p-3 mb-2 rounded-lg cursor-pointer transition-all duration-200",
                    isSelected
                      ? "bg-primary/10 border border-primary/30 shadow-sm"
                      : "hover:bg-muted/50"
                  )}
                  onClick={() => handleSessionSelect(session.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {editingId === session.id ? (
                        <div className="flex items-center gap-1">
                          <Input
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") saveRename(session.id);
                              if (e.key === "Escape") cancelRename();
                            }}
                            className="h-6 text-sm px-2 py-1"
                            autoFocus
                            onBlur={() => saveRename(session.id)}
                          />
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              saveRename(session.id);
                            }}
                          >
                            <Check className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              cancelRename();
                            }}
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-2 mb-1">
                            <MessageSquare
                              className={cn(
                                "w-4 h-4 flex-shrink-0",
                                isSelected
                                  ? "text-primary"
                                  : "text-muted-foreground"
                              )}
                            />
                            <h3
                              className={cn(
                                "font-medium text-sm truncate",
                                isSelected
                                  ? "text-primary font-semibold"
                                  : "text-foreground"
                              )}
                            >
                              {session.title}
                            </h3>
                          </div>
                          <p
                            className={cn(
                              "text-xs truncate mb-1",
                              isSelected
                                ? "text-primary/70"
                                : "text-muted-foreground"
                            )}
                          >
                            {session.lastMessage}
                          </p>
                          <div className="flex items-center justify-between">
                            <span
                              className={cn(
                                "text-xs",
                                isSelected
                                  ? "text-primary/60"
                                  : "text-muted-foreground"
                              )}
                            >
                              {formatTimestamp(session.timestamp)}
                            </span>
                            <span
                              className={cn(
                                "text-xs",
                                isSelected
                                  ? "text-primary/60"
                                  : "text-muted-foreground"
                              )}
                            >
                              {session.messageCount} messages
                            </span>
                          </div>
                        </>
                      )}
                    </div>

                    {editingId !== session.id && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 ml-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRename(session.id, session.title);
                            }}
                          >
                            <Edit2 className="w-4 h-4 mr-2" />
                            Rename
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(session.id);
                            }}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>

      <Separator />

      {/* Footer */}
      <div className="p-3">
        <p className="text-xs text-muted-foreground text-center">
          Your conversations are private and secure
        </p>
      </div>
    </div>
  );
};

export default ChatSessionsSidebar;