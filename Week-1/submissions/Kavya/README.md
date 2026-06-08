# 🏥 Healthcare Assistant Agent

A conversational AI agent powered by Groq that helps users calculate BMI, estimate daily water intake, and retrieve drug information through natural language interactions.

---

## 📋 Domain: Healthcare Assistant

People often have basic health-related questions before consulting a medical professional:

* "Is my BMI in a healthy range?"
* "How much water should I drink daily?"
* "What is this medicine used for?"

This Healthcare Assistant Agent helps answer these questions by selecting and executing the appropriate healthcare tool based on the user's request.

The agent follows a simple ReAct-style workflow:

**Reason → Select Tool → Execute Tool → Return Result**

---

## 🛠️ Tools

| Tool             | Description                                   |
| ---------------- | --------------------------------------------- |
| bmi_calculator   | Calculates BMI using weight and height        |
| water_intake     | Recommends daily water intake based on weight |
| drug_information | Retrieves information about a medicine        |

---

## ⚙️ Features

### BMI Calculator

Calculates Body Mass Index and categorizes the result as:

* Underweight
* Normal
* Overweight
* Obese

### Water Intake Calculator

Estimates recommended daily water intake using:

```text
Water Intake (Liters) = Weight × 0.033
```

### Drug Information Tool

Retrieves medicine information using the OpenFDA API.

---

## 🚀 Setup & Run

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install groq python-dotenv requests
```

Or:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

### 5. Run the Agent

```bash
python agent.py
```

---

## 💬 Sample Output

### BMI Calculation

```text
Ask Healthcare Assistant:
My weight is 70 kg and height is 1.75 m

→ Tool Called: bmi_calculator
← Observation:
{'bmi': 22.86, 'category': 'Normal'}

Agent:
Your BMI is 22.86.
You are in the Normal category.
```

---

### Water Intake

```text
Ask Healthcare Assistant:
How much water should I drink if I weigh 65 kg?

→ Tool Called: water_intake
← Observation:
{'water_intake_liters': 2.15}

Agent:
You should drink approximately
2.15 liters of water per day.
```

---

### Drug Information

```text
Ask Healthcare Assistant:
Tell me about Paracetamol

→ Tool Called: drug_information

Agent:
Information retrieved for Paracetamol.
```

---

## 📁 Project Structure

```text
Healthcare Assistant Agent/
│
├── agent.py
├── .env
└── README.md
```

---

## 🧠 Agent Workflow

```text
User Query
     │
     ▼
Agent Reasoning
     │
     ▼
Tool Selection
     │
     ▼
Tool Execution
     │
     ▼
Observation
     │
     ▼
Final Response
```

---