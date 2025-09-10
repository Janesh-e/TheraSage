import React, { useState } from "react";
import Layout from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  Filter,
  BookOpen,
  Headphones,
  Play,
  ExternalLink,
  Heart,
  Share2,
  Clock,
  Star,
  Download,
  Eye,
} from "lucide-react";

interface Resource {
  id: string;
  title: string;
  description: string;
  type: "article" | "audio" | "video";
  category: string;
  image: string;
  duration?: string;
  source: string;
  url: string;
  isExternal: boolean;
  rating: number;
  views: number;
  tags: string[];
  isBookmarked: boolean;
}

const mockResources: Resource[] = [
  {
    id: "1",
    title: "Understanding Anxiety: A Complete Guide for Students",
    description:
      "Learn practical techniques to manage anxiety during college life, including breathing exercises and mindfulness practices.",
    type: "article",
    category: "Mental Health",
    image:
      "https://images.unsplash.com/photo-1544027993-37dbfe43562a?w=400&h=250&fit=crop",
    source: "MindSpace Blog",
    url: "/article/1",
    isExternal: false,
    rating: 4.8,
    views: 1250,
    tags: ["anxiety", "mindfulness", "students"],
    isBookmarked: false,
  },
  {
    id: "2",
    title: "Meditation for Beginners",
    description:
      "A 20-minute guided meditation to help you start your mindfulness journey and reduce daily stress.",
    type: "audio",
    category: "Mindfulness",
    image:
      "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=250&fit=crop",
    duration: "20 min",
    source: "Calm Stories",
    url: "https://example.com/audio/meditation",
    isExternal: true,
    rating: 4.9,
    views: 890,
    tags: ["meditation", "relaxation", "mindfulness"],
    isBookmarked: true,
  },
  {
    id: "3",
    title: "Study Techniques That Actually Work",
    description:
      "Evidence-based study methods that will improve your academic performance and reduce study stress.",
    type: "video",
    category: "Academic Success",
    image:
      "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=400&h=250&fit=crop",
    duration: "15 min",
    source: "YouTube",
    url: "https://youtube.com/watch?v=example",
    isExternal: true,
    rating: 4.7,
    views: 2100,
    tags: ["study", "productivity", "academic"],
    isBookmarked: false,
  },
  {
    id: "4",
    title: "The Science of Sleep and Mental Health",
    description:
      "Discover the crucial connection between quality sleep and mental wellbeing, with actionable tips for better sleep hygiene.",
    type: "article",
    category: "Health & Wellness",
    image:
      "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=400&h=250&fit=crop",
    source: "Sleep Foundation",
    url: "/article/4",
    isExternal: false,
    rating: 4.6,
    views: 1580,
    tags: ["sleep", "health", "wellbeing"],
    isBookmarked: true,
  },
  {
    id: "5",
    title: "Building Resilience Through Difficult Times",
    description:
      "An inspiring audiobook excerpt about developing emotional resilience and coping strategies for life challenges.",
    type: "audio",
    category: "Personal Growth",
    image:
      "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=250&fit=crop",
    duration: "45 min",
    source: "Audible",
    url: "https://audible.com/example",
    isExternal: true,
    rating: 4.9,
    views: 750,
    tags: ["resilience", "growth", "coping"],
    isBookmarked: false,
  },
  {
    id: "6",
    title: "Time Management for Overwhelmed Students",
    description:
      "Learn how to balance academics, social life, and self-care without burning out.",
    type: "video",
    category: "Productivity",
    image:
      "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=400&h=250&fit=crop",
    duration: "12 min",
    source: "TED-Ed",
    url: "https://youtube.com/watch?v=example2",
    isExternal: true,
    rating: 4.8,
    views: 1890,
    tags: ["time-management", "productivity", "balance"],
    isBookmarked: true,
  },
];

const categories = [
  "All",
  "Mental Health",
  "Mindfulness",
  "Academic Success",
  "Health & Wellness",
  "Personal Growth",
  "Productivity",
];

const ResourceHub = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedType, setSelectedType] = useState("all");
  const [resources, setResources] = useState(mockResources);

  const filteredResources = resources.filter((resource) => {
    const matchesSearch =
      resource.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      resource.tags.some((tag) =>
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      );

    const matchesCategory =
      selectedCategory === "All" || resource.category === selectedCategory;
    const matchesType =
      selectedType === "all" || resource.type === selectedType;

    return matchesSearch && matchesCategory && matchesType;
  });

  const toggleBookmark = (id: string) => {
    setResources((prev) =>
      prev.map((resource) =>
        resource.id === id
          ? { ...resource, isBookmarked: !resource.isBookmarked }
          : resource
      )
    );
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "article":
        return <BookOpen className="h-4 w-4" />;
      case "audio":
        return <Headphones className="h-4 w-4" />;
      case "video":
        return <Play className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "article":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300";
      case "audio":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300";
      case "video":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300";
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Search and Filters */}
      <div className="bg-card rounded-2xl p-6 shadow-sm border border-border">
        <div className="flex flex-col lg:flex-row gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-background"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
                className="rounded-full"
              >
                {category}
              </Button>
            ))}
          </div>
        </div>

        {/* Type Filter Tabs */}
        <Tabs
          value={selectedType}
          onValueChange={setSelectedType}
          className="mt-4"
        >
          <TabsList className="grid w-full grid-cols-4 bg-muted rounded-xl">
            <TabsTrigger value="all" className="rounded-lg">
              All Types
            </TabsTrigger>
            <TabsTrigger value="article" className="rounded-lg">
              Articles
            </TabsTrigger>
            <TabsTrigger value="audio" className="rounded-lg">
              Audio
            </TabsTrigger>
            <TabsTrigger value="video" className="rounded-lg">
              Videos
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Results Count */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Filter className="h-4 w-4" />
        <span>Showing {filteredResources.length} resources</span>
      </div>

      {/* Resources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredResources.map((resource) => (
          <Card
            key={resource.id}
            className="group overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
          >
            <div className="relative overflow-hidden">
              <img
                src={resource.image}
                alt={resource.title}
                className="w-full h-48 object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div className="absolute top-3 left-3 flex gap-2">
                <Badge
                  className={`${getTypeColor(
                    resource.type
                  )} flex items-center gap-1`}
                >
                  {getTypeIcon(resource.type)}
                  {resource.type}
                </Badge>
                {resource.duration && (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1"
                  >
                    <Clock className="h-3 w-3" />
                    {resource.duration}
                  </Badge>
                )}
              </div>
              <Button
                variant="ghost"
                size="sm"
                className={`absolute top-3 right-3 p-2 rounded-full ${
                  resource.isBookmarked
                    ? "text-red-500 bg-white/90"
                    : "text-white bg-black/20"
                } hover:bg-white/90 hover:text-red-500`}
                onClick={() => toggleBookmark(resource.id)}
              >
                <Heart
                  className={`h-4 w-4 ${
                    resource.isBookmarked ? "fill-current" : ""
                  }`}
                />
              </Button>
            </div>

            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-lg leading-tight line-clamp-2 group-hover:text-primary transition-colors">
                  {resource.title}
                </CardTitle>
              </div>
              <CardDescription className="line-clamp-3 text-sm leading-relaxed">
                {resource.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-0">
              <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                <div className="flex items-center gap-1">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  <span>{resource.rating}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  <span>{resource.views.toLocaleString()}</span>
                </div>
                <span>by {resource.source}</span>
              </div>

              <div className="flex flex-wrap gap-1 mb-4">
                {resource.tags.slice(0, 3).map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="text-xs px-2 py-1"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </CardContent>

            <CardFooter className="pt-0 flex gap-2">
              <Button className="flex-1" size="sm">
                {resource.type === "article" &&
                  !resource.isExternal &&
                  "Read Article"}
                {resource.type === "article" && resource.isExternal && (
                  <>
                    Read <ExternalLink className="h-3 w-3 ml-1" />
                  </>
                )}
                {resource.type === "audio" && (
                  <>
                    Listen <ExternalLink className="h-3 w-3 ml-1" />
                  </>
                )}
                {resource.type === "video" && (
                  <>
                    Watch <ExternalLink className="h-3 w-3 ml-1" />
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" className="p-2">
                <Share2 className="h-4 w-4" />
              </Button>
              {resource.type === "audio" && (
                <Button variant="outline" size="sm" className="p-2">
                  <Download className="h-4 w-4" />
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>

      {filteredResources.length === 0 && (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-foreground mb-2">
            No resources found
          </h3>
          <p className="text-muted-foreground">
            Try adjusting your search or filters
          </p>
        </div>
      )}

      {/* Bottom CTA */}
      <div className="bg-gradient-to-r from-primary/5 to-secondary/5 rounded-2xl p-8 text-center">
        <h3 className="text-2xl font-semibold text-foreground mb-2">
          Can't find what you're looking for?
        </h3>
        <p className="text-muted-foreground mb-4">
          Suggest a resource or topic you'd like to see added to our hub
        </p>
        <Button>Suggest a Resource</Button>
      </div>
    </div>
  );
};

export default ResourceHub;
