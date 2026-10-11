// Meldet ab (z. B. wenn das iPhone weitergegeben wird).
export default function handler(req, res) {
  res.writeHead(303, {
    "Set-Cookie": "tklst=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax",
    "Clear-Site-Data": '"cache", "storage"',
    Location: "/login.html",
  }).end();
}
