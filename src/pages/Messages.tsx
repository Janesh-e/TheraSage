import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Send, Users, UserCheck, AlertTriangle, Clock } from 'lucide-react';

interface ChatSession {
  id: string;
  type: 'peer' | 'therapist';
  name: string;
  lastMessage: string;
  timestamp: string;
  unread: number;
  status?: 'online' | 'offline' | 'scheduled';
  isUrgent?: boolean;
}

interface Message {
  id: string;
  sender: 'me' | 'other';
  content: string;
  timestamp: string;
  senderName?: string;
}

const Messages = () => {
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');

  // Mock data
  const chatSessions: ChatSession[] = [
    {
      id: '1',
      type: 'therapist',
      name: 'Dr. Sarah Johnson',
      lastMessage: 'How are you feeling today? Our session is scheduled for 3 PM.',
      timestamp: '2 hours ago',
      unread: 1,
      status: 'scheduled',
      isUrgent: true
    },
    {
      id: '2',
      type: 'peer',
      name: 'Anonymous_Phoenix',
      lastMessage: 'Thanks for sharing your experience, it really helped me feel less alone.',
      timestamp: '1 day ago',
      unread: 0,
      status: 'offline'
    },
    {
      id: '3',
      type: 'peer',
      name: 'Study_Buddy_22',
      lastMessage: 'I totally understand the anxiety about finals. Want to study together?',
      timestamp: '2 days ago',
      unread: 2,
      status: 'online'
    }
  ];

  const messages: { [key: string]: Message[] } = {
    '1': [
      {
        id: '1',
        sender: 'other',
        content: 'Hello! I see you were matched with me based on your recent conversations. How are you feeling today?',
        timestamp: '10:30 AM',
        senderName: 'Dr. Sarah Johnson'
      },
      {
        id: '2',
        sender: 'me',
        content: 'Hi Dr. Johnson. I have been feeling overwhelmed lately with everything going on.',
        timestamp: '10:35 AM'
      },
      {
        id: '3',
        sender: 'other',
        content: 'I understand. That sounds really challenging. Our session is scheduled for 3 PM today. Would you like to talk about what has been overwhelming you?',
        timestamp: '10:40 AM',
        senderName: 'Dr. Sarah Johnson'
      }
    ],
    '2': [
      {
        id: '1',
        sender: 'other',
        content: 'Hey, I saw your post about struggling with sleep. I have been dealing with the same thing.',
        timestamp: 'Yesterday 8:30 PM',
        senderName: 'Anonymous_Phoenix'
      },
      {
        id: '2',
        sender: 'me',
        content: 'Really? It has been so hard to get a good night sleep lately.',
        timestamp: 'Yesterday 8:45 PM'
      },
      {
        id: '3',
        sender: 'other',
        content: 'Thanks for sharing your experience, it really helped me feel less alone.',
        timestamp: 'Yesterday 9:15 PM',
        senderName: 'Anonymous_Phoenix'
      }
    ]
  };

  const handleSendMessage = () => {
    if (newMessage.trim() && activeChat) {
      // In real implementation, this would send to API
      console.log('Sending message:', newMessage);
      setNewMessage('');
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'scheduled': return 'bg-blue-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Messages</h1>
        <p className="text-muted-foreground">
          Connect with peers anonymously or communicate with your assigned therapist
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[700px]">
        {/* Chat Sessions List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Conversations
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              {chatSessions.map((session) => (
                <div
                  key={session.id}
                  className={`p-4 border-b cursor-pointer hover:bg-muted/50 transition-colors ${
                    activeChat === session.id ? 'bg-muted' : ''
                  }`}
                  onClick={() => setActiveChat(session.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="relative">
                      <Avatar className="h-10 w-10">
                        <AvatarFallback>
                          {session.type === 'therapist' ? (
                            <UserCheck className="h-5 w-5" />
                          ) : (
                            <Users className="h-5 w-5" />
                          )}
                        </AvatarFallback>
                      </Avatar>
                      <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full ${getStatusColor(session.status)}`} />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium truncate">{session.name}</span>
                        {session.type === 'therapist' && (
                          <Badge variant="secondary" className="text-xs">
                            <UserCheck className="h-3 w-3 mr-1" />
                            Therapist
                          </Badge>
                        )}
                        {session.isUrgent && (
                          <AlertTriangle className="h-4 w-4 text-orange-500" />
                        )}
                      </div>
                      
                      <p className="text-sm text-muted-foreground truncate mb-1">
                        {session.lastMessage}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {session.timestamp}
                        </span>
                        {session.unread > 0 && (
                          <Badge className="h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                            {session.unread}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Chat Interface */}
        <Card className="lg:col-span-2">
          {activeChat ? (
            <>
              <CardHeader className="border-b">
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback>
                      {chatSessions.find(s => s.id === activeChat)?.type === 'therapist' ? (
                        <UserCheck className="h-5 w-5" />
                      ) : (
                        <Users className="h-5 w-5" />
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold">
                      {chatSessions.find(s => s.id === activeChat)?.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {chatSessions.find(s => s.id === activeChat)?.status === 'online' ? 'Online' : 
                       chatSessions.find(s => s.id === activeChat)?.status === 'scheduled' ? 'Session Scheduled' : 'Offline'}
                    </p>
                  </div>
                  {chatSessions.find(s => s.id === activeChat)?.type === 'therapist' && (
                    <Badge variant="outline" className="ml-auto">
                      <UserCheck className="h-3 w-3 mr-1" />
                      Licensed Therapist
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              <CardContent className="p-0">
                <ScrollArea className="h-[450px] p-4">
                  <div className="space-y-4">
                    {(messages[activeChat] || []).map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.sender === 'me' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[80%] ${
                          message.sender === 'me' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        } rounded-lg p-3`}>
                          {message.sender === 'other' && message.senderName && (
                            <p className="text-xs font-medium mb-1 opacity-70">
                              {message.senderName}
                            </p>
                          )}
                          <p className="text-sm">{message.content}</p>
                          <p className={`text-xs mt-2 opacity-70`}>
                            {message.timestamp}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
                
                <Separator />
                
                <div className="p-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Type your message..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      className="flex-1"
                    />
                    <Button onClick={handleSendMessage}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                  {chatSessions.find(s => s.id === activeChat)?.type === 'therapist' && (
                    <p className="text-xs text-muted-foreground mt-2">
                      This is a secure, confidential conversation with a licensed mental health professional.
                    </p>
                  )}
                </div>
              </CardContent>
            </>
          ) : (
            <CardContent className="flex items-center justify-center h-full">
              <div className="text-center">
                <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="font-semibold mb-2">Select a conversation</h3>
                <p className="text-muted-foreground">
                  Choose a peer chat or therapist session to start messaging
                </p>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
    </div>
  );
};

export default Messages;