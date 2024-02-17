import json
import requests
import os
import time
from .app import (
    client,
    get_chat_history,
    summarize_chat_history,
    abstract_summary_extraction,
    save_message,
    format_chat_history,

)
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from redis import Redis
from ..models.models import init_app, db, Conversation, Message

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  

# from langchain_community.document_loaders import ArxivLoader

GPT_MODEL = "gpt-3.5-turbo-0613"
client = OpenAI()

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


def use_functions(user_input, tools): # maybe I should define tools at route??
    messages = [{"role": "system", "content": "turn the following user input into a search query for a search engine and then use the function with that query to get result: "},
 {"role": "user", "content": user_input}]

    chat_response = chat_completion_request(
        messages, tools,
    )
    chat_response.choices[0].message
    response_message = chat_response.choices[0].message
    tool_calls = response_message.tool_calls
    response_message = chat_response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        available_functions = {
            "ddg_search": ddg_search,
        }
        messages.append(response_message)
        for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                print(function_args)
                function_response = function_to_call(
                    q = function_args["q"],
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )
        second_response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=messages,
            )  
        res = second_response.choices[0].message.content.strip()
        print('response message: ', response_message)
        print('second response: ', second_response)
    return res    

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