import json
import logging
from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time
from .care_assistant import generate_care_response
# from ..app.functions.freshworks import create_contact
# from ..app.functions.agent_funtions import create_freshworks_contact

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
OPEN_AI_ASSISTANT_ID = "asst_L8uwOaGnTlf6ie4jhAHL5UEL"
PROMPT_FILE_PATH = "/home/gocricit-admin/gocricit/app/data/prompt.txt"
# assistant_id = None

client = OpenAI(api_key=OPEN_AI_API_KEY)
trigger_agent2 = False
thread_for_agent2 = None



def create_assistant(file=None):
    

# Read the file and assign content to the `prompt` variable
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as file:
        prompt = file.read()
    assistant = client.beta.assistants.create(
        name="Dobbie",
        instructions=prompt,
        tools=[],
        model='gpt-4o',
    )
    return assistant

def get_assistant():

    assistant = client.beta.assistants.retrieve(OPEN_AI_ASSISTANT_ID)
     
    return assistant

def update_assistant():
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as file:
        prompt = file.read()
    update_assistant = client.beta.assistants.update(
        assistant_id=OPEN_AI_ASSISTANT_ID,
        instructions = prompt,
        temperature=0.66,
        top_p=0.71,
        tools=[
            {
                "type": "function",
                "function": create_contact,
            }
        ],
        
    )



# Thread Management

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


# generate response
def generate_response(message_body, wa_id, name):
    
    # check if there is already a thread for the wa_id
    thread_id = check_if_thread_exists(wa_id=wa_id)

    # if a thread exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        
        store_thread(wa_id, thread.id)
        
        thread_id = thread.id
        print(thread_id)
    # Otherwise retrive the existing thread
    else:
        print(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)
        print(thread)

    
    logging.info(f"tthread is -> {thread}")
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    # logging.info(f"message after appending -> {message}")
    # logging.info(f"thread -> {thread}")
    # new_message = "12"
    new_message = run_assistant(thread)
    print(f"To {name}:", new_message)
    return new_message

def generate_summary(context):

    if context.type != "summary":
        raise ValueError("Invalid context type of summazrization")
    
def check_for_help(message):
    escalation_keywords = [
        "customer care", 
        "talk to someone", 
        "escalate", 
        "speak to a representative",
        "connect me to support"
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in escalation_keywords)


# Run Assistant
def run_assistant(thread):
    # Retrieve the Assistant
    assistant = get_assistant()
    # logging.info(f"Assistant created -> {assistant}")
    # print(assistant)
    # run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    # wait for completion
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        

    
    
    # retrieve the messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    logging.info(f"From thread Messages -> {messages}")
    new_message = messages.data[0].content[0].text.value

    response = check_for_help(new_message)
    if response:
        global trigger_agent2, thread_for_agent2
        trigger_agent2 = True
        thread_for_agent2 = messages


    return new_message

def sales_connect(user_phonenumber):
    global trigger_agent2
    if trigger_agent2:  
        care_response = generate_care_response(thread_for_agent2, user_phonenumber)
        logging.info(f"response from care -> {care_response}")
        trigger_agent2 = False
        return care_response
    else:
        return ""