import mongoose from "mongoose";

const InputProfileSchema = new mongoose.Schema(
  {
    educationLevel: { type: String, required: true },
    degreeStream: { type: String, required: true },
    skills: [{ type: String, required: true }],
    location: { type: String, required: true },
    interests: [{ type: String }],
    riskPreference: {
      type: String,
      enum: ["low", "medium", "high"],
      required: true
    },
    yearsToSimulate: { type: Number, default: 10 }
  },
  { _id: false }
);

const YearProjectionSchema = new mongoose.Schema(
  {
    year: Number,
    salary: Number,
    demandTrend: { type: String, enum: ["increasing", "stable", "declining"] },
    stabilityScore: Number,
    burnoutRisk: Number
  },
  { _id: false }
);

const PathScenarioSchema = new mongoose.Schema(
  {
    pathName: String,
    bestCase: [YearProjectionSchema],
    averageCase: [YearProjectionSchema],
    worstCase: [YearProjectionSchema],
    switchOptions: [String]
  },
  { _id: false }
);

const SimulationSchema = new mongoose.Schema(
  {
    inputProfile: { type: InputProfileSchema, required: true },
    generatedPaths: [PathScenarioSchema],
    salaryMeta: {
      currency: { type: String, default: "INR" },
      period: { type: String, default: "yearly" }
    },
    modelMetadata: {
      salaryModelVersion: String,
      demandModelVersion: String,
      transitionModelVersion: String,
      burnoutModelVersion: String
    }
  },
  { timestamps: true }
);

export const Simulation = mongoose.model("Simulation", SimulationSchema);
