from fastapi import FastAPI, HTTPException

app =FastAPI()

@app.get("/hello world")
def index():
    return{"HI hellocdworld"}