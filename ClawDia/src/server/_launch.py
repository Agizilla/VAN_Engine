import sys
sys.path.insert(0, r'C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ClawDia')
from src.server.app import app
import uvicorn
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
