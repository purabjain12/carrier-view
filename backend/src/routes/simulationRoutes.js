import express from "express";
import { runSimulationAndPersist } from "../services/simulationService.js";
import { Simulation } from "../models/Simulation.js";

const router = express.Router();

router.post("/simulate", async (req, res) => {
  try {
    const {
      educationLevel,
      degreeStream,
      skills,
      location,
      interests,
      riskPreference,
      yearsToSimulate
    } = req.body;

    if (
      !educationLevel ||
      !degreeStream ||
      !Array.isArray(skills) ||
      skills.length === 0 ||
      !location ||
      !riskPreference
    ) {
      return res.status(400).json({
        error:
          "Missing required fields: educationLevel, degreeStream, skills, location, riskPreference"
      });
    }

    const simulation = await runSimulationAndPersist({
      inputProfile: {
        educationLevel,
        degreeStream,
        skills,
        location,
        interests: interests || [],
        riskPreference,
        yearsToSimulate: yearsToSimulate || 10
      },
      mlServiceUrl: process.env.ML_SERVICE_URL
    });

    return res.status(201).json(simulation);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

router.get("/simulations", async (_req, res) => {
  try {
    const simulations = await Simulation.find().sort({ createdAt: -1 }).limit(20);
    return res.json(simulations);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

router.get("/simulations/:id", async (req, res) => {
  try {
    const simulation = await Simulation.findById(req.params.id);
    if (!simulation) {
      return res.status(404).json({ error: "Simulation not found" });
    }
    return res.json(simulation);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
