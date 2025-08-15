export { default } from "next-auth/middleware";

export const config = {
  // The following routes are matching all routes except for the ones starting with /api/auth
  matcher: ["/((?!api/auth).*)"],
};
