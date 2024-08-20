import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=key)

with open('prompts.json', 'r') as f:
    prompts = json.load(f)
prompts = { p['prompt']: p['template'] for p in prompts }


def generate_text(input_text: str) -> tuple[str, bool]:
    response = client.chat.completions.create(
        model='gpt-4o',
        temperature=0.0,
        messages=[{'role': 'user', 'content': input_text}],
        stream=False,
    )
    finish = response.choices[0].finish_reason == 'stop'
    response_text = response.choices[0].message.content
    response_text = response_text if response_text else ''
    return (response_text, finish)


def transform_query(input_query: str):
    transform_prompt = prompts.get('transform_query', '')
    transformed_query, _ = generate_text(transform_prompt.format(query=input_query))
    # questions_prompt = prompts.get('generate_questions')
    # questions, _ = generate_text(questions_prompt.format())
    keywords_prompt = prompts.get('generate_keywords', '')
    keywords, _ = generate_text(keywords_prompt.format(queries=transformed_query))
    return transformed_query, keywords


def generate_questions(input_query: str) -> str:
    questions_prompt = prompts.get('generate_questions', '')
    questions, _ = generate_text(questions_prompt.format(num_queries=3, query=input_query))
    return questions


def answer_questions(questions: str, context: str) -> str:
    answer_prompt = prompts.get('answer_question', '')
    answer, _ =  generate_text(answer_prompt.format(question=questions, context=context))
    return answer
