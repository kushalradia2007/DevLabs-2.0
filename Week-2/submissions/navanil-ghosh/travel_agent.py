"""
Week 2 — Submission 2:
Domain: Travel Agent

Demonstrates:
- Typed tool inputs with Pydantic
- Real API calls (no hardcoded data)
- Tool class pattern with auto-generated Ollama definitions
- Graceful error handling in tools
"""

import requests
import json
import ollama  # CHANGED: Replaced anthropic with ollama
from pydantic import BaseModel, Field, field_validator
from typing import Callable, Any


# ─────────────────────────────────────────────
# TOOL INPUT SCHEMAS (Pydantic)
# ─────────────────────────────────────────────

class LocalAmenityInput(BaseModel):
    city: str = Field(description="The name of the destination city (e.g., 'Paris', 'Tokyo').")
    amenity_type: str = Field(description="Type of amenity to search for (e.g., 'hotel', 'restaurant').")

    @field_validator("city")
    @classmethod
    def city_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("city cannot be empty")
        return v.strip()
    
    @field_validator("amenity_type")
    @classmethod
    def enforce_allowed_amenities(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "hotel" in cleaned:
            return "hotel"
        elif "restaurant" in cleaned:
            return "restaurant"
        else:
            raise ValueError("amenity_type must be either 'hotel' or 'restaurant'")

class TimezoneInput(BaseModel):
    timezone: str = Field(description="The strict IANA timezone string for the destination (e.g., 'Europe/Paris', 'Asia/Tokyo', 'America/New_York').")

    @field_validator("timezone")
    @classmethod
    def validate_timezone_format(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("Timezone must be in 'Area/Location' format (e.g., 'Europe/London').")
        return v.strip()

# ─────────────────────────────────────────────
# REAL API FUNCTIONS
# ─────────────────────────────────────────────

def get_local_amenities(city: str, amenity_type: str) -> str:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{amenity_type} in {city}", 
        "format": "json",                
        "limit": 3                        
    }
    headers = {
        "User-Agent": "MyLocalConciergeAgent/1.0"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return json.dumps({"error": f"No {amenity_type}s found in {city}."})
        clean_results = []
        for place in data[:3]:
            address = place.get("display_name", "Address not available")
            short_address = ", ".join(address.split(",")[:3]).strip()
            clean_results.append({
                "name": place.get("name", "Unnamed Location"),
                "address": short_address
            })
        return json.dumps(clean_results)
    except requests.RequestException as e:
        return json.dumps({"error": f"Could not fetch local amenities for {city}: {str(e)}"})

import time
import json

def get_timezone_info(timezone: str) -> str:
    url = "https://timeapi.io/api/Time/current/zone"
    params = {"timeZone": timezone}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            date_str = data.get("date", "Unknown Date")
            time_str = data.get("time", "Unknown Time")
            day_of_week = data.get("dayOfWeek", "Unknown Day")
            is_dst = data.get("dstActive", False)

            result_dict = {
                "current_time": f"{date_str} {time_str}",
                "day_of_week": day_of_week,
                "timezone": data.get("timeZone", timezone),
                "daylight_saving_active": is_dst
            }
            
            return json.dumps(result_dict)
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"  [!] Network blip for timezone. Retrying... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                return json.dumps({"error": f"Could not fetch time for {timezone} after {max_retries} attempts. Error: {str(e)}"})


# ─────────────────────────────────────────────
# TOOL CLASS
# ─────────────────────────────────────────────

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        func: Callable[..., str],
    ) -> None:
        self.name = name
        self.description = description
        self.input_model = input_model
        self.func = func

    def run(self, raw_input: dict[str, Any]) -> str:
        """Validate inputs with Pydantic, then call the function."""
        try:
            validated = self.input_model(**raw_input)
            return self.func(**validated.model_dump())
        except Exception as e:
            return f"Tool '{self.name}' failed: {e}"

    # CHANGED: Formatted schema for Ollama instead of Claude
    def to_ollama_definition(self) -> dict[str, Any]:
        """Auto-generate Ollama tool definition from Pydantic model."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            }
        }


# ─────────────────────────────────────────────
# TOOL REGISTRY
# ─────────────────────────────────────────────

TOOLS: list[Tool] = [
    Tool(
        name="get_local_amenities",
        description=(
            "Find local businesses, lodging, or dining options (like hotels, restaurants, cafes, or pubs) "
            "in a specific city. Always use this tool when the user is looking for places to stay, eat, or drink "
            "at a location — do not guess or hallucinate options."
        ),
        input_model=LocalAmenityInput,
        func=get_local_amenities,
    ),
    Tool(
        name="get_timezone_info",
        description=(
            "Fetch the current local time and UTC offset for a specific timezone."
        ),
        input_model=TimezoneInput,
        func=get_timezone_info,
    ),
]

TOOL_MAP: dict[str, Tool] = {t.name: t for t in TOOLS}


# ─────────────────────────────────────────────
# AGENT
# ─────────────────────────────────────────────

class TravelAgent:
    def __init__(self) -> None:
        # CHANGED: Removed anthropic client, updated definition call
        self.tool_definitions = [t.to_ollama_definition() for t in TOOLS]

    def run(self, user_message: str) -> str:
        # CHANGED: Ollama expects the system prompt directly in the messages list
        messages: list[dict[str, Any]] = [
            {
                "role": "system", 
                "content": (
                    "You are a helpful travel assistant.try to give answers in nice user readable form "
                    "Use tools to find real information. "
                    "When a tool returns data, you MUST use that data to answer the user's question. Do not apologize or say you cannot find it if the tool provided data.If the tool doesnt return data then say you don't have the info"
                    "When suggesting places (hotels, restaurants, etc.), ALWAYS format your response as a clean, bulleted list."
                )
            },
            {"role": "user", "content": user_message}
        ]

        print(f"\nUser: {user_message}")

        while True:
            # CHANGED: Replaced anthropic.messages.create with ollama.chat
            response = ollama.chat(
                model="llama3.1", # Ensure you have a tool-capable model pulled locally
                messages=messages,
                tools=self.tool_definitions,
            )

            msg = response["message"]
            messages.append(msg)

            # CHANGED: Handled Ollama's flatter tool_calls format
            if not msg.get("tool_calls"):
                return msg.get("content", "")

            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                print(f"  → {func_name}({args})")
                
                if func_name in TOOL_MAP:
                    result = TOOL_MAP[func_name].run(args)
                else:
                    result = f"Error: Tool {func_name} does not exist."
                    
                print(f"  ← {result}")
                
                # CHANGED: Fed the result back using the standard 'tool' role
                messages.append({
                    "role": "tool",
                    "content": str(result),
                })


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    agent = TravelAgent()

    queries = [
        "What are some good hotels in Tokyo?",
        "Can you find me a nice restaurant in Paris?",
        "What is the current time in Paris?",
    ]

    for query in queries:
        answer = agent.run(query)
        print(f"\nAgent: {answer}")
        print("─" * 60)
