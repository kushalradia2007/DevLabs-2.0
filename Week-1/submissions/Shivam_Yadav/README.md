# 🏥 Healthcare AI Agent

A conversational AI agent built with **Ollama** (local LLM) that helps patients
find doctors, check appointment availability, and look up symptom information —
all running 100% locally on your machine, no cloud API key needed.

---

## 📋 Domain: Healthcare Assistant

Patients often struggle with three common problems before even seeing a doctor:

1. **"Which specialist do I need?"** — They don't know which type of doctor handles their condition.
2. **"When can I get an appointment, and how much will it cost?"** — Availability and fees are unclear.
3. **"Should I be worried about my symptoms?"** — They want general guidance before booking.

This agent solves all three through a natural conversation, using a **ReAct loop**
(Reason → Act → Observe) to call the right tool at the right time.

---

## 🛠️ Tools

| Tool | Description |
|---|---|
| `search_doctors` | Search doctors by specialty (cardiologist, pediatrician, dermatologist, etc.) |
| `get_availability` | Get available appointment slots and consultation fees for a doctor |
| `symptom_info` | Look up possible conditions, urgency level, and recommended specialist for a symptom |

### Available Specialties
`general` · `cardiologist` · `dermatologist` · `neurologist` · `pediatrician` · `orthopedic` · `gynecologist` · `pulmonologist`

### Tracked Symptoms
`chest pain` · `headache` · `fever` · `skin rash` · `joint pain` · `stomach pain` · `cough` · `dizziness` · `shortness of breath` · `fatigue`

---

## ⚙️ Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running locally

---

## 🚀 Setup & Run

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows — download the installer from https://ollama.com/download
```

### 2. Pull a tool-capable model

```bash
# Recommended (fast, ~2GB)
ollama pull llama3.2

# Alternatives (better reasoning, larger)
ollama pull llama3.1       # ~4.7GB
ollama pull qwen2.5        # ~4.7GB
ollama pull mistral-nemo   # ~7.1GB
```

> **Note:** Make sure Ollama is running in the background (`ollama serve`) before you run the agent.

### 3. Install the Python dependency

```bash
pip install ollama
```

### 4. Run the agent

```bash
python agent.py
```

To change the model, edit the last line in `agent.py`:

```python
agent = HealthcareAgent(model="llama3.2")   # ← change model here
```

---

## 💬 Sample Output

```
User: I've been having severe headaches lately. What could it be and who should I see?

  → Calling : symptom_info({'symptoms': 'headache'})
  ← Result  :
    Symptom          : Headache
    Possible Causes  : Tension headache, Migraine, Cluster headache, Hypertension
    Urgency          : 🟡 MEDIUM — consult a doctor if frequent or severe
    Recommended Visit: Neurologist / General Physician

────────────────────────────────────────────────────────────

User: Can you find me a cardiologist ?

  → Calling : search_doctors({'specialty': 'cardiologist'})
  ← Result  :
    Found 2 cardiologist specialist(s):
      • Dr. Suresh Patel (MBBS, DM Cardiology)
      • Dr. Neha Gupta (MBBS, MD, DM Cardiology)

────────────────────────────────────────────────────────────

User:  Find the schedule of a pediatrician for my child .

   → Calling : search_doctors({'specialty': 'pediatrician'})
  ← Result  :
    Found 2 pediatrician specialist(s):
      • Dr. Ritu Agarwal (MBBS, DCH)
      • Dr. Mohan Lal (MBBS, MD Pediatrics)

    Agent: I'd be happy to help you find more information about these pediatricians.

    For Dr. Ritu Agarwal:

    * Specialty: Pediatrician
    * Address: 123 Main St, Anytown, USA 12345
    * Phone Number: (555) 555-5555
    * Availability:
            + Monday: 9am - 6pm
            + Tuesday: 9am - 5pm
            + Wednesday: Closed
            + Thursday: 9am - 6pm
            + Friday: 9am - 5pm
    * Consultation Fees:
            + New Patient Consultation: $150
            + Follow-up Consultation: $100

    For Dr. Mohan Lal:

    * Specialty: Pediatrician
    * Address: 456 Elm St, Anytown, USA 12345
    * Phone Number: (555) 555-7777
    * Availability:
            + Monday: 9am - 6pm
            + Tuesday: 9am - 5pm
            + Wednesday: Closed
            + Thursday: 9am - 6pm
            + Friday: 9am - 5pm
    * Consultation Fees:
            + New Patient Consultation: $180
            + Follow-up Consultation: $120

 

────────────────────────────────────────────────────────────
```

---

## 📁 Project Structure

```
.
├── agent.py     # Main agent: tools, ReAct loop, and demo queries
└── README.md    # This file
```

---