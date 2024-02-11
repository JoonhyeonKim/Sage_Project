from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, jsonify, flash, current_app
from flask_session import Session
from werkzeug.utils import secure_filename
from ..models.models import db, Conversation, Message
from .app import (
    load_prompts,
    is_informal,
    get_embedding,
    get_most_similar_prompt,
    get_chat_history,
    summarize_chat_history,
    abstract_summary_extraction,
    save_message,
    format_chat_history,
    get_ai_response,
    format_ai_response,
    expert_prompts,
    parse_character_card,
    extract_metadata_with_exiftool,
)
from .work_mode_handler import process_user_query_with_ai, generate_document, use_functions
import os

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

main = Blueprint('main', __name__)

@main.route('/set_name')
def set_name():
    session['name'] = 'Alice'
    return 'Name set in session'

@main.route('/get_name')
def get_name():
    name = session.get('name', 'Guest')
    return f'Hello, {name}'

@main.route('/start_session', methods=['GET', 'POST'])
def start_session():
    # Create a new conversation instance
    new_conversation = Conversation()
    
    # Add the new conversation to the database
    db.session.add(new_conversation)
    db.session.commit()

    # Store the conversation ID in the session
    session['conversation_id'] = new_conversation.id

    # Redirect to the home page to start interacting
    return redirect(url_for('main.home'))

@main.route('/end_session', methods=['GET'])
def end_session():
    # Remove the conversation ID from the session
    if 'conversation_id' in session:
        session.pop('conversation_id', None)

    # Redirect to the home page
    return redirect(url_for('main.home'))

@main.route('/past_conversations')
def past_conversations():
    # Fetch all past conversations, ordered by timestamp
    all_conversations = Conversation.query.order_by(Conversation.timestamp.desc()).all()
    return render_template('past_conversations.html', conversations=all_conversations)

@main.route('/view_conversation/<int:conversation_id>')
def view_conversation(conversation_id):
    # Fetch the specific conversation
    conversation = Conversation.query.get_or_404(conversation_id)
    return render_template('view_conversation.html', conversation=conversation)

@main.route('/api/conscious_mode', methods=['POST'])
def toggle_conscious_mode():
    # Ensure that the request contains JSON data
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    conscious_mode_enabled = data.get('enabled', False)

    session['conscious_mode'] = conscious_mode_enabled
    return jsonify({'enabled': conscious_mode_enabled})

@main.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    # Toggle dark mode in the session
    session['dark_mode'] = not session.get('dark_mode', False)
    return jsonify({'dark_mode': session['dark_mode']})

@main.route('/test_safe')
def test_safe():
    test_html = "<p>This should be <strong>bold</strong>.</p>"
    return render_template('test_template.html', test_html=test_html)

@main.route('/')
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

@main.route('/interact', methods=['POST'])
def interact():
    # Check if Conscious Mode is enabled
    conscious_mode_enabled = session.get('conscious_mode', False)
    instruction = parse_character_card()
    user_input = None

    if 'character_card' in request.files:
        file = request.files['character_card']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
                
            # Process the character card
            chara_data_encoded = extract_metadata_with_exiftool(filepath)
            if chara_data_encoded:
                instruction = parse_character_card(chara_data_encoded)
                session['personality_instruction'] = instruction
                # print('INSTRUCTION ON THE ROUTE_: ', instruction)
            else:
                return jsonify({'error': 'Failed to process character card.'}), 400
        else:
            return jsonify({'error': 'Invalid file type.'}), 400
    else:
        # If no file is uploaded, check if request is JSON and process accordingly
        if request.is_json:
            data = request.get_json()
            user_input = data.get('user_input', '').strip()
        else:
            return jsonify({'error': 'No character card or JSON data provided.'}), 400

    # print('INSTRUCTION ON THE ROUTE~', instruction)
    if request.content_type == 'application/json':
        data = request.get_json()
        user_input = data.get('user_input', '').strip() if data else ''
    else:
        user_input = request.form.get('user_input', '').strip()

    if not user_input:
        return jsonify({'error': 'Empty message.'}), 400
    # print('INSTRUCTION ON THE ROUTE~!!', instruction)

    instruction = session.get('personality_instruction', parse_character_card())
    user_input = str(user_input)

    if conscious_mode_enabled:
        prompts_file_path = './data/prompt/conscious.json'
        cs_prompts = load_prompts(prompts_file_path)
        most_similar_prompt_content = f'This is the rule you have to follow: {cs_prompts}'
    else:
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
    ai_response = get_ai_response(summarized_history, user_input, most_similar_prompt_content, instruction)

    print("AI Response:", ai_response)  # Check the response format
    # ai_response = format_ai_response(ai_response)  # Format for display

    # Save the user input and AI response
    save_message(user_input, conversation_id, is_user=True)
    save_message(ai_response, conversation_id, is_user=False)

    return jsonify({'ai_response': ai_response})

@main.route('/work_mode', methods=['GET', 'POST'])
def work_mode():
    # Ensure entering work mode disables conscious mode
    session['conscious_mode'] = False

    tools = [
        {
            "type": "function",
            "function": {
                "name": "ddg_search",
                "description": "Get the info from the web search engine DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["q"],
                },
            },
        }
    ]

    if request.method == 'POST':
        # Assuming the AJAX call sends JSON data
        data = request.get_json() if request.is_json else None
        if data:
            user_input = data.get('user_input', '') if data else '' # is user_input present then et it else empty string
            query_type = data.get('query_type', 'self_discover') # Default to 'self_discover'

            if query_type == 'self_discover':
                ai_response = process_user_query_with_ai(user_input)
            elif query_type == 'use_tool':
                # tools = data.get('tools', {}) # Get the tools from the request
                ai_response = use_functions(user_input, tools)
            else:
                ai_response = "Unknown query type."

            return jsonify({"ai_response": ai_response})
    dark_mode_enabled = session.get('dark_mode', False)
    return render_template('work_mode.html', dark_mode_enabled=dark_mode_enabled)