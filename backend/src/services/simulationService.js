import { callMLService } from "./mlClient.js";
import { Simulation } from "../models/Simulation.js";

export async function runSimulationAndPersist({
  inputProfile,
  mlServiceUrl
}) {
  const simulationResult = await callMLService(
    mlServiceUrl,
    "/simulate-career",
    inputProfile
  );

  const doc = await Simulation.create({
    inputProfile,
    generatedPaths: simulationResult.generatedPaths,
    salaryMeta: simulationResult.salaryMeta || {
      currency: "INR",
      period: "yearly"
    },
    modelMetadata: simulationResult.modelMetadata
  });

  return doc;
}
