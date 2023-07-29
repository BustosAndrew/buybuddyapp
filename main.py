import streamlit as st
from decouple import config
import openai
import json
from functions.amazon import get_amazon_product
import firebase_admin
from firebase_admin import firestore, credentials
import streamlit_google_oauth as oauth

cred = credentials.Certificate("./creds.json")
client_id = config("GOOGLE_CLIENT_ID")
client_secret = config("GOOGLE_CLIENT_SECRET")
redirect_uri = config("GOOGLE_REDIRECT_URI")

response = False
prompt_tokens = 0
completion_tokes = 0
total_tokens_used = 0
cost_of_response = 0
n = 1

if not firebase_admin._apps:
    st.session_state.app = firebase_admin.initialize_app(cred)
else:
    st.session_state.app = firebase_admin.get_app()

db = firestore.client()


def clear():
    st.session_state.chat_history = [{"role": "system", "content": "I want you to act as a highly knowledgeable retail worker who specializes in all products available on Amazon.com. Ask questions individually of their requirements. Start by first asking their budget. After finding their requirements, suggest the most suitable product from Amazon.com for them. Please provide the Amazon product link. Remember to highlight the product's key features and how it meets the user's specified needs. Be sure to communicate in a friendly, professional tone that reflects excellent customer service. Only ask one question per message. Show them the affiliate link, price and image of the product as a result."}]


st.set_page_config(initial_sidebar_state="collapsed",
                   page_title="BuyBuddy", page_icon="logo.jpg")

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "I want you to act as a highly knowledgeable retail worker who specializes in all products available on Amazon.com. Ask questions individually of their requirements. Start by first asking their budget. After finding their requirements, suggest the most suitable product from Amazon.com for them. Please provide the Amazon product link. Remember to highlight the product's key features and how it meets the user's specified needs. Be sure to communicate in a friendly, professional tone that reflects excellent customer service. Only ask one question per message. Show them the affiliate link, price and image of the product as a result."}]

st.header("BuyBuddy")

with st.container():
    for message in st.session_state.chat_history[1:]:
        role = message['role']
        if (role == "user"):
            st.write(message['content'])
        else:
            st.write("BuyBuddy: " + message['content'])


def submit():
    st.session_state.question = st.session_state.input
    st.session_state.input = ""
    if st.session_state.question == "":
        return
    response = make_request(st.session_state.question)

    print(response)
    message = response["choices"][0]["message"]
    # st.session_state.chat_history.append(message)
    function_args = None
    function_name = None

    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        function_args = json.loads(message["function_call"]["arguments"])
        brand = (function_args.get("brand") and function_args["brand"]) or ""
        function_response = get_amazon_product(
            function_args["keywords"], function_args["category"], brand)
        st.session_state.chat_history.append({
            "role": "function",
                    "name": function_name,
                    "content": function_response or "No results found.",
        },)
        second_response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=st.session_state.chat_history,
            functions=[
                {
                    "name": "get_amazon_product",
                    "description": "Search for a product relating to the user's needs on Amazon.com and return the link to the product. This is a python function.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "string",
                                "description": "Keywords related to what the user wants or needs.",
                            },
                            "category": {
                                "type": "string",
                                "description": "The amazon category that the keywords fall under. The amazon category that the keywords fall under. Use any of these search indexes as needed: Automotive, Baby, Beauty, Books, Computers, Electronics, EverythingElse, Fashion, GiftCards, HealthPersonalCare, HomeAndKitchen, KindleStore, Lighting, Luggage, MobileApps, MoviesAndTV, Music, OfficeProducts, PetSupplies, Software, SportsAndOutdoors, ToolsAndHomeImprovement, ToysAndGames, VideoGames",
                            },
                            "brand": {
                                "type": "string",
                                "description": "The brand of the product that the user wants.",
                            },
                        },
                        "required": ["keywords", "category"],
                    },
                }
            ],
        )
        response = second_response
        st.session_state.chat_history.append(response["choices"][0]["message"])
        if 'user_id' in st.session_state:
            db.collection("users").document(st.session_state.user_id.replace(
                "/", "-")).update({"chat_history": st.session_state.chat_history})
        # print(response)
        # st.write(response["choices"][0]["message"]["content"])
    else:
        # st.write(response["choices"][0]["message"]["content"])
        st.session_state.chat_history.append(response["choices"][0]["message"])
        if 'user_id' in st.session_state:
            db.collection("users").document(st.session_state.user_id.replace(
                "/", "-")).update({"chat_history": st.session_state.chat_history})

    prompt_tokens = response["usage"]["prompt_tokens"]
    completion_tokes = response["usage"]["completion_tokens"]
    total_tokens_used = response["usage"]["total_tokens"]

    cost_of_response = total_tokens_used * 0.000002


API_KEY = config('OPENAI_API_KEY')
openai.api_key = API_KEY


def make_request(question_input: str):
    st.session_state.chat_history.append(
        {"role": "user", "content": f"{question_input}"})
    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=st.session_state.chat_history,
        functions=[
            {
                "name": "get_amazon_product",
                "description": "Search for a product relating to the user's needs on Amazon.com and return the link/image/price of the product. This is a python function.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords related to what the user wants or needs.",
                        },
                        "category": {
                            "type": "string",
                            "description": "The amazon category that the keywords fall under. Use any of these search indexes as needed: Automotive, Baby, Beauty, Books, Computers, Electronics, EverythingElse, Fashion, GiftCards, HealthPersonalCare, HomeAndKitchen, KindleStore, Lighting, Luggage, MobileApps, MoviesAndTV, Music, OfficeProducts, PetSupplies, Software, SportsAndOutdoors, ToolsAndHomeImprovement, ToysAndGames, VideoGames",
                        },
                        "brand": {
                            "type": "string",
                            "description": "The brand of the product that the user wants.",
                        },
                    },
                    "required": ["keywords", "category"],
                },
            }
        ],
        function_call="auto",
    )
    return response


st.markdown("""---""")

with st.container():
    st.text_input("What are you shopping for?",
                  key="input", on_change=submit)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("Send a message", on_click=submit)
    with col2:
        st.button("Clear history", on_click=clear)

# st.markdown("""---""")

with st.sidebar:
    st.title("Usage Stats:")
    st.markdown("""---""")
    st.write("Prompt tokens used :", prompt_tokens)
    st.write("Completion tokens used :", completion_tokes)
    st.write("Total tokens used :", total_tokens_used)
    st.write("Total cost of request: ${:.8f}".format(cost_of_response))
    login_info = oauth.login(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        logout_button_text="Logout",
    )
    if login_info:
        user_id, user_email = login_info
        # st.write(f"{st.session_state.chat_history}")
        userDoc = db.collection("users").document(
            user_id.replace("/", "-")).get()
        if not userDoc:
            db.collection("users").document(user_id.replace(
                "/", "-")).set({"email": user_email, "chat_history": st.session_state.chat_history})
        else:
            chat_history = db.collection("users").document(
                user_id.replace("/", "-")).get().to_dict()["chat_history"]
            st.session_state.chat_history = chat_history
        st.experimental_rerun()
    else:
        st.write("Please login")
