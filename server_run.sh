rm -rf __pycache__
fuser -kn tcp 8000 # Kill process on 8000 port
uvicorn fastapi_server:app --workers 4 --reload # run server