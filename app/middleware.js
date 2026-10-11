// Zugangsschutz pro Person (Vercel Routing Middleware).
// - Ohne gültiges Login-Cookie → Login-Seite.
// - /me/… wird auf den eigenen Ordner /u/<name>/… umgeleitet.
// - Direkter Zugriff auf /u/… ist gesperrt, damit niemand fremde Reisen öffnen kann.
// Frei ohne Login: Login-Seite, Login-API, Manifest, Icons (iOS braucht sie für „Zum Home-Bildschirm“).
import { next, rewrite } from "@vercel/functions";

export const config = {
  matcher: ["/((?!login\\.html|api/login|manifest\\.webmanifest|icons/).*)"],
};

export const USERS = { toby: "PW_TOBY", laura: "PW_LAURA" };

export async function tokenFor(user, password) {
  const data = new TextEncoder().encode(user + ":" + password + ":tklst-v2");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function currentUser(request) {
  const cookie = request.headers.get("cookie") || "";
  const m = cookie.match(/(?:^|;\s*)tklst=(toby|laura)\.([a-f0-9]{64})/);
  if (!m) return null;
  const password = process.env[USERS[m[1]]];
  if (!password) return null;
  return m[2] === (await tokenFor(m[1], password)) ? m[1] : null;
}

export default async function middleware(request) {
  const url = new URL(request.url);
  const user = await currentUser(request);
  if (!user) {
    if (url.pathname.startsWith("/api/")) return new Response("Nicht angemeldet", { status: 401 });
    return Response.redirect(new URL("/login.html", request.url), 302);
  }
  if (url.pathname.startsWith("/u/")) return new Response("Kein Zugriff", { status: 403 });
  if (url.pathname.startsWith("/me/")) {
    const target = new URL("/u/" + user + url.pathname.slice(3) + url.search, request.url);
    return rewrite(target);
  }
  return next();
}
