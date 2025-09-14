import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Plus, MessageSquare, MoreHorizontal, Edit2, Trash2, Check, X } from "lucide-react";
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
  onNewSession 
}: ChatSessionsSidebarProps) => {
  // Mock data for sessions
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: "1",
      title: "Feeling anxious about exams",
      lastMessage: "Thank you for listening to me today...",
      timestamp: new Date(2024, 8, 14, 15, 30),
      messageCount: 12
    },
    {
      id: "2", 
      title: "Daily check-in",
      lastMessage: "I'm feeling much better today...",
      timestamp: new Date(2024, 8, 13, 10, 15),
      messageCount: 8
    },
    {
      id: "3",
      title: "Sleep issues discussion",
      lastMessage: "The breathing exercises helped...",
      timestamp: new Date(2024, 8, 12, 22, 45),
      messageCount: 15
    },
    {
      id: "4",
      title: "Relationship concerns",
      lastMessage: "I think I understand now...",
      timestamp: new Date(2024, 8, 11, 14, 20),
      messageCount: 20
    }
  ]);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

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

  const saveRename = (sessionId: string) => {
    setSessions(prev => prev.map(session => 
      session.id === sessionId 
        ? { ...session, title: editTitle.trim() || session.title }
        : session
    ));
    setEditingId(null);
    setEditTitle("");
  };

  const cancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleDelete = (sessionId: string) => {
    setSessions(prev => prev.filter(session => session.id !== sessionId));
    if (currentSessionId === sessionId) {
      // If deleting current session, create a new one
      onNewSession();
    }
  };

  const handleNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: "New conversation",
      lastMessage: "",
      timestamp: new Date(),
      messageCount: 0
    };
    setSessions(prev => [newSession, ...prev]);
    onNewSession();
    onSessionSelect(newSession.id);
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
          {sessions.map((session) => (
            <div
              key={session.id}
              className={cn(
                "group relative p-3 mb-2 rounded-lg cursor-pointer transition-all duration-200 hover:bg-accent/50",
                currentSessionId === session.id 
                  ? "bg-accent border border-primary/20" 
                  : "hover:bg-muted/30"
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
                        <MessageSquare className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <h3 className="font-medium text-sm text-foreground truncate">
                          {session.title}
                        </h3>
                      </div>
                      <p className="text-xs text-muted-foreground truncate mb-1">
                        {session.lastMessage}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">
                          {formatTimestamp(session.timestamp)}
                        </span>
                        <span className="text-xs text-muted-foreground">
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
          ))}
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