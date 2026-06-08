import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq

# --------------------------------------------------
# SETUP
# --------------------------------------------------

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# --------------------------------------------------
# TOOLS
# --------------------------------------------------

def bmi_calculator(weight: float, height: float) -> dict:
    if weight <= 0 or height <= 0:
        return {"error": "Weight and height must be positive"}

    bmi = weight / (height ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return {
        "bmi": round(bmi, 2),
        "category": category
    }


def water_intake(weight: float) -> dict:
    liters = weight * 0.033

    return {
        "water_intake_liters": round(liters, 2)
    }


def drug_information(drug_name: str) -> dict:

    url = (
        f"https://api.fda.gov/drug/label.json?"
        f"search=openfda.generic_name:{drug_name}&limit=1"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "drug": drug_name,
            "data": data
        }

    except Exception as e:
        return {
            "error": str(e)
        }

# --------------------------------------------------
# TOOL REGISTRY
# --------------------------------------------------

TOOL_FUNCTIONS = {
    "bmi_calculator": bmi_calculator,
    "water_intake": water_intake,
    "drug_information": drug_information,
}

# --------------------------------------------------
# TOOL DEFINITIONS
# --------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "bmi_calculator",
        "description": "Calculate BMI using weight in kg and height in meters."
    },
    {
        "name": "water_intake",
        "description": "Calculate recommended daily water intake."
    },
    {
        "name": "drug_information",
        "description": "Retrieve information about a drug."
    }
]

# --------------------------------------------------
# AGENT
# --------------------------------------------------

class HealthcareAgent:

    def __init__(self):

        self.system_prompt = """
        You are a healthcare assistant.

        Available tools:
        - bmi_calculator
        - water_intake
        - drug_information

        Rules:
        1. Use bmi_calculator when weight and height are provided.
        2. Use water_intake when only weight is provided for hydration.
        3. Use drug_information when asked about medicines.
        4. Otherwise answer normally.
        """

    def decide_tool(self, query: str):

        query_lower = query.lower()

        if "height" in query_lower and "weight" in query_lower:
            return "bmi_calculator"

        if "water" in query_lower:
            return "water_intake"

        if (
            "drug" in query_lower
            or "medicine" in query_lower
            or "tablet" in query_lower
        ):
            return "drug_information"

        return None

    def run(self, user_query: str):

        import re

        print(f"\nUser: {user_query}")

        tool_name = self.decide_tool(user_query)

    # -------------------------
    # BMI TOOL
    # -------------------------

        if tool_name == "bmi_calculator":

            numbers = re.findall(r"(\d+(?:\.\d+)?)", user_query)

            if len(numbers) >= 2:

                weight = float(numbers[0])
                height = float(numbers[1])

                result = bmi_calculator(weight, height)

                print(f"-> Tool Called: {tool_name}")
                print(f"<- Observation: {result}")

                return (
                    f"Your BMI is {result['bmi']}. "
                    f"You are in the '{result['category']}' category."
                )

            return "Please provide both weight and height."

        # -------------------------
        # WATER TOOL
        # -------------------------

        elif tool_name == "water_intake":

            match = re.search(r"(\d+(?:\.\d+)?)", user_query)

            if match:

                weight = float(match.group(1))

                result = water_intake(weight)

                print(f"-> Tool Called: {tool_name}")
                print(f"<- Observation: {result}")

                return (
                    f"You should drink approximately "
                    f"{result['water_intake_liters']} liters "
                    f"of water per day."
                )

            return "Please provide your weight."

        # -------------------------
        # DRUG TOOL
        # -------------------------

        elif tool_name == "drug_information":

            words = user_query.split()

            drug_name = words[-1]

            result = drug_information(drug_name)

            print(f"-> Tool Called: {tool_name}")
            print(f"<- Observation: Tool executed")

            if "error" in result:
                return f"Could not retrieve information: {result['error']}"

            return f"Information retrieved for {drug_name}."

        # -------------------------
        # GENERAL LLM RESPONSE
        # -------------------------

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
        )

        return response.choices[0].message.content


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    agent = HealthcareAgent()

    while True:

        query = input("\nAsk Healthcare Assistant: ")

        if query.lower() in ["exit", "quit"]:
            break

        answer = agent.run(query)

        print("\nAgent Response:")
        print(answer)