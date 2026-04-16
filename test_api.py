import os
import json
from openai import OpenAI
from dotenv import load_dotenv

def test_openai_api():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file.")
        return

    print(f"📡 Testing OpenAI API with key: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Simple test call to GPT-4o (the model used in VerifAI)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a KYC assistant."},
                {"role": "user", "content": "Say 'API Connection Successful' and tell me the current date."}
            ],
            max_tokens=50
        )
        
        print("\n✅ SUCCESS!")
        print(f"🤖 AI Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print("\n❌ API TEST FAILED!")
        print(f"Error Details: {str(e)}")

if __name__ == "__main__":
    test_openai_api()
