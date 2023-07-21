import requests

r = requests.head("https://ak.hypergryph.com/downloads/android_lastest")

with open("game.txt", "w") as f:
    f.write(r.headers.get("location"))
