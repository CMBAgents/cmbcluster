import { NextRequest, NextResponse } from 'next/server';
import { getToken } from 'next-auth/jwt';

export async function POST(
  req: NextRequest,
  { params }: { params: { storageId: string } }
) {
  const { storageId } = params;

  if (!storageId) {
    return NextResponse.json(
      { error: 'Storage ID is required.' },
      { status: 400 }
    );
  }

  // Secure the endpoint by checking for a valid session
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  if (!token || !token.accessToken) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const backendApiUrl = `${process.env.API_URL}/storage/${storageId}/upload`;

  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const path = formData.get('path') as string | '';

    if (!file) {
      return NextResponse.json({ error: 'No file provided.' }, { status: 400 });
    }

    // We need to create a new FormData to stream to the backend
    const backendFormData = new FormData();
    backendFormData.append('file', file, file.name);
    backendFormData.append('path', path);

    const response = await fetch(backendApiUrl, {
      method: 'POST',
      headers: {
        // Pass the user's access token to the backend API
        Authorization: `Bearer ${token.accessToken}`,
      },
      body: backendFormData,
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('Backend API Error:', data);
      return NextResponse.json(
        { error: data.detail || 'Failed to upload file.' },
        { status: response.status }
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error('Error handling file upload:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred.' },
      { status: 500 }
    );
  }
}
