import { type NextRequest } from "next/server";
import { updateSession } from "./utils/supabase/middleware";

export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  // Run middleware on all routes except static resource extensions, api files
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
