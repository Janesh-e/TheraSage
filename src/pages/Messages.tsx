import React, { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, Users, UserCheck, AlertTriangle, Clock } from "lucide-react";

interface ChatSession {
  id: string;
  type: "peer" | "therapist";
  name: string;
  lastMessage: string;
  timestamp: string;
  unread: number;
  status?: "online" | "offline" | "scheduled";
  isUrgent?: boolean;
}

interface Message {
  id: string;
  sender: "me" | "other";
  content: string;
  timestamp: string;
  senderName?: string;
}

const Messages = () => {
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [newMessage]);

  // Mock data
  const chatSessions: ChatSession[] = [
    {
      id: "1",
      type: "therapist",
      name: "Dr. Sarah Johnson",
      lastMessage:
        "How are you feeling today? Our session is scheduled for 3 PM.",
      timestamp: "2 hours ago",
      unread: 1,
      status: "scheduled",
      isUrgent: true,
    },
    {
      id: "2",
      type: "peer",
      name: "Anonymous_Phoenix",
      lastMessage:
        "Thanks for sharing your experience, it really helped me feel less alone.",
      timestamp: "1 day ago",
      unread: 0,
      status: "offline",
    },
    {
      id: "3",
      type: "peer",
      name: "Study_Buddy_22",
      lastMessage:
        "I totally understand the anxiety about finals. Want to study together?",
      timestamp: "2 days ago",
      unread: 2,
      status: "online",
    },
  ];

  const messages: { [key: string]: Message[] } = {
    "1": [
      {
        id: "1",
        sender: "other",
        content:
          "Hello! I see you were matched with me based on your recent conversations. How are you feeling today?",
        timestamp: "10:30 AM",
        senderName: "Dr. Sarah Johnson",
      },
      {
        id: "2",
        sender: "me",
        content:
          "Hi Dr. Johnson. I have been feeling overwhelmed lately with everything going on.",
        timestamp: "10:35 AM",
      },
      {
        id: "3",
        sender: "other",
        content:
          "I understand. That sounds really challenging. Our session is scheduled for 3 PM today. Would you like to talk about what has been overwhelming you?",
        timestamp: "10:40 AM",
        senderName: "Dr. Sarah Johnson",
      },
    ],
    "2": [
      {
        id: "1",
        sender: "other",
        content:
          "Hey, I saw your post about struggling with sleep. I have been dealing with the same thing.",
        timestamp: "Yesterday 8:30 PM",
        senderName: "Anonymous_Phoenix",
      },
      {
        id: "2",
        sender: "me",
        content:
          "Really? It has been so hard to get a good night sleep lately.",
        timestamp: "Yesterday 8:45 PM",
      },
      {
        id: "3",
        sender: "other",
        content:
          "Thanks for sharing your experience, it really helped me feel less alone.",
        timestamp: "Yesterday 9:15 PM",
        senderName: "Anonymous_Phoenix",
      },
    ],
  };

  const handleSendMessage = () => {
    if (newMessage.trim() && activeChat) {
      // In real implementation, this would send to API
      console.log("Sending message:", newMessage);
      setNewMessage("");
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "online":
        return "bg-green-500";
      case "scheduled":
        return "bg-primary";
      default:
        return "bg-muted-foreground";
    }
  };

  return (
    <div className="h-full bg-background flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Sessions List */}
        <div className="w-96 border-r border-border bg-card shadow-sm flex flex-col">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-heading-md font-semibold text-card-foreground flex items-center gap-3">
              <Users className="h-5 w-5 text-primary" />
              Peer & Therapist Chats
            </h2>
          </div>

          <ScrollArea className="flex-1">
            <div className="space-y-1 p-2">
              {chatSessions.map((session) => (
                <div
                  key={session.id}
                  className={`p-4 cursor-pointer rounded-xl transition-all duration-200 mx-2 ${
                    activeChat === session.id
                      ? "bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/20 shadow-sm"
                      : "hover:bg-accent/50 hover:shadow-sm"
                  }`}
                  onClick={() => setActiveChat(session.id)}
                >
                  <div className="flex items-start gap-4">
                    <div className="relative flex-shrink-0">
                      <Avatar className="h-12 w-12 shadow-sm">
                        <AvatarFallback
                          className={
                            session.type === "therapist"
                              ? "bg-primary/10 text-primary"
                              : "bg-accent text-accent-foreground"
                          }
                        >
                          {session.type === "therapist" ? (
                            <UserCheck className="h-6 w-6" />
                          ) : (
                            <Users className="h-6 w-6" />
                          )}
                        </AvatarFallback>
                      </Avatar>
                      <div
                        className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-card ${getStatusColor(
                          session.status
                        )} shadow-sm`}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-card-foreground truncate">
                          {session.name}
                        </span>
                        {session.type === "therapist" && (
                          <Badge
                            variant="secondary"
                            className="text-xs px-2 py-1"
                          >
                            <UserCheck className="h-3 w-3 mr-1" />
                            Therapist
                          </Badge>
                        )}
                        {session.isUrgent && (
                          <AlertTriangle className="h-4 w-4 text-secondary" />
                        )}
                      </div>

                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
                        {session.lastMessage}
                      </p>

                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {session.timestamp}
                        </span>
                        {session.unread > 0 && (
                          <Badge className="h-6 w-6 rounded-full p-0 flex items-center justify-center text-xs bg-primary text-primary-foreground shadow-sm">
                            {session.unread}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 bg-background flex flex-col">
          {activeChat ? (
            <>
              {/* Chat Header */}
              <div className="flex-shrink-0 border-b border-border bg-card/50 backdrop-blur-sm px-8 py-6 shadow-sm">
                <div className="flex items-center gap-4">
                  <Avatar className="h-14 w-14 shadow-md">
                    <AvatarFallback
                      className={
                        chatSessions.find((s) => s.id === activeChat)?.type ===
                        "therapist"
                          ? "bg-primary/10 text-primary"
                          : "bg-accent text-accent-foreground"
                      }
                    >
                      {chatSessions.find((s) => s.id === activeChat)?.type ===
                      "therapist" ? (
                        <UserCheck className="h-7 w-7" />
                      ) : (
                        <Users className="h-7 w-7" />
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <h3 className="text-heading-md font-bold text-foreground">
                      {chatSessions.find((s) => s.id === activeChat)?.name}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <p className="text-body-sm text-muted-foreground">
                        {chatSessions.find((s) => s.id === activeChat)
                          ?.status === "online"
                          ? "🟢 Online"
                          : chatSessions.find((s) => s.id === activeChat)
                              ?.status === "scheduled"
                          ? "📅 Session Scheduled"
                          : "⚫ Offline"}
                      </p>
                      {chatSessions.find((s) => s.id === activeChat)?.type ===
                        "therapist" && (
                        <Badge
                          variant="outline"
                          className="border-primary/30 text-primary"
                        >
                          <UserCheck className="h-3 w-3 mr-1" />
                          Licensed Therapist
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Messages Area */}
              <ScrollArea className="flex-1">
                <div className="p-8 space-y-6 max-w-4xl mx-auto">
                  {(messages[activeChat] || []).map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.sender === "me"
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[75%] ${
                          message.sender === "me"
                            ? "bg-primary text-primary-foreground"
                            : "bg-card border border-border text-card-foreground"
                        } rounded-xl p-4 shadow-sm`}
                      >
                        {message.sender === "other" && message.senderName && (
                          <p className="text-xs font-semibold mb-2 opacity-70">
                            {message.senderName}
                          </p>
                        )}
                        <p className="text-sm leading-relaxed">
                          {message.content}
                        </p>
                        <p
                          className={`text-xs mt-3 ${
                            message.sender === "me"
                              ? "text-white/70"
                              : "text-muted-foreground"
                          }`}
                        >
                          {message.timestamp}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>

              {/* Message Input */}
              <div className="border-t border-border bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60 px-8 py-6 shadow-lg">
                <div className="max-w-4xl mx-auto">
                  <div className="flex items-start gap-4">
                    <Textarea
                      ref={textareaRef}
                      placeholder="Type your message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      className="flex-1 px-4 py-3 bg-background border-border focus:border-primary focus:ring-2 focus:ring-primary/20 rounded-xl shadow-sm resize-none overflow-y-hidden"
                      rows={1}
                    />
                    <Button
                      onClick={handleSendMessage}
                      className="h-12 px-6 bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl shadow-md hover:shadow-lg transition-all duration-200 self-end"
                    >
                      <Send className="h-5 w-5" />
                    </Button>
                  </div>
                  {/* You can add therapist-specific UI here if needed */}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-accent/5">
              <div className="text-center p-8">
                <div className="w-24 h-24 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
                  <Users className="h-12 w-12 text-primary" />
                </div>
                <h3 className="text-heading-md font-bold text-foreground mb-3">
                  Select a conversation
                </h3>
                <p className="text-body text-muted-foreground max-w-sm">
                  Choose a peer chat or therapist session to start messaging
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Messages;
