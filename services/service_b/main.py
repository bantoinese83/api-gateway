from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "service_a_healthy": True,
        "service_b_healthy": True
    }

@app.get("/some-path")
async def get_some_path():
    return {"message": "This is service-b"}

@app.post("/some-path")
async def post_some_path(data: dict):
    return {"message": "POST request to service-b", "data": data}

@app.put("/some-path")
async def put_some_path(data: dict):
    return {"message": "PUT request to service-b", "data": data}

@app.delete("/some-path")
async def delete_some_path():
    return {"message": "DELETE request to service-b"}

@app.patch("/some-path")
async def patch_some_path(data: dict):
    return {"message": "PATCH request to service-b", "data": data}
