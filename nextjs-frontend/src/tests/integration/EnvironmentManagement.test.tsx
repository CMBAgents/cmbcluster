import { describe, test, expect, jest, beforeEach, afterEach } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SessionProvider } from 'next-auth/react';
import { apiClient } from '@/lib/api-client';
import EnvironmentManagement from '@/components/environments/EnvironmentManagement';
import type { Environment, StorageItem, ApiResponse } from '@/types';

// Mock API client
vi.mock('@/lib/api-client');

// Mock next-auth
vi.mock('next-auth/react', () => ({
  useSession: () => ({
    data: {
      user: {
        sub: 'test-user-123',
        name: 'Test User',
        email: 'test@example.com'
      },
      accessToken: 'mock-access-token'
    },
    status: 'authenticated'
  }),
  SessionProvider: ({ children }: any) => children
}));

// Mock notification
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    notification: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
    }
  };
});

describe('Environment Management Integration Tests', () => {
  let queryClient: QueryClient;
  const mockApiClient = apiClient as any;

  // Test data matching backend models exactly
  const mockEnvironments: Environment[] = [
    {
      id: 'env-running-123',
      env_id: 'env-running-123',
      status: 'running',
      created_at: '2024-08-23T10:00:00Z',
      updated_at: '2024-08-23T10:30:00Z',
      last_activity: '2024-08-23T11:00:00Z',
      url: 'https://env-running-123.cmbcluster.dev',
      resource_config: {
        cpu_limit: 2.0,
        memory_limit: '4Gi',
        storage_size: '50Gi'
      }
    },
    {
      id: 'env-pending-456',
      env_id: 'env-pending-456', 
      status: 'pending',
      created_at: '2024-08-23T11:00:00Z',
      resource_config: {
        cpu_limit: 1.0,
        memory_limit: '2Gi',
        storage_size: '25Gi'
      }
    },
    {
      id: 'env-failed-789',
      env_id: 'env-failed-789',
      status: 'failed',
      created_at: '2024-08-23T09:00:00Z',
      updated_at: '2024-08-23T09:05:00Z',
      resource_config: {
        cpu_limit: 4.0,
        memory_limit: '8Gi', 
        storage_size: '100Gi'
      }
    }
  ];

  const mockStorageOptions: StorageItem[] = [
    {
      id: 'storage-123',
      display_name: 'Research Data Workspace',
      bucket_name: 'cmbcluster-storage-123',
      storage_class: 'standard',
      status: 'active',
      created_at: '2024-08-20T10:00:00Z',
      size_bytes: 1024000000,
      object_count: 150,
      region: 'us-central1'
    },
    {
      id: 'storage-456',
      display_name: 'Archive Workspace',
      bucket_name: 'cmbcluster-storage-456', 
      storage_class: 'coldline',
      status: 'active',
      created_at: '2024-08-15T10:00:00Z',
      size_bytes: 5120000000,
      object_count: 75,
      region: 'us-central1'
    }
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });

    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <SessionProvider session={null}>
          {component}
        </SessionProvider>
      </QueryClientProvider>
    );
  };

  describe('Environment List Display', () => {
    test('should display environments correctly when API returns data', async () => {
      // Mock successful API response
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success',
        environments: mockEnvironments
      });

      renderWithProviders(<EnvironmentManagement />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Research Computing Environments')).toBeInTheDocument();
      });

      // Check that environments are displayed
      expect(screen.getByText('env-running-123')).toBeInTheDocument();
      expect(screen.getByText('env-pending-456')).toBeInTheDocument();
      expect(screen.getByText('env-failed-789')).toBeInTheDocument();

      // Check status badges
      expect(screen.getByText('Running')).toBeInTheDocument();
      expect(screen.getByText('Starting')).toBeInTheDocument(); // Pending shows as "Starting"
      expect(screen.getByText('Failed')).toBeInTheDocument();

      // Check resource configurations
      expect(screen.getByText('2 cores')).toBeInTheDocument();
      expect(screen.getByText('4Gi')).toBeInTheDocument();
      expect(screen.getByText('50Gi')).toBeInTheDocument();
    });

    test('should display empty state when no environments exist', async () => {
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success',
        environments: []
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('No Environments Found')).toBeInTheDocument();
        expect(screen.getByText("You don't have any environments yet. Launch your first environment to get started!")).toBeInTheDocument();
      });
    });

    test('should handle API errors gracefully', async () => {
      mockApiClient.listEnvironments.mockRejectedValue(new Error('Network error'));

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Environments')).toBeInTheDocument();
        expect(screen.getByText('Failed to load environments. Please try again.')).toBeInTheDocument();
      });
    });
  });

  describe('Environment Actions', () => {
    beforeEach(() => {
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success', 
        environments: mockEnvironments
      });
    });

    test('should successfully restart environment', async () => {
      mockApiClient.restartEnvironment.mockResolvedValue({
        status: 'success',
        message: 'Environment restarted successfully'
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Find and click restart button
      const restartButtons = screen.getAllByTestId(/restart-button/);
      fireEvent.click(restartButtons[0]);

      // Confirm in modal
      const confirmButton = await screen.findByText('Restart');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockApiClient.restartEnvironment).toHaveBeenCalledWith('env-running-123');
      });
    });

    test('should successfully stop environment', async () => {
      mockApiClient.stopEnvironment.mockResolvedValue({
        status: 'success',
        message: 'Environment stopped successfully'
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Find and click stop button
      const stopButtons = screen.getAllByTestId(/stop-button/);
      fireEvent.click(stopButtons[0]);

      // Confirm in modal
      const confirmButton = await screen.findByText('Stop');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockApiClient.stopEnvironment).toHaveBeenCalledWith('env-running-123');
      });
    });

    test('should successfully delete environment', async () => {
      mockApiClient.deleteEnvironment.mockResolvedValue({
        status: 'deleted',
        message: 'Environment deleted successfully'
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Find and click delete button  
      const deleteButtons = screen.getAllByTestId(/delete-button/);
      fireEvent.click(deleteButtons[0]);

      // Confirm in modal
      const confirmButton = await screen.findByText('Delete');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockApiClient.deleteEnvironment).toHaveBeenCalledWith('env-running-123');
      });
    });
  });

  describe('Environment Launch', () => {
    beforeEach(() => {
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success',
        environments: []
      });
      mockApiClient.listUserStorages.mockResolvedValue({
        status: 'success',
        storages: mockStorageOptions
      });
    });

    test('should open launch modal and display preset options', async () => {
      renderWithProviders(<EnvironmentManagement />);

      // Click launch button
      const launchButton = await screen.findByText('Launch Environment');
      fireEvent.click(launchButton);

      // Check modal opened
      await waitFor(() => {
        expect(screen.getByText('Launch New Environment')).toBeInTheDocument();
      });

      // Check preset options
      expect(screen.getByText('Light Analysis')).toBeInTheDocument();
      expect(screen.getByText('Standard Research')).toBeInTheDocument(); 
      expect(screen.getByText('Heavy Computation')).toBeInTheDocument();

      // Check storage options
      expect(screen.getByText('Use Existing Workspace (2 available)')).toBeInTheDocument();
      expect(screen.getByText('Create New Workspace')).toBeInTheDocument();
    });

    test('should successfully launch environment with existing storage', async () => {
      mockApiClient.createEnvironment.mockResolvedValue({
        status: 'created',
        message: 'Environment created successfully',
        environment: {
          ...mockEnvironments[0],
          id: 'new-env-123',
          status: 'pending'
        }
      });

      renderWithProviders(<EnvironmentManagement />);

      // Open launch modal
      const launchButton = await screen.findByText('Launch Environment');
      fireEvent.click(launchButton);

      await waitFor(() => {
        expect(screen.getByText('Launch New Environment')).toBeInTheDocument();
      });

      // Select existing storage
      const existingStorageRadio = screen.getByLabelText(/Use Existing Workspace/);
      fireEvent.click(existingStorageRadio);

      // Submit form
      const submitButton = screen.getByText('Launch Environment');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.createEnvironment).toHaveBeenCalledWith({
          cpu_limit: 2.0,
          memory_limit: '4Gi',
          storage_size: '50Gi',
          storage_id: 'storage-123',
          create_new_storage: false
        });
      });
    });

    test('should launch environment with new storage creation', async () => {
      mockApiClient.createEnvironment.mockResolvedValue({
        status: 'created',
        message: 'Environment created successfully'
      });

      renderWithProviders(<EnvironmentManagement />);

      // Open launch modal
      const launchButton = await screen.findByText('Launch Environment');
      fireEvent.click(launchButton);

      await waitFor(() => {
        expect(screen.getByText('Launch New Environment')).toBeInTheDocument();
      });

      // Select create new storage
      const newStorageRadio = screen.getByLabelText('Create New Workspace');
      fireEvent.click(newStorageRadio);

      // Submit form
      const submitButton = screen.getByText('Launch Environment');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiClient.createEnvironment).toHaveBeenCalledWith({
          cpu_limit: 2.0,
          memory_limit: '4Gi', 
          storage_size: '50Gi',
          storage_id: null,
          create_new_storage: true,
          storage_class: 'standard'
        });
      });
    });

    test('should handle launch errors gracefully', async () => {
      mockApiClient.createEnvironment.mockRejectedValue({
        message: 'Insufficient resources'
      });

      renderWithProviders(<EnvironmentManagement />);

      // Open launch modal and submit
      const launchButton = await screen.findByText('Launch Environment');
      fireEvent.click(launchButton);

      await waitFor(() => {
        expect(screen.getByText('Launch New Environment')).toBeInTheDocument();
      });

      const existingStorageRadio = screen.getByLabelText(/Use Existing Workspace/);
      fireEvent.click(existingStorageRadio);

      const submitButton = screen.getByText('Launch Environment');
      fireEvent.click(submitButton);

      // Should show error notification
      await waitFor(() => {
        expect(screen.getByText('Launch failed!')).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filtering', () => {
    beforeEach(() => {
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success',
        environments: mockEnvironments
      });
    });

    test('should filter environments by search text', async () => {
      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Search for specific environment
      const searchInput = screen.getByPlaceholderText('Search environments...');
      fireEvent.change(searchInput, { target: { value: 'running' } });

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
        expect(screen.queryByText('env-pending-456')).not.toBeInTheDocument();
        expect(screen.queryByText('env-failed-789')).not.toBeInTheDocument();
      });
    });

    test('should filter environments by status', async () => {
      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Filter by status
      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.change(statusFilter, { target: { value: 'running' } });

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
        expect(screen.queryByText('env-pending-456')).not.toBeInTheDocument();
        expect(screen.queryByText('env-failed-789')).not.toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    test('should refresh data automatically', async () => {
      // Initial data
      mockApiClient.listEnvironments.mockResolvedValueOnce({
        status: 'success',
        environments: [mockEnvironments[0]]
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        expect(screen.getByText('env-running-123')).toBeInTheDocument();
      });

      // Updated data after interval
      mockApiClient.listEnvironments.mockResolvedValueOnce({
        status: 'success',
        environments: mockEnvironments
      });

      // Fast-forward time to trigger refetch
      vi.advanceTimersByTime(10000);

      await waitFor(() => {
        expect(mockApiClient.listEnvironments).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Statistics Display', () => {
    test('should calculate and display correct statistics', async () => {
      mockApiClient.listEnvironments.mockResolvedValue({
        status: 'success',
        environments: mockEnvironments
      });

      renderWithProviders(<EnvironmentManagement />);

      await waitFor(() => {
        // Total environments: 3
        expect(screen.getByText('3')).toBeInTheDocument();
        
        // Running: 1 
        expect(screen.getByText('1')).toBeInTheDocument();
        
        // Pending: 1
        expect(screen.getByText('1')).toBeInTheDocument();
      });
    });
  });
});

describe('Storage Integration Tests', () => {
  const mockApiClient = apiClient as any;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('should load and display storage options', async () => {
    mockApiClient.listUserStorages.mockResolvedValue({
      status: 'success',
      storages: mockStorageOptions
    });

    // Test storage selector component
    const { getByText } = render(
      <StorageSelector
        storageOptions={mockStorageOptions}
        selectedStorage={null}
        onStorageChange={vi.fn()}
      />
    );

    expect(getByText('Research Data Workspace (standard)')).toBeInTheDocument();
    expect(getByText('Archive Workspace (coldline)')).toBeInTheDocument();
  });
});

// Mock component for testing
const StorageSelector = ({ storageOptions, selectedStorage, onStorageChange }: any) => (
  <div>
    {storageOptions.map((storage: StorageItem) => (
      <div key={storage.id}>
        {storage.display_name} ({storage.storage_class})
      </div>
    ))}
  </div>
);
