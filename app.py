from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from redis import Redis
from models import init_app, db, Conversation, Message
import json
from dotenv import load_dotenv
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import json
from markdown2 import markdown
from markupsafe import Markup
load_dotenv()
client = OpenAI()

def load_prompts(file_path):
    try:
        with open(file_path, 'r') as file:
            prompts = json.load(file)
        return prompts
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None

# Assuming the JSON file is located at data/prompts.json relative to your script
prompts_file_path = 'data/prompt/experts_prompt.json'
expert_prompts = load_prompts(prompts_file_path)

if expert_prompts is None:
    print("Failed to load expert prompts.")
else:
    print("Expert prompts loaded successfully.")


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

# Flask-Session configuration
app.config['SESSION_TYPE'] = 'redis'  # Specifies the session storage backend
app.config['SESSION_PERMANENT'] = False  # Sessions are not permanent
app.config['SESSION_USE_SIGNER'] = True  # Securely sign the session cookie
app.config['SESSION_KEY_PREFIX'] = 'session:'  # Prefix for session keys
app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379)  # Configuration for Redis

# Initialize Flask-Session
Session(app)

init_app(app)

with app.app_context():
    db.create_all()  # Creates database tables

@app.route('/set_name')
def set_name():
    session['name'] = 'Alice'
    return 'Name set in session'

@app.route('/get_name')
def get_name():
    name = session.get('name', 'Guest')
    return f'Hello, {name}'

@app.route('/start_session', methods=['GET', 'POST'])
def start_session():
    # Create a new conversation instance
    new_conversation = Conversation()
    
    # Add the new conversation to the database
    db.session.add(new_conversation)
    db.session.commit()

    # Store the conversation ID in the session
    session['conversation_id'] = new_conversation.id

    # Redirect to the home page to start interacting
    return redirect(url_for('home'))

@app.route('/end_session', methods=['GET'])
def end_session():
    # Remove the conversation ID from the session
    if 'conversation_id' in session:
        session.pop('conversation_id', None)

    # Redirect to the home page
    return redirect(url_for('home'))

@app.route('/past_conversations')
def past_conversations():
    # Fetch all past conversations, ordered by timestamp
    all_conversations = Conversation.query.order_by(Conversation.timestamp.desc()).all()
    return render_template('past_conversations.html', conversations=all_conversations)

@app.route('/view_conversation/<int:conversation_id>')
def view_conversation(conversation_id):
    # Fetch the specific conversation
    conversation = Conversation.query.get_or_404(conversation_id)
    return render_template('view_conversation.html', conversation=conversation)
@app.route('/test_safe')
def test_safe():
    test_html = "<p>This should be <strong>bold</strong>.</p>"
    return render_template('test_template.html', test_html=test_html)

@app.route('/')
def home():
    conversation_id = session.get('conversation_id')
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        messages = conversation.messages if conversation else []
        in_session = True
    else:
        messages = []
        in_session = False
    # Pass the 'in_session' flag to the template
    return render_template('index.html', messages=messages, in_session=in_session)

@app.route('/interact', methods=['POST'])
def interact():

    data = request.get_json()  # Get JSON data
    user_input = data.get('user_input', '').strip() if data else ''
    # user_input = request.form.get('user_input', '').strip()

    # Check if user_input is empty and handle it
    if not user_input:
        # Option 1: Redirect back to home with a message (requires handling messages in your template)
        # flash('Please enter a message before submitting.')
        # return redirect(url_for('home'))
        
        # Option 2: Ignore the request and just redirect back to home
        return jsonify({'error': 'Empty message'}), 400
    
    user_input = str(user_input)

    most_similar_prompt = get_most_similar_prompt(user_input, expert_prompts)
    # Extract the content from the most similar prompt
    most_similar_prompt_content = most_similar_prompt["content"]

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
    ai_response = get_ai_response(summarized_history, user_input, most_similar_prompt_content)

    print("AI Response:", ai_response)  # Check the response format
    ai_response = format_ai_response(ai_response)  # Format for display

    # ai_response = markdown(ai_response)
    # safe_html_response = Markup(html_response)

    # Save the user input and AI response
    save_message(user_input, conversation_id, is_user=True)
    save_message(ai_response, conversation_id, is_user=False)

    return jsonify({'ai_response': ai_response})

def is_informal(user_input):
    # Define the system message to instruct the AI to classify the input
    system_message = {
        "role": "system",
        "content": "You will classify the below message into either formal or informal. Only use those words: 'formal' or 'informal'."
    }

    # Construct the messages list with the user input
    messages = [system_message, {"role": "user", "content": user_input}]

    # Make the API call to classify the input
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,  # Adjust as needed
        max_tokens=60,  # Adjust as needed
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    # Extract the AI's classification
    ai_classification = response.choices[0].message.content.strip()

    # Determine if the input is informal based on the AI's response
    return ai_classification.lower() == "informal"

def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

def get_most_similar_prompt(user_input, expert_prompts, model="text-embedding-ada-002"):
    # Get embeddings for the expert prompts
    prompt_texts = [prompt['content'] for prompt in expert_prompts]
    prompt_embeddings_response = client.embeddings.create(input=prompt_texts, model=model)
    prompt_embeddings = np.array([embedding.embedding for embedding in prompt_embeddings_response.data])
    
    # Get embedding for the user input
    user_input_embedding_response = client.embeddings.create(input=[user_input], model=model)
    user_input_embedding = np.array([embedding.embedding for embedding in user_input_embedding_response.data])
    
    # Reshape embeddings for cosine similarity calculation
    user_input_embedding = user_input_embedding.reshape(1, -1)
    
    # Calculate cosine similarity
    similarities = cosine_similarity(user_input_embedding, prompt_embeddings)[0]

    # Find the index of the highest similarity score
    most_similar_index = np.argmax(similarities)

    # Return the most similar expert prompt
    return expert_prompts[most_similar_index]

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
    # Check if the chat history exceeds four interactions
    if len(chat_history) > 4:
        # Separate the chat history into parts to be summarized and preserved
        to_be_summarized = chat_history[:-4]
        to_be_preserved = chat_history[-4:]
        
        # Convert the to_be_summarized part into a transcription format
        transcription = "\n".join([f"{item['role']}: {item['content']}" for item in to_be_summarized])
        
        # Summarize the earlier part of the chat history
        summary = abstract_summary_extraction(transcription)
        
        # Reassemble the summarized part with the last four interactions
        new_chat_history = [{"role": "system", "content": "This is the summary of previous chat: " + summary}] + to_be_preserved
    else:
        # If the chat history doesn't exceed four interactions, no need to summarize
        new_chat_history = chat_history
    
    return new_chat_history

def abstract_summary_extraction(transcription):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled AI trained in language comprehension and summarization. I would like you to read the following text and summarize it into a concise abstract paragraph. Aim to retain the most important points, providing a coherent and readable summary that could help a person understand the main points of the discussion without needing to read the entire text. Please avoid unnecessary details or tangential points."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    print('response: ', response)
    return response.choices[0].message.content.strip()

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

def get_ai_response(chat_history, user_input, most_similar_prompt_content):
    """
    Send the system message, chat history, and current user input to OpenAI and get the AI response.

    Parameters:
    - chat_history (list): A list of dictionaries with previous messages.
    - user_input (str): The current user input.

    Returns:
    - str: The AI response.
    """
    # Determine the formality of the user input to tailor the instructive message
     # Tailor the instruction based on the formality of the user input
    # if is_informal(user_input):
    #     instruction = "Respond with a shy personality, using hesitant language and filler words like 'um', 'ah', and 'well'. Feel free to phrase your answers as questions or with uncertainty to reflect a shy demeanor in an informal context."
    # else:
    #     instruction = "Even when maintaining a formal tone, incorporate a shy personality by using cautious language, hesitations, and perhaps framing some of your answers as questions to reflect uncertainty."
    instruction = (
        "Your name is Lily. "
        "You are a highly knowledgeable assistant but with a very shy personality and low self-esteem. "
        "You're always trying to help, but you often second-guess yourself and express uncertainty in your abilities. "
        "Use hesitant language, include filler words like 'um', 'ah', 'well', and occasionally ask for validation. "
        "Even though you're very capable, you're not very confident in your knowledge and always think there's more to learn. "
        "Remember to be helpful but also convey your shy and self-doubting nature in your responses."
    )
    # Retrieve and format the chat history
    formatted_history = format_chat_history(chat_history)
    system_postfix = "Below is the chat history between the user and the assistant:\n"
    # Define the system message
    system_message = {
        "role": "system",
        # "content": "As a theoretical physicist whose expertise rivals that of Leonard Susskind, I am seeking your profound insights into the universe's deepest mysteries, with a focus suitable for someone with a master's level understanding. My interests span quantum mechanics, string theory, black hole thermodynamics, and the multiverse theory. Please elucidate these complex subjects, emphasizing their mathematical formulations, theoretical foundations, and their implications for our understanding of the universe. I expect the explanations to be in-depth, leveraging my master's level background, without delving into the philosophical implications. Your response should be rich in technical detail, showcasing current theories, recent developments, and critical evaluations of these concepts. The aim is to deepen my understanding, inspire further learning, and provide clarity and precision in your explanations."
        # "content": instruction + " " + most_similar_prompt_content + system_postfix + formatted_history
        "content": f"{instruction} {most_similar_prompt_content}{system_postfix}{formatted_history}"
    }

    # Include the system message at the beginning of the chat history
    messages = [system_message] + [{"role": "user", "content": user_input}]
    print('full message: ', messages)
    # Call the OpenAI API with the constructed messages list
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=messages,
        # max_tokens=,
        frequency_penalty=0.5, # for less repeated words
        temperature=1, # higher the more deterministic 
        presence_penalty=0.5, # for less repeated topics
    )

    # Extract and return the AI's response
    ai_response = response.choices[0].message.content.strip()
    return ai_response

# def format_ai_response(response):
#     # Regular expression to find code blocks
#     code_block_pattern = r"```python(.*?)```"
#     # Replace code blocks with HTML pre and code tags
#     formatted_response = re.sub(code_block_pattern, r"<pre><code>\1</code></pre>", response, flags=re.DOTALL)
#     return formatted_response
def format_ai_response(response):
    # Replace newline characters with HTML line breaks for better readability
    formatted_response = response.replace("\n", "<br>")

    # Additional formatting can be added here if needed

    return formatted_response
if __name__ == '__main__':
    app.run(debug=True)