import NextAuth from "next-auth";
import { JWT } from "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user: {
      id?: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      sub?: string;
    };
  }

  interface User {
    id?: string;
    sub?: string;
  }

  interface Profile {
    sub?: string;
    email_verified?: boolean;
    picture?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendAccessToken?: string;
    sub?: string;
    email?: string;
    name?: string;
    picture?: string;
  }
}
