import express from "express";
import pricesRouter from "./routes/oil-prices.js";

const app = express();
const PORT = process.env.PORT || 8000;

app.use(express.json());

app.use("/prices", pricesRouter);

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
