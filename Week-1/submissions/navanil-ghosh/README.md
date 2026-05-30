# Travel Agent 

**Domain:** Travel & Hospitality
**Description:** A ReAct-based AI agent that assists users with planning trips. It strictly relies on internal tools to prevent hallucination.

## Tools Used
1. `get_weather`: Fetches current weather conditions for a given city.
2. `recommend_hotels`: Suggests hotels based on a city and budget tier (budget, mid-range, luxury).
3. `convert_currency`: Converts amounts between USD, EUR, JPY, and INR.

## Sample Output
**User:** I have Rs.500 , how much is that in JPY?
**Agent:** 500 INR is approximately 937.50 JPY.
------------------------------------------------------------

**User:** I'm going to Paris. suggest mid-range hotel options?
**Agent:** Recommended mid-range hotel in Paris: Lumios Hotel (Rs.18,000/night)
------------------------------------------------------------

**User:** Tell me about the weather in kolkata
**Agent:** 100°F (38°C), Sunny and humid weather.
------------------------------------------------------------
