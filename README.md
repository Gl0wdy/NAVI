# Ultra-Flexible AI Assistant - NAVI

![Laingif](https://i.pinimg.com/originals/34/67/fc/3467fc8d0dd144536008b2fa04887b22.gif)

⚠️ WARNING: NAVI may not function correctly due to its current development stage. This is an experimental project, so please use NAVI at your own risk.

## How Does It Work?
The operating principle is straightforward: instead of relying on predefined commands in the code, NAVI responds to voice requests. It generates and executes code to complete tasks as instructed. NAVI has access to all the information on your computer and can perform a wide range of actions, including:
- Manipulating files
- Opening any application on your PC
- Gathering system information to execute tasks
- Essentially, anything you can imagine!

## Installation
1. Clone the repository: \
   ```git clone https://github.com/Gl0wdy/NAVI.git```
2. Download the voice model from the official [Vosk website](https://alphacephei.com/vosk/models) and unpack it in the directory where you cloned NAVI.
3. Install the required dependencies:\
   ```pip install -r requirements.txt```

## Usage
1. Run the main script:\
   ```python main.py```
2. Enjoy!

## Last update
Basic interface & settings added. Also testing code caching system to improve productivity.

## Additional Information
- AI Model: gpt-4o-mini ([with g4f](https://github.com/xtekky/gpt4free))
- Voice recognizing Model: Vosk
- TTS model: [SileroTTS](https://github.com/denisxab/speakerpy)
- Future plans include adding a user interface and improving voice synthesis quality, among other enhancements...
