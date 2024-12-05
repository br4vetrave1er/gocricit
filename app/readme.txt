# **Gocricit**

Gocricit is a modular application designed to handle WhatsApp-based conversational workflows powered by OpenAI assistants. The system uses a multi-agent architecture, with **Dobbee** as the primary agent for general user interactions and **Deek** as the escalation agent for advanced support queries.

---

## **System Overview**

The application processes incoming WhatsApp messages, interacts with OpenAI assistants to generate responses, and ensures contextual and efficient user interactions. The pipeline ensures a seamless flow from message receipt to response delivery, including support for escalation workflows.

### **Workflow**
1. **Incoming Webhook Events**:
   - Receives and processes POST requests from WhatsApp containing user messages and metadata.
2. **Message Validation**:
   - Validates incoming messages and parses user details and message content.
3. **Primary Interaction**:
   - Routes general queries to **Dobbee**, the primary assistant, for response generation.
4. **Escalation Handling**:
   - Detects escalation conditions (e.g., specific keywords like "help" or "escalate") and passes the query to **Deek**, the support assistant.
5. **Response Delivery**:
   - Formats and sends responses back to the user via WhatsApp’s messaging API.

---

## **Installation**

### **1. Clone the Repository**
```bash
git clone https://github.com/br4vetrave1er/gocricit.git
cd gocricit

2. Install Dependencies

Ensure you have Python 3.8+ installed. Install the required Python packages:

pip install -r requirements.txt

3. Set Up Environment Variables

Create a .env file in the root directory with the following keys:

OPEN_AI_API_KEY=<your_openai_api_key>
SALES_AGENT_ID=<your_dobbee_agent_id>
SUPPORT_AGENT_ID=<your_deek_agent_id>
PROMPT_FILE_PATH=<path_to_prompt_files>

Usage
Run the Application

Start the Flask server:

python run.py

Webhook Endpoint

The application listens for WhatsApp webhook events at:

POST /webhook

Sample Payload

{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "id": "message-id",
                "from": "user-whatsapp-id",
                "text": {
                  "body": "Hello, I need help."
                }
              }
            ],
            "contacts": [
              {
                "profile": {
                  "name": "User Name"
                },
                "wa_id": "user-whatsapp-id"
              }
            ]
          }
        }
      ]
    }
  ]
}

Expected Behavior

    Dobbee responds to general queries.
    If escalation is required, Deek takes over to handle support queries.
    Responses are delivered back to WhatsApp.

Key Components
1. WhatsApp Webhook Handler

    Parses incoming webhook events and validates their structure.
    Extracts user information, message content, and metadata.
    Routes messages to the appropriate processing pipeline.

2. OpenAI Assistant Management

    Manages the lifecycle of assistants (Dobbee and Deek), including creation, updates, and usage.
    Configures assistants with custom prompts and parameters to handle different types of queries.

3. Thread Management

    Ensures session continuity by associating each user with a unique thread ID.
    Tracks active sessions and retrieves context for ongoing conversations.

4. Response Delivery

    Formats assistant responses into WhatsApp-compatible structures.
    Sends responses back to users and logs delivery statuses.

Example Interactions
General Query (Handled by Dobbee)

    User: "What are your operating hours?"
    Dobbee: "Our operating hours are 9 AM to 6 PM, Monday to Friday."

Escalation (Handled by Deek)

    User: "I need urgent help with my order."
    Dobbee: "Let me connect you with support."
    Deek: "Hi! Can you provide more details about your order issue?"

Detailed Example
1. Incoming Webhook Event
Payload:

{
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "id": "message-id",
                "from": "user-whatsapp-id",
                "text": {
                  "body": "Hello, I need help."
                }
              }
            ],
            "contacts": [
              {
                "profile": {
                  "name": "User Name"
                },
                "wa_id": "user-whatsapp-id"
              }
            ]
          }
        }
      ]
    }
  ]
}

Process:

    Extract wa_id, name, and message_body from the payload.
    Check if the wa_id has an active thread:
        If yes, retrieve the thread.
        If no, create a new thread and store the ID.
    Route the message_body to Dobbee.
    Dobbee generates a response and checks for escalation conditions.
    If escalation is triggered, Deek handles the advanced query.
    Format and send the response back to the user.