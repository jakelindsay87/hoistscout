import useSWR, { mutate } from 'swr';
import { apiFetch } from '@/lib/apiFetch';
import { WebsiteCredential, WebsiteCredentialCreate, CredentialValidationResult } from '@/types/credentials';
import { useToast } from './use-toast';

const CREDENTIALS_KEY = '/api/credentials';

export function useCredentials() {
  const { data, error, isLoading } = useSWR<WebsiteCredential[]>(
    CREDENTIALS_KEY,
    () => apiFetch('/api/credentials')
  );

  return {
    credentials: data || [],
    isLoading,
    isError: !!error,
    error,
  };
}

export function useWebsiteCredential(websiteId: number | undefined) {
  const { data, error, isLoading } = useSWR<WebsiteCredential>(
    websiteId ? `/api/credentials/${websiteId}` : null,
    () => websiteId ? apiFetch(`/api/credentials/${websiteId}`) : null
  );

  return {
    credential: data,
    isLoading,
    isError: !!error,
    error,
  };
}

export function useCredentialActions() {
  const { toast } = useToast();

  const createOrUpdateCredential = async (credential: WebsiteCredentialCreate) => {
    try {
      const result = await apiFetch('/api/credentials/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credential),
      });
      
      // Refresh credentials list
      await mutate(CREDENTIALS_KEY);
      // Refresh specific credential
      await mutate(`/api/credentials/${credential.website_id}`);
      
      toast({
        title: 'Success',
        description: 'Credentials saved successfully',
      });
      
      return result;
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save credentials',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const deleteCredential = async (websiteId: number) => {
    try {
      await apiFetch(`/api/credentials/${websiteId}`, {
        method: 'DELETE',
      });
      
      // Refresh credentials list
      await mutate(CREDENTIALS_KEY);
      // Clear specific credential cache
      await mutate(`/api/credentials/${websiteId}`, undefined);
      
      toast({
        title: 'Success',
        description: 'Credentials deleted successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete credentials',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const validateCredential = async (websiteId: number) => {
    try {
      const result = await apiFetch<CredentialValidationResult>(
        `/api/credentials/${websiteId}/validate`,
        {
          method: 'POST',
        }
      );
      
      if (result.valid) {
        toast({
          title: 'Valid',
          description: 'Credentials are valid and can be decrypted',
        });
      } else {
        toast({
          title: 'Invalid',
          description: result.message || 'Credentials validation failed',
          variant: 'destructive',
        });
      }
      
      return result;
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to validate credentials',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const markInvalid = async (websiteId: number) => {
    try {
      await apiFetch(`/api/credentials/${websiteId}/mark-invalid`, {
        method: 'POST',
      });
      
      // Refresh credentials
      await mutate(CREDENTIALS_KEY);
      await mutate(`/api/credentials/${websiteId}`);
      
      toast({
        title: 'Updated',
        description: 'Credentials marked as invalid',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update credentials',
        variant: 'destructive',
      });
      throw error;
    }
  };

  return {
    createOrUpdateCredential,
    deleteCredential,
    validateCredential,
    markInvalid,
  };
}