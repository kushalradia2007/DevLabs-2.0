"""
Healthcare AI Agent
Domain: Healthcare Assistant

A healthcare assistant that helps patients find doctors by specialty,
check appointment availability and consultation fees,
and look up general symptom information.

Run:
    pip install ollama
    ollama pull llama3.2        # or: llama3.1 / qwen2.5 / mistral-nemo
    python agent.py
"""

import json
import ollama

# ─────────────────────────────────────────────
# TOOLS — functions the agent can call
# ─────────────────────────────────────────────

def search_doctors(specialty: str) -> str:
    """
    Search for available doctors by medical specialty.

    Args:
        specialty: Medical specialty to search for,
                   e.g. 'cardiologist', 'pediatrician', 'general'.

    Returns:
        A formatted list of matching doctors, or a helpful
        message listing available specialties if none found.
    """
    doctor_catalog = {
        "general": [
            "Dr. Priya Sharma (MBBS, MD)",
            "Dr. Rajesh Kumar (MBBS, MD)",
            "Dr. Anita Verma (MBBS)",
        ],
        "cardiologist": [
            "Dr. Suresh Patel (MBBS, DM Cardiology)",
            "Dr. Neha Gupta (MBBS, MD, DM Cardiology)",
        ],
        "dermatologist": [
            "Dr. Kavita Singh (MBBS, MD Dermatology)",
            "Dr. Arjun Mehta (MBBS, DVD)",
        ],
        "neurologist": [
            "Dr. Vikram Rao (MBBS, DM Neurology)",
            "Dr. Sunita Joshi (MBBS, MD, DM Neurology)",
        ],
        "pediatrician": [
            "Dr. Ritu Agarwal (MBBS, DCH)",
            "Dr. Mohan Lal (MBBS, MD Pediatrics)",
        ],
        "orthopedic": [
            "Dr. Deepak Nair (MBBS, MS Ortho)",
            "Dr. Pooja Tiwari (MBBS, DNB Ortho)",
        ],
        "gynecologist": [
            "Dr. Meera Reddy (MBBS, MD Gynecology)",
            "Dr. Shanti Pillai (MBBS, DGO)",
        ],
        "pulmonologist": [
            "Dr. Anil Bose (MBBS, MD Pulmonology)",
        ],
    }

    key = specialty.lower().strip()
    for catalog_key, doctors in doctor_catalog.items():
        if catalog_key in key or key in catalog_key:
            return (
                f"Found {len(doctors)} {catalog_key} specialist(s):\n"
                + "\n".join(f"  • {d}" for d in doctors)
            )

    available = ", ".join(doctor_catalog.keys())
    return (
        f"No doctors found for '{specialty}'.\n"
        f"Available specialties: {available}"
    )


def get_availability(doctor_name: str) -> str:
    """
    Get the available appointment slots and consultation fee for a doctor.

    Args:
        doctor_name: Full or partial name of the doctor,
                     e.g. 'Dr. Priya Sharma'.

    Returns:
        A formatted string with consultation fee and available
        time slots, or an error message if the doctor is not found.
    """
    schedules = {
        "Dr. Priya Sharma": {
            "slots": ["Mon 10:00 AM", "Mon 11:00 AM", "Wed 3:00 PM", "Fri 10:00 AM"],
            "fee": 500,
        },
        "Dr. Rajesh Kumar": {
            "slots": ["Tue 9:00 AM", "Thu 4:00 PM", "Sat 11:00 AM"],
            "fee": 600,
        },
        "Dr. Anita Verma": {
            "slots": ["Mon 9:00 AM", "Wed 9:00 AM", "Fri 9:00 AM"],
            "fee": 450,
        },
        "Dr. Suresh Patel": {
            "slots": ["Mon 2:00 PM", "Wed 10:00 AM", "Fri 3:00 PM"],
            "fee": 1500,
        },
        "Dr. Neha Gupta": {
            "slots": ["Tue 11:00 AM", "Thu 2:00 PM"],
            "fee": 1200,
        },
        "Dr. Kavita Singh": {
            "slots": ["Mon 9:00 AM", "Wed 4:00 PM", "Sat 10:00 AM", "Sat 11:00 AM"],
            "fee": 800,
        },
        "Dr. Arjun Mehta": {
            "slots": ["Tue 10:00 AM", "Fri 2:00 PM"],
            "fee": 700,
        },
        "Dr. Vikram Rao": {
            "slots": ["Mon 11:00 AM", "Thu 3:00 PM"],
            "fee": 1800,
        },
        "Dr. Sunita Joshi": {
            "slots": ["Wed 11:00 AM", "Fri 4:00 PM"],
            "fee": 1600,
        },
        "Dr. Ritu Agarwal": {
            "slots": ["Mon 10:00 AM", "Tue 9:00 AM", "Wed 10:00 AM", "Thu 9:00 AM"],
            "fee": 700,
        },
        "Dr. Mohan Lal": {
            "slots": ["Tue 11:00 AM", "Sat 10:00 AM"],
            "fee": 650,
        },
        "Dr. Deepak Nair": {
            "slots": ["Tue 2:00 PM", "Thu 11:00 AM", "Sat 9:00 AM"],
            "fee": 1000,
        },
        "Dr. Pooja Tiwari": {
            "slots": ["Mon 3:00 PM", "Wed 9:00 AM"],
            "fee": 900,
        },
        "Dr. Meera Reddy": {
            "slots": ["Mon 9:00 AM", "Wed 2:00 PM", "Fri 11:00 AM"],
            "fee": 1000,
        },
        "Dr. Anil Bose": {
            "slots": ["Tue 10:00 AM", "Thu 10:00 AM"],
            "fee": 1100,
        },
    }

    name_lower = doctor_name.lower()
    for name, info in schedules.items():
        if name.lower() in name_lower or name_lower in name.lower():
            slots_str = " | ".join(info["slots"])
            return (
                f"Doctor          : {name}\n"
                f"Consultation Fee: ₹{info['fee']}\n"
                f"Available Slots : {slots_str}"
            )

    return (
        f"No schedule found for '{doctor_name}'.\n"
        "Tip: Use the exact name returned by search_doctors."
    )


def symptom_info(symptoms: str) -> str:
    """
    Look up possible conditions, urgency level, and the recommended
    specialist for a given symptom or set of symptoms.

    Args:
        symptoms: Symptom description, e.g. 'chest pain', 'fever',
                  'skin rash', 'joint pain'.

    Returns:
        A formatted string with possible causes, urgency level,
        and recommended specialist, plus a disclaimer.
    """
    symptom_db = {
        "chest pain": {
            "possible_conditions": [
                "Angina", "Heart Attack", "GERD", "Costochondritis", "Anxiety"
            ],
            "urgency": "🔴 HIGH — seek emergency care immediately if severe",
            "specialist": "Cardiologist",
        },
        "headache": {
            "possible_conditions": [
                "Tension headache", "Migraine", "Cluster headache", "Hypertension"
            ],
            "urgency": "🟡 MEDIUM — consult a doctor if frequent or severe",
            "specialist": "Neurologist / General Physician",
        },
        "fever": {
            "possible_conditions": [
                "Viral infection", "Bacterial infection", "Dengue", "Typhoid", "COVID-19"
            ],
            "urgency": "🟡 MEDIUM — see a doctor if fever > 103°F or lasts more than 3 days",
            "specialist": "General Physician",
        },
        "skin rash": {
            "possible_conditions": [
                "Eczema", "Psoriasis", "Allergic reaction", "Fungal infection", "Hives"
            ],
            "urgency": "🟢 LOW — schedule a routine appointment",
            "specialist": "Dermatologist",
        },
        "joint pain": {
            "possible_conditions": [
                "Arthritis", "Gout", "Sports injury", "Bursitis", "Lupus"
            ],
            "urgency": "🟡 LOW–MEDIUM — see a doctor if persistent or worsening",
            "specialist": "Orthopedic",
        },
        "stomach pain": {
            "possible_conditions": [
                "Gastritis", "IBS", "Appendicitis", "Peptic ulcer", "Food poisoning"
            ],
            "urgency": "🟡 MEDIUM — seek immediate care if pain is sudden and severe",
            "specialist": "General Physician / Gastroenterologist",
        },
        "cough": {
            "possible_conditions": [
                "Common cold", "Asthma", "Bronchitis", "COVID-19", "Tuberculosis"
            ],
            "urgency": "🟢 LOW–MEDIUM — consult a doctor if lasting more than 2 weeks",
            "specialist": "General Physician / Pulmonologist",
        },
        "dizziness": {
            "possible_conditions": [
                "Vertigo", "Low blood pressure", "Anemia", "Inner ear infection", "Dehydration"
            ],
            "urgency": "🟡 MEDIUM — see a doctor if recurring or accompanied by fainting",
            "specialist": "Neurologist / General Physician",
        },
        "shortness of breath": {
            "possible_conditions": [
                "Asthma", "Pneumonia", "Heart failure", "Pulmonary embolism", "Anxiety"
            ],
            "urgency": "🔴 HIGH — seek emergency care if sudden or severe",
            "specialist": "Pulmonologist / Cardiologist",
        },
        "fatigue": {
            "possible_conditions": [
                "Anemia", "Thyroid disorder", "Diabetes", "Depression", "Sleep disorder"
            ],
            "urgency": "🟢 LOW — schedule a check-up if persistent beyond 2 weeks",
            "specialist": "General Physician",
        },
    }

    symptoms_lower = symptoms.lower()
    matched = []

    for key, info in symptom_db.items():
        if key in symptoms_lower or any(word in symptoms_lower for word in key.split()):
            conditions = ", ".join(info["possible_conditions"])
            matched.append(
                f"Symptom          : {key.title()}\n"
                f"Possible Causes  : {conditions}\n"
                f"Urgency          : {info['urgency']}\n"
                f"Recommended Visit: {info['specialist']}"
            )

    if matched:
        result = "\n\n".join(matched)
        return result + "\n\n⚠️  Disclaimer: This is general information only. Always consult a qualified doctor for proper diagnosis and treatment."

    tracked = ", ".join(symptom_db.keys())
    return (
        f"No specific information found for '{symptoms}'.\n"
        f"Tracked symptoms: {tracked}.\n"
        "⚠️  Please consult a doctor for symptoms not listed above."
    )


# ─────────────────────────────────────────────
# TOOL REGISTRY
# Maps tool name → (function, Ollama tool definition)
# ─────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "search_doctors": search_doctors,
    "get_availability": get_availability,
    "symptom_info": symptom_info,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_doctors",
            "description": (
                "Search for available doctors by medical specialty. "
                "Use this when the user mentions a specialty or needs to find a doctor type. "
                "E.g. 'cardiologist', 'general physician', 'pediatrician'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "The medical specialty to search for, e.g. 'cardiologist', 'dermatologist'.",
                    }
                },
                "required": ["specialty"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_availability",
            "description": (
                "Get available appointment slots and consultation fee for a specific doctor. "
                "Requires the doctor's name as returned by search_doctors."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_name": {
                        "type": "string",
                        "description": "Full or partial name of the doctor, e.g. 'Dr. Priya Sharma'.",
                    }
                },
                "required": ["doctor_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "symptom_info",
            "description": (
                "Look up general medical information about a symptom: possible conditions, "
                "urgency level, and recommended specialist. "
                "Use when the user describes a symptom like 'chest pain', 'fever', or 'dizziness'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "string",
                        "description": "The symptom(s) to look up, e.g. 'chest pain', 'skin rash'.",
                    }
                },
                "required": ["symptoms"],
            },
        },
    },
]


# ─────────────────────────────────────────────
# AGENT — ReAct loop
# ─────────────────────────────────────────────

class HealthcareAgent:
    """
    A conversational healthcare assistant that uses a ReAct loop
    (Reason → Act → Observe) to answer patient queries using
    domain-specific tools via a locally running Ollama model.
    """

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.system = (
            "You are a compassionate and knowledgeable healthcare assistant. "
            "Your role is to help patients:\n"
            "  1. Find doctors by specialty.\n"
            "  2. Check doctor availability and consultation fees.\n"
            "  3. Understand general information about their symptoms.\n\n"
            "Always use the available tools to fetch accurate information. "
            "Never invent doctor names, fees, or medical facts. "
            "Always remind patients that your symptom information is general guidance only, "
            "and they should consult a qualified doctor for diagnosis and treatment. "
            "Be concise, clear, and empathetic."
        )

    def run(self, user_message: str) -> str:
        """Run the ReAct agent loop for a single user query."""
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": user_message},
        ]

        print(f"\nUser: {user_message}")

        while True:
            # ── THOUGHT ──────────────────────────────────────────────
            # Model reasons and decides the next action (tool call or reply)
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )

            assistant_msg = response.message
            messages.append(assistant_msg)  # Add to history

            # No more tool calls → return the final answer
            if not assistant_msg.tool_calls:
                return assistant_msg.content or "[No response generated]"

            # ── ACTION + OBSERVATION ─────────────────────────────────
            # Execute each tool call and feed results back into context
            for tool_call in assistant_msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = tool_call.function.arguments

                # Ollama may return args as a JSON string; parse if needed
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                if fn_name not in TOOL_FUNCTIONS:
                    result = f"Error: Unknown tool '{fn_name}'."
                else:
                    print(f"  → Calling : {fn_name}({fn_args})")
                    result = TOOL_FUNCTIONS[fn_name](**fn_args)
                    print(f"  ← Result  :\n    "
                          + result.replace("\n", "\n    "))

                # Observation: feed result back to the model
                messages.append({
                    "role": "tool",
                    "content": result,
                })


# ─────────────────────────────────────────────
# DEMO — 4 test queries
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Change model to any Ollama model that supports tool-use:
    # llama3.2 | llama3.1 | qwen2.5 | mistral-nemo
    agent = HealthcareAgent(model="llama3.2")

    queries = [
        "I've been having severe headaches lately. What could it be and who should I see?",
        "Can you find me a cardiologist ?",
        " Find the schedule of a pediatrician for my child .",
    ]

    for query in queries:
        answer = agent.run(query)
        print(f"\nAgent: {answer}")
        print("─" * 60)
