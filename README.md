# .NET Legacy to Microservices Migration Tool

This is a powerful tool designed to automatically analyze legacy .NET WCF projects and migrate them to modern microservice architectures using both REST API and gRPC patterns. It consists of a FastAPI-based backend for handling analysis and migration logic, a React-based frontend for user interaction, and integrated RAG services for intelligent code understanding. The tool simplifies the process of transforming monolithic .NET applications into scalable, modular microservices.

## Overview

The tool provides a seamless way to modernize legacy .NET applications, supporting Web Forms, ASP.NET MVC, and other .NET project types. It intelligently analyzes code structures, generates microservice architectures, and supports both REST and gRPC API patterns. With support for multiple input sources like Git repositories and ZIP files, the tool offers flexibility and automation for developers looking to upgrade to .NET 6.0, 7.0, or 8.0. Additionally, it includes user authentication to secure access to key functionalities, ensuring only authorized users can perform analysis and migration tasks.

## Key Features

The tool is packed with features to streamline the migration process:

- **Automatic Code Analysis**: Analyzes legacy .NET Web Forms, ASP.NET MVC, and other .NET projects to understand their structure and dependencies.
- **Microservice Architecture Generation**: Converts monolithic applications into microservices following onion architecture principles.
- **Dual API Support**: Supports both REST API and gRPC microservice patterns for flexible deployment.
- **Multiple Input Sources**: Accepts Git repository URLs or ZIP file uploads for project analysis.
- **Intelligent Structure Detection**: Automatically identifies controllers, models, views, services, and other components in the source code.
- **Target Framework Support**: Migrates projects to .NET 6.0, 7.0, or 8.0, ensuring compatibility with modern .NET ecosystems.
- **Database Migration**: Handles both Entity Framework and ADO.NET patterns with MySQL support for data access.
- **Authentication Handling**: Integrates JWT-based user authentication with registration and login, securing API endpoints and enabling user-specific analysis and migration sessions.
- **Interactive Frontend**: Provides a user-friendly React interface for submitting analysis requests, viewing results, editing target structures, and managing user authentication.
- **RAG-Enhanced Intelligence**: Utilizes retrieval-augmented generation for contextual understanding of source code and target architectures.
- **LangSmith Integration**: Tracks and monitors migration processes, including token usage for LLM calls, to optimize performance and aid debugging.

## Architecture

The tool is built with a modular architecture, consisting of the following key components:

- **Backend Services**:
  - **Analysis Service**: Responsible for analyzing the structure and dependencies of legacy .NET code.
  - **Migration Service**: Performs the actual code transformation and migration to the target microservice architecture.
  - **Authentication Service**: Manages user registration, login, and JWT token-based authentication for securing API endpoints.
- **Frontend Components**:
  - React-based user interface for input submission, result visualization, interactive editing of analysis outputs, and user authentication (login and registration).
- **RAG Services**:
  - **Analysis RAG Service**: Manages vector embeddings and querying for source code structure understanding.
  - **Target Structure RAG Service**: Handles context for desired microservice architectures using vector stores.
- **File Utilities**: Manages file operations, including Git cloning and ZIP file handling.
- **Database Layer**: Stores analysis results, migration history, user credentials, and project metadata using SQLAlchemy models.

## LangSmith Integration

The tool integrates **LangSmith** for tracing and monitoring the migration process, particularly for logging token usage and debugging LLM-driven operations. LangSmith is initialized in the backend (`migration_service.py`) using a secure session with an API key stored in the environment variable `LANGCHAIN_API_KEY`. Key aspects include:

- **Token Usage Tracking**: The `TokenTracker` class logs comprehensive token usage for LLM calls, including total tokens, prompt tokens, response tokens, and per-microservice breakdowns.
- **Traceable Operations**: Critical methods like `generate_code`, `generate_gateway`, and `process_and_zip_projects` are decorated with `@traceable`, enabling detailed tracing of inputs, outputs, and performance metrics in LangSmith's dashboard (accessible via https://smith.langchain.com).
- **Debugging and Optimization**: Logs token summaries (saved to JSON files, e.g., `<repo_name>_grpc_token_usage.json`) and detailed prompts for each file generation, helping developers identify high-token-consuming files and optimize LLM usage.
- **Setup**: Requires the `LANGCHAIN_API_KEY` environment variable to be set in the `.env` file for authentication with LangSmith's API.

This integration enhances transparency into the migration process, allowing developers to monitor resource usage and troubleshoot issues effectively.

## API Endpoints

The backend exposes several API endpoints to facilitate analysis, migration, and user authentication:

### `/analyze` (POST)
Analyzes a legacy .NET project and generates a proposed microservice structure. Requires authentication.

**Parameters**:
- `repo_url` (optional): URL of the Git repository containing the legacy project.
- `zip_file` (optional): ZIP file containing the legacy project.
- `target_version`: Target .NET version (e.g., `net6.0`, `net7.0`, `net8.0`).
- `api_type`: Desired API pattern (`rest` or `grpc`).
- `instruction` (optional): Custom migration instructions.
- `source_type` (optional): Source type (`git` or `zip`), auto-detected if not specified.

**Response**:
```json
{
  "status": "success",
  "data": {
    "analysis_id": "uuid",
    "repo_url": "repository-url",
    "target_version": "net8.0",
    "api_type": "rest",
    "structure": {}, // Basic project structure
    "target_structure": {} // Generated microservice architecture
  }
}
```

### `/migrate` (POST)
Performs the migration based on the analysis results. Requires authentication.

**Request Body**:
```json
{
  "analysis_id": "uuid",
  "target_structure": {}, // Microservice structure
  "instruction": "optional custom instructions"
}
```

**Response**: Returns a JSON object containing:
- `zip_data`: Base64-encoded ZIP file of the migrated microservices.
- `filename`: Name of the ZIP file (e.g., `<repo_name>.zip`).
- `token_usage`: Token usage summary, including total tokens, prompt/response tokens, and microservice breakdowns.

### `/regenerate` (POST)
Regenerates the target microservice structure based on user feedback. Requires authentication.

**Request Body**:
```json
{
  "analysis_id": "uuid",
  "target_structure": {}, // Current structure
  "comments": "feedback for improvements"
}
```

**Response**: Returns an updated target structure.

### `/register` (POST)
Registers a new user, enabling access to authenticated endpoints.

**Parameters**:
- `username`: The desired username for the user.
- `password`: The user's password (hashed and stored securely in the database).

**Response**:
```json
{
  "status": "success",
  "message": "User registered successfully"
}
```

### `/login` (POST)
Authenticates a user and returns a JWT token for accessing protected endpoints.

**Parameters**:
- `username`: The user's username.
- `password`: The user's password.

**Response**:
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

## Migration Patterns

The tool supports two primary migration patterns to cater to different use cases:

### REST API Migration
For projects targeting REST APIs, the tool:
- Converts legacy applications to modern ASP.NET Core Web APIs.
- Implements the MVC pattern with Controllers, Models, and Views.
- Integrates Ocelot API Gateway for efficient routing.
- Supports Entity Framework Core or ADO.NET for data access.
- Incorporates JWT authentication for secure API access, using tokens issued via the `/login` endpoint.

### gRPC Migration
For projects targeting gRPC microservices, the tool:
- Transforms legacy applications into gRPC-based microservices.
- Generates `.proto` files from entities and repositories.
- Implements onion architecture with Domain, Application, Infrastructure, and Presentation layers.
- Uses ADO.NET with MySQL for data access.
- Includes a Gateway for HTTP-to-gRPC routing and a WebUI layer for user interfaces.

## Supported Source Patterns

The tool can handle a variety of legacy .NET project types and components, including:
- ASP.NET Web Forms (`.aspx`, `.aspx.cs`, `.ascx` files)
- ASP.NET MVC (Controllers, Views, Models)
- SOAP Services (`.asmx` files)
- Entity Framework (`DbContext`, Entities)
- ADO.NET (Connection and Command patterns)
- Configuration Files (`Web.config`, `appsettings.json`)

## Target Architecture Patterns

The tool follows the Onion Architecture for the generated microservices, organized into the following layers:
1. **Domain**: Contains entities, domain services, and repository interfaces.
2. **Application**: Includes DTOs, application services, and use cases.
3. **Infrastructure**: Manages data access, external services, and repository implementations.
4. **Presentation**: Handles controllers, views, and API endpoints.

## Authentication Strategies

The tool supports multiple authentication strategies for migrated applications:
- **Case 1**: No authentication, with the Gateway handling routing only.
- **Case 2**: A separate AuthService microservice for authentication.
- **Case 3**: Authentication integrated directly into the Gateway.

Additionally, the tool itself implements JWT-based user authentication to secure access to its functionality:
- **User Registration**: Users can register via the `/register` endpoint or the React frontend's Register component, providing a username and password. Credentials are securely hashed and stored in a MySQL database using SQLAlchemy.
- **User Login**: The `/login` endpoint authenticates users and issues a JWT token, which is stored in the browser's `localStorage`. This token is sent in the `Authorization` header (`Bearer <token>`) for all protected endpoints (`/analyze`, `/migrate`, `/regenerate`).
- **Protected Endpoints**: All key API endpoints require a valid JWT token, verified by the FastAPI backend using the `OAuth2PasswordBearer` scheme. The frontend automatically attaches the token to requests via an Axios interceptor.
- **Security**: Passwords are hashed using SHA-256, and JWT tokens have a configurable expiry (default: 24 hours). In production, the JWT secret key should be stored securely in an environment variable.

## Frontend

The frontend is built with React and provides an intuitive interface for users to:
- **Register and Log In**: Use the `Register` and `Login` components to create accounts and authenticate, securing access to analysis and migration features.
- Select source types (Git or ZIP) and provide inputs.
- Choose target .NET versions and API types (REST or gRPC).
- Submit custom instructions for migration.
- View and edit analysis results, including interactive project structure visualization.
- Initiate migrations and download resulting ZIP files.
- Handle existing analyses with options to start new ones or continue with previous results.
- View token usage details in a dedicated Token Usage tab, displaying total tokens, prompt/response tokens, and microservice breakdowns (powered by LangSmith data).

Key components include:
- `Login.jsx`: Provides a form for users to log in, storing the JWT token in `localStorage` upon successful authentication.
- `Register.jsx`: Allows new users to register, creating secure credentials in the backend database.
- `Analysis.jsx`: Handles analysis submission, result visualization, and migration initiation, with protected API calls.
- `AnalysisResult.jsx`: Displays and allows editing of analysis results, with options to save changes or start new analyses.
- `TokenUsage.jsx`: Displays token usage metrics (e.g., total tokens, per-microservice stats) from the `/migrate` endpoint, stored in `localStorage`.
- Forms for analysis submission, editable result displays, and modal views for detailed structure inspection.

## RAG Integration

The tool leverages LlamaIndex for intelligent code understanding through dedicated RAG services:
- **Target Structure RAG Service**: Initializes and manages vector stores for understanding desired architecture patterns in the target microservices. It loads JSON data, creates or loads indexes, and provides query engines for contextual retrieval.
- **Analysis RAG Service**: Maintains context of the source code structure for accurate analysis, using vector embeddings for semantic code matching and contextual code generation.
- Uses vector embeddings for semantic code matching and contextual code generation across both services.

## Error Handling

The tool includes robust error handling for:
- Invalid Git repository URLs
- Corrupted or invalid ZIP files
- Unsupported project structures
- Database connection issues
- LLM API failures
- Authentication failures (e.g., invalid credentials, expired tokens)
- Frontend validation for inputs, file types, and authentication status

## Installation and Setup

### Prerequisites
To use the tool, ensure you have the following installed:
- Python 3.8 or higher
- Git
- MySQL (for target applications and user authentication storage)
- Node.js and npm (for the React frontend)

### Installation
Clone the repository and install the required dependencies:
```bash
git clone <repository-url>
cd migration-tool
pip install -r requirements.txt
```

If needed, you can create a virtual environment and then install all the requirements:
```bash
python -m venv <environment_name>
<environment_name>\Scripts\Activate
pip install -r requirements.txt
```

### For Frontend
```bash
cd frontend
npm install
```

### Configuration
1. Configure the database connection in `config/db_config.py` for storing analysis results and user credentials.
2. Set up LLM settings in `config/llm_config.py`.
3. Configure frontend settings, such as API endpoints in React components (e.g., `VITE_BACKEND_URL` in the frontend's `.env` file).
4. Set the JWT secret key in `auth.py` or as an environment variable (`JWT_SECRET_KEY`) for secure authentication.
5. Set your Azure OpenAI API and embeddings endpoint and key, and database credentials in the `.env` file.
6. Set the `LANGCHAIN_API_KEY` environment variable in the `.env` file for LangSmith integration.

### Running the Service
Start the FastAPI backend server:
```bash
cd dotnet-microservice-extraction
python server.py
```

In a separate terminal, start the React Vite frontend:
```bash
cd dotnet-microservice-extractor-ui
npm run dev
```

For Swagger Documentation:
```
http://127.0.0.1:8000/docs
```
