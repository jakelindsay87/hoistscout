export interface Site {
  id: string;
  name: string;
  start_urls: string[];
  status: 'active' | 'captcha_blocked' | 'legal_blocked' | 'disabled';
  auth?: {
    type: 'login_form' | 'basic_auth' | 'api_key';
    username_env?: string;
    password_env?: string;
    login_url?: string;
    selectors?: {
      user: string;
      pass: string;
      submit: string;
    };
  };
  pagination?: {
    selector: string;
    limit: number;
  };
  selectors?: Record<string, string>;
  delay?: number;
  timeout?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Opportunity {
  id: string;
  title: string;
  description: string;
  organization: string;
  deadline?: string;
  amount?: string;
  eligibility?: string;
  categories: string[];
  location?: string;
  contact_info?: string;
  application_url?: string;
  requirements: string[];
  site_name: string;
  source_url: string;
  crawl_timestamp?: string;
  created_at: string;
  updated_at: string;
}

export interface CrawlResult {
  site: string;
  status: 'completed' | 'failed';
  crawl_summary: {
    total_pages: number;
    errors: string[];
    opportunities_found: number;
  };
  opportunities: Opportunity[];
  error?: string;
}

export interface SecretConfig {
  name: string;
  env_var_name: string;
  description?: string;
  required: boolean;
}

export interface AddSiteFormData {
  urls: string[];
  auth_required: boolean;
  auth_type?: 'login_form' | 'basic_auth' | 'api_key';
  username_env?: string;
  password_env?: string;
  login_url?: string;
  user_selector?: string;
  pass_selector?: string;
  submit_selector?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
} 