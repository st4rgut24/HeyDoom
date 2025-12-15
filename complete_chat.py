import os
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration ---
# 1. Base URL: Open WebUI exposes the OpenAI API at the /api endpoint.
# The base URL must point to the root of the API service.
# NOTE: Open WebUI typically uses /api/chat/completions, which is handled
# automatically by setting the base_url correctly for the OpenAI SDK.

# 2. API Key (Use your generated token)
# Replace 'YOUR_OPENWEBUI_API_KEY' with the key you generated in settings

# 3. Model ID: This must be the name of one of the models you have configured
# and available in your Open WebUI interface (e.g., Llama 3, Mixtral, etc.).


# --- Client Initialization ---

# Load variables from the .env file and set them in os.environ
load_dotenv()

# --- Configuration: Access variables using os.getenv() ---
# os.getenv() retrieves the variable's value from the environment
OPENWEBUI_KEY = os.getenv("OPENWEBUI_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

if not OPENWEBUI_KEY:
    raise ValueError("OPENWEBUI_API_KEY not found. Check your .env file and .gitignore.")

base_url = os.getenv("OPENWEBUI_BASE_URL")

if base_url:
    # 2. Use an f-string to concatenate the base URL and the fixed path
    OPENWEBUI_URL = f"{base_url}/api"
    
    print(f"Generated URL: {OPENWEBUI_URL}")
else:
    print("WARNING: OPENWEBUI_BASE_URL environment variable is not set.")
    # Set a default or raise an error here if the URL is mandatory

try:
    client = OpenAI(
        # The base_url points to your Open WebUI API endpoint
        base_url=OPENWEBUI_URL,
        # The API key is used for the Bearer Token authentication
        api_key=OPENWEBUI_KEY,
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    # Exit or handle the error appropriately
    exit()


def get_chat_completion(prompt: str):
    """
    Calls the Open WebUI Chat Completions API with a user prompt.
    """
    print(f"Sending prompt to model:...")
    
    # The 'messages' array defines the conversation history.
    # For a single prompt, you only need the 'user' role message.
    messages = [
        {
            "role": "system",
            "content": "You are a helpful and concise assistant.",
        },
        {
            "role": "user",
            "content": prompt,
        }
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            # Optional parameters to control generation:
            max_tokens=250,
            temperature=0.7
        )

        # Extract and return the model's response text
        if response.choices:
            return response.choices[0].message.content
        return "Error: No response choices received."

    except Exception as e:
        error_message = f"Chat completion failed due to an API error. Original error: {e}"
        raise ValueError(error_message) from e

# --- Execution ---
if __name__ == "__main__":
    user_prompt = "Explain how a star is born in two sentences."
    
    completion_text = get_chat_completion(user_prompt)
    
    print("\n--- Model Response ---")
    print(completion_text)
    print("----------------------\n")
