import json
import logging
import os
import time
import shelve
from dotenv import load_dotenv
from openai import OpenAI
from .care_assistant import generate_care_response

# Load environment variables
load_dotenv()

# Constants
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
PROMPT_FILE_PATH = os.getenv("PROMPT_FILE_PATH")
AGENT_IDS_ENV_FILE = ".env"  # Path to the .env file

# OpenAI Client
client = OpenAI(api_key=OPEN_AI_API_KEY)

# Agent Configuration
AGENTS = {
    "sales_agent": {"name": "Deek", "prompt_file": "/home/gocricit-admin/gocricit/app/data/sales.txt"},
    "support_agent": {"name": "Dobbee", "prompt_file": "/home/gocricit-admin/gocricit/app/data/support.txt"},
}

# Globals for Escalation
trigger_agent2 = False
thread_for_agent2 = None


# Utility: Update Environment Variables
def update_env_variable(key, value):
    """
    Update or add a key-value pair in the .env file.

    Args:
        key (str): The environment variable key.
        value (str): The environment variable value.
    """
    with open(AGENT_IDS_ENV_FILE, "a") as env_file:
        env_file.write(f"{key}={value}\n")
    os.environ[key] = value  # Update the runtime environment
    logging.info(f"Updated {key} in .env")


# Agent Management
def get_or_create_agent(agent_key):
    """
    Retrieve an existing agent or create a new one if it doesn't exist.

    Args:
        agent_key (str): The key identifying the agent in AGENTS.

    Returns:
        dict: The agent details.
    """
    try:
        # logging.info(f"from here -> {agent_key}")
        agent_config = AGENTS[agent_key]
        agent_id_env_key = f"{AGENTS[agent_key]["name"].upper()}_ASSISTANT_ID"

        # logging.info(f"from here -> {agent_id_env_key}")

        # Check if the agent ID exists in the environment
        agent_id = os.getenv(agent_id_env_key)
        logging.info(agent_config)
        if agent_id:
            logging.info(f"Retrieving existing agent: {agent_config['name']}")
            return client.beta.assistants.retrieve(agent_id)

        # Create a new agent if it doesn't exist
        with open(agent_config["prompt_file"], "r", encoding="utf-8") as file:
            prompt = file.read()

        new_agent = client.beta.assistants.create(
            name=agent_config["name"],
            instructions=prompt,
            tools=[],
            model="gpt-4o",
        )

        # Update the .env file with the new agent ID
        update_env_variable(agent_id_env_key, new_agent.id)
        logging.info(f"Created new agent: {agent_config['name']} with ID {new_agent.id}")
        return new_agent

    except Exception as e:
        logging.error(f"Failed to retrieve or create agent: {e}")
        raise


def customize_agent(agent_key, instructions=None, temperature=0.3, top_p=0.90, tools=None):
    """
    Customize an existing agent.

    Args:
        agent_key (str): The key identifying the agent in AGENTS.
        instructions (str): Custom instructions or prompt for the agent.
        temperature (float): Controls randomness in responses.
        top_p (float): Controls diversity in responses.
        tools (list): Additional tools to integrate.

    Returns:
        dict: The updated agent details.
    """
    try:
        # logging.info(f"from here -> {agent_key}")
        agent_config = AGENTS[agent_key]
        agent_id_env_key = f"{AGENTS[agent_key]["name"].upper()}_ASSISTANT_ID"
        logging.info(agent_id_env_key)

        # logging.info(f"from here -> {agent_id_env_key}")

        # Check if the agent ID exists in the environment
        agent_id = os.getenv(agent_id_env_key)
        logging.info(agent_config)
        if agent_id:
            logging.info(f"Retrieving existing agent: {agent_config['name']}")
            try:
                client.beta.assistants.retrieve(agent_id)
                logging.info("Assisatnt loaded succefully for update")
            except Exception as e:
                logging.error("Error",e)

        # Load new instructions if provided
        logging.info(f"here -> {instructions}")
        if instructions:
            # Update agent prompt
            with open(instructions, "r", encoding="utf-8") as file:
                prompt = file.read()
                logging.info(prompt)

        if tools is None:
            tools = []

        updated_agent = client.beta.assistants.update(
            assistant_id=agent_id,
            instructions=prompt,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            model='gpt-4o',
        )

        logging.info(f"Customized agent: {AGENTS[agent_key]['name']}")
        return updated_agent

    except Exception as e:
        logging.error(f"Failed to customize agent: {e}")
        raise


# Thread Management
def check_if_thread_exists(wa_id):
    """
    Check if a thread exists for the given WhatsApp ID.
    """
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    """
    Store a thread ID for the given WhatsApp ID.
    """
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


def manage_thread(wa_id):
    """
    Retrieve or create a thread for the given WhatsApp ID.
    """
    thread_id = check_if_thread_exists(wa_id)
    if thread_id is None:
        logging.info(f"Creating a new thread for wa_id: {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        return thread
    else:
        logging.info(f"Retrieving thread for wa_id: {wa_id}")
        return client.beta.threads.retrieve(thread_id)


# Response Generation
def generate_response(agent_key, message_body, wa_id):
    """
    Generate a response for the given message using a specified agent.
    """
    try:
        logging.info(AGENTS[agent_key]["prompt_file"])
        agent = customize_agent(agent_key=agent_key, instructions=AGENTS[agent_key]["prompt_file"])
        # logging.info(f"update response -> {agent_key}")
        agent = get_or_create_agent(agent_key)
        thread = manage_thread(wa_id)


        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_body,
        )
        response = run_assistant(agent, thread)
        return response
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process your message."


def run_assistant(agent, thread, timeout=120):
    """
    Run the assistant for the given thread and wait for completion.

    Args:
        agent (dict): Assistant details.
        thread (dict): Thread details.
        timeout (int): Timeout in seconds for the assistant run.

    Returns:
        str: The assistant's response message.

    Raises:
        TimeoutError: If the assistant run exceeds the specified timeout.
    """
    try:
        # Start the assistant run
        logging.info(f"Starting assistant run for thread: {thread.id}")
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=agent.id,
        )

        start_time = time.time()
        while True:
            # Check if the run is completed

            if run.status == "completed":
                logging.info("Assistant run completed successfully.")
                break

            # Timeout logic
            if time.time() - start_time > timeout:
                logging.error(f"Assistant run timed out after {timeout} seconds.")
                raise TimeoutError("Assistant run timed out.")
            
            # logging.info(f"run -> {run}")
            # Handle unexpected statuses
            if run.status not in ["queued", "in_progress"]:
                logging.error(f"Unexpected run status: {run.status}")
                raise RuntimeError(f"Assistant run failed with status: {run.status}")

            # Wait and poll for the status
            logging.debug(f"Assistant run status: {run.status}")
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        
        # Retrieve the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Extract the latest message
        new_message = messages.data[0].content[0].text.value
        logging.info(f"Retrieved messages from thread: {new_message}")
        return new_message

    except TimeoutError as e:
        logging.error(f"TimeoutError: {e}")
        raise
    except Exception as e:
        logging.error(f"Error during assistant run: {e}")
        raise


# Escalation Handling
def check_for_help(message):
    """
    Check if the message contains escalation keywords.
    """
    escalation_keywords = [
        "customer care",
        "talk to someone",
        "escalate",
        "speak to a representative",
        "connect me to support",
    ]

    # logging.info(any(keyword in message.lower() for keyword in escalation_keywords))
    return any(keyword in message.lower() for keyword in escalation_keywords)


def sales_connect(user_messages, user_phonenumber):
    """
    Connect the user to the sales team if escalation is triggered.
    """
    global trigger_agent2

    logging.info("Deek Started")
    logging.info(f"trigger_Agent2 -> {trigger_agent2}")
    try:
        care_response = generate_care_response(user_messages, user_phonenumber)
        logging.info(f"Response from care: {care_response}")
        return care_response
    except Exception as e:
        logging.error(f"Error during assistant run: {e}")
        raise


def deek_update(agent_key, user_id, user_phonenumber):
    """
    Update the existing assistant's instructions with context and phone number.
    before getting response

    Args:
        user_thread (str): Context thread to update the assistant's instructions.
        user_phonenumber (str): User's phone number to personalize the assistant.

    Returns:
        dict: Details of the updated assistant.
    """

    deek_id_env_key = os.getenv(f"{AGENTS[agent_key]["name"].upper()}_ASSISTANT_ID")
    user_thread = check_if_thread_exists(user_id)
    if not user_thread:
        return "No messages from user found"
    else:
        user_thread = client.beta.threads.retrieve(thread_id=user_thread)



    with open(AGENTS[agent_key]["prompt_file"], "r", encoding="utf-8") as file:
        prompt = file.read()

    # Format the prompt with provided context and phone number
    prompt = prompt.format(context=user_thread, phone_number=user_phonenumber)

    logging.info(f"Updated prompt: {prompt}")

    # Update the assistant with new instructions
    updated_assistant = client.beta.assistants.update(
        assistant_id=deek_id_env_key,
        instructions=prompt,
        temperature=0.66,  # Controls response randomness
        top_p=0.71,  # Controls diversity of responses
    )

    logging.info(f"Assistant updated successfully: {updated_assistant}")
    return updated_assistant


def generate_care_response(agent_key, user_id, user_phonenumber):
    """
    Generate a response from the care assistant.

    Args:
        user_thread (str): Context thread to provide the assistant.
        user_phonenumber (str): User's phone number for personalization.

    Returns:
        str: Generated response from the assistant.
    """
    deek_id_env_key = os.getenv(f"{AGENTS[agent_key]["name"].upper()}_ASSISTANT_ID")
    logging.info(deek_id_env_key)

    try:
        # Update the assistant with user-specific context and phone number
        deek_update(agent_key, user_id, user_phonenumber)
    
        # Create a new thread for the response generation
        cc_thread = client.beta.threads.create()
        logging.info(f"New thread created: {cc_thread.id}")

        # Start the assistant run
        run = client.beta.threads.runs.create(
            thread_id=cc_thread.id,
            assistant_id=deek_id_env_key,
        )

        # Wait for the run to complete
        while run.status != "completed":
            logging.info("Waiting for assistant run to complete...")
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(thread_id=cc_thread.id, run_id=run.id)

        # Retrieve messages generated by the assistant
        messages = client.beta.threads.messages.list(thread_id=cc_thread.id)
        new_message = messages.data[0].content[0].text.value

        logging.info(f"Generated response: {new_message}")
        return new_message

    except Exception as e:
        logging.error(f"Error generating care response: {e}")
        return "Sorry, an error occurred while processing your request."
