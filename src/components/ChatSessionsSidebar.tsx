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

  const loadSessions = async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) return;

      const response = await fetch(`http://localhost:8000/sessions/user/${userId}`, {
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const data = await response.json();
        const formattedSessions = data.map((session: any) => ({
          id: session.id,
          title: session.title,
          lastMessage: session.last_message || "No messages yet",
          timestamp: new Date(session.updated_at),
          messageCount: session.message_count || 0,
        }));
        setSessions(formattedSessions);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    if (diffInHours < 48) return "Yesterday";
    return date.toLocaleDateString();
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
      const userId = localStorage.getItem('user_id');
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}/rename`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ new_title: newTitle, user_id: userId }),
      });

      if (response.ok) {
        setSessions((prev) =>
          prev.map((session) =>
            session.id === sessionId
              ? { ...session, title: newTitle }
              : session
          )
        );
      }
    } catch (error) {
      console.error('Error renaming session:', error);
    }
    
    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleDelete = async (sessionId: string) => {
    try {
      const userId = localStorage.getItem('user_id');
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        setSessions((prev) => prev.filter((session) => session.id !== sessionId));
        if (currentSessionId === sessionId) {
          onNewSession();
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleNewSession = async () => {
    try {
      const userId = localStorage.getItem('user_id');
      const response = await fetch('http://localhost:8000/sessions/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ 
          title: "New conversation",
          user_id: userId
        }),
      });

      if (response.ok) {
        const newSession = await response.json();
        const formattedSession: ChatSession = {
          id: newSession.id,
          title: newSession.title,
          lastMessage: "",
          timestamp: new Date(newSession.created_at),
          messageCount: 0,
        };
        
        setSessions((prev) => [formattedSession, ...prev]);
        onNewSession();
        onSessionSelect(newSession.id);
      }
    } catch (error) {
      console.error('Error creating new session:', error);
    }
  };

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
          {sessions.map((session) => {
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
                onClick={() => onSessionSelect(session.id)}
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
          })}
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
