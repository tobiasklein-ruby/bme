// Prüft das Passwort, erkennt daran die Person (Toby oder Laura) und setzt ein Login-Cookie für ein Jahr.
import { createHash, timingSafeEqual } from "node:crypto";

const USERS = { toby: "PW_TOBY", laura: "PW_LAURA" };

function readBody(req) {
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (c) => { raw += c; if (raw.length > 4096) req.destroy(); });
    req.on("end", () => resolve(raw));
  });
}

const sha = (s) => createHash("sha256").update(s).digest();

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.writeHead(303, { Location: "/login.html" }).end();
    return;
  }
  const given = new URLSearchParams(await readBody(req)).get("password") || "";
  let user = null;
  for (const [name, env] of Object.entries(USERS)) {
    const pw = process.env[env];
    if (pw && timingSafeEqual(sha(given), sha(pw))) user = name;
  }
  if (!user) {
    res.writeHead(303, { Location: "/login.html?f=1" }).end();
    return;
  }
  const token = createHash("sha256").update(user + ":" + process.env[USERS[user]] + ":tklst-v2").digest("hex");
  res.writeHead(303, {
    "Set-Cookie": `tklst=${user}.${token}; Max-Age=31536000; Path=/; HttpOnly; Secure; SameSite=Lax`,
    Location: "/",
  }).end();
}
