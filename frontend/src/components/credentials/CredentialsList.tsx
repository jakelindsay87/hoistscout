'use client';

import { useState } from 'react';
import { WebsiteCredential } from '@/types/credentials';
import { useCredentialActions } from '@/hooks/useCredentials';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { 
  KeyIcon, 
  ShieldCheckIcon, 
  ShieldExclamationIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from '@/lib/utils';

interface CredentialsListProps {
  credentials: WebsiteCredential[];
  onEdit: (credential: WebsiteCredential) => void;
}

export function CredentialsList({ credentials, onEdit }: CredentialsListProps) {
  const { deleteCredential, validateCredential, markInvalid } = useCredentialActions();
  const [deleteTarget, setDeleteTarget] = useState<WebsiteCredential | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [validatingId, setValidatingId] = useState<number | null>(null);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    
    setIsDeleting(true);
    try {
      await deleteCredential(deleteTarget.website_id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleValidate = async (credential: WebsiteCredential) => {
    setValidatingId(credential.website_id);
    try {
      await validateCredential(credential.website_id);
    } finally {
      setValidatingId(null);
    }
  };

  const authTypeBadgeVariant = (type: string) => {
    switch (type) {
      case 'basic':
        return 'default';
      case 'form':
        return 'secondary';
      case 'oauth':
        return 'outline';
      default:
        return 'default';
    }
  };

  if (credentials.length === 0) {
    return (
      <div className="text-center py-8">
        <KeyIcon className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          No credentials configured
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Website</TableHead>
              <TableHead>Username</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Used</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {credentials.map((credential) => (
              <TableRow key={credential.id}>
                <TableCell className="font-medium">
                  {credential.website?.name || `Website ${credential.website_id}`}
                </TableCell>
                <TableCell>{credential.username}</TableCell>
                <TableCell>
                  <Badge variant={authTypeBadgeVariant(credential.auth_type)}>
                    {credential.auth_type}
                  </Badge>
                </TableCell>
                <TableCell>
                  {credential.is_valid ? (
                    <div className="flex items-center gap-1 text-green-600">
                      <CheckCircleIcon className="h-4 w-4" />
                      <span className="text-sm">Valid</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-red-600">
                      <XCircleIcon className="h-4 w-4" />
                      <span className="text-sm">Invalid</span>
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  {credential.last_used_at
                    ? formatDistanceToNow(new Date(credential.last_used_at))
                    : 'Never'
                  }
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onEdit(credential)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleValidate(credential)}
                      disabled={validatingId === credential.website_id}
                    >
                      {validatingId === credential.website_id ? (
                        'Validating...'
                      ) : (
                        <>
                          <ShieldCheckIcon className="h-4 w-4 mr-1" />
                          Test
                        </>
                      )}
                    </Button>
                    {credential.is_valid && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => markInvalid(credential.website_id)}
                      >
                        <ShieldExclamationIcon className="h-4 w-4 mr-1" />
                        Mark Invalid
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setDeleteTarget(credential)}
                      className="text-destructive hover:text-destructive"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Credentials</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the credentials for{' '}
              <strong>{deleteTarget?.website?.name || 'this website'}</strong>?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}