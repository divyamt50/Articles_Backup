# Articles Backend Services

A FastAPI-based backend service with authentication, database migrations, caching, background task processing, and pub/sub support.

## Features

- FastAPI application setup
- Authentication utilities
- Database integration
- Alembic migrations
- Rate limiting
- Caching support
- Background task processing
- Pub/Sub listener service

## Tech Stack

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Async Python

## Project Structure

```text
.
├── auth.py
├── cache.py
├── database.py
├── main.py
├── models.py
├── schema.py
├── tasks.py
├── pubsub_listener.py
├── rate_limit.py
├── migrations/
└── requirements.txt
