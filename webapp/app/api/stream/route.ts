// webapp/app/api/stream/route.ts
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge'; // Use edge runtime for streaming

export async function GET(req: NextRequest) {
  const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';

  // In a real app, you'd get the token from the user's session or a secure cookie
  // For this example, we'll use the dev token.
  const token = 'dev-token';

  try {
    const response = await fetch(`${backendUrl}/stream`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
      },
      // Important: prevent Next.js from caching the response
      cache: 'no-store',
    });

    if (!response.body) {
      return new NextResponse('No response body from backend', { status: 500 });
    }

    // Create a new ReadableStream from the backend response
    const stream = new ReadableStream({
      start(controller) {
        const reader = response.body!.getReader();
        function push() {
          reader.read().then(({ done, value }) => {
            if (done) {
              controller.close();
              return;
            }
            controller.enqueue(value);
            push();
          }).catch(err => {
            console.error('Error reading from backend stream:', err);
            controller.error(err);
          });
        }
        push();
      }
    });

    // Return the stream as the response
    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Error fetching from backend:', error);
    return new NextResponse('Failed to connect to backend stream', { status: 500 });
  }
}
