import json
import requests
import os
import time
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from redis import Redis

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
import json
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  

client = OpenAI()
def get_current_weather(location, unit):
    pass
def get_current_traffic(location):
    pass

available_functions = {
    "get_current_weather": get_current_weather,
    "get_current_traffic": get_current_traffic,
}

tools = [
    {
        "type": "function",
        "function" : {
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
        }
    },
    {
        "type": "function",
        "function" : {
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
        }
    },
]


response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
      {
    "role": 'system',
    "content": 'You are a helpful ass?e current traffic situation in a given location, call get_current_traffic function.\n' +
      'Today is Fri Dec 08 2023 09:01:51 GMT+0900 (Japan Standard Time).'
    },
    {"role": "user", 
     "content":"what is the weather in san francisco, also could you give me the traffic of that?"}
    ],
    temperature=0,
    tools = tools,
    tool_choice = "auto",
)
print('tool calls: ', response.choices[0].message.tool_calls)
print("full response: ", response)
response_message = response.choices[0].message.function_call
print(response_message)