import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import type { NextAuthOptions } from 'next-auth';
import { JWT } from 'next-auth/jwt';

// Force dynamic rendering for NextAuth
export const dynamic = 'force-dynamic';

// Only validate environment variables at runtime, not during build
const isRuntime = typeof window === 'undefined' && !process.env.SKIP_ENV_VALIDATION;

// Validate required environment variables only at runtime
if (isRuntime && (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET)) {
  throw new Error('Missing required OAuth environment variables');
}

if (isRuntime && !process.env.NEXTAUTH_SECRET) {
  throw new Error('NEXTAUTH_SECRET environment variable is required');
}

// Backend API URL for token exchange
const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Exchange Google OAuth token for backend JWT token
 */
async function exchangeTokenWithBackend(googleToken: string, userInfo: any): Promise<string | null> {
  try {
    console.log('=== TOKEN EXCHANGE DEBUG ===');
    console.log('Backend API URL:', BACKEND_API_URL);
    console.log('User Info:', { email: userInfo.email, sub: userInfo.sub });
    console.log('Token length:', googleToken?.length);
    
    const response = await fetch(`${BACKEND_API_URL}/auth/exchange`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${googleToken}`,
      },
      body: JSON.stringify({
        google_token: googleToken,
        user_info: userInfo
      }),
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error('=== TOKEN EXCHANGE FAILED ===');
      console.error('Status:', response.status, response.statusText);
      console.error('Error:', errorText);
      console.error('============================');
      return null;
    }

    const data = await response.json();
    console.log('=== TOKEN EXCHANGE SUCCESS ===');
    console.log('Received backend token length:', data.access_token?.length);
    console.log('==============================');
    return data.access_token;
  } catch (error) {
    console.error('=== TOKEN EXCHANGE ERROR ===');
    console.error('Error:', error);
    console.error('============================');
    return null;
  }
}

/**
 * Get NextAuth configuration with runtime validation
 */
function getAuthOptions(): NextAuthOptions {
  // Only validate at runtime when actually handling requests
  const isHandlingRequest = process.env.NODE_ENV === 'production' && !process.env.SKIP_ENV_VALIDATION;
  
  if (isHandlingRequest) {
    if (!process.env.GOOGLE_CLIENT_ID || !process.env.GOOGLE_CLIENT_SECRET) {
      throw new Error('Missing required OAuth environment variables at runtime');
    }
    if (!process.env.NEXTAUTH_SECRET) {
      throw new Error('NEXTAUTH_SECRET environment variable is required at runtime');
    }
  }

  return {
    providers: [
      GoogleProvider({
        clientId: process.env.GOOGLE_CLIENT_ID || 'build-time-placeholder',
        clientSecret: process.env.GOOGLE_CLIENT_SECRET || 'build-time-placeholder',
        authorization: {
          params: {
            scope: 'openid email profile',
            // Add security parameters
            prompt: 'consent',
            access_type: 'offline',
          },
        },
      }),
    ],
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      // Initial OAuth callback - exchange Google token for backend JWT
      if (account?.provider === 'google') {
        try {
          console.log('Processing Google OAuth callback...');
          
          const userInfo = {
            sub: profile?.sub,
            email: profile?.email,
            name: profile?.name,
            picture: profile?.picture,
          };

          let backendToken = null;

          // Try ID token first (preferred for backend validation)
          if (account.id_token) {
            console.log('Trying token exchange with ID token...');
            backendToken = await exchangeTokenWithBackend(account.id_token, userInfo);
          }

          // If ID token exchange failed, try access token
          if (!backendToken && account.access_token) {
            console.log('Trying token exchange with access token...');
            backendToken = await exchangeTokenWithBackend(account.access_token, userInfo);
          }

          if (backendToken) {
            token.backendAccessToken = backendToken;
            token.sub = profile?.sub;
            token.email = profile?.email;
            token.name = profile?.name;
            token.picture = profile?.picture;
            console.log('Successfully obtained backend token for user:', profile?.email);
            return token;
          } else {
            // Token exchange failed - this will result in a session without API access
            console.error('Backend token exchange failed for user:', profile?.email);
            console.error('Available tokens:', {
              hasIdToken: !!account.id_token,
              hasAccessToken: !!account.access_token,
            });
            return token;
          }
        } catch (error) {
          console.error('JWT callback error for user:', profile?.email, error);
          return token;
        }
      }

      // For existing sessions, just return the token as-is
      // Token verification will happen at the API level when needed
      return token;
    },
    
    async session({ session, token }) {
      // Debug session creation
      console.log('=== SESSION CALLBACK DEBUG ===');
      console.log('Token has backendAccessToken:', !!token.backendAccessToken);
      console.log('User email:', token.email);
      
      // Only send backend JWT to client, never Google tokens
      if (token.backendAccessToken) {
        session.accessToken = token.backendAccessToken as string;
        console.log('✅ Session has backend token');
      } else {
        // No backend token available - user will have limited access
        console.warn('❌ Session created without backend token for user:', token.email);
        console.warn('User will not be able to access protected API endpoints');
      }
      
      session.user = {
        id: token.sub as string,
        name: token.name as string,
        email: token.email as string,
        image: token.picture as string,
        sub: token.sub as string,
      };
      
      console.log('Final session:', { 
        hasAccessToken: !!session.accessToken, 
        userEmail: session.user.email 
      });
      console.log('==============================');
      
      return session;
    },

    async signIn({ user, account, profile }) {
      // Additional security checks
      if (account?.provider === 'google') {
        // Verify email domain if needed (add your domain restrictions here)
        // if (!user.email?.endsWith('@yourdomain.com')) {
        //   return false;
        // }
        
        // Email verification check
        if (profile?.email_verified === false) {
          console.error('Email not verified for user:', user.email);
          return false;
        }
        
        return true;
      }
      
      return false;
    },
  },
  
  session: {
    strategy: 'jwt',
    maxAge: 8 * 60 * 60, // 8 hours maximum
    updateAge: 60 * 60, // Update session every hour
  },
  
  jwt: {
    maxAge: 8 * 60 * 60, // 8 hours
  },
  
  secret: process.env.NEXTAUTH_SECRET || 'build-time-placeholder',
  
  // Security configurations
  useSecureCookies: process.env.NODE_ENV === 'production',
  cookies: {
    sessionToken: {
      name: process.env.NODE_ENV === 'production' ? '__Secure-next-auth.session-token' : 'next-auth.session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 8 * 60 * 60, // 8 hours
      },
    },
    callbackUrl: {
      name: process.env.NODE_ENV === 'production' ? '__Secure-next-auth.callback-url' : 'next-auth.callback-url',
      options: {
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      },
    },
    csrfToken: {
      name: process.env.NODE_ENV === 'production' ? '__Host-next-auth.csrf-token' : 'next-auth.csrf-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      },
    },
  },
  
  // Enable debug only in development
  debug: process.env.NODE_ENV === 'development',
  
  // Additional security
  events: {
    async signIn({ user, account, profile, isNewUser }) {
      console.log(`User signed in: ${user.email} (New user: ${isNewUser})`);
    },
    async signOut({ session, token }) {
      console.log(`User signed out: ${session?.user?.email}`);
    },
    async session({ session, token }) {
      // Log session access for security monitoring
      if (process.env.NODE_ENV === 'development') {
        console.log(`Session accessed: ${session?.user?.email}`);
      }
    },
  },
};
}

const handler = NextAuth(getAuthOptions());

export { handler as GET, handler as POST };
