# Bookkeeping Control Workflow with LLM

*A controllable bookkeeping workflow using rules, historical similarity, and LLM-assisted posting suggestions.*

> **Work in progress:** This repository is an early-stage prototype for exploring how bookkeeping control workflows can be supported by a hybrid architecture combining deterministic rules, similar historical cases, and LLM-assisted suggestion generation.

---

## Overview

This project explores how parts of the bookkeeping control process can be structured into a controllable workflow rather than treated as a pure prediction problem.

The core idea is simple:

- use **hard rules** where the system must be strict
- use **historical similarity** where prior cases are informative
- use **LLM support** where contextual interpretation is useful
- keep a **human in the loop** when confidence is insufficient or controls are triggered

The goal is **not** to build a fully autonomous posting engine.  
The goal is to build a workflow that can support consistent, explainable, and auditable bookkeeping suggestions.

---

## Current scope

This repository currently focuses on a small MVP that demonstrates the end-to-end flow:

1. ingest synthetic invoice / voucher-like input
2. normalize and structure the input
3. apply basic control rules
4. retrieve similar historical examples
5. generate a posting suggestion
6. assign a confidence score
7. route the case to:
   - `stop`
   - `review`
   - `suggest`

At this stage, the repository is intended as a **prototype and design artifact**, not a production-ready accounting system.

---

## Why this project exists

Bookkeeping and posting control often involve a mix of:

- formal rules
- known accounting patterns
- supplier-specific practice
- contextual judgment
- exception handling

This makes the problem poorly suited to a "model-only" approach.

A more realistic design is a **hybrid workflow**, where different parts of the decision process are handled by different mechanisms:

- **rules** for policy constraints and hard stops
- **similarity search** for learning from prior handled cases
- **LLM assistance** for interpreting text and supporting structured suggestions
- **human review** where uncertainty remains

---

## Architecture

The current MVP follows this simplified architecture:

```text
Input
  -> ETL / normalization
  -> Rules engine
  -> Historical similarity lookup
  -> Suggestion + confidence scoring
  -> Decision routing
