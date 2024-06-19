import logging
from openai import OpenAI
from config_manager import config_manager as appenv


def is_available():
    # Check if the OPENAI_API_KEY is present in the environment variables
    return appenv.environ['OPENAI_API_KEY'] is not None


def get_chatgpt_response(prompt):
    try:
        client = OpenAI(api_key=appenv.environ['OPENAI_API_KEY'])
        response = client.chat.completions.create(model="gpt-3.5-turbo",  # Updated model
                                                  response_format={"type": "json_object"},
                                                  messages=[{"role": "user", "content": prompt}],
                                                  max_tokens=4096,  # Adjust the number of tokens as needed
                                                  temperature=0.7)
        return {
            "message": "success",
            "response": response.choices[0].message.content.strip()
        }
    except Exception as e:
        logging.info(f"Error while calling chatgpt api....\n{e}")
        return {
            "message": "error"
        }
