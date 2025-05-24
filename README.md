# RhettAI - AI-Powered Educational Assistant

RhettAI is an intelligent educational assistant designed to help university students with their course materials. It automatically processes course content from Google Drive and provides interactive learning support through chat and quizzes.

## Features

- Automatic content processing from Google Drive
- Interactive chat interface for course-related questions
- Quiz generation from course materials
- Study planning and deadline reminders
- Context-aware responses with citations

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up Google Drive API:
   - Create a project in Google Cloud Console
   - Enable Google Drive API
   - Create credentials (OAuth 2.0)
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root

4. Create a `.env` file with the following variables:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id
   OPENAI_API_KEY=your_openai_api_key
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
RhettAI/
├── src/
│   ├── drive/
│   │   ├── monitor.py
│   │   └── downloader.py
│   ├── processor/
│   │   ├── pdf_parser.py
│   │   └── slide_parser.py
│   ├── knowledge/
│   │   ├── store.py
│   │   └── index.py
│   └── ai/
│       ├── chat.py
│       └── quiz.py
├── main.py
├── requirements.txt
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 