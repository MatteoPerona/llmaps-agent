from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_tavily():
    try:
        client = TavilyClient()
        response = client.search("test query")
        print("Tavily API test successful!")
        print(response)
    except Exception as e:
        print(f"Tavily API test failed: {str(e)}")

if __name__ == "__main__":
    test_tavily() 