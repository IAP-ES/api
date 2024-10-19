# API Project Setup

This document explains how to set up and run the API using Poetry and Uvicorn. Follow these steps to install dependencies, activate the virtual environment, and run the application.

## Prerequisites

Before you start, make sure you have the following installed on your machine:

- [Python 3.x](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation) (for dependency management)

## Installation Instructions

### Step 1: Install Project Dependencies

To install all required dependencies for this project, run the following command:

```bash
poetry install
```

This will install all dependencies listed in the pyproject.toml file.

### Step 2: Activate the Virtual Environment

Once the dependencies are installed, you need to activate the virtual environment created by Poetry. Run:

```bash
poetry shell
```

This will activate the environment, and you’ll be able to run the app with the dependencies isolated from the global environment.

### Step 3: Run the Application

After activating the environment, start the application using Uvicorn:

```bash
uvicorn main:app --reload
```

This command starts the FastAPI application in development mode with live-reloading enabled. The API will be available at http://127.0.0.1:8000.

## Additional Information

- **Uvicorn:** Uvicorn is an ASGI server used to run FastAPI applications.
- **Poetry:** Poetry is a dependency management and packaging tool for Python that helps manage the project’s virtual environment and dependencies.
