import { getApiUrlAsync } from '@/lib/env-validator';

/**
 * Get API base URL for client-side usage
 * This fetches the runtime config on first call and caches it
 */
let cachedApiUrl: string | null = null;

async function getClientApiUrl(): Promise<string> {
  if (cachedApiUrl) {
    return cachedApiUrl;
  }

  // Fetch runtime config from the API route
  try {
    const response = await fetch('/api/config');
    if (response.ok) {
      const config = await response.json();
      const apiUrl = config.apiUrl || '';
      cachedApiUrl = apiUrl;
      return apiUrl;
    }
  } catch (error) {
    console.warn('Failed to fetch API config:', error);
  }

  // Fallback: return empty string and let it fail gracefully
  cachedApiUrl = '';
  return '';
}

/**
 * Convert a relative image URL (from icon_url field) to an absolute API URL
 * @param iconUrl - The relative path from the database (e.g., "/data/uploads/applications/image.png")
 * @returns Promise<string> - The absolute URL to the API domain
 */
export async function getImageUrl(iconUrl: string | undefined | null): Promise<string> {
  if (!iconUrl) {
    return '';
  }

  // If it's already an absolute URL, return as-is
  if (iconUrl.startsWith('http://') || iconUrl.startsWith('https://')) {
    return iconUrl;
  }

  // Get API base URL
  const apiBaseUrl = await getApiUrlAsync();

  // If it's a relative URL starting with /data/, convert to API URL
  if (iconUrl.startsWith('/data/')) {
    return `${apiBaseUrl}${iconUrl}`;
  }

  // For other relative URLs, assume they're meant for the API
  const cleanIconUrl = iconUrl.startsWith('/') ? iconUrl : `/${iconUrl}`;
  return `${apiBaseUrl}${cleanIconUrl}`;
}

/**
 * Synchronous version that constructs the URL directly (for use in components)
 * This fetches the API URL from the runtime config endpoint on first render
 */
export function getImageUrlSync(iconUrl: string | undefined | null): string {
  if (!iconUrl) {
    return '';
  }

  // If it's already an absolute URL, return as-is
  if (iconUrl.startsWith('http://') || iconUrl.startsWith('https://')) {
    return iconUrl;
  }

  // Get API base URL from window object if available (set by config route)
  let apiBaseUrl = '';
  if (typeof window !== 'undefined') {
    // Check if we have a cached config in window
    const windowWithConfig = window as any;
    if (windowWithConfig.__RUNTIME_CONFIG__?.apiUrl) {
      apiBaseUrl = windowWithConfig.__RUNTIME_CONFIG__.apiUrl;
    }
  }

  // If not available, trigger async fetch for next time
  if (!apiBaseUrl && !cachedApiUrl) {
    getClientApiUrl(); // Fire and forget - will cache for next render
  }

  // Use cached value if available
  apiBaseUrl = apiBaseUrl || cachedApiUrl || '';

  // If it's a relative URL starting with /data/, convert to API URL
  if (iconUrl.startsWith('/data/')) {
    return `${apiBaseUrl}${iconUrl}`;
  }

  // For other relative URLs, assume they're meant for the API
  const cleanIconUrl = iconUrl.startsWith('/') ? iconUrl : `/${iconUrl}`;
  return `${apiBaseUrl}${cleanIconUrl}`;
}