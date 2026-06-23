from fastapi import FastAPI
from src.utils.db import Base, engine
from src.staff.router import staff_router
from src.orders.router import orders_router
from src.menu.router import menu_router
from src.deadline.router import deadline_router

from fastapi.middleware.cors import CORSMiddleware
from src.utils.settings import settings
from src.utils.limiter import limiter
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# import logging

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
from datetime import datetime

# Set up standard logging to catch catch-all errors
# logger = logging.getLogger("uvicorn.error")

# Log every request (method, path, status, duration), auth failures, and database errors.
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("foodhub")


# Create the FastAPI app with metadata
app = FastAPI(
    title="FoodHub API",
    version="1.0.0",
    description="Meal ordering platform API",
    docs_url=None,
    redoc_url=None,
)
app.state.limiter = limiter

#Upload directory for menu images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#This is the permission method that allows sharing between your servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_LINK], #Allows only CORS with this server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], #Allows ALL methods in the server
    allow_headers=["*"],
)

#Link the routes from the router.py file into the main backend server
app.include_router(staff_router)
app.include_router(orders_router)
app.include_router(menu_router)
app.include_router(deadline_router)

# Base.metadata.create_all(bind=engine)

#################################################################################


# Global Exception Handler
# FastAPI() without exception handlers. 
# 500 errors return the default FastAPI JSON.
# This prevents stack traces leaking in production and provides consistent error format.
#################################################################################
# @app.exception_handler(HTTPException)
# @app.exception_handler(RequestValidationError)
# @app.exception_handler(Exception)  # catch-all

# 1. Catch intentional HTTPExceptions raised in your routers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_type": "HttpError"}
    )

# 2. Catch Pydantic validation errors (bad/missing frontend data)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Simplify the complex validation error payload for your frontend
    readable_errors = [
        {"field": " -> ".join(str(loc) for loc in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid data format sent to server.", "errors": readable_errors, "error_type": "ValidationError"}
    )

# 3. The Catch-All: Handle unexpected bugs, DB crashes, or broken code
@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    # Log the full stack trace to your terminal/logs so you can debug it later
    # logger.error(f"Unhandled error occurred: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later.", "error_type": "SystemError"}
    )

# GET /health endpoint for load balancers or monitoring.
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}