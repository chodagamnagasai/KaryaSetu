import os, json, re, logging
import httpx
from fastapi import HTTPException

logger = logging.getLogger('karyasetu.ai')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/free')
OPENROUTER_URL = os.getenv('OPENROUTER_URL', 'https://openrouter.ai/api/v1/chat/completions')
OPENROUTER_SITE = os.getenv('OPENROUTER_SITE_URL', 'https://karya-setu.vercel.app')
OPENROUTER_APP = os.getenv('OPENROUTER_APP_NAME', 'KaryaSetu')


def _extract_json(text: str):
    text = (text or '').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.S)
        if not match:
            raise ValueError('Model did not return valid JSON')
        return json.loads(match.group(0))


async def chat_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.1):
    if not OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured')
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': OPENROUTER_SITE,
        'X-Title': OPENROUTER_APP,
    }
    payload = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': temperature,
        'response_format': {'type': 'json_object'},
    }
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
    if response.status_code >= 400:
        logger.error('OpenRouter %s: %s', response.status_code, response.text[:1000])
        raise RuntimeError(f'OpenRouter request failed ({response.status_code})')
    data = response.json()
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    return _extract_json(content)


async def chat_text(system_prompt: str, user_prompt: str, *, temperature: float = 0.2):
    if not OPENROUTER_API_KEY:
        raise RuntimeError('OPENROUTER_API_KEY is not configured')
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': OPENROUTER_SITE,
        'X-Title': OPENROUTER_APP,
    }
    payload = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': temperature,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(f'OpenRouter request failed ({response.status_code})')
    return response.json()['choices'][0]['message']['content']
