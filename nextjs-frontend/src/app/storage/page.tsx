'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import MainLayout from '@/components/layout/MainLayout';
import StorageManagement from '@/components/storage/StorageManagement';

// Force dynamic rendering
export const dynamic = 'force-dynamic';

export default function StoragePage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  return (
    <ProtectedRoute>
      <MainLayout>
        <StorageManagement />
      </MainLayout>
    </ProtectedRoute>
  );
}
