import json

with open("config/config.json") as f:
    server = json.load(f)["server"]
HOST = server["host"]
PORT = server["port"]

with open("_.js", encoding="utf-8") as f:
    s = f.read()

s = s.replace(
    "@@@DOCTORATE@@@HOST@@@", HOST, 1
).replace(
    "@@@DOCTORATE@@@PORT@@@", str(PORT), 1
)

with open("_.static.js", "w", encoding="utf-8") as f:
    f.write(s)
