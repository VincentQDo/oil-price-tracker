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
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
});

app.use("/prices", pricesRouter);

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
