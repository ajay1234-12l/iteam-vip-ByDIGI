// api/image.js
const fs = require("fs");
const path = require("path");

const IMAGES_DIR = path.join(process.cwd(), "public", "images");
const EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".gif"];
const MIME = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
};

module.exports = (req, res) => {
  try {
    // allow GET only
    if (req.method !== "GET") {
      res.statusCode = 405;
      res.setHeader("Allow", "GET");
      return res.end("Method Not Allowed");
    }

    const itemid = (req.query && req.query.itemid) ? String(req.query.itemid) : "";

    // validation: digits only (prevents path traversal)
    if (!/^\d+$/.test(itemid)) {
      res.statusCode = 400;
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      return res.end(JSON.stringify({ error: "invalid itemid. use digits only." }));
    }

    // find the file by trying each extension
    let found = null;
    for (const ext of EXTENSIONS) {
      const p = path.join(IMAGES_DIR, `${itemid}${ext}`);
      if (fs.existsSync(p) && fs.statSync(p).isFile()) {
        found = { path: p, ext };
        break;
      }
    }

    if (!found) {
      // 404 JSON response
      res.statusCode = 404;
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      return res.end(JSON.stringify({ error: "image not found" }));
    }

    // stream the image
    const stat = fs.statSync(found.path);
    const mime = MIME[found.ext] || "application/octet-stream";

    res.statusCode = 200;
    res.setHeader("Content-Type", mime);
    res.setHeader("Content-Length", stat.size);
    // cache one day (adjust if you want)
    res.setHeader("Cache-Control", "public, max-age=86400, immutable");

    const stream = fs.createReadStream(found.path);
    stream.pipe(res);
    stream.on("error", (err) => {
      console.error("stream error:", err);
      if (!res.headersSent) res.statusCode = 500;
      try { res.end(); } catch (e) {}
    });
  } catch (err) {
    console.error("handler error:", err);
    if (!res.headersSent) {
      res.statusCode = 500;
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      res.end(JSON.stringify({ error: "internal server error" }));
    } else {
      try { res.end(); } catch (e) {}
    }
  }
};