import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import CognitoProvider from 'next-auth/providers/cognito';
import type { NextAuthOptions } from 'next-auth';
import { JWT } from 'next-auth/jwt';
import jwt from 'jsonwebtoken';

// Force dynamic rendering for NextAuth
export const dynamic = 'force-dynamic';

// Only validate environment variables at runtime, not during build
const isRuntime = typeof window === 'undefined' && !process.env.SKIP_ENV_VALIDATION;

// Validate required environment variables only at runtime
// Note: At least one auth provider (Google OR Cognito) must be configured
if (isRuntime) {
  const hasGoogle = process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET;
  const hasCognito = process.env.COGNITO_CLIENT_ID && process.env.COGNITO_CLIENT_SECRET && process.env.COGNITO_ISSUER;

  if (!hasGoogle && !hasCognito) {
    throw new Error('At least one OAuth provider must be configured (Google or Cognito)');
  }

  if (!process.env.NEXTAUTH_SECRET) {
    throw new Error('NEXTAUTH_SECRET environment variable is required');
  }
}

// Backend API URL for token exchange
const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Exchange OAuth token (Google or Cognito) for backend JWT token
 */
async function exchangeTokenWithBackend(oauthToken: string, userInfo: any, provider: string): Promise<string | null> {
  try {
    const response = await fetch(`${BACKEND_API_URL}/auth/exchange`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${oauthToken}`,
      },
      body: JSON.stringify({
        oauth_token: oauthToken,
        google_token: oauthToken, // For backward compatibility
        user_info: userInfo,
        provider: provider
      }),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`Token exchange failed for ${provider}:`, errorText);
      return null;
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error(`Token exchange error for ${provider}:`, error);
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
  // Build providers array dynamically based on available credentials
  const providers: any[] = [];

  // Add Google provider if configured
  if (process.env.GOOGLE_CLIENT_ID &&
      process.env.GOOGLE_CLIENT_SECRET &&
      process.env.GOOGLE_CLIENT_ID !== 'build-time-placeholder') {
    console.log('Adding Google OAuth provider');
    providers.push(
      GoogleProvider({
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        authorization: {
          params: {
            scope: 'openid email profile',
            prompt: 'consent',
            access_type: 'offline',
          },
        },
      })
    );
  }

  // Add Cognito provider if configured
  if (process.env.COGNITO_CLIENT_ID &&
      process.env.COGNITO_CLIENT_SECRET &&
      process.env.COGNITO_ISSUER) {
    console.log('Adding AWS Cognito provider');
    providers.push(
      CognitoProvider({
        clientId: process.env.COGNITO_CLIENT_ID,
        clientSecret: process.env.COGNITO_CLIENT_SECRET,
        issuer: process.env.COGNITO_ISSUER,
      })
    );
  }

  // Validate at least one provider is configured
  if (providers.length === 0) {
    throw new Error('No authentication providers configured');
  }

  return {
    providers,
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      // Initial OAuth callback - exchange OAuth token (Google or Cognito) for backend JWT
      if (account?.provider) {
        try {
          const providerName = account.provider; // "google" or "cognito"
          console.log(`Processing OAuth callback for provider: ${providerName}`);

          const userInfo = {
            sub: profile?.sub,
            email: profile?.email,
            name: profile?.name,
            picture: profile?.picture,
          };

          let backendToken = null;

          // Try ID token first (preferred for backend validation)
          if (account.id_token) {
            backendToken = await exchangeTokenWithBackend(account.id_token, userInfo, providerName);
          }

          // If ID token exchange failed, try access token
          if (!backendToken && account.access_token) {
            backendToken = await exchangeTokenWithBackend(account.access_token, userInfo, providerName);
          }

          if (backendToken) {
            token.backendAccessToken = backendToken;
            token.sub = profile?.sub;
            token.email = profile?.email;
            token.name = profile?.name;
            token.picture = profile?.picture;
            token.provider = providerName;
            console.log(`Token exchange successful for ${providerName}`);
            return token;
          } else {
            // Token exchange failed - this will result in a session without API access
            console.error(`Token exchange failed for ${providerName}`);
            return token;
          }
        } catch (error) {
          console.error('JWT callback error:', error);
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
      // Additional security checks for all OAuth providers
      if (account?.provider === 'google' || account?.provider === 'cognito') {
        // Verify email domain if needed (add your domain restrictions here)
        // if (!user.email?.endsWith('@yourdomain.com')) {
        //   return false;
        // }

        // Email verification check
        // For Cognito, email_verified might be a string "true"/"false"
        const emailVerified = profile?.email_verified;
        if (emailVerified === false || emailVerified === 'false') {
          console.error(`Email not verified for user: ${user.email} (provider: ${account.provider})`);
          return false;
        }

        console.log(`Sign-in approved for ${account.provider}: ${user.email}`);
        return true;
      }

      // Reject unknown providers
      console.error(`Unknown provider: ${account?.provider}`);
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
