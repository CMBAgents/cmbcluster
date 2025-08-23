'use client';

import EnvironmentDetails from '@/components/environments/EnvironmentDetails';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function EnvironmentDetailsPage({ params }: { params: { id: string } }) {
  return (
    <ProtectedRoute>
      <EnvironmentDetails envId={params.id} />
    </ProtectedRoute>
  );
}
