from fastapi import FastAPI

def create_app():
    app = FastAPI(title="ORA Core", version="0.1")
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ora_core.main:app", host="0.0.0.0", port=8001, reload=True)
