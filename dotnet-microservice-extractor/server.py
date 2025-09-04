import uvicorn
# import os
# os.environ['CURL_CA_BUNDLE'] = './huggingface.co.crt'
import os
import certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
 
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
 