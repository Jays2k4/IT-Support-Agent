# AI-Powered IT Support Assistant

A full-stack application built with FastAPI, SQLite, React, and Google Gemini API to provide automated IT support in under 45 minutes for a coding assessment round !

## Project Structure
- `main.py`: The FastAPI backend application.
- `index.html`: The React frontend application (using CDN and Babel for in-browser transpilation).
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables (create this based on `.env.example`).

## Prerequisites
- Python 3.8+
- Google Gemini API Key

## Setup & Installation

1. **Install Dependencies**
   Navigate to the project directory and install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Create a `.env` file in the root of the project directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Run the Backend Server**
   Start the FastAPI server using Uvicorn:
   ```bash
   python main.py
   ```
   The backend will run on `http://localhost:8000`. On first run, it will automatically initialize the SQLite database (`it_support.db`) with some common Knowledge Base entries.

4. **Run the Frontend**
   Simply double-click the `index.html` file to open it in your web browser. The frontend interacts directly with the local backend API.

## API Endpoints

- `GET /api/kb`: Returns all predefined Knowledge Base entries.
- `POST /api/ticket`: Accepts a user query (`{"user_query": "..."}`), finds the best matching context from the Knowledge Base, queries the Gemini LLM for a solution, and stores the interaction as a Ticket in the database.
