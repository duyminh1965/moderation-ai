export interface ModerationResult {
  id: string;
  content: string;
  type: 'text' | 'image' | 'video';
  status: 'pending' | 'approved' | 'flagged' | 'rejected';
  confidence: number;
  flags: string[];
  timestamp: Date;
  processingTime: number;
}

export interface ModerationResultss {
  id: string;
  bucket: string;
  key: string;
  content_type: string;
  file_size: number;
  timestamp: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  moderation_results: Record<string, any>; // or define a stricter type if needed
  is_inappropriate: boolean;
  confidence_score: number;
}

export interface AnalyticsData {
  totalProcessed: number;
  approved: number;
  flagged: number;
  rejected: number;
  averageProcessingTime: number;
  topFlags: { flag: string; count: number }[];
}

export interface ModerationSettings {
  sensitivityLevel: 'low' | 'medium' | 'high';
  autoReject: boolean;
  enabledCategories: string[];
  confidenceThreshold: number;
}

import { BarChart3, History, Cloud, Zap } from "lucide-react";

export const navigationtab = [
  {
    imgURL:Cloud,
    route: "/",
    label: "S3 → Lambda ",    
  },
  {
    imgURL:Zap,
    route: "/architecture",
    label: "Architecture",    
  },
  {
    imgURL: BarChart3,
    route: "/analytics",
    label: "Analytics",    
  },
  {
    imgURL: History,
    route: "/history",
    label: "History",    
  },

];