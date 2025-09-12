import { getApiUrlAsync } from '@/lib/env-validator';

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
  
  // If it's a relative URL starting with /data/, convert to API URL
  if (iconUrl.startsWith('/data/')) {
    const apiBaseUrl = await getApiUrlAsync();
    return `${apiBaseUrl}${iconUrl}`;
  }
  
  // For other relative URLs, assume they're meant for the API
  const apiBaseUrl = await getApiUrlAsync();
  const cleanIconUrl = iconUrl.startsWith('/') ? iconUrl : `/${iconUrl}`;
  return `${apiBaseUrl}${cleanIconUrl}`;
}

/**
 * Synchronous version that constructs the URL directly (for use in components)
 * This uses the known API domain pattern for production
 */
export function getImageUrlSync(iconUrl: string | undefined | null): string {
  if (!iconUrl) {
    return '';
  }
  
  // If it's already an absolute URL, return as-is
  if (iconUrl.startsWith('http://') || iconUrl.startsWith('https://')) {
    return iconUrl;
  }
  
  // If it's a relative URL starting with /data/, convert to API URL
  if (iconUrl.startsWith('/data/')) {
    // Use the known API domain pattern
    return `https://api.35.188.79.156.nip.io${iconUrl}`;
  }
  
  // For other relative URLs, assume they're meant for the API
  const cleanIconUrl = iconUrl.startsWith('/') ? iconUrl : `/${iconUrl}`;
  return `https://api.35.188.79.156.nip.io${cleanIconUrl}`;
}