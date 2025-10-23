import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import type { NextAuthOptions } from 'next-auth';
import { JWT } from 'next-auth/jwt';
import jwt from 'jsonwebtoken';

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

   
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
   
      return null;
    }

    const data = await response.json();

    return data.access_token;
  } catch (error) {

    return null;
  }
}

/**
 * Decode JWT token to extract user role information
 */
function decodeBackendToken(token: string): { role?: string; [key: string]: any } | null {
  try {
    // Decode without verification since we trust our backend
    const decoded = jwt.decode(token) as { role?: string; [key: string]: any } | null;
    return decoded;
  } catch (error) {
    console.error('Failed to decode backend token:', error);
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
         
          
          const userInfo = {
            sub: profile?.sub,
            email: profile?.email,
            name: profile?.name,
            picture: profile?.picture,
          };

          let backendToken = null;

          // Try ID token first (preferred for backend validation)
          if (account.id_token) {
            backendToken = await exchangeTokenWithBackend(account.id_token, userInfo);
          }

          // If ID token exchange failed, try access token
          if (!backendToken && account.access_token) {
            backendToken = await exchangeTokenWithBackend(account.access_token, userInfo);
          }

          if (backendToken) {
            token.backendAccessToken = backendToken;
            token.sub = profile?.sub;
            token.email = profile?.email;
            token.name = profile?.name;
            token.picture = profile?.picture;
            return token;
          } else {
            // Token exchange failed - this will result in a session without API access
        
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
    
      
      // Only send backend JWT to client, never Google tokens
      if (token.backendAccessToken) {
        session.accessToken = token.backendAccessToken as string;
        
        // Decode backend token to extract role
        const decodedToken = decodeBackendToken(token.backendAccessToken as string);
        if (decodedToken && decodedToken.role) {
          session.user.role = decodedToken.role as 'user' | 'admin' | 'researcher';
        } else {
          session.user.role = 'user'; // Default role
        }
      } else {
        // No backend token available - user will have limited access
    
        session.user.role = 'user'; // Default role
      }
      
      session.user = {
        id: token.sub as string,
        name: token.name as string,
        email: token.email as string,
        image: token.picture as string,
        sub: token.sub as string,
        role: session.user.role, // Add the extracted role
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
    },
    async signOut({ session, token }) {
    },
    async session({ session, token }) {
      // Log session access for security monitoring
      if (process.env.NODE_ENV === 'development') {
      }
    },
  },
};
}

const handler = NextAuth(getAuthOptions());

export { handler as GET, handler as POST };
