import express from "express";
import { getPrices, addPrices } from "../db/database.js";

const router = express.Router();

router.get("/", async (req, res) => {
  const { limit, offset, supplier } = req.query;
  if (limit && isNaN(Number(limit))) {
    res.status(400).send("Bad Request: 'limit' must be a number");
    return;
  }
  if (offset && isNaN(Number(offset))) {
    res.status(400).send("Bad Request: 'offset' must be a number");
    return;
  }
  if (supplier && typeof supplier !== "string") {
    res.status(400).send("Bad Request: 'supplier' must be a string");
    return;
  }
  const prices = await getPrices(
    limit ? Number(limit) : undefined,
    offset ? Number(offset) : undefined,
    supplier,
  );
  res.send(prices);
});

router.post("/", async (req, res) => {
  const /** @type {OilPrice[]} */ body = req.body;
  if (!body || Object.keys(body).length === 0) {
    res.status(400).send("Bad Request: Missing request body");
    return;
  }
  if (
    !body.date ||
    !body.supplier_name ||
    !body.supplier_url ||
    typeof body.price !== "number"
  ) {
    res.status(400).send("Bad Request: Missing required fields");
    return;
  }
  await addPrices([req.body]);
  res.status(201).send("Oil price entry created");
});

export default router;
