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
    const response = await fetch(`${BACKEND_API_URL}/auth/token-exchange`, {
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

    if (!response.ok) {
      console.error('Token exchange failed:', response.status, response.statusText);
      return null;
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error('Token exchange error:', error);
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
      if (account?.provider === 'google' && account.access_token) {
        try {
          // Exchange Google token for backend JWT
          const backendToken = await exchangeTokenWithBackend(
            account.access_token,
            {
              sub: profile?.sub,
              email: profile?.email,
              name: profile?.name,
              picture: profile?.picture,
            }
          );

          if (backendToken) {
            token.backendAccessToken = backendToken;
            token.sub = profile?.sub;
            token.email = profile?.email;
            token.name = profile?.name;
            token.picture = profile?.picture;
            return token;
          } else {
            // Token exchange failed - return token without backend access
            console.error('Backend token exchange failed');
            return token;
          }
        } catch (error) {
          console.error('JWT callback error:', error);
          return token;
        }
      }

      // Token refresh logic - check if backend token is still valid
      if (token.backendAccessToken) {
        try {
          // Verify token with backend
          const response = await fetch(`${BACKEND_API_URL}/auth/verify-token`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token.backendAccessToken}`,
            },
          });

          if (!response.ok) {
            // Backend token is invalid - remove it
            console.log('Backend token invalid, removing from session');
            delete token.backendAccessToken;
          }
        } catch (error) {
          console.error('Token verification error:', error);
          // Remove invalid token
          delete token.backendAccessToken;
        }
      }

      return token;
    },
    
    async session({ session, token }) {
      // Only send backend JWT to client, never Google tokens
      if (token.backendAccessToken) {
        session.accessToken = token.backendAccessToken as string;
      }
      
      session.user = {
        id: token.sub as string,
        name: token.name as string,
        email: token.email as string,
        image: token.picture as string,
        sub: token.sub as string,
      };
      
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
