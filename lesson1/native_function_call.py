
from openai import OpenAI
import requests
import json


import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3-haiku"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

user_question = input("Ask something: ")

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user",
        "content": user_question
    }
]


tools = [

    {
        "type": "function",
        "function": {
            "name": "search_for_capital_city",
            "description": "Get the capital city of a country",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Name of the country"
                    }
                },
                "required": ["country"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_book",
            "description": "Get the book title",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_terms":{
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List search terms to find books"
                    }
                },
                "required": ["search_terms"]
            }
        }

    }

]


# tools implementation

#Capital city
def get_capital_city(country):
    database = {
        "France": "Paris",
        "Cambodia": "Phnom Penh",
        "Japan": "Tokyo",
        "USA": "Washington D.C."
    }
    return database.get(country, "Unknown")


# books
def search_book(search_terms):
    search_query = search_terms[0]
    response = requests.get(
        "https://gutendex.com/books",
        params={"search": search_query}
    )
    results = []

    print("SEARCH QUERY:", search_query)
    print("RESULT COUNT:", len(results))
    print("RESULTS:", results[:2])

    for book in response.json().get("results", []):

        results.append({
            "id": book.get("id"),
            "title": book.get("title"),
            "authors": book.get("authors"),
        })

    return results



# Agent loop
while True:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )

    message = response.choices[0].message

    messages.append(message)

    # final response
    if not message.tool_calls:
        print("\nFinal Answer:\n", message.content)
        break


    # tools calls
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)


        # for tool 1
        if name == "search_for_capital_city":
            result = get_capital_city(args["country"])

            tool_response = {
                "capital" : result
            }


        #tool 2
        elif name == "search_book":
            result = search_book(args["search_terms"])

            tool_response = result


        else:
            tool_response = {
                "error": "unknown tool"
            }

        # tool result message
        messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": json.dumps(tool_response)
        })

