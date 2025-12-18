from fastapi import FastAPI
from app.api.routes import auth, users, tenants

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])

@app.get("/ping")
async def ping():
    return {"message": "pong"}
