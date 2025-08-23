'use client';

import EnvironmentManagement from '@/components/environments/EnvironmentManagement';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

export default function EnvironmentsPage() {
  return (
    <ProtectedRoute>
      <EnvironmentManagement />
    </ProtectedRoute>
  );
}
