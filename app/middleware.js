// Passwortschutz für die ganze App (Vercel Routing Middleware).
// Freigegeben ohne Login: Login-Seite, Login-API, Manifest und Icons (iOS braucht sie für „Zum Home-Bildschirm“).
import { next } from "@vercel/functions";

export const config = {
  matcher: ["/((?!login\\.html|api/login|manifest\\.webmanifest|icons/).*)"],
};

async function expectedToken(password) {
  const data = new TextEncoder().encode(password + ":tklst-v1");
  const hash = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export default async function middleware(request) {
  const password = process.env.APP_PASSWORD;
  if (!password) return new Response("APP_PASSWORD fehlt in den Vercel-Einstellungen.", { status: 500 });
  const cookie = request.headers.get("cookie") || "";
  const token = cookie.match(/(?:^|;\s*)tklst=([a-f0-9]{64})/)?.[1];
  if (token && token === (await expectedToken(password))) return next();
  return Response.redirect(new URL("/login.html", request.url), 302);
}
