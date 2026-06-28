import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const isLoggedIn = request.cookies.get("visoora_logged_in")?.value === "true";
  const { pathname } = request.nextUrl;

  // List of paths that constitute authentication phases
  const authRoutes = ["/login", "/signup", "/forgotpass", "/resetpass"];
  const isAuthRoute = authRoutes.includes(pathname);

  // List of public marketing routes
  const publicRoutes = ["/", "/about", "/contact"];
  const isPublicRoute = publicRoutes.includes(pathname) || pathname.startsWith("/blog");

  console.log(`[Middleware] Path: ${pathname} | isLoggedIn: ${isLoggedIn} | isAuthRoute: ${isAuthRoute} | isPublicRoute: ${isPublicRoute}`);

  // Don't intercept static assets, next internals, and icons
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // Redirect to login if user is not authenticated and trying to access private dashboard routes
  if (!isLoggedIn && !isAuthRoute && !isPublicRoute) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Redirect to dashboard if user is authenticated and trying to access login/signup screens
  if (isLoggedIn && isAuthRoute) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run middleware on all routes except static resource extensions, api files
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
