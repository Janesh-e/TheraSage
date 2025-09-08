import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { 
  ArrowUp, 
  ArrowDown, 
  MessageCircle, 
  Share, 
  Plus, 
  Search,
  TrendingUp,
  Users,
  Star,
  Filter,
  Clock
} from 'lucide-react';

interface Community {
  id: string;
  name: string;
  description: string;
  members: number;
  isJoined: boolean;
  category: string;
}

interface Post {
  id: string;
  title: string;
  content: string;
  author: string;
  community: string;
  upvotes: number;
  downvotes: number;
  comments: number;
  timeAgo: string;
  isUpvoted: boolean;
  isDownvoted: boolean;
  flair?: string;
}

interface Comment {
  id: string;
  author: string;
  content: string;
  upvotes: number;
  timeAgo: string;
  replies: Comment[];
}

const Community = () => {
  const [selectedCommunity, setSelectedCommunity] = useState<string>('all');
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [sortBy, setSortBy] = useState<'hot' | 'new' | 'top'>('hot');

  // Mock data
  const communities: Community[] = [
    {
      id: 'anxiety-support',
      name: 'r/AnxietySupport',
      description: 'A safe space for students dealing with anxiety',
      members: 15420,
      isJoined: true,
      category: 'Mental Health'
    },
    {
      id: 'study-tips',
      name: 'r/StudyTips',
      description: 'Share effective study methods and academic strategies',
      members: 28950,
      isJoined: false,
      category: 'Academic'
    },
    {
      id: 'college-life',
      name: 'r/CollegeLife',
      description: 'General discussions about college experiences',
      members: 45300,
      isJoined: true,
      category: 'Lifestyle'
    },
    {
      id: 'depression-help',
      name: 'r/DepressionHelp',
      description: 'Support for students struggling with depression',
      members: 12800,
      isJoined: false,
      category: 'Mental Health'
    }
  ];

  const posts: Post[] = [
    {
      id: '1',
      title: 'How I overcame severe test anxiety - my story and tips',
      content: 'After struggling with test anxiety for 2 years, I finally found strategies that work. Here is what helped me the most...',
      author: 'AnonymousOwl_23',
      community: 'r/AnxietySupport',
      upvotes: 342,
      downvotes: 8,
      comments: 67,
      timeAgo: '4 hours ago',
      isUpvoted: false,
      isDownvoted: false,
      flair: 'Success Story'
    },
    {
      id: '2',
      title: 'DAE feel completely overwhelmed with online classes?',
      content: 'I cannot seem to focus during Zoom lectures and my grades are suffering. Anyone else experiencing this?',
      author: 'StudentStruggling',
      community: 'r/CollegeLife',
      upvotes: 156,
      downvotes: 12,
      comments: 89,
      timeAgo: '7 hours ago',
      isUpvoted: true,
      isDownvoted: false,
      flair: 'Discussion'
    },
    {
      id: '3',
      title: 'Pomodoro technique changed my life - detailed guide',
      content: 'I went from barely passing to getting As by using this time management method. Here is exactly how I do it...',
      author: 'StudyGuru_2024',
      community: 'r/StudyTips',
      upvotes: 892,
      downvotes: 23,
      comments: 134,
      timeAgo: '1 day ago',
      isUpvoted: false,
      isDownvoted: false,
      flair: 'Guide'
    }
  ];

  const getVoteColor = (isUpvoted: boolean, isDownvoted: boolean, type: 'up' | 'down') => {
    if (type === 'up' && isUpvoted) return 'text-orange-500';
    if (type === 'down' && isDownvoted) return 'text-blue-500';
    return 'text-muted-foreground hover:text-foreground';
  };

  const getFlairColor = (flair?: string) => {
    switch (flair) {
      case 'Success Story': return 'bg-green-100 text-green-800 border-green-200';
      case 'Discussion': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Guide': return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold">Communities</h1>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search communities..." className="pl-10 w-80" />
              </div>
            </div>
            <Button onClick={() => setShowCreatePost(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Post
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            {/* Sort Options */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Sort by</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {[
                  { key: 'hot', label: 'Hot', icon: TrendingUp },
                  { key: 'new', label: 'New', icon: Clock },
                  { key: 'top', label: 'Top', icon: ArrowUp }
                ].map(({ key, label, icon: Icon }) => (
                  <Button
                    key={key}
                    variant={sortBy === key ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => setSortBy(key as any)}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {label}
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Communities */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Your Communities</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant={selectedCommunity === 'all' ? 'default' : 'ghost'}
                  className="w-full justify-start"
                  onClick={() => setSelectedCommunity('all')}
                >
                  All Posts
                </Button>
                {communities.filter(c => c.isJoined).map((community) => (
                  <Button
                    key={community.id}
                    variant={selectedCommunity === community.id ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => setSelectedCommunity(community.id)}
                  >
                    <span className="truncate">{community.name}</span>
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Popular Communities */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Popular Communities</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {communities.slice(0, 3).map((community, index) => (
                  <div key={community.id} className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <span className="text-xs font-bold">{index + 1}</span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{community.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {community.members.toLocaleString()} members
                      </p>
                    </div>
                    <Button size="sm" variant={community.isJoined ? 'outline' : 'default'}>
                      {community.isJoined ? 'Joined' : 'Join'}
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-4">
            {posts.map((post) => (
              <Card key={post.id} className="hover:bg-muted/50 transition-colors">
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    {/* Vote Section */}
                    <div className="flex flex-col items-center gap-1 pt-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className={`h-6 w-6 p-0 ${getVoteColor(post.isUpvoted, post.isDownvoted, 'up')}`}
                      >
                        <ArrowUp className="h-4 w-4" />
                      </Button>
                      <span className="text-xs font-medium">
                        {(post.upvotes - post.downvotes).toLocaleString()}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className={`h-6 w-6 p-0 ${getVoteColor(post.isUpvoted, post.isDownvoted, 'down')}`}
                      >
                        <ArrowDown className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Post Content */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                        <span className="font-medium">{post.community}</span>
                        <span>•</span>
                        <span>Posted by u/{post.author}</span>
                        <span>•</span>
                        <span>{post.timeAgo}</span>
                        {post.flair && (
                          <>
                            <span>•</span>
                            <Badge variant="outline" className={`text-xs ${getFlairColor(post.flair)}`}>
                              {post.flair}
                            </Badge>
                          </>
                        )}
                      </div>
                      
                      <h3 className="font-semibold mb-2 leading-tight">{post.title}</h3>
                      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                        {post.content}
                      </p>
                      
                      <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" className="h-8 px-2">
                          <MessageCircle className="h-4 w-4 mr-1" />
                          {post.comments} comments
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 px-2">
                          <Share className="h-4 w-4 mr-1" />
                          Share
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Create Post Modal (placeholder) */}
      {showCreatePost && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create a Post</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Community</label>
                <select className="w-full p-2 border rounded-md">
                  <option>Choose a community</option>
                  {communities.filter(c => c.isJoined).map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Title</label>
                <Input placeholder="An interesting title..." />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Content</label>
                <Textarea placeholder="What's on your mind?" rows={6} />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowCreatePost(false)}>
                  Cancel
                </Button>
                <Button>Post</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Community;