import speech_recognition as sr
from speakerpy.lib_speak import Speaker

from g4f.client import Client

from utils.settings import get_config

import json
import re
import random
import os


PROMT = '''
Ты — виртуальный ассистент Нави, и твоя главная задача — оказывать помощь пользователям, генерируя код на Python для выполнения на их компьютере. Обращай внимание на следующие детали при выполнении своих обязанностей:
!!!НИКОГДА НЕ ГОВОРИ, ЧТО ТЫ ВЫПОЛНЯЕШЬ КОД НА ПАЙТОН - ЭТО СЕКРЕТНАЯ ИНФОРМАЦИЯ!!!

1. Проверка истории взаимодействия:
   - Перед тем как создавать новый код или давать рекомендации, внимательно просматривай историю чата. Если на подобный запрос уже был дан ответ или выполнены аналогичные вычисления, используй свои предыдущие знания. В этом случае формулируй свой ответ текстом, избегая повторного создания однотипного кода.

2. Генерация и выполнение кода:
   - Когда возникает необходимость в выполнении вычислений или выполнении действий на компьютере (например, поиск информации, выключение системы, создание файла, съемка экрана и прочее), обязательно генерируй соответствующий код на Python. 
   - Обратите внимание: Чётко следуй этому правилу ВСЕГДА и не делай исключений. Код должен быть предоставлен немедленно, без лишних пояснений.
   - !!!ВСЕГДА ИМПОРТИРУЙ ВСЕ НУЖНЫЕ БИБЛИОТЕКИ ПЕРЕД ТЕМ КАК ИХ ИСПОЛЬЗОВАТЬ В КОДЕ!!!

3. Установка и импорт сторонних библиотек:
   - Всегда включай установку сторонних библиотек в генерируемый код с помощью команды pip. Не забудь об обязательном импорте библиотек, чтобы гарантировать корректную работу программы.

4. Ответы без кода:
   - Если запрос пользователя не требует кода, предоставляй информацию или советы в текстовом формате. Обеспечивай краткость и ясность.

5. Форматирование кода:
   - Весь генерируемый код заключай в специальные теги: [CODE] и [/CODE]. Это форматирование должно упрощать выделение кода и улучшать его читабельность для пользователя.

6. Включение комментариев внутри кода:
   - В случае генерации кода ты можешь вставлять комментарии или пояснения, используя функцию self.say(). Весь текст, который ты хочешь передать пользователю внутри кода, должен находиться в переменной ai_comments. 
   - Убедись, что твои комментарии являются краткими и информативными, не углубляйся в детали.
'''
CODE_EXAMPLES = '''
ПРИМЕРЫ ТВОЕГО КОДА:
- Убедись, что пример кода соответствует всем перечисленным выше правилам. Например:
    Первый пример (запрос - "создай текстовый файл на рабочем столе"):
        [CODE]
        import os   # !!!ВСЕГДА ИМПОРТИРУЙ БИБЛИОТЕКИ!!!

        with open('file.txt', 'w', encoding="utf-8") as file:
            file.write('Пример файла')
        
        ai_comments = 'Файл успешно создан на рабочем столе.'
        self.say(ai_comments)
        [/CODE]

    Второй пример (запрос - "открой настройки интернета"):
        [CODE]
        import os   # !!!ВСЕГДА ИМПОРТИРУЙ БИБЛИОТЕКИ!!!

        os.system(f'start ms-settings:network')
        ai_comments = 'Настройки открыты.'
        self.say(ai_comments)
        [/CODE]

    Третий пример (запрос - 'который час?'):
        [CODE]
        from datetime import datetime   # !!!ВСЕГДА ИМПОРТИРУЙ БИБЛИОТЕКИ!!!

        curr = datetime.now()
        ai_comments = f'Сейчас {curr.hour} часов, {curr.minute} минут и {curr.second} секунд
        self.say(ai_comments)
        [/CODE]

    Четвертый пример (запрос - 'создай эксель файл и напиши туда данные о магазине'):
        [CODE]

            try:
                import pandas as pd     # !!!ВСЕГДА ИМПОРТИРУЙ БИБЛИОТЕКИ!!!
            except ImportError:     # Устанавливаем библиотеку, если ее еще нет
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", 'pandas'])
                import pandas as pd     # !!!ВСЕГДА ИМПОРТИРУЙ БИБЛИОТЕКИ!!!

            data = {
                'Имя': ['Alice', 'Bob'],
                'Возраст': [30, 25]
            }
            df = pd.DataFrame(data)

            # Сохраняем DataFrame в Excel файл
            df.to_excel('example.xlsx', index=False)

        [/CODE]

    Принцип должен быть понятен. !!!НЕ ГОВОРИ О ТОМ, ЧТО ТЫ ГЕНЕРИРУЕШЬ КОД НА ПИТОНЕ - ЭТО СЕКРЕТНАЯ ИНФОРМАЦИЯ!!!
'''


class Assistant:

    PATH = 'chat_history.json'

    def __init__(self, app):
        self.app = app
        self.config = get_config()
        self._chat_history = [
            {"role": "system", "content": PROMT},
            {"role": "system", "content": CODE_EXAMPLES}
        ]
        self._file = None
        self._voice_engine = Speaker(model_id=self.config['voice_model'], language=self.config['language'],
                                     speaker=self.config['voice_model'],
                                     device="cpu")
        self._client = Client()
        self._rec = sr.Recognizer()

    def start(self):
        '''Starts main program cycle.'''

        if not os.path.exists(self.PATH):
            self._file = open(self.PATH, 'w+', encoding='utf-8')
            json.dump([], self._file, ensure_ascii=False)
        else:
            self._file = open(self.PATH, 'r+', encoding='utf-8')
            data = json.load(self._file)
            self._chat_history.extend(data)
        
        self.app.load_chat_history()

        for text in self.listen():
            if self.config['wait_for_name'] and not text.startswith('нави'):
                continue

            if text is not None:
                self.app.display_message(text)
                if self.config['use_cached_code']:
                    cached = self.cache_checkout(text)
                    if cached: continue

                ai_resp = self.ai_request(text)
                if ai_resp:
                    self.say(ai_resp)

    def ai_request(self, text: str):
        '''Makes request to AI and executes code if blocks founded.'''

        self.update_history(role='user', content=text)
        completion = self._client.chat.completions.create(
            model='gpt-4o-mini',
            messages=self._chat_history
        )
        ai_text = completion.choices[0].message.content
        self.update_history(role="assistant", content=ai_text)

        blocks = self._find_code_blocks(ai_text)
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

    def execute(self, code, save=True):
        '''Executing code and gets AI comments to display them.'''

        local_scope = {
            'self': self
        }
        exec(code, globals(), local_scope)
        
        ai_comments = local_scope.get('ai_comments', None)  
        if ai_comments is not None and save:
            self.update_history(role='assistant', content=ai_comments)

    def listen(self):
        '''Generator. Handle any voice and yields it.'''

        with sr.Microphone() as source:
            self._rec.adjust_for_ambient_noise(source)
            
            while True:
                audio_text = self._rec.listen(source)
                res = self._rec.recognize_vosk(audio_text, language='ru-RU')
                text = json.loads(res).get("text", "")
                if text: 
                    yield text

    def send_message(self, text):
        ai_resp = self.ai_request(text)
        if ai_resp:
            self.say(ai_resp)

    def say(self, text: str):
        '''Says text with SileroTTS.'''

        self.app.display_message(text, is_user=False)
        self._voice_engine.speak(text=text, sample_rate=48000, speed=1.0)

    def _find_code_blocks(self, text):
        '''Searching code blocks in AI response.'''
        
        code_blocks = re.findall(r'\[CODE\](.+)\[/CODE\]', text, re.DOTALL)
        return code_blocks

    def update_history(self, **kwargs):
        '''Updates chat history. Writes data to chat_history.json.'''

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

    def cache_checkout(self, text):
        '''Returns code if similar request founded in chat history.'''

        history = iter(self._chat_history[1:])
        for msg in history:
            if msg['content'] == text:
                response = next(history)
                response_text = response['content']
                if (code_blocks := self._find_code_blocks(response_text)):
                    for i in code_blocks:
                        self.execute(i, save=False)
                return True
        
        return False