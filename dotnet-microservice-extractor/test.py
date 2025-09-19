# test.py
import os
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
from langsmith import Client
from langsmith.wrappers import wrap_openai
from langsmith import traceable

# --- Load env vars ---
load_dotenv()

# --- Disable SSL verification for LangSmith ---
insecure_session = requests.Session()
insecure_session.verify = False
requests.packages.urllib3.disable_warnings()

# --- LangSmith client with insecure session ---
ls_client = Client(
    api_key=os.environ["LANGCHAIN_API_KEY"],
    session=insecure_session
)

# --- Azure OpenAI client ---
azure_client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)

# --- Wrap Azure client with LangSmith manually ---
client = wrap_openai(azure_client)
client._ls_client = ls_client   # <-- attach your custom LangSmith client

# --- Pipeline function ---
@traceable(client=ls_client)
def pipeline(user_input: str):
    result = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],  # deployment name
        messages=[{"role": "user", "content": user_input}],
    )
    return result.choices[0].message.content

# --- Run ---
if __name__ == "__main__":
    print(pipeline("Hello, world!"))