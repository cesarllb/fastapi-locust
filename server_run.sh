rm -rf __pycache__
fuser -kn tcp 8000 # Kill process on 8000 port
uvicorn fastapi_server:app --reload # run server