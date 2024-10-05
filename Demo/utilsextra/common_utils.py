import math
import openai
import logging
import requests
import json
import os
import csv
import re
import datetime
import base64
import numpy as np
from collections import Counter
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores import Chroma




def load_json_file(file_path, debug=False):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if debug:
                print(data)
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at {file_path} was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"The file at {file_path} contains invalid JSON.")

def load_text(fpaths, by_lines=False):
    with open(fpaths, "r") as fp:
        if by_lines:
            return fp.readlines()
        else:
            return fp.read()

def load_prompt(prompt):
    return load_text(f"prompts/{prompt}.txt")
    # /home/**/Workspace/MP5/MP5_agent/agent/prompts/{prompt}.txt
    # prompts/{prompt}.txt


def log_info(info, is_logging=True):
    if not is_logging:
        logging.disable(logging.CRITICAL + 1)

    logging.info(info)

    if not is_logging:
        logging.disable(logging.NOTSET)

    print(info)

### For generating prompts
def list_dict_to_prompt(list_data):
    if len(list_data) == 0:
        return "- None\n"

    text = ""
    for dict_data in list_data:
        text += dict_to_prompt(dict_data)

    return text

def list_to_prompt(list_data):
    text = ""
    for item in list_data:
        if item:  # Check if item is not None or an empty dictionary/list
            text += f"- {item}\n"
        else:
            text += "- None\n"
    return text


def dict_to_prompt(dict_data):
    text = ""
    for key in dict_data:
        if dict_data[key]:
            text += f"- {key}: {dict_data[key]}\n"
        else:
            text += f"- {key}: None\n"
    return text

# Custom JSON Encoder for NumPy types including scalar conversions
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Convert ndarray to list
        if isinstance(obj, np.integer):
            return int(obj)  # Convert np.int* to int
        if isinstance(obj, np.floating):
            return float(obj)  # Convert np.float* to float
        if isinstance(obj, np.bool_):
            return bool(obj)  # Convert np.bool_ to bool
        return json.JSONEncoder.default(self, obj)