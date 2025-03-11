import speech_recognition as sr
import pyttsx3
from mss import mss

from g4f.client import Client
from g4f.models import gigachat

from assistant.condition import Condition

import json
import re
import random


with open('promt.txt', 'r', encoding='utf-8') as file:
    promt = file.read()


class Assistant:
    def __init__(self):
        self.condition = Condition.active
        self._chat_history = [
            {"role": "system", "content": promt}
        ]

        self._voice_engine = pyttsx3.init()
        self._voice_engine.setProperty('rate', 180)
        self._voice_engine.setProperty('volume', 0.9)

        self._client = Client()
        self._rec = sr.Recognizer()

    def start(self):
        for text in self.listen():
            if text and self.condition == Condition.active:
                is_base = self.base_commands_checkout(text)
                if not is_base:
                    print(f'Request: {text}')
                    ai_resp = self.ai_request(text)
                    if ai_resp:
                        print(f'Response: {ai_resp}\n')
                        self.say(ai_resp)

    def base_commands_checkout(self, text):
        match text.lower():
            case 'скрин' | 'скриншот':
                with mss() as sct:
                    sct.shot()
            case _:
                return False

    def ai_request(self, text: str):
        self.update_history(role='user', content=text)
        completion = self._client.chat.completions.create(
            model='gpt-4o-mini',
            messages=self._chat_history
        )
        ai_text = completion.choices[0].message.content

        blocks = self._find_text_blocks(ai_text)
        if blocks:
            self.say('выполняю код...')
            for code in blocks:
                try:
                    self.execute(code)
                except Exception as exc:
                    print(exc)
        else:
            return ai_text
        self.update_history(role="assistant", content=ai_text)

    def execute(self, code):
        local_scope = {
            'self': self
        }
        exec(code, globals(), local_scope)
        
        ai_comments = local_scope.get('ai_comments', None)  
        if ai_comments is not None:
            print(f'Response: {ai_comments}')
        else:
            print("No comments returned.")

    def listen(self):
        while True:
            with sr.Microphone() as source:
                audio_text = self._rec.listen(source)
                try:
                    res = self._rec.recognize_vosk(audio_text)
                    text = json.loads(res)['text']
                    if text in ('стоп', 'спи'):
                        self.condition = Condition.sleep
                    yield text

                except Exception as exc:
                    print("Sorry, I did not get that")

    def say(self, text: str):
        self._voice_engine.say(text)
        self._voice_engine.runAndWait()

    def update_history(self, **kwargs):
        self._chat_history.append(kwargs)

    def _find_text_blocks(self, text):
        code_blocks = re.findall(r'\[CODE\](.+)\[/CODE\]', text, re.DOTALL)
        return code_blocks