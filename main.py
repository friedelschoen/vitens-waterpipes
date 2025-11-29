import threading
import backend.water_network_control
from backend.api_server import app as api_server
from backend import database_api

database_api.create_tables()

def run_api_server():
    api_server.run(host='0.0.0.0', port=5000)

threading.Thread(target=backend.water_network_control.main).start()
run_api_server()
