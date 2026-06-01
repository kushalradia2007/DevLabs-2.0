# Tadka House — ReAct Food Ordering Agent

An intelligent, multi-turn conversational food ordering assistant for **Tadka House**—a casual Indian multi-cuisine restaurant. This agent uses the **Groq API** and function-calling capabilities to allow users to interactively browse the menu, examine dish details, check real-time item availability, and securely compile multi-item orders alongside an itemized billing layout.

---

## 🚀 Features

* **Menu Navigation**: Dynamically group and search items by food categories (`starters`, `mains`, `breads`, `desserts`, `drinks`).
* **Granular Item Diagnostics**: Inspect comprehensive descriptions, specific pricing, accurate spice designations, and culinary classifications (`🟢 Veg` or `🔴 Non-Veg`).
* **Dynamic Inventory Tracking**: Validates item availability in real-time, preventing out-of-stock options from corrupting ongoing orders.
* **Automatic Bill Compiling**: Accumulates accepted menu selections, handles unknown or sold-out items elegantly, adds mandatory `5% GST` and a `10% Service Charge`, and prints out a polished transaction receipt.
* **ReAct Logic Flow**: Operates via a robust Reasoning-and-Acting execution loop, enabling the model to make logical decisions over multi-turn prompts before answering.

---

## 🛠️ Tech Stack & Prerequisites

* **Runtime**: Python 3.10+
* **Inference Compute**: [Groq Cloud Platform](https://console.groq.com/)
* **Default LLM**: `openai/gpt-oss-20b` (or any tool-capable foundation model supported via Groq)
* **Libraries**: `groq`, `json`, `typing`

---

## 📦 Installation & Setup

1. **Clone the Project Repository**
   ```bash
   git clone [https://github.com/kushalradia2007/DevLabs-2.0.git](https://github.com/kushalradia2007/DevLabs-2.0.git)
   cd DevLabs-2.0