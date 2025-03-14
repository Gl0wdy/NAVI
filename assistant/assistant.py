import speech_recognition as sr
from speakerpy.lib_speak import Speaker

from mss import mss
import webbrowser

from g4f.client import Client
from g4f.models import gigachat

from assistant.condition import Condition

import json
import re
import random
import os


with open(r'NAVI\assistant\promt.txt', 'r', encoding='utf-8') as file:
    promt = file.read()


class Assistant:

    PATH = 'chat_history.json'

    def __init__(self):
        self.condition = Condition.always_active
        self._chat_history = [
            {"role": "system", "content": promt}
        ]
        self._file = None

        self._voice_engine = Speaker(model_id="ru_v3", language="ru", speaker="kseniya", device="cpu")

        self._client = Client()
        self._rec = sr.Recognizer()

    def start(self, text_mode: bool = False):
        if text_mode:
            while (u_input := input('Request: ') != 'стоп'):
                print('Response: ', end='')
                ai_resp = self.ai_request(u_input)
                print(ai_resp + '\n')

        for text in self.listen():
            if text is not None and self.condition != Condition.sleep:
                is_base = self.base_commands_checkout(text)
                if is_base == False:
                    print(f'>> {text}')
                    ai_resp = self.ai_request(text)
                    if ai_resp:
                        self.say(ai_resp)
                    print()

    def base_commands_checkout(self, text: str):
        if not text:
            return
        match text.split()[0].lower():
            case 'скрин' | 'скриншот':
                with mss() as sct:
                    sct.shot()
            case 'браузер':
                webbrowser.open('https://google.com/')
            case 'поиск' | 'найди':
                text = '+'.join(text.split()[1:])
                url = f'https://duckduckgo.com/?q={text}'
                webbrowser.open(url)
            case 'стоп' | 'спи':
                self.condition = Condition.sleep
                self.say('Отключаюсь.')
            case 'режим диалога':
                print('да')
                self.condition = Condition.always_active
                self.say('Режим диалога включен.')
            case 'режим команд':
                self.condition = Condition.command_active
                self.say('Режим команд включен.')
            case _:
                return False

    def ai_request(self, text: str):
        self.update_history(role='user', content=text)
        completion = self._client.chat.completions.create(
            model='gpt-4o-mini',
            messages=self._chat_history
        )
        ai_text = completion.choices[0].message.content
        self.update_history(role="assistant", content=ai_text)

        blocks = self._find_text_blocks(ai_text)
        if blocks:
            phrases = ['один момент...', 'секунду...', 'запрос принят.', 'выполняю код.']
            self.say(random.choice(phrases))
            for code in blocks:
                try:
                    self.execute(code)
                except Exception as exc:
                    print(exc)
        else:
            return ai_text

    def execute(self, code):
        local_scope = {
            'self': self
        }
        exec(code, globals(), local_scope)
        
        ai_comments = local_scope.get('ai_comments', None)  
        if ai_comments is not None:
            self.update_history(role='assistant', content=ai_comments)

    def listen(self):
        while True:
            with sr.Microphone() as source:
                audio_text = self._rec.listen(source, timeout=10, phrase_time_limit=10)
                
                try:
                    res = self._rec.recognize_vosk(audio_text, language='ru-RU')
                    text = json.loads(res)['text']
                    if self.condition == Condition.always_active:
                        yield text
                        continue

                    splited_text = text.split(maxsplit=1)
                    if splited_text and (splited_text[0] == 'нави' and self.condition == Condition.command_active):
                        yield text

                except Exception as exc:
                    print(f"Sorry, I did not get that ({exc})")

    def say(self, text: str):
        self._voice_engine.speak(text=text, sample_rate=48000, speed=1.0)

    def _find_text_blocks(self, text):
        code_blocks = re.findall(r'\[CODE\](.+)\[/CODE\]', text, re.DOTALL)
        return code_blocks

    def update_history(self, **kwargs):
        try:
            self._file.seek(0)
            existing_data = json.load(self._file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        existing_data.append(kwargs)

        self._file.seek(0) 
        json.dump(existing_data, self._file, indent=4, ensure_ascii=False)
        self._file.truncate()

        self._chat_history.append(kwargs)
    
    def __enter__(self):
        if not os.path.exists(self.PATH):
            self._file = open(self.PATH, 'w+', encoding='utf-8')
            json.dump([], self._file, ensure_ascii=False)
        else:
            self._file = open(self.PATH, 'r+', encoding='utf-8')
            data = json.load(self._file)
            self._chat_history.extend(data)
        return self

    def __exit__(self, *args):
        self._file.close()