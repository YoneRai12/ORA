import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
    const url = request.nextUrl;
    const hostname = request.headers.get("host") || "";

    // Define domain mappings (In production, this could come from a DB or Config)
    // Format: "domain": "guildId"
    const domainMap: Record<string, string> = {
        "dev.ora.bot": "1307177622366851135", // Example mapping
        // "another-server.ora.bot": "another_guild_id",
    };

    // Check if current hostname is in the map
    let matchedGuildId: string | undefined;

    // Handle local development where host might include port
    const cleanHostname = hostname.split(":")[0];

    if (domainMap[hostname] || domainMap[cleanHostname]) {
        matchedGuildId = domainMap[hostname] || domainMap[cleanHostname];
    } else if (hostname.includes("trycloudflare.com")) {
        // Wildcard for testing with random Cloudflare Tunnels -> Map to Dev Server
        matchedGuildId = "1307177622366851135";
    }

    // If a match is found, rewrite the URL
    if (matchedGuildId) {
        // Only rewrite if we are at the root or not already in the dashboard path?
        // Actually, we want to map the root of the subdomain to the dashboard of that guild.
        // e.g. dev.ora.bot/ -> /dashboard/123
        // e.g. dev.ora.bot/some/path -> /dashboard/123 (if we want to lock it)

        // For now, let's just rewrite the root path to the dashboard
        // For now, let's just rewrite the root path to the dashboard
        // if (url.pathname === "/") {
        //    return NextResponse.rewrite(new URL(`/dashboard/${matchedGuildId}`, request.url));
        // }
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        "/((?!api|_next/static|_next/image|favicon.ico).*)",
    ],
};
