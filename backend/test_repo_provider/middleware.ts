// LIFE//OS — Middleware (Protected Routes)

import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLoggedIn = !!req.auth?.user;

  // Public paths that don't need auth
  const publicPaths = ['/', '/login', '/signup'];
  const isPublic = publicPaths.some((p) => pathname === p);

  // API auth routes are always public
  const isAuthApi = pathname.startsWith('/api/auth') || pathname === '/api/signup';

  if (isAuthApi || isPublic) {
    // Redirect logged-in users away from login/signup
    if (isLoggedIn && (pathname === '/login' || pathname === '/signup')) {
      return NextResponse.redirect(new URL('/dashboard', req.url));
    }
    return NextResponse.next();
  }

  // Protected: requires auth
  if (!isLoggedIn) {
    const callbackUrl = encodeURIComponent(pathname);
    return NextResponse.redirect(
      new URL(`/login?callbackUrl=${callbackUrl}`, req.url)
    );
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.svg$).*)',
  ],
};
