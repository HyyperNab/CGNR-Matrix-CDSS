# CGNR Matrix — Clinical Decision Support System

This repository contains the mathematical core and safety validation framework for the **Constraint-Grounded Nutritional Recovery (CGNR) Matrix**, as submitted to *Clinical Nutrition ESPEN*.


## 🚀 Overview
The CGNR Matrix is a 3-mode tensor-based CDSS designed for personalized post-gastrectomy nutrition. It operates behind three deterministic **Human-in-the-Loop (HIL) safety gates**.


## 🛡️ Safety Gates (The Logic)
- **Gate 1: Dynamic Floor** (CRP-dependent hormonal attenuation)
- **Gate 2: 3σ Residual Norm** (CORCONDIA stability check)
- **Gate 3: Zero-Veto** (Per-intervention compliance enforcement)


## 📋 Repository Contents
- `/logic`: Contains the Python implementation of the CRP sigmoid curve and HIL gate pseudocode.
- `/audit`: Contains the full 29-point Single Point of Failure (SPOF) audit matrix.


## ⚖️ Citation & Liability
This system implements the **SOC-29 (Safety Override Clause)** framework for algorithmic liability. See the Main Paper for the full legal specification.

