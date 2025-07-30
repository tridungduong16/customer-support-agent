# Customer Support Agent

An intelligent customer support system built with LangGraph and FastAPI that provides automated support through specialized agents handling different aspects of customer inquiries.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Agent System**: Specialized agents for different support areas:
  - Technical Support Agent
  - Billing Agent
  - General Information Agent
  - Supervisor Agent
- **Intelligent Routing**: Automatically routes customer inquiries to the most appropriate agent
- **MongoDB Integration**: Persistent storage for conversation history and customer data
- **FastAPI Backend**: High-performance API endpoints with automatic documentation
- **LangGraph Framework**: Sophisticated conversation flow management
- **Real-time Processing**: Asynchronous request handling for better performance

## Architecture

The project follows a modular architecture with the following components:

```
src/
├── agents/              # Agent definitions and logic
│   ├── members/        # Individual agent implementations
│   ├── builder.py      # Agent construction utilities
│   ├── nodes.py        # Graph node definitions
│   ├── run.py          # Agent execution logic
│   └── types.py        # Type definitions
├── database_handler/    # Database interaction layer
├── main.py             # Application entry point
├── prompt_lib.py       # Prompt templates and utilities
└── schema.py           # Data models and schemas
```

## Installation

1. Ensure you have Python 3.13+ installed
2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd customer-support-agent
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

4. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

1. Start the FastAPI server:
   ```bash
   uvicorn src.main:app --reload
   ```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. Make API requests to interact with the customer support system:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "I need help with billing"}'
   ```

## Configuration

The application can be configured through environment variables:

- `MONGODB_URI`: MongoDB connection string
- `API_KEY`: Your API key for authentication
- `LOG_LEVEL`: Logging level (default: INFO)
- `PORT`: Server port (default: 8000)

See `.env.example` for all available configuration options.

## Development

This project uses several development tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **pytest**: Testing framework
- **uvicorn**: ASGI server

Development commands:

```bash
# Format code
black src/
isort src/

# Run tests
pytest

# Run with hot reload
uvicorn src.main:app --reload
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
