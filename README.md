# WorkOrder App API

A FastAPI backend for managing users, work orders, and activity logs. The project uses SQLAlchemy for database access, JWT authentication for protected work order routes, and Pydantic schemas for request/response validation.

## Features

- User registration and login
- JWT-based authentication for protected work order routes
- CRUD operations for work orders
- Activity log creation and retrieval
- SQLite or other SQL database via SQLAlchemy connection string

## Tech stack

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PyJWT
- pwdlib

## Project structure

- `main.py` - application entry point
- `src/users/` - user registration, login and authentication logic
- `src/workorders/` - work order API routes and controller logic
- `src/activityLog/` - activity log routes and controller logic
- `src/utils/` - database access, settings, and auth helper

## Requirements

Install required packages in your virtual environment.

```powershell
python -m venv myenv
myenv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic-settings pyjwt pwdlib
```

> Note: `requirement.txt` is currently empty, so install dependencies manually or add pinned versions if needed.

## Environment variables

Create a `.env` file at the project root with the following values:

```env
DB_CONNECTION=sqlite:///./app.db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
EXPIRY_TIME=30
```

Update `DB_CONNECTION` to your database URL as needed.

## Run the app

Start the FastAPI app with Uvicorn:

```powershell
uvicorn main:app --reload
```

By default, the app will be available at:

- `http://127.0.0.1:8000`
- Open `http://127.0.0.1:8000/docs` for Swagger UI

## API Endpoints

### User endpoints

- `POST /user/register`
  - Body: `UserSchema`
  - Registers a new user

- `GET /user/all`
  - Returns all users

- `POST /user/login`
  - Body: `LoginSchema`
  - Returns a JWT token

- `GET /user/auth`
  - Validates the provided token

- `DELETE /user/delete/{id}`
  - Deletes a user by ID

### Work order endpoints (protected)

All work order routes require an `Authorization` header with a valid JWT:

```http
Authorization: Bearer <token>
```

- `POST /workorders/create`
  - Body: `WorkSchema`
  - Creates a work order

- `GET /workorders/all`
  - Returns all work orders

- `GET /workorders/id/{id}`
  - Returns one work order by ID

- `PUT /workorders/edit/{id}`
  - Body: `WorkSchema`
  - Updates the work order with the given ID

- `DELETE /workorders/delete/{id}`
  - Deletes the work order with the given ID

### Activity log endpoints

- `POST /activity_log/create`
  - Creates a new activity log item

- `GET /activity_log/all`
  - Lists all activity log entries

- `GET /activity_log/id/{id}`
  - Returns a single activity log entry by ID

- `DELETE /activity_log/delete/{id}`
  - Deletes an activity log entry by ID

## Data models

### User request schema

```json
{
  "user_id": 1,
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "role": "admin",
  "hash_password": "password123"
}
```

### Login request schema

```json
{
  "email": "jane@example.com",
  "password": "password123"
}
```

### Work order request schema

```json
{
  "id": 1,
  "name": "Inspect site",
  "description": "Inspect the repair site",
  "priority": "High",
  "site": "Head Office",
  "created_at": "2026-05-18T10:00:00",
  "due_date": "2026-05-20T18:00:00"
}
```

## Token usage example

After a successful login, use the returned token for protected work order requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Notes

- The app automatically creates database tables on startup using `Base.metadata.create_all(bind=engine)`.
- If you want to add dependency pinning, populate `requirement.txt` with exact package versions.
- Keep your `SECRET_KEY` private and do not commit `.env` to source control.
