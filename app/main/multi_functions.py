import json
import requests
import os
import time
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from redis import Redis

from .wiki import execute_wiki_agent
from .work_mode_handler import process_user_query_with_ai

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  

client = OpenAI()
GPT_MODEL = 'gpt-3.5-turbo-1106'

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

def ddg_search(q):
    search = DuckDuckGoSearchResults()
    answer = search.run(q)
    return answer


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
    
def get_current_traffic(location):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "traffic": "busy"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "traffic": "normal"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "traffic": "sparse"})
    else:
        return json.dumps({"location": location, "traffic": "unknown"})

def run_conversation(user_input):
    # Step 1: send the conversation and available functions to the model
    messages = [{"role": "system", "content": "You are a great decision maker. You always choose right tool for the task."} , {"role": "user", "content": user_input}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_current_traffic",
                "description": "Get the current traffic in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "ddg_search",
                "description": "Get the information from web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": "The search query for web search",
                        },
                    },
                    "required": ["q"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_wiki_agent",
                "description": "Get the information from wiki",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "The search query for the wikipedia",
                        },
                    },
                    "required": ["user_input"],
                },
            },
        },   
        {
            "type": "function",
            "function": {
                "name": "process_user_query_with_ai",
                "description": "Reason a complicated question by following multiple steps",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "A user query from an input",
                        },
                    },
                    "required": ["user_input"],
                },
            },
        },  
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
            "get_current_traffic": get_current_traffic,
            "ddg_search": ddg_search,
            "execute_wiki_agent": execute_wiki_agent,
            "process_user_query_with_ai": process_user_query_with_ai,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            print(f'{function_name} Arguments: ', tool_call.function.arguments)
            if function_name == 'get_current_weather':
                function_response = function_to_call(
                    location=function_args.get("location"),
                    unit=function_args.get("unit"),
                )
            elif function_name == 'get_current_traffic':
                function_response = function_to_call(
                    location=function_args.get("location"),
                )
            elif function_name == 'ddg_search':
                    function_response = function_to_call(
                    q=function_args.get("q"),
                )
            elif function_name == 'execute_wiki_agent':
                    function_response = function_to_call(
                    user_input=function_args.get("user_input"),
                )
            elif function_name == 'process_user_query_with_ai':
                    function_response = function_to_call(
                    user_input=function_args.get("user_input"),
                )
            
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        print('multi function: ', second_response.choices[0].message.content.strip())

        return second_response.choices[0].message.content.strip()