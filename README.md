<div align="center">
<h1>TGUploadAPI</h1>

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-available-2496ED?logo=docker)](docker-compose.yml)

</div>

A FastAPI service that helps Telegram bots handle large files by using private channels as a bridge. 🚀

## Overview

Telegram bots are great, but they're stuck with a 50MB file limit. That's where this small project comes in! ✨

This service helps you:

- Upload files up to 2GB (4GB with premium) 📤
- Manage uploads through a simple API 🎯
- Handle different file types automatically 🎨

## Important Setup Notes

1. Your bot must be an admin in the private channel
2. The bot should watch for messages in the channel that start with `Task ID:`
3. Each uploaded file will be posted in the channel with its task ID in the caption
4. For webhook bots: make sure `channel_post` is included in your `allowed_updates`
5. If you're not using this on a remote server, make sure to close port 8000. For example:
   ```bash
   sudo ufw deny 8000
   ```

## Getting Started

### Option 1: Docker Installation (Recommended)

1. Make sure you have Docker and Docker Compose installed
2. Clone the repository:

```bash
git clone https://github.com/ASafarzadeh/tguploadapi.git
cd tguploadapi
```

3. Create your config file:

```bash
cp env.example .env
```

4. Edit the `.env` file with your Telegram credentials

5. Create a data directory for persistent storage and set proper permissions:

```bash
mkdir -p ./data
chmod 777 ./data
```

> **Note:** For production environments, consider using more restrictive permissions for the `./data` directory (e.g., `chmod 700 ./data` or adjusting ownership) based on your security requirements and how your Docker container user is configured.

6. Start the service:

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000

### Option 2: Manual Installation

1. Clone the repository:

```bash
git clone https://github.com/ASafarzadeh/tguploadapi.git
cd tguploadapi
pip install -r requirements.txt
```

2. Create your config file:

```bash
cp env.example .env
```

3. Add your Telegram credentials to `.env`

4. Start the service:

```bash
python run.py
```

## API Documentation

### Base URL

```
http://localhost:8000
```

### Endpoints

#### 1. Upload File

Upload a file from a URL to the Telegram channel.

```http
POST /api/upload
Content-Type: application/json
```

**Request Body:**

```json
{
  "url": "https://example.com/file.mp4",
  "force_document": false
}
```

| Parameter      | Type    | Required | Description                                                       |
| -------------- | ------- | -------- | ----------------------------------------------------------------- |
| url            | string  | Yes      | The URL of the file to upload. Must be a valid HTTP(S) URL.       |
| force_document | boolean | No       | If true, forces the file to be sent as a document. Default: false |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com/file.mp4",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid URL or request body
- `422 Unprocessable Entity`: Invalid URL format
- `500 Internal Server Error`: Server-side error

#### 2. Check File Status

Get the status of an uploaded file.

```http
GET /api/file/{task_id}
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|--------|-------------|
| task_id | string | The ID of the upload task |

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "channel_message_id": "12345",
  "status": "completed",
  "error_message": null
}
```

**Response (425 Too Early):**

```json
{
  "detail": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "message": "File is still being processed"
  }
}
```

**Error Responses:**

- `404 Not Found`: Task ID not found
- `500 Internal Server Error`: Server-side error

### Status Codes

| Status     | Description                           |
| ---------- | ------------------------------------- |
| pending    | Task created, waiting to be processed |
| processing | File is being downloaded and uploaded |
| completed  | File successfully uploaded to channel |
| failed     | Upload failed (check error_message)   |

## Environment Variables

The application uses the following environment variables:

#### API Configuration

| Variable   | Description     | Default |
| ---------- | --------------- | ------- |
| `API_HOST` | Host to bind to | 0.0.0.0 |
| `API_PORT` | Port to bind to | 8000    |

#### Telegram Configuration

| Variable             | Description                                    | Required |
| -------------------- | ---------------------------------------------- | -------- |
| `TELEGRAM_API_ID`    | Your Telegram API ID from my.telegram.org/apps | Yes      |
| `TELEGRAM_API_HASH`  | Your Telegram API Hash                         | Yes      |
| `TELEGRAM_PHONE`     | Your phone number with country code            | Yes      |
| `PRIVATE_CHANNEL_ID` | ID of your private channel (starts with -100)  | Yes      |
| `BOT_TOKEN`          | Your bot token from @BotFather                 | No       |

#### Database Configuration

| Variable       | Description                    | Default               |
| -------------- | ------------------------------ | --------------------- |
| `DATABASE_URL` | SQLite database connection URL | sqlite:///tgupload.db |

Note: Log level and auto-reload options can only be configured through command-line arguments.

### Example .env File

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Telegram Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE="+1234567890"
PRIVATE_CHANNEL_ID=-100123456789
BOT_TOKEN=your_bot_token

# Database Configuration
DATABASE_URL=sqlite:///data/tgupload.db
```

### Command Line Options

The application can be configured using command-line arguments:

```bash
python run.py [options]
```

Available options:

| Option        | Description                                           | Default |
| ------------- | ----------------------------------------------------- | ------- |
| `--host`      | Host to bind to                                       | 0.0.0.0 |
| `--port`      | Port to bind to                                       | 8000    |
| `--reload`    | Enable auto-reload on code changes                    | False   |
| `--log-level` | Set logging level (debug/info/warning/error/critical) | info    |

Examples:

1. Run on a specific port:

```bash
python run.py --port 8080
```

2. Run on localhost only:

```bash
python run.py --host 127.0.0.1
```

3. Run with auto-reload enabled:

```bash
python run.py --reload
```

4. Run with debug logging:

```bash
python run.py --log-level debug
```

5. Combine multiple options:

```bash
python run.py --host 127.0.0.1 --port 8080 --reload --log-level debug
```

### Docker Configuration

When using Docker, you can override the default configuration by modifying the `docker-compose.yml` file:

```yaml
services:
  api:
    # ... other settings ...
    ports:
      - "8080:8000" # Change host port (8080) to your preferred port
    environment:
      - DATABASE_URL=sqlite:///data/tgupload.db
      - API_HOST=127.0.0.1
      - API_PORT=8080
```

## Built with

- Python 3.8+ 🐍
- FastAPI ⚡
- Telethon 📱
- SQLAlchemy 🗄️
- Docker 🐳

## License

MIT License - Feel free to use it! 🎨

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=ASafarzadeh/tguploadapi&type=Date)](https://www.star-history.com/#ASafarzadeh/tguploadapi&Date)

</div>
