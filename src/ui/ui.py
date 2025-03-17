from assistant import Assistant
from . import settings

import customtkinter as ctk
import tkinter as tk
from PIL import Image

import threading
import os
import sys



class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Settings")
        self.geometry("400x300")

        config = settings.get_config()

        self.wait_for_name_var = ctk.BooleanVar(value=config['wait_for_name'])
        self.use_cached_code_var = ctk.BooleanVar(value=config['use_cached_code'])

        self.wait_for_name_checkbox = ctk.CTkCheckBox(
            self, 
            text="Wait for name", 
            variable=self.wait_for_name_var
        )
        self.wait_for_name_checkbox.pack(pady=10)

        self.use_cached_code_checkbox = ctk.CTkCheckBox(
            self, 
            text="Use cached code", 
            variable=self.use_cached_code_var
        )
        self.use_cached_code_checkbox.pack(pady=10)

        self.apply_button = ctk.CTkButton(self, text="Apply", command=self.apply_changes)
        self.apply_button.pack(pady=20)

    def apply_changes(self):
        settings.update_config(
            use_cached_code=self.use_cached_code_checkbox.get(),
            wait_for_name=self.wait_for_name_checkbox.get()
        )
        self.master.destroy()
        os.execv(sys.executable, ['python'] + sys.argv)


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Navi app")
        self.geometry("800x600")
        self.resizable = False

        self.logo = ctk.CTkImage(
            dark_image=Image.open(r'NAVI\src\ui\logo.png'), size=(100, 89)
        )
        self.logo_label = ctk.CTkLabel(self, image=self.logo, text="")
        self.logo_label.pack()

        self.chat_frame = ctk.CTkScrollableFrame(self)
        self.chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(padx=10, pady=10, fill="x")

        self.message_entry = ctk.CTkEntry(self.input_frame)
        self.message_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.send_button = ctk.CTkButton(self.input_frame, text="Отправить", command=self.send_message)
        self.send_button.pack(side="right", padx=10, pady=10)

        self.settings_button = ctk.CTkButton(self, text="Настройки", command=self.open_settings)
        self.settings_button.pack(pady=20)

        self.assistant = Assistant(self)
        self.run_in_thread(self.assistant.start)

    def open_settings(self):
        settings_window = SettingsWindow(self)

    def display_message(self, message, is_user=True):
        message_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        message_frame.pack(fill="x", pady=5, padx=10, anchor="e" if is_user else "w")

        bubble_color = "#d2e6f3" if is_user else "#8480fd"
        text_color = "#000000"

        message_bubble = ctk.CTkLabel(
            message_frame,
            text=message,
            wraplength=500,
            justify="left",
            fg_color=bubble_color,
            text_color=text_color,
            corner_radius=15,
            padx=10,
            pady=5,
            font=ctk.CTkFont(size=15)
        )
        message_bubble.pack(anchor="e" if is_user else "w")

        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def send_message(self):
        user_message = self.message_entry.get()
        if user_message.strip():
            self.display_message(user_message, is_user=True)
            self.run_in_thread(self.assistant.send_message, user_message)
        self.message_entry.delete(0, tk.END)

    def load_chat_history(self):
        for i in self.assistant._chat_history[1:]:
            text  = i['content']
            if '[CODE]' not in text:
                if i['role'] == 'user':
                    self.display_message(text, is_user=True)
                else:
                    self.display_message(text, is_user=False)

    def run_in_thread(self, func, *args):
        assistant_thread = threading.Thread(target=func, args=args)
        assistant_thread.daemon = True
        assistant_thread.start()
