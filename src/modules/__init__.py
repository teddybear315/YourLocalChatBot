import json
from modules.utils import Utils

config = json.load(open("config/config.json"))
secrets = json.load(open("config/secrets.json"))

utils = Utils(config)

db = {} # FIXME database dont even work yet lmao