from flask import Flask
from config import DevelopmentConfig
import peewee

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
configdb = app.config['DATABASE']


db = peewee.MySQLDatabase("wifi_db",
                              host = configdb['host'],
                              user = configdb['user'],
                              password =configdb['password']
                              )

# This hook ensures that a connection is opened to handle any queries
# generated by the request.
@app.before_request
def _db_connect():
    db.connect()
 
# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()
        
