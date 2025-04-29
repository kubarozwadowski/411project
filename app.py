from flask import Flask
from config import ProductionConfig
from chefs_kitchen.db import db

app = Flask(__name__)
app.config.from_object(ProductionConfig)

db.init_app(app)
