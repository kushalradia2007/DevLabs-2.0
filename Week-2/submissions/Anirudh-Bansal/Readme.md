# 🤖 LangChain & Groq LLM Agent

A lightweight, terminal-based AI Agent built with **LangChain**, **Pydantic V2**, and **Groq** (`llama-3.3-70b-versatile`). The agent implements an autonomous ReAct (Reasoning and Acting) execution loop capable of parsing complex queries, calling multiple tools sequentially, handling input validation gracefully, and compiling complete answers.

---

## 🚀 Features

* **Autonomous Tool Use:** Loops up to 10 iterations (`MAX_STEPS`) processing model thoughts and mapping tool outputs back into the conversation state.
* **Pydantic V2 Data Validation:** Enforces strict parameter data typing and value normalizations directly on incoming LLM tool arguments before execution.
* **Live API Integrations:** Leverages public endpoints for real-time exchange rates and global city geocoding—completely zero-config/no API tokens required.
* **Self-Healing Loop:** Automatically forwards raw Pydantic validation exceptions back into the conversation history so the LLM can rewrite bad inputs.

---

## 🛠️ Installation & Setup

1. **Clone the repository and install dependencies:**
   pip install langchain-groq langchain-core pydantic requests pytz

2. **Configure your environment variable:**
   export GROQ_API_KEY="your-groq-api-key-here"

3. **Launch the agent interface:**
   python agent.py

---

## 🏗️ Core Architecture & Tool Design

The engine relies on a custom `Tool` abstraction wrapper that maps Pydantic baseline schemas straight to Groq function schemas via `.model_json_schema()`.

| Tool Name | Input Schema | Backend Implementation | Description |
| :--- | :--- | :--- | :--- |
| `convert_currency` | `from_currency`, `to_currency`, `amount` | `open.er-api.com` v6 API | Resolves live exchange quotes. Automates casing normalization via custom `@field_validator`. |
| `get_time` | `city` | `geocoding-api.open-meteo.com` + `pytz` | Looks up geographical lat/long context to extract a real-time string with proper timezone offsets. |

---

## 🎯 Production Testing & Outputs

Here are 3 verified execution examples showcasing exact query inputs alongside the agent's final loop evaluations:

### Example 1: Multi-Currency Conversion
* **User Query:** Convert 150 USD to EUR, and also tell me how much that is in JPY.
* **Agent Output:** 150 USD is equivalent to 130.06 EUR and 24038.55 JPY.

### Example 2: Multi-City Cross-Timezone Analysis
* **User Query:** What time is it right now in Tokyo and what time is it in London?
* **Agent Output:** The current time in Tokyo is 03:06:58 JST+0900 and the current time in London is 19:07:00 BST+0100.

### Example 3: Mixed Multi-Tool Chain Loop
* **User Query:** I am planning a trip. Can you check what time it currently is in Paris, and let me know how many Euros I can get for 500 USD?
* **Agent Output:** The current time in Paris is 20:07:25 CEST+0200. You can get 433.54 Euros for 500 USD.
