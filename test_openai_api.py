import os
from openai import OpenAI
from dotenv import load_dotenv

def test_openai_api():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env!")
        return

    print(f"Testing OpenAI API key...")
    client = OpenAI(api_key=api_key)
    
    try:
        # Perform a very simple chat completion request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API is working!'"}],
            max_tokens=10
        )
        print(f"✅ OpenAI API: SUCCESSFUL")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API: FAILED - {e}")

if __name__ == "__main__":
    test_openai_api()
