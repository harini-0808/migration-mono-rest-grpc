import os
import certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['SSL_CERT_FILE'] = certifi.where()
import uvicorn
# import os
# os.environ['CURL_CA_BUNDLE'] = './huggingface.co.crt'
import os
from dotenv import load_dotenv
import certifi
load_dotenv()
 
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
 