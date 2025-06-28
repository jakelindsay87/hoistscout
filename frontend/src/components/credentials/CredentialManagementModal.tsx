'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { PlusIcon } from '@heroicons/react/24/outline';
import { CredentialsList } from './CredentialsList';
import { CredentialFormModal } from './CredentialFormModal';
import { useCredentials } from '@/hooks/useCredentials';
import { useSites } from '@/hooks/useSites';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { WebsiteCredential } from '@/types/credentials';

interface CredentialManagementModalProps {
  websiteId: number;
  websiteName: string;
  onClose: () => void;
}

export function CredentialManagementModal({
  websiteId,
  websiteName,
  onClose,
}: CredentialManagementModalProps) {
  const { credentials, isLoading, isError } = useCredentials();
  const { data: sites } = useSites();
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingCredential, setEditingCredential] = useState<WebsiteCredential | undefined>();

  const website = sites?.find(s => s.id === websiteId);
  const websiteCredentials = credentials.filter(c => c.website_id === websiteId);

  const handleEdit = (credential: WebsiteCredential) => {
    setEditingCredential(credential);
    setShowAddForm(true);
  };

  const handleCloseForm = () => {
    setShowAddForm(false);
    setEditingCredential(undefined);
  };

  if (!website) return null;

  return (
    <>
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="sm:max-w-[800px] max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Manage Credentials</DialogTitle>
            <DialogDescription>
              Authentication credentials for {websiteName}
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : isError ? (
              <div className="text-center py-8">
                <p className="text-destructive">Failed to load credentials</p>
              </div>
            ) : (
              <>
                <div className="mb-4 flex justify-between items-center">
                  <p className="text-sm text-muted-foreground">
                    {websiteCredentials.length === 0
                      ? 'No credentials configured for this website'
                      : `${websiteCredentials.length} credential${websiteCredentials.length === 1 ? '' : 's'} configured`
                    }
                  </p>
                  {websiteCredentials.length === 0 && (
                    <Button
                      size="sm"
                      onClick={() => setShowAddForm(true)}
                    >
                      <PlusIcon className="h-4 w-4 mr-1" />
                      Add Credentials
                    </Button>
                  )}
                </div>

                <CredentialsList
                  credentials={websiteCredentials}
                  onEdit={handleEdit}
                />

                {websiteCredentials.length > 0 && (
                  <div className="mt-4 flex justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowAddForm(true)}
                    >
                      <PlusIcon className="h-4 w-4 mr-1" />
                      Update Credentials
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h4 className="text-sm font-medium mb-2">Security Information</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Credentials are encrypted using AES-256 encryption</li>
              <li>• Passwords are never exposed in API responses</li>
              <li>• Failed authentication attempts will mark credentials as invalid</li>
              <li>• Credentials are only used during automated scraping</li>
            </ul>
          </div>
        </DialogContent>
      </Dialog>

      {showAddForm && (
        <CredentialFormModal
          open={showAddForm}
          onClose={handleCloseForm}
          website={website}
          credential={editingCredential}
        />
      )}
    </>
  );
}