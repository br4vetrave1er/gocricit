import time
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import shelve

load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
PROMPT_FILE_PATH = "/home/gocricit-admin/gocricit/app/data/sales.txt"
CARE_ASSISTANT_ID = "asst_ytPflX4SN34UhplqhXHdm2lv"

# Initialize OpenAI client
client = OpenAI(api_key=OPEN_AI_API_KEY)


def create_assistant(file=None):
    """
    Create a new assistant using the OpenAI API.

    Args:
        file (str): Path to the prompt file (optional, defaults to PROMPT_FILE_PATH).

    Returns:
        dict: Details of the created assistant.
    """
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as file:
        prompt = file.read()

    assistant = client.beta.assistants.create(
        name="Deek",
        instructions=prompt,
        tools=[],  # Specify tools if required in the future
        model='gpt-4o',  # GPT-4 optimized model
    )

    logging.info(f"Assistant created: {assistant}")
    return assistant


def update_assistant(user_thread, user_phonenumber):
    """
    Update the existing assistant's instructions with context and phone number.

    Args:
        user_thread (str): Context thread to update the assistant's instructions.
        user_phonenumber (str): User's phone number to personalize the assistant.

    Returns:
        dict: Details of the updated assistant.
    """
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as file:
        prompt = file.read()

    # Format the prompt with provided context and phone number
    prompt = prompt.format(context=user_thread, phone_number=user_phonenumber)

    logging.info(f"Updated prompt: {prompt}")

    # Update the assistant with new instructions
    updated_assistant = client.beta.assistants.update(
        assistant_id=CARE_ASSISTANT_ID,
        instructions=prompt,
        temperature=0.66,  # Controls response randomness
        top_p=0.71,  # Controls diversity of responses
    )

    logging.info(f"Assistant updated successfully: {updated_assistant}")
    return updated_assistant


def generate_care_response(user_thread, user_phonenumber):
    """
    Generate a response from the care assistant.

    Args:
        user_thread (str): Context thread to provide the assistant.
        user_phonenumber (str): User's phone number for personalization.

    Returns:
        str: Generated response from the assistant.
    """
    try:
        # Update the assistant with user-specific context and phone number
        update_assistant(user_thread, user_phonenumber)

        # Create a new thread for the response generation
        cc_thread = client.beta.threads.create()
        logging.info(f"New thread created: {cc_thread.id}")

        # Start the assistant run
        run = client.beta.threads.runs.create(
            thread_id=cc_thread.id,
            assistant_id=CARE_ASSISTANT_ID,
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