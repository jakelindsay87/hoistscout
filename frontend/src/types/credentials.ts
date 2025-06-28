export interface WebsiteCredential {
  id: number;
  website_id: number;
  username: string;
  auth_type: 'basic' | 'form' | 'cookie' | 'oauth';
  additional_fields?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  is_valid: boolean;
  website?: {
    id: number;
    name: string;
    url: string;
  };
}

export interface WebsiteCredentialCreate {
  website_id: number;
  username: string;
  password: string;
  auth_type: 'basic' | 'form' | 'cookie' | 'oauth';
  additional_fields?: string;
  notes?: string;
}

export interface CredentialValidationResult {
  valid: boolean;
  username: string;
  message?: string;
}