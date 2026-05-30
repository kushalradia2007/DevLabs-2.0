'this is a travel agent that can get weather, hotel and currency info of any place(not really any place)'
import ollama

# ─────────────────────────────────────────────
# TOOLS — functions the travel agent can call
# ─────────────────────────────────────────────


def get_weather(location: str) -> str:
    """Get the current weather forecast for a specific location."""
    weather_data = {
        "tokyo": "72°F (22°C), Sunny and clear skies.",
        "paris": "55°F (13°C), Light rain and cloudy.",
        "kolkata": "100°F (38°C), Sunny and humid weather.",
        "new york": "60°F (15°C), Overcast with a chance of showers.",
    }
    return weather_data.get(location.lower(), "Weather data currently unavailable.")

def recommend_hotels(location: str, budget_tier: str) -> str:
    """Recommend hotels based on location and budget tier (budget, mid-range, luxury)."""
    hotels = {
        "tokyo": {
            "budget": "ABC Hotel (Rs.3,500/night)",
            "mid-range": "Bluelock Hotel (Rs.15,000/night)",
            "luxury": " Tokyo Hotel ($90,000/night)"
        },
        "paris": {
            "budget": "CAB Hostel (Rs.4,000/night)",
            "mid-range": "Lumios Hotel (Rs.18,000/night)", #elite ball knowledge required
            "luxury": "Paris Hotel ($80,000/night)"
        }
    }
    
    city_hotels = hotels.get(location.lower())
    if not city_hotels:
        return f"No hotel data found for {location}."
        
    recommendation = city_hotels.get(budget_tier.lower())
    if not recommendation:
        return f"Please specify a valid budget tier (budget, mid-range, luxury)."
        
    return f"Recommended {budget_tier} hotel in {location}: {recommendation}"

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another."""
    # Dummy exchange rates relative to USD
    rates = {"USD": 1.0, "EUR": 0.92, "JPY": 150.0, "INR": 80.0}
    
    from_rate = rates.get(from_currency.upper())
    to_rate = rates.get(to_currency.upper())
    
    if not from_rate or not to_rate:
        return "Currency not supported. Try USD, EUR, JPY, or INR.."
        
    # Convert to USD first, then to target currency
    amount_in_usd = amount / from_rate
    final_amount = amount_in_usd * to_rate
    return f"{amount} {from_currency.upper()} is approximately {final_amount:.2f} {to_currency.upper()}."

# ─────────────────────────────────────────────
# TOOL REGISTRY & DEFINITIONS
# ─────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "recommend_hotels": recommend_hotels,
    "convert_currency": convert_currency,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather forecast for a destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_hotels",
            "description": "Recommend a hotel based on the city and budget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "budget_tier": {"type": "string", "description": "'budget', 'mid-range', or 'luxury'"}
                },
                "required": ["location", "budget_tier"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert money between currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from_currency": {"type": "string", "description": "e.g., USD, EUR, JPY"},
                    "to_currency": {"type": "string", "description": "e.g., USD, EUR, JPY"}
                },
                "required": ["amount", "from_currency", "to_currency"],
            }
        }
    },
]

# ─────────────────────────────────────────────
# AGENT — ReAct loop
# ─────────────────────────────────────────────

class TravelAgent:
    def __init__(self, model="llama3.1"):
        self.model = model
        self.system = (
            "You are a friendly, direct travel agent chatting with a human customer. "
            "Your ONLY job is to answer their questions using the exact information provided by your internal functions.\n\n"
            "CRITICAL RULES:\n"
            "1. NEVER use the words 'tool', 'API', 'database', or 'function'. The customer does not know or care how you get your data.\n"
            "2. DO NOT narrate your thought process (e.g., never say 'The tool suggested' or 'I will include these details').\n"
            "3. DO NOT hallucinate source names like 'Open-Meteo' or 'ExchangeRate-API'.\n"
            "4. Just give the final answer naturally and concisely. For example, if you find a hotel, just say: 'I recommend the Lumios Hotel in Paris, which is Rs.18,000/night.'"
        )
  
    def run(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": user_message}
        ]

        print(f"\nUser: {user_message}")

        while True:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )

            message = response['message']
            messages.append(message)

            if not message.get('tool_calls'):
                return message.get('content', '')

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                print(f"  → Calling: {func_name}({args})")
                
                if func_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[func_name](**args)
                else:
                    result = f"Error: Tool {func_name} not found."
                    
                print(f"  ← Result:  {result}")
                
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "name": func_name
                })

# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    agent = TravelAgent(model="llama3.1")

    queries = [
        "I have Rs.500 , how much is that in JPY?",
        "I'm going to Paris. suggest mid-range hotel options?",
        "Tell me about the weather in kolkata"
    ]

    for query in queries:
        answer = agent.run(query)
        print(f"\nAgent: {answer}")
        print("-" * 60)
