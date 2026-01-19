# spaceRescue

# 🚀 SpaceRescue — Agent-Based Simulation

**SpaceRescue** is an **agent-based simulation** that models coordinated rescue missions in a damaged space station. The project compares **random agent behavior** with a **collaborative, optimized strategy**, demonstrating how intelligent decision-making improves mission efficiency.

> Built as an academic project focused on **multi-agent systems, pathfinding, and real-time visualization**.

---

## 🔍 What This Project Demonstrates

- Multi-agent modeling and coordination  
- Strategy design vs. baseline (random) behavior  
- Pathfinding and decision-making (A\*)  
- Client–server architecture  
- Real-time visualization of simulations  

---

## 🧠 Simulation Summary

- **Scenario:** 7 victims trapped across a space station  
- **Goal:** Rescue as many victims as possible before time runs out  
- **Agents:** Autonomous robots with defined roles  
- **Evaluation:** Rescue time, movements, and victims saved  

Two approaches were implemented:
- **Random strategy** (baseline)
- **Optimized collaborative strategy** (pair-based, role-driven)

The optimized strategy achieved **~40% higher mission efficiency**.

---

## 🛠 Tech Stack

- **Python + MESA** — agent-based simulation  
- **Flask** — REST API for simulation state  
- **Unity + C#** — 3D visualization client  

---

## 🧩 Architecture (High Level)

MESA (Python) → Flask API → Unity Client


- Simulation logic runs in Python  
- Unity consumes real-time state data for visualization  

---

## 📊 Key Results

- Maximum victims rescued: **7**
- Significant reduction in agent collisions and redundant movement
- Clear performance gap between random and strategic agents

---

## 📽 Demo & Documentation

- **Full Presentation (design, strategy, results):**  
  See the presentation PDF included in this repository.

- Simulation demo videos are linked inside the presentation.

---

## 🚀 What I Learned

- How to model and analyze **multi-agent systems**
- Designing strategies using **pathfinding algorithms**
- Integrating **Python simulations with Unity**
- Building maintainable client–server systems

---

## 👥 Team

Developed by:
- Kamila Jeanette Martínez Ibarra  
- Andrea Fátima Figueroa López  
- Alejandra Arredondo  
