from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/some-path")
async def get_some_path():
    return {"message": "This is service-a"}

@app.post("/some-path")
async def post_some_path(data: dict):
    return {"message": "POST request to service-a", "data": data}

@app.put("/some-path")
async def put_some_path(data: dict):
    return {"message": "PUT request to service-a", "data": data}

@app.delete("/some-path")
async def delete_some_path():
    return {"message": "DELETE request to service-a"}

@app.patch("/some-path")
async def patch_some_path(data: dict):
    return {"message": "PATCH request to service-a", "data": data}