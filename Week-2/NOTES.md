# Week 2 — Tool Use & Function Calling

**Dates:** Jun 2 – Jun 8

---

## What We're Building This Week

Last week you built an agent with 3 fake tools and hardcoded data.

This week you'll understand **how tool calling actually works under the hood**, wire up **real APIs**, use **typed inputs with Pydantic** so your tools don't break silently, and build an agent that calls tools in the right order based on what the user asks.

By the end of this week, you'll understand the thing that separates a toy agent from a real one.

---

## 1. How Tool Calling Actually Works

Here's the thing most tutorials skip: **the LLM doesn't actually call your function.**

You do.

Here's the real flow:

```
You → "What's the weather in Mumbai?" → Claude

Claude → thinks → "I should call get_weather. Here's the input:"
        {
          "tool": "get_weather",
          "input": { "city": "Mumbai" }
        }

You → see that Claude wants to call a tool
You → actually run get_weather("Mumbai")
You → send the result back to Claude

Claude → reads the result → responds to the user
```

The model never runs any code. It just says "I want to call X with these inputs." Your code executes X and passes the result back.

This is why the ReAct loop from Week 1 has a `while True` — you keep looping until the model stops asking for tool calls.

---

## 2. Why Pydantic?

Last week your tools looked like this:

```python
def get_product_price(product_name: str) -> str:
    ...
```

That's fine. But what happens when Claude sends:

```json
{ "product_name": 42 }
```

Or:

```json
{ "productName": "iPhone" }
```

Your function silently gets the wrong input. It fails with a cryptic error, or worse, returns wrong data.

**Pydantic** solves this. It's a library that:
- Validates input types at runtime (not just at type-check time)
- Coerces values where possible (e.g. `"42"` → `42` if you asked for an int)
- Throws a clear error with the exact field and reason when something is wrong

Think of it as a bouncer for your function's inputs.

```python
from pydantic import BaseModel

class WeatherInput(BaseModel):
    city: str
    unit: str = "celsius"   # optional with a default

# This works
WeatherInput(city="Mumbai")

# This also works — pydantic coerces
WeatherInput(city="Mumbai", unit="fahrenheit")

# This FAILS with a clear error
WeatherInput(city=123)  # city must be a string
```

---

## 3. Structured Outputs — Getting JSON Back From Claude

Sometimes you don't want a conversational response. You want **structured data**.

Example: you're extracting product info from a review and need it as a Python dict with guaranteed fields.

Without structured output:
```
"The product is an iPhone 15, costs around ₹80,000 and has 4.5 stars."
```

With structured output:
```json
{
  "product": "iPhone 15",
  "price": 80000,
  "rating": 4.5
}
```

How? You define the shape with Pydantic and tell Claude to match it:

```python
from pydantic import BaseModel
from langchain_groq import ChatGroq
from dotenv import load_dotenv

class ProductReview(BaseModel):
    product: str
    price: int
    rating: float
    sentiment: str   # "positive", "negative", "neutral"

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

structured_llm = llm.with_structured_output(ProductReview)
review_text = "I bought the iPhone 15 for about 80k. It's amazing, easily 4.5/5."

response = llm.invoke(review_text)
print(response.content)

structured_response=structured_llm.invoke(review_text)

print(structured_response.product) # type: ignore
print(structured_response.price) # type: ignore
print(structured_response.rating) # type: ignore
print(structured_response.sentiment) # type: ignore
```

---

## 4. Connecting to Real APIs

Last week: hardcoded dictionaries.
This week: real HTTP calls.

Here's the pattern. We'll use [wttr.in](https://wttr.in) — a free weather API, no key needed:

```python
import requests
from pydantic import BaseModel

class WeatherInput(BaseModel):
    city: str
    unit: str = "celsius"

# Function to fetch weather information
def get_weather(city: str, unit: str = "celsius") -> str:
    """
    Fetch current weather data from wttr.in API.

    Parameters:
    city (str)  -> Name of the city
    unit (str)  -> Temperature unit ("celsius" or "fahrenheit")

    Returns:
    str -> Formatted weather information
    """

    # API format parameter
    # "j1" tells wttr.in to return data in JSON format
    fmt = "j1"

    # Send GET request to wttr.in API
    # Example URL:
    # https://wttr.in/Delhi?format=j1
    response = requests.get(
        f"https://wttr.in/{city}?format={fmt}",
        timeout=5  # wait maximum 5 seconds
    )

    # Raise an error if request failed
    # Example:
    # 404 error
    # connection error
    # server error
    response.raise_for_status()

    # Convert JSON response into Python dictionary
    data = response.json()

    # Extract current weather information
    # "current_condition" is a list
    # [0] gets first item from that list
    current = data["current_condition"][0]

    # Select temperature unit
    # If unit is "celsius", use temp_C
    # Otherwise use temp_F
    temp = (
        current["temp_C"]
        if unit == "celsius"
        else current["temp_F"]
    )

    # Extract weather description
    # Example:
    # "Sunny"
    # "Partly cloudy"
    desc = current["weatherDesc"][0]["value"]

    # Return formatted weather string
    # Example:
    # "32°C, Sunny in Delhi"
    return (
        f"{temp}°"
        f"{'C' if unit == 'celsius' else 'F'}, "
        f"{desc} in {city}"
    )


# Call the function
weather = get_weather("Delhi")

# Print output
print(weather)
```

Key things to notice:
- `timeout=5` — never make an HTTP call without a timeout. Your agent will hang forever otherwise.
- `raise_for_status()` — throws an exception if the API returns 4xx/5xx. Catch this in your tool and return a useful error string to the agent.
- The function still returns a `str` — that's what you send back to Claude as the tool result.

---

## 5. Typed Tool Registry — The Right Way to Build This

In Week 1, tools were scattered — the function here, the definition there. Let's clean that up.

Here's a pattern that keeps everything in one place and uses Pydantic for validation:

```python
from pydantic import BaseModel
from typing import Callable, Any
import requests
from langchain_groq import ChatGroq
from dotenv import load_dotenv

class WeatherInput(BaseModel):
    city: str


class SearchInput(BaseModel):
    query: str
    max_results: int = 3


def get_weather(city: str) -> str:

    try:

        res = requests.get(
            f"https://wttr.in/{city}?format=3",
            timeout=5
        )

        res.raise_for_status()

        return res.text.strip()

    except requests.RequestException as e:

        return f"Weather lookup failed: {e}"


def search_web(query: str, max_results: int = 3) -> str:

    try:

        url = "https://html.duckduckgo.com/html/"

        res = requests.post(
            url,
            data={"q": query},
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        res.raise_for_status()

        html = res.text

        # VERY simple parsing
        lines = []

        for line in html.split("\n"):

            if 'result__title' in line:

                cleaned = (
                    line
                    .replace("<a", "")
                    .replace("</a>", "")
                    .strip()
                )

                lines.append(cleaned)

            if len(lines) >= max_results:
                break

        if not lines:
            return "No results found."

        return "\n".join(
            f"• {line}"
            for line in lines
        )

    except requests.RequestException as e:

        return f"Search failed: {e}"

# 2. One class per tool
class Tool:

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        func: Callable[..., str],
    ):

        self.name = name
        self.description = description
        self.input_model = input_model
        self.func = func

    def run(self, raw_input: dict[str, Any]) -> str:

        validated = self.input_model(**raw_input)

        return self.func(
            **validated.model_dump()
        )

    def to_groq_tool(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }

#Now you define tools like this:

TOOLS = [

    Tool(
        "get_weather",
        "Get current weather for a city.",
        WeatherInput,
        get_weather,
    ),

    Tool(
        "search_web",
        "Search the web for a query.",
        SearchInput,
        search_web,
    ),
]

TOOL_MAP = {
    t.name: t
    for t in TOOLS
}

```
---

## 6. Full Example — Research Agent With Real APIs

```python
"""
Week 2 — Research Agent
Uses 2 real APIs: wttr.in (weather) + DuckDuckGo search (no key needed)
"""

import json
import requests
from pydantic import BaseModel
from typing import Callable, Any
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage,ToolMessage


# ── Tool inputs ──────────────────────────────────────────────
class WeatherInput(BaseModel):
    city: str


class SearchInput(BaseModel):
    query: str
    max_results: int = 3


# ── Real API functions ────────────────────────────────────────


def get_weather(city: str) -> str:

    try:

        res = requests.get(
            f"https://wttr.in/{city}?format=3",
            timeout=5
        )

        res.raise_for_status()

        return res.text.strip()

    except requests.RequestException as e:

        return f"Weather lookup failed: {e}"


def search_web(query: str, max_results: int = 3) -> str:

    try:

        url = "https://html.duckduckgo.com/html/"

        res = requests.post(
            url,
            data={"q": query},
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        res.raise_for_status()

        html = res.text

        # VERY simple parsing
        lines = []

        for line in html.split("\n"):

            if 'result__title' in line:

                cleaned = (
                    line
                    .replace("<a", "")
                    .replace("</a>", "")
                    .strip()
                )

                lines.append(cleaned)

            if len(lines) >= max_results:
                break

        if not lines:
            return "No results found."

        return "\n".join(
            f"• {line}"
            for line in lines
        )

    except requests.RequestException as e:

        return f"Search failed: {e}"


# ── Tool class ────────────────────────────────────────────────

class Tool:

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        func: Callable[..., str],
    ):

        self.name = name
        self.description = description
        self.input_model = input_model
        self.func = func

    def run(self, raw_input: dict[str, Any]) -> str:

        validated = self.input_model(**raw_input)

        return self.func(
            **validated.model_dump()
        )

    def to_groq_tool(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }


# ── Registry ──────────────────────────────────────────────────

TOOLS = [

    Tool(
        "get_weather",
        "Get current weather for a city.",
        WeatherInput,
        get_weather,
    ),

    Tool(
        "search_web",
        "Search the web for a query.",
        SearchInput,
        search_web,
    ),
]

TOOL_MAP = {
    t.name: t
    for t in TOOLS
}


# ── Agent ─────────────────────────────────────────────────────


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Bind tools to model
llm_with_tools = llm.bind_tools(
    [t.to_groq_tool() for t in TOOLS]
)


class ResearchAgent:

    def run(self, user_message: str):

        print(f"\nUser: {user_message}")

        messages = [
            HumanMessage(content=user_message)
        ]

        while True:

            # Call LLM
            response = llm_with_tools.invoke(messages)

            messages.append(response) # type: ignore

            # If no tool calls → final answer
            if not response.tool_calls:

                return response.content

            # Execute tool calls
            for tool_call in response.tool_calls:

                tool_name = tool_call["name"]

                tool_args = tool_call["args"]

                print(f"→ {tool_name}({tool_args})")

                result = TOOL_MAP[tool_name].run(tool_args)

                print(f"← {result}")

                # Send tool result back
                messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"],
                    ) # type: ignore
                )


agent = ResearchAgent()

queries = [

    "What's the weather in Delhi and Mumbai right now?",

    "Search for recent AI safety news and summarize them."
]

for q in queries:

    result = agent.run(q)

    print("\nFinal Answer:")
    print(result)

    print("-" * 60)
```

---

## 7. When Does Claude Call a Tool vs Just Reply?

This is one of the most important things to understand.

Claude uses your **tool description** to decide. Vague descriptions → wrong decisions.

| Bad description | Good description |
|---|---|
| `"Get info"` | `"Fetch real-time stock price for a ticker symbol from Yahoo Finance"` |
| `"Search"` | `"Search the web for recent news articles on a topic. Use this when the user asks about current events or recent information."` |
| `"Weather"` | `"Get current temperature and conditions for a city. Always use this tool — do not guess weather."` |

**Always use this when** in your description is a powerful phrase. It tells Claude: don't try to answer from memory, use this tool.

---

## Week 2 Deliverable

**Harder than Week 1.**

Build a **typed research or productivity agent** that:

1. Uses **2 real APIs** (not hardcoded data)
2. All tool inputs validated with **Pydantic BaseModel**
3. Uses the **Tool class pattern** from Section 5 (not scattered functions)
4. Handles **API errors gracefully** — tool should return an error string, not crash
5. Add **type hints everywhere** — function args, return types, class attributes

**Bonus challenge:** Add a third tool that chains off the first two. Example: search for a city → get weather for it → summarise both.

Submit in `submissions/your-name/` with a README showing 3 sample runs and their outputs.
