'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { WebsiteCredential, WebsiteCredentialCreate } from '@/types/credentials';
import { Website } from '@/types';
import { useCredentialActions } from '@/hooks/useCredentials';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

interface CredentialFormModalProps {
  open: boolean;
  onClose: () => void;
  website: Website;
  credential?: WebsiteCredential;
}

const authTypeOptions = [
  { value: 'basic', label: 'Basic Authentication' },
  { value: 'form', label: 'Form-based Login' },
  { value: 'cookie', label: 'Cookie-based' },
  { value: 'oauth', label: 'OAuth' },
];

const authTypeHelp = {
  basic: 'Standard HTTP Basic Authentication',
  form: 'Login via web form (requires login URL and field selectors)',
  cookie: 'Pre-authenticated cookie values',
  oauth: 'OAuth 2.0 authentication flow',
};

const additionalFieldsTemplate = {
  form: JSON.stringify({
    login_url: 'https://example.com/login',
    username_field: 'input[name="username"]',
    password_field: 'input[name="password"]',
    submit_button: 'button[type="submit"]',
  }, null, 2),
  cookie: JSON.stringify({
    cookies: [
      { name: 'session_id', value: 'your-session-value' }
    ]
  }, null, 2),
  oauth: JSON.stringify({
    client_id: 'your-client-id',
    client_secret: 'your-client-secret',
    auth_url: 'https://example.com/oauth/authorize',
    token_url: 'https://example.com/oauth/token',
  }, null, 2),
};

export function CredentialFormModal({
  open,
  onClose,
  website,
  credential,
}: CredentialFormModalProps) {
  const { createOrUpdateCredential } = useCredentialActions();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const [formData, setFormData] = useState<Partial<WebsiteCredentialCreate>>({
    website_id: website.id,
    username: '',
    password: '',
    auth_type: 'basic',
    additional_fields: '',
    notes: '',
  });

  useEffect(() => {
    if (credential) {
      setFormData({
        website_id: website.id,
        username: credential.username,
        password: '', // Password is never returned from API
        auth_type: credential.auth_type,
        additional_fields: credential.additional_fields || '',
        notes: credential.notes || '',
      });
    } else {
      setFormData({
        website_id: website.id,
        username: '',
        password: '',
        auth_type: 'basic',
        additional_fields: '',
        notes: '',
      });
    }
  }, [credential, website.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username || !formData.password) {
      return;
    }

    setIsLoading(true);
    try {
      await createOrUpdateCredential(formData as WebsiteCredentialCreate);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthTypeChange = (value: string) => {
    setFormData(prev => ({
      ...prev,
      auth_type: value as any,
      additional_fields: additionalFieldsTemplate[value as keyof typeof additionalFieldsTemplate] || '',
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {credential ? 'Update' : 'Add'} Credentials
            </DialogTitle>
            <DialogDescription>
              {credential 
                ? `Update authentication credentials for ${website.name}`
                : `Add authentication credentials for ${website.name}`
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="auth_type">Authentication Type</Label>
              <Select
                value={formData.auth_type}
                onValueChange={handleAuthTypeChange}
              >
                <SelectTrigger id="auth_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {authTypeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {authTypeHelp[formData.auth_type as keyof typeof authTypeHelp]}
              </p>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={formData.username}
                onChange={(e) =>
                  setFormData(prev => ({ ...prev, username: e.target.value }))
                }
                placeholder="Enter username"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) =>
                    setFormData(prev => ({ ...prev, password: e.target.value }))
                  }
                  placeholder={credential ? 'Leave blank to keep existing' : 'Enter password'}
                  required={!credential}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {formData.auth_type !== 'basic' && (
              <div className="grid gap-2">
                <Label htmlFor="additional_fields">Additional Configuration</Label>
                <Textarea
                  id="additional_fields"
                  value={formData.additional_fields}
                  onChange={(e) =>
                    setFormData(prev => ({ ...prev, additional_fields: e.target.value }))
                  }
                  placeholder="JSON configuration for authentication"
                  rows={6}
                  className="font-mono text-sm"
                />
                <p className="text-sm text-muted-foreground">
                  Configuration specific to {formData.auth_type} authentication
                </p>
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) =>
                  setFormData(prev => ({ ...prev, notes: e.target.value }))
                }
                placeholder="Any additional notes about these credentials"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : credential ? 'Update' : 'Save'} Credentials
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}