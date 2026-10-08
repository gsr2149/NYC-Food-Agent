# NYC Food Hunter 

NYC Food Hunter is an agent that will cure your indecisiveness when searching for food in NYC. With so many options, it is hard to choose but whether you are craving something specific or just want to be surpised, NYC Food Hunter can give you an answer. 


## Installation

**Requirements:** Python 3.10, a Gemini API key, and a Google Maps API key.

1. Clone the repo
   ```bash
   git clone https://github.com/gsr2149/nyc-food-agent.git
   cd nyc-food-agent

2. Create your virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt

3. Add your API Keys
cp .env.example .env

4. Open .env and fill in 
**GEMINI_API_KEY: get one at https://aistudio.google.com/apikey
**GOOGLE_MAPS_API: create your own in Google Cloud Console with Places API(New) and make sure it is enabled

5. Start the app 
python -m uvicorn main:app --port 8080 
open http://localhost:8080

## Tools 
| Tool | Usage |
|- - -|- - -|
| `search_restaurants` |: Sends the user's preferences to Places API as text search and returns up to five matching restaurants|
| `surprise_pick` |: Unique tool that has a set amount of cuisines and decides for a user that is unsure where they want to go |
| `estimate_total_cost` |: Calculates an estimate of how much the meal might be and depends on user prompts to be called asking for prices | 
| `suggest_cuisines` |: Similar to the `surprise_pick` tool that works to suggest food based off the user's mood |

## How To Use
Made for ease of use, just start the conversation with the agent once everything is loaded properly. If you are unsure of what to say, feel free to use the little discussion prompts to get a conversation started!

## Prompts for Testing/Grading the Agent and Activating Diffferent Tool Calls
1. "Where can I find cheap Thai food near the Financial District? 
2. "Can you pick something for me?" 
3. "Recommend a Japanese restaurant that is in Jersey City" (this one shouldn't work andf will bring up an error as this agent is localized to NYC area only)
4. "How much would a 2 person dinner at Izakaya Mew cost?" (have to tell the agent the price worth in $ amount first of the given restaurant)
5. "Any ideas on a cozy meal?" 