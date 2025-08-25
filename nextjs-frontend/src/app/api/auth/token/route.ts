import { getToken } from 'next-auth/jwt';
import { NextRequest, NextResponse } from 'next/server';

// Force dynamic rendering for this API route
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const secret = process.env.NEXTAUTH_SECRET || 'dummy-secret-for-build';
    
    // Get the JWT token from the request
    const token = await getToken({
      req: request,
      secret,
    });

    if (!token) {
      return NextResponse.json(
        { error: 'No valid session found' },
        { status: 401 }
      );
    }

    // Return the raw JWT token for backend exchange
    return NextResponse.json({
      token: token,
      // Don't expose the raw JWT string for security
      hasToken: true,
    });
  } catch (error) {
    console.error('Error getting JWT token:', error);
    return NextResponse.json(
      { error: 'Failed to get authentication token' },
      { status: 500 }
    );
  }
}