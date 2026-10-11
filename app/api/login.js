// Prüft das App-Passwort und setzt ein Login-Cookie für ein Jahr.
import { createHash, timingSafeEqual } from "node:crypto";

function readBody(req) {
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (c) => { raw += c; if (raw.length > 4096) req.destroy(); });
    req.on("end", () => resolve(raw));
  });
}

export default async function handler(req, res) {
  const password = process.env.APP_PASSWORD;
  if (req.method !== "POST" || !password) {
    res.writeHead(303, { Location: "/login.html" }).end();
    return;
  }
  const given = new URLSearchParams(await readBody(req)).get("password") || "";
  const a = createHash("sha256").update(given).digest();
  const b = createHash("sha256").update(password).digest();
  if (!timingSafeEqual(a, b)) {
    res.writeHead(303, { Location: "/login.html?f=1" }).end();
    return;
  }
  const token = createHash("sha256").update(password + ":tklst-v1").digest("hex");
  res.writeHead(303, {
    "Set-Cookie": `tklst=${token}; Max-Age=31536000; Path=/; HttpOnly; Secure; SameSite=Lax`,
    Location: "/",
  }).end();
}
