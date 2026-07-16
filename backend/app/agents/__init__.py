"""MARA Agent Package — Microsoft Agent Framework specialised agents.

All agents in this package:
    ✅ Use Microsoft Agent Framework (agent_framework.Agent)
    ✅ Call planning tools exclusively through MCPPlanningClient
    ✅ Never import Planning Services directly
    ✅ Never perform calculations — they only interpret and explain tool results

Agents:
    InventoryAgent     — stock levels, safety status, usable inventory
    ProductionAgent    — production impact, shortage timelines, BOM explosions
    SupplierAgent      — late POs, PO coverage, supplier risk
    ReplenishmentAgent — replenishment actions, cross-plant transfers
    ExplanationAgent   — natural language synthesis of all evidence

Orchestrator:
    MaterialPlanningOrchestrator — routes user intent to the right agent(s)
"""
