import express from "express";
import pricesRouter from "./routes/oil-prices.js";

if (process.env.NODE_ENV !== "production") {
  await import("dotenv/config");
}

const app = express();
const PORT = process.env.PORT || 8000;
const API_KEY = process.env.API_KEY || "";

app.use(express.json());

app.use((req, res, next) => {
  const apiKey = req.header("x-api-key");
  if (API_KEY && apiKey !== API_KEY) {
    console.error("Unauthorized access attempt detected", {
      providedKey: apiKey,
      origin: req.headers.origin || "unknown",
      referer: req.headers.referer || "unknown",
      ip: req.headers['cf-connecting-ip'] || req.ip || "unknown",
      originIp: req.headers["x-forwarded-for"] || "unknown",
      userAgent: req.headers['user-agent'] || 'unknown',
      at: new Date().toISOString(),
    });
    return res.status(401).json({ error: "Unauthorized" });
  }
  console.error("Authorized request", {
      origin: req.headers.origin || "unknown",
      referer: req.headers.referer || "unknown",
      ip: req.headers['cf-connecting-ip'] || req.ip || "unknown",
      originIp: req.headers["x-forwarded-for"] || "unknown",
      userAgent: req.headers['user-agent'] || 'unknown',
      at: new Date().toISOString(),
    });
  next();
});

app.use("/prices", pricesRouter);

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
