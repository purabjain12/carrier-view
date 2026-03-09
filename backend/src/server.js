import dotenv from "dotenv";
import express from "express";
import cors from "cors";
import { connectDB } from "./config/db.js";
import simulationRoutes from "./routes/simulationRoutes.js";

dotenv.config();

const app = express();
const port = process.env.PORT || 4000;

app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "backend-api" });
});

app.use("/api", simulationRoutes);

await connectDB(process.env.MONGODB_URI);

app.listen(port, () => {
  console.log(`Backend running on port ${port}`);
});
