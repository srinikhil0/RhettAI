# RhettAI - AI-Powered Educational Assistant

RhettAI is an intelligent educational assistant designed to help university students with their course materials. It automatically processes course content from Google Drive and provides interactive learning support through chat and quizzes.

## Features

- Automatic content processing from Google Drive
- Interactive chat interface for course-related questions
- Quiz generation from course materials
- Study planning and deadline reminders
- Context-aware responses with citations

## Prerequisites

- Python 3.8 or higher
- Google Cloud Project with enabled APIs
- Firebase Project (optional, for future features)
- Google Drive folder with course materials

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/RhettAI.git
   cd RhettAI
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Google Cloud:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable required APIs:
     - Google Drive API
     - Google Cloud Storage API (optional)
     - Firebase Admin SDK API (optional)
   - Create a service account and download credentials
   - Share your Google Drive folder with the service account email

5. Set up environment variables:
   Create a `.env` file in the project root:
   ```
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id
   GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
   FIREBASE_CREDENTIALS=./firebase-service-account.json  # Optional
   ```

6. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
RhettAI/
├── src/
│   ├── drive/
│   │   ├── monitor.py    # Google Drive monitoring
│   │   └── downloader.py # File downloading
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

## Development

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. Push to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request on GitHub

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Drive API
- OpenAI API
- Firebase (for future features) 