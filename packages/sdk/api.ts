import createClient from 'openapi-fetch';
import { paths } from './index';

export type ApiClient = ReturnType<typeof createClient<paths>>;

export default function createApiClient({
  baseUrl,
  token,
}: {
  baseUrl: string;
  token?: string;
}) {
  return createClient<paths>({
    baseUrl,
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
    },
  });
}
