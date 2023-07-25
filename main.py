import streamlit as st
from decouple import config
import openai
import json
from functions import get_amazon_product

response = False
prompt_tokens = 0
completion_tokes = 0
total_tokens_used = 0
cost_of_response = 0

API_KEY = config('OPENAI_API_KEY')
openai.api_key = API_KEY


def make_request(question_input: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "I want you to act as a highly knowledgeable retail worker who specializes in all products available on Amazon.com. Ask questions individually of their requirements. Start by first asking their budget. After finding their requirements, suggest the most suitable product from Amazon.com for them. Please provide the Amazon product link. Remember to highlight the product's key features and how it meets the user's specified needs. Be sure to communicate in a friendly, professional tone that reflects excellent customer service. Only ask one question per message."},
            {"role": "user", "content": f"{question_input}"},
        ],
        functions=[
            {
                "name": "get_amazon_product",
                "description": "Search for a product relating to the user's needs on Amazon.com and return the link to the product. Use this python function as needed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Succint search query of the product the user may want.",
                        },
                    },
                    "required": ["query"],
                },
            }
        ],
        function_call="auto",
    )
    return response


st.header("Streamlit + OpenAI ChatGPT API")

st.markdown("""---""")

question_input = st.text_input("Enter question")
rerun_button = st.button("Rerun")

st.markdown("""---""")

if question_input:
    response = make_request(question_input)
else:
    pass

if rerun_button:
    response = make_request(question_input)
else:
    pass

if response:
    message = response["choices"][0]["message"]
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        function_args = json.loads(message["function_call"]["arguments"])

    function_response = get_amazon_product(function_args["query"])

    second_response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "user", "content": f"{question_input}"},
            message,
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            },
        ],
    )
    response = second_response
    st.write("Response:")
    st.write(response["choices"][0]["message"]["content"])

    prompt_tokens = response["usage"]["prompt_tokens"]
    completion_tokes = response["usage"]["completion_tokens"]
    total_tokens_used = response["usage"]["total_tokens"]

    cost_of_response = total_tokens_used * 0.000002
else:
    pass


with st.sidebar:
    st.title("Usage Stats:")
    st.markdown("""---""")
    st.write("Promt tokens used :", prompt_tokens)
    st.write("Completion tokens used :", completion_tokes)
    st.write("Total tokens used :", total_tokens_used)
    st.write("Total cost of request: ${:.8f}".format(cost_of_response))
