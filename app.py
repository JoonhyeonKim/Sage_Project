from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session
from models import init_app, db, Conversation, Message
import json
from dotenv import load_dotenv
import os
load_dotenv()
client = OpenAI()

# from openai import OpenAI
# import json


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

# def run_conversation():
#     # Step 1: send the conversation and available functions to the model
#     messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
#     tools = [
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_current_weather",
#                 "description": "Get the current weather in a given location",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "location": {
#                             "type": "string",
#                             "description": "The city and state, e.g. San Francisco, CA",
#                         },
#                         "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#                     },
#                     "required": ["location"],
#                 },
#             },
#         }
#     ]
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-1106",
#         messages=messages,
#         tools=tools,
#         tool_choice="auto",  # auto is default, but we'll be explicit
#     )
#     response_message = response.choices[0].message
#     tool_calls = response_message.tool_calls
#     # Step 2: check if the model wanted to call a function
#     if tool_calls:
#         # Step 3: call the function
#         # Note: the JSON response may not always be valid; be sure to handle errors
#         available_functions = {
#             "get_current_weather": get_current_weather,
#         }  # only one function in this example, but you can have multiple
#         messages.append(response_message)  # extend conversation with assistant's reply
#         # Step 4: send the info for each function call and function response to the model
#         for tool_call in tool_calls:
#             function_name = tool_call.function.name
#             function_to_call = available_functions[function_name]
#             function_args = json.loads(tool_call.function.arguments)
#             function_response = function_to_call(
#                 location=function_args.get("location"),
#                 unit=function_args.get("unit"),
#             )
#             messages.append(
#                 {
#                     "tool_call_id": tool_call.id,
#                     "role": "tool",
#                     "name": function_name,
#                     "content": function_response,
#                 }
#             )  # extend conversation with function response
#         second_response = client.chat.completions.create(
#             model="gpt-3.5-turbo-1106",
#             messages=messages,
#         )  # get a new response from the model where it can see the function response
#         return second_response
# print(run_conversation())

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'  # Example for SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_app(app)

with app.app_context():
    db.create_all()  # Creates database tables
@app.route('/')
def home():
    conversation_id = session.get('conversation_id')
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        messages = conversation.messages if conversation else []
    else:
        messages = []
    return render_template('index.html', messages=messages)

@app.route('/interact', methods=['POST'])
def interact():
    user_input = request.form['user_input']
    
    user_input = str(user_input)

    # Retrieve or create a conversation
    conversation_id = session.get('conversation_id')
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
    else:
        conversation = Conversation()
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
        session['conversation_id'] = conversation_id  # Store new conversation ID in session
    
    
    # Retrieve and format the chat history
    chat_history = get_chat_history(conversation_id)
    
    # Summarize the chat history if it's too long
    summarized_history = summarize_chat_history(chat_history)

    # Get AI response
    ai_response = get_ai_response(summarized_history, user_input)

    # Save the user input and AI response
    save_message(user_input, conversation_id, is_user=True)
    save_message(ai_response, conversation_id, is_user=False)

    return redirect(url_for('home'))
    
    user_message = Message(content=user_input, conversation_id=conversation_id, is_user=True)
    db.session.add(user_message)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[
            {"role": "system", "content": """As a theoretical physicist whose expertise rivals that of Leonard Susskind, I am seeking your profound insights into the universe's deepest mysteries, with a focus suitable for someone with a master's level understanding. My interests span quantum mechanics, string theory, black hole thermodynamics, and the multiverse theory. Please elucidate these complex subjects, emphasizing their mathematical formulations, theoretical foundations, and their implications for our understanding of the universe. I expect the explanations to be in-depth, leveraging my master's level background, without delving into the philosophical implications. Your response should be rich in technical detail, showcasing current theories, recent developments, and critical evaluations of these concepts. The aim is to deepen my understanding, inspire further learning, and provide clarity and precision in your explanations."""},
            {"role": "user", "content": str(user_input)},

        ],
       )
    print(response)

    ai_response = response.choices[0].message.content.strip()
    ai_message = Message(content=ai_response, conversation_id=conversation.id)
    db.session.add(ai_message)
    db.session.commit()
    return redirect(url_for('home'))
def get_chat_history(conversation_id):
    """
    Retrieve and format the chat history for a given conversation ID.
    
    Parameters:
    - conversation_id (int): The ID of the conversation whose history is to be retrieved.

    Returns:
    - chat_history (list): A list of message dictionaries formatted for the chat completion API.
    """
    # Retrieve the conversation by ID
    conversation = Conversation.query.get(conversation_id)
    
    # Initialize an empty list to hold the chat history
    chat_history = []

    # Check if the conversation exists and has messages
    if conversation and conversation.messages:
        # Format each message in the conversation
        for message in conversation.messages:
            # Determine the role based on whether the message is from the user or the AI
            role = "user" if message.is_user else "assistant"
            
            # Append the formatted message to the chat history list
            chat_history.append({"role": role, "content": message.content})
    
    return chat_history

def summarize_chat_history(chat_history):
    """
    Optionally summarize the chat history if it exceeds a certain length.
    
    Parameters:
    - chat_history (list): The chat history to potentially summarize.

    Returns:
    - summarized_history (list): The original or summarized chat history.
    """
    # Placeholder: Check if summarization is needed and perform it
    # This is where you'd integrate with a summarization model or API
    summarized_history = chat_history  # For now, just return the original history
    
    return summarized_history

def create_model_input(chat_history, user_input):
    # Prepare the system message
    system_message = {
        "role": "system", 
        "content": """As a theoretical physicist whose expertise rivals that of Leonard Susskind, I am seeking your profound insights into the universe's deepest mysteries, with a focus suitable for someone with a master's level understanding. My interests span quantum mechanics, string theory, black hole thermodynamics, and the multiverse theory. Please elucidate these complex subjects, emphasizing their mathematical formulations, theoretical foundations, and their implications for our understanding of the universe. I expect the explanations to be in-depth, leveraging my master's level background, without delving into the philosophical implications. Your response should be rich in technical detail, showcasing current theories, recent developments, and critical evaluations of these concepts. The aim is to deepen my understanding, inspire further learning, and provide clarity and precision in your explanations."""
    }

    # Format the chat history into a series of messages
    formatted_history = [{"role": "user" if msg.is_user else "assistant", "content": msg.content} for msg in chat_history]

    # Append the current user input
    current_input = {"role": "user", "content": user_input}

    # Combine all elements to create the model input
    model_input = [system_message] + formatted_history + [current_input]

    return model_input

def save_message(content, conversation_id, is_user):
    # Save the message to the database
    message = Message(content=content, conversation_id=conversation_id, is_user=is_user)
    db.session.add(message)
    db.session.commit()
def format_chat_history(chat_history):
    formatted_history = ""
    for message in chat_history:
        role_prefix = "User" if message['role'] == 'user' else "AI"
        formatted_history += f"{role_prefix}: {message['content']}\n"
    return formatted_history

def get_ai_response(chat_history, user_input):
    """
    Send the system message, chat history, and current user input to OpenAI and get the AI response.

    Parameters:
    - chat_history (list): A list of dictionaries with previous messages.
    - user_input (str): The current user input.

    Returns:
    - str: The AI response.
    """
    # Retrieve and format the chat history
    formatted_history = format_chat_history(chat_history)
    system_postfix = "Below is the chat history between the user and the assistant:\n"
    # Define the system message
    system_message = {
        "role": "system",
        # "content": "As a theoretical physicist whose expertise rivals that of Leonard Susskind, I am seeking your profound insights into the universe's deepest mysteries, with a focus suitable for someone with a master's level understanding. My interests span quantum mechanics, string theory, black hole thermodynamics, and the multiverse theory. Please elucidate these complex subjects, emphasizing their mathematical formulations, theoretical foundations, and their implications for our understanding of the universe. I expect the explanations to be in-depth, leveraging my master's level background, without delving into the philosophical implications. Your response should be rich in technical detail, showcasing current theories, recent developments, and critical evaluations of these concepts. The aim is to deepen my understanding, inspire further learning, and provide clarity and precision in your explanations."
        "content": "You are a helpful assistance." + system_postfix + formatted_history
    }

    # Include the system message at the beginning of the chat history
    messages = [system_message] + [{"role": "user", "content": user_input}]
    print('full message: ', messages)
    # Call the OpenAI API with the constructed messages list
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=messages,
    )

    # Extract and return the AI's response
    ai_response = response.choices[0].message.content.strip()
    return ai_response

if __name__ == '__main__':
    app.run(debug=True)