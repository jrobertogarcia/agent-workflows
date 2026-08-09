---
name: phase-breakdown
description: Divide a large change into small, independently verifiable phases. Use before planning implementation of a complex task.
model: opus
effort: medium
---

# Phase Breakdown

Analyze and systematically divide a complex implementation into logical, independent, and incrementally testable phases. Reuse context already gathered in this thread rather than re-reading it.

## Principles
* **Atomicity**: Each phase must be logically complete and independently verifiable.
* **Risk-First**: Prioritize high-uncertainty, architectural, or foundational components early.
* **Feedback Loops**: Keep changes small to establish fast, reliable feedback loops.

## Outcome
* **Phase-Only**: Focus exclusively on proposing the execution sequence. Do not write source code or draft final implementation plans.

Propose a prioritized, evidence-based sequence of execution phases, detailing the **Rationale** for the sequence, key **Deliverables**, and **Verification methods** to prove stability at each step. Create a file only when requested.
