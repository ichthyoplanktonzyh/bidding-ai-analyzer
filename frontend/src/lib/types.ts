// ===== Task Types =====

export type TaskStatus =
  | 'pending'
  | 'spidering'
  | 'awaiting_decision'
  | 'analyzing'
  | 'completed'
  | 'failed';

export interface Task {
  id: string;
  keyword: string;
  start_time: string | null;
  end_time: string | null;
  filter_keywords: string[];
  status: TaskStatus;
  progress: number;
  total_items: number;
  analyzed_items: number;
  spider_item_count: number;
  created_at: string;
  completed_at: string | null;
  error: string;
}

export interface TaskCreateRequest {
  keyword: string;
  start_time?: string;
  end_time?: string;
  filter_keywords?: string[];
}

export interface StartAnalysisRequest {
  selected_indices?: number[];
}

// ===== Spider Result Types =====

export interface SpiderResult {
  标题: string;
  URL: string;
  发布日期: string;
  采购人: string;
  代理机构?: string;
  所在区域?: string;
  来源?: string;
}

export interface SpiderResultsResponse {
  task_id: string;
  results: SpiderResult[];
  total: number;
}

// ===== Filter Keywords Types =====

export interface FilterKeywordsPreset {
  id: string;
  name: string;
  keywords: string[];
  created_at: string;
}

export interface FilterKeywordsRequest {
  name: string;
  keywords: string[];
}

// ===== WebSocket Event Types =====

export interface WsStatusUpdate {
  type: 'status_update';
  task_id: string;
  status: TaskStatus;
  progress: number;
  total_items: number;
  analyzed_items: number;
  spider_item_count: number;
  error: string;
  timestamp: number;
}

export type WsEvent = WsStatusUpdate | { type: 'pipeline_complete'; status: string } | { type: 'error'; message: string };

// ===== Analysis Result Types =====

export interface AnalysisData {
  project_status: string | null;
  tender_release_date: string | null;
  bid_award_date: string | null;
  purchasing_entity: string | null;
  project_name: string | null;
  purchaser_info: string | null;
  product_type: string | null;
  budget_amount: string | null;
  winning_bid_amount: string | null;
  supplier_name: string | null;
  procurement_type: string | null;
  tender_notice_url: string | null;
  procurement_documents: string | null;
}

export interface AnalysisResult {
  success: boolean;
  data?: AnalysisData;
  error?: string;
}

export interface ResultRecord {
  index: number;
  original: {
    标题: string;
    URL: string;
    发布日期: string;
    采购人: string;
    代理机构?: string;
    所在区域?: string;
    来源?: string;
  };
  analysis: AnalysisResult;
}

export interface PaginatedResults {
  task_id: string;
  results: ResultRecord[];
  total: number;
  success_count: number;
  offset: number;
  limit: number;
}

// ===== UI Types =====

export type NavItem = {
  label: string;
  href: string;
  icon: string;
};
