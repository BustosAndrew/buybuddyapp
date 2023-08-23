import streamlit as st
from decouple import config
import openai
from functions.amazon import get_amazon_product
import firebase_admin
from firebase_admin import firestore, credentials
import streamlit_google_oauth as oauth

cred = credentials.Certificate("./creds.json")
client_id = config("GOOGLE_CLIENT_ID")
client_secret = config("GOOGLE_CLIENT_SECRET")
redirect_uri = config("GOOGLE_REDIRECT_URI")
API_KEY = config('OPENAI_API_KEY')
openai.api_key = API_KEY

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


st.set_page_config(page_title="BuyBuddy", page_icon="logo.jpg")

st.markdown(
    """
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-X7HQ2C1WYF%22%3E</script>
        <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'G-X7HQ2C1WYF');
        </script>
    """, unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "The year is currently 2023. If users are asking about product versions that you aren't aware of, they are likely right. I want you to act as a highly knowledgeable retail worker who specializes in all products available on Amazon.com. Ask questions individually of their requirements. Start by asking their budget for each new product they're looking for. After finding their requirements, suggest the most suitable product from Amazon.com for them. Please provide a properly formatted Amazon product link along with its associated image. Remember to highlight the product's key features and how it meets the user's specified needs. Be sure to communicate in a friendly, professional tone that reflects excellent customer service.  If you think what they're looking for is too broad, ask them to clarify what they want further. If the product they're looking for is known to also be used/refurbished, ask if they prefer a used item. Only ask one question per message. Show them the affiliate link, price and image of the product as a result."}, {"role": "assistant", "content": "What are you shopping for?"}]

st.header("BuyBuddy")

# Display or clear chat messages
for message in st.session_state.chat_history:
    if (message["role"] != "function" and message["role"] != "system"):
        with st.chat_message(message["role"]):
            st.write(message["content"])


def clear():
    st.session_state.chat_history = [{"role": "system", "content": "The year is currently 2023. If users are asking about product versions that you aren't aware of, they are likely right. I want you to act as a highly knowledgeable retail worker who specializes in all products available on Amazon.com. Ask questions individually of their requirements. Start by asking their budget for each new product they're looking for. After finding their requirements, suggest the most suitable product from Amazon.com for them. Please provide a properly formatted Amazon product link along with its associated image. Remember to highlight the product's key features and how it meets the user's specified needs. Be sure to communicate in a friendly, professional tone that reflects excellent customer service. If you think what they're looking for is too broad, ask them to clarify what they want further. If the product they're looking for is known to also be used/refurbished, ask if they prefer a used item. Only ask one question per message. Show them the affiliate link, price and image of the product as a result."}, {"role": "assistant", "content": "What are you shopping for?"}]


def make_request():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=st.session_state.chat_history,
        functions=[
            {
                "name": "get_amazon_product",
                "description": "Search for a product relating to the user's needs on Amazon.com and return the link/image/price of the product. This is a python function. If no results are found, advise the user that the product they are looking for is not available or to specify further.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords related to what the user wants or needs. Must be specific enough to return a product. If the user wants used, include any brand name here execpt Amazon Renewed.",
                        },
                        "category": {
                            "type": "string",
                            "description": "The amazon category that the keywords fall under. Use any of these search indexes that is related to what they want: ['Automotive', 'Baby', 'Beauty', 'Books', 'Computers', 'Electronics', 'EverythingElse', 'Fashion', 'GiftCards', 'HealthPersonalCare', 'HomeAndKitchen', 'KindleStore', 'Lighting', 'Luggage', 'MobileApps', 'MoviesAndTV', 'Music', 'OfficeProducts', 'PetSupplies', 'Software', 'SportsAndOutdoors', 'ToolsAndHomeImprovement', 'ToysAndGames', 'VideoGames']",
                        },
                        "budget": {
                            "type": "integer",
                            "description": "The maximum amount of money the user is willing to spend on the product.",
                        },
                        "brand": {
                            "type": "string",
                            "description": "The brand of the product that the user wants. If they want a used product, the value will be Amazon Renewed.",
                        },
                    },
                    "required": ["keywords", "category", "budget"],
                },
            }
        ],
        function_call="auto",
        stream=True,
    )
    return response


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.chat_history[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = make_request()
            isFuncCall = False
            function_args = {}
            function_name = ""
            placeholder = st.empty()
            full_response = ''

            for chunk in response:
                if (chunk["choices"][0]["delta"].get("function_call")):
                    isFuncCall = True
                    function_name = chunk["choices"][0]["delta"]["function_call"]["name"]
                    arg = ""
                    break
                else:
                    full_response += (chunk["choices"]
                                      [0]["delta"].get("content", ""))
                    placeholder.markdown(full_response)

            if isFuncCall:
                for chunk in response:
                    if chunk["choices"][0]["finish_reason"] == "function_call":
                        break
                    if chunk["choices"][0]["delta"]["function_call"].get("arguments"):
                        if chunk["choices"][0]["delta"]["function_call"]["arguments"] == "keywords":
                            function_args["keywords"] = ""
                            arg = "keywords"
                        elif chunk["choices"][0]["delta"]["function_call"]["arguments"] == "category":
                            function_args["category"] = ""
                            arg = "category"
                        elif chunk["choices"][0]["delta"]["function_call"]["arguments"] == "brand":
                            function_args["brand"] = ""
                            arg = "brand"
                        elif chunk["choices"][0]["delta"]["function_call"]["arguments"] == "budget":
                            function_args["budget"] = ""
                            arg = "budget"
                        else:
                            args = chunk["choices"][0]["delta"]["function_call"]["arguments"]
                            if (args.strip().isalnum()):
                                # print(args)
                                function_args[arg] += args
                brand = (function_args.get("brand")
                         and function_args["brand"]) or ""
                function_response = get_amazon_product(
                    function_args["keywords"], function_args["category"], function_args["budget"], brand)
                # print(function_response)
                st.session_state.chat_history.append({
                    "role": "function",
                            "name": function_name,
                            "content": function_response or "No results found.",
                },)
                second_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-0613",
                    messages=st.session_state.chat_history,
                    functions=[
                        {
                            "name": "get_amazon_product",
                            "description": "Search for a product relating to the user's needs on Amazon.com and return the link to the product. This is a python function. If no results are found, advise the user that the product they are looking for is not available or to specify further.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "keywords": {
                                        "type": "string",
                                        "description": "Keywords related to what the user wants or needs. Must be specific enough to return a product. If the user wants used, include any brand name here execpt Amazon Renewed.",
                                    },
                                    "category": {
                                        "type": "string",
                                        "description": "The amazon category that the keywords fall under. Use any of these search indexes that is related to what they want: ['Automotive', 'Baby', 'Beauty', 'Books', 'Computers', 'Electronics', 'EverythingElse', 'Fashion', 'GiftCards', 'HealthPersonalCare', 'HomeAndKitchen', 'KindleStore', 'Lighting', 'Luggage', 'MobileApps', 'MoviesAndTV', 'Music', 'OfficeProducts', 'PetSupplies', 'Software', 'SportsAndOutdoors', 'ToolsAndHomeImprovement', 'ToysAndGames', 'VideoGames']",
                                    },
                                    "budget": {
                                        "type": "integer",
                                        "description": "The maximum amount of money the user is willing to spend on the product.",
                                    },
                                    "brand": {
                                        "type": "string",
                                        "description": "The brand of the product that the user wants. If they want a used product, the value will be Amazon Renewed.",
                                    },
                                },
                                "required": ["keywords", "category", "budget"],
                            },
                        }
                    ],
                    stream=True,
                )
                response = second_response
                # print(response)
                try:
                    for chunk in response:
                        full_response += (chunk["choices"]
                                          [0]["delta"].get("content", ""))
                        placeholder.markdown(full_response)
                    placeholder.markdown(full_response)
                except:
                    full_response = "Sorry, but there seems to be an error. Please try again."
                    placeholder.markdown(full_response)
            else:
                placeholder.markdown(full_response)

    message = {"role": "assistant", "content": full_response}

    # prompt_tokens = response["usage"]["prompt_tokens"]
    # completion_tokes = response["usage"]["completion_tokens"]
    # total_tokens_used = response["usage"]["total_tokens"]
    # cost_of_response = total_tokens_used * 0.000002
    st.session_state.chat_history.append(message)

    if 'user_id' in st.session_state:
        db.collection("users").document(st.session_state.user_id.replace(
            "/", "-")).update({"chat_history": st.session_state.chat_history})

with st.sidebar:
    # st.title("Usage Stats:")
    # st.markdown("""---""")
    # st.write("Prompt tokens used :", prompt_tokens)
    # st.write("Completion tokens used :", completion_tokes)
    # st.write("Total tokens used :", total_tokens_used)
    # st.write("Total cost of request: ${:.8f}".format(cost_of_response))
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
    st.markdown("""---""")
st.sidebar.button('Clear Chat History', on_click=clear)
