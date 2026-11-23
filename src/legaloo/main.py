from fastapi import FastAPI

from .api.routes import auth, chat, courses, health, lessons
from .core.errors import install_error_handlers

app = FastAPI(title="Legaloo API")
install_error_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(lessons.router)
app.include_router(chat.router)
