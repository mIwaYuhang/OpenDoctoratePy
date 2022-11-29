import os
import socket
import hashlib
import requests

from datetime import datetime
from flask import Response, stream_with_context, redirect
from constants import CONFIG_PATH
from core.function.loadMods import loadMods
from utils import read_json, write_json

header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53"}
modsList = {"mods": [], "name": [], "path": [], "download": []}
if read_json(CONFIG_PATH)["assets"]["enableMods"]:
    modsList = loadMods()


def writeLog(data):

    time = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    clientIp = socket.gethostbyname(socket.gethostname())
    print(f'{clientIp} - - [{time}] {data}')


def getFile(assetsHash, fileName):

    server_config = read_json(CONFIG_PATH)
    version = server_config["version"]["android"]["resVersion"]
    basePath  = os.path.join('.', 'assets', version, 'redirect')

    if not server_config["assets"]["downloadLocally"]:
        basePath  = os.path.join('.', 'assets', version)
        if fileName != 'hot_update_list.json'and fileName not in modsList["download"]:

            return redirect('https://ak.hycdn.cn/assetbundle/official/Android/assets/{}/{}'.format(version, fileName), 302)

    if not os.path.isdir(basePath):
        os.makedirs(basePath)
    filePath = os.path.join(basePath, fileName)

    wrongSize = False
    if not os.path.basename(fileName) == 'hot_update_list.json':
        temp_hot_update_path = os.path.join(basePath, "hot_update_list.json")
        hot_update = read_json(temp_hot_update_path)
        if os.path.exists(filePath):
            for pack in hot_update["packInfos"]:
                if pack["name"] == fileName.rsplit(".", 1)[0]:
                    wrongSize = os.path.getsize(filePath) != pack["totalSize"]
                    break

    if server_config["assets"]["enableMods"] and fileName in modsList["download"]:
        for mod, path in zip(modsList["download"], modsList["path"]):
            if fileName == mod and os.path.exists(path):
                wrongSize = False
                filePath = path

    writeLog('/{}/{}'.format(version, fileName))

    return export('https://ak.hycdn.cn/assetbundle/official/Android/assets/{}/{}'.format(version, fileName), filePath, assetsHash, wrongSize)


def downloadFile(url, filePath):

    writeLog('\033[1;33mDownload {}\033[0;0m'.format(os.path.basename(filePath)))
    file = requests.get(url, headers=header, stream=True)

    with open(filePath, 'wb') as f:
        for chunk in file.iter_content(chunk_size=512):
            f.write(chunk)
            yield chunk


def export(url, filePath, assetsHash, redownload = False):

    server_config = read_json(CONFIG_PATH)

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Content-Disposition": "attachment; filename=" + os.path.basename(filePath),
        "Content-Type": "application/octet-stream",
        "Expires": "0",
        "Etag": hashlib.md5(filePath.encode('utf-8')).hexdigest(),
        "Last-Modified": datetime.now(),
        "Pragma": "no-cache"
    }

    if os.path.basename(filePath) == 'hot_update_list.json':
        
        if os.path.exists(filePath):
            hot_update_list = read_json(filePath)
        else:
            hot_update_list = requests.get(url, headers=header).json()
            write_json(hot_update_list, filePath)
            
        abInfoList = hot_update_list["abInfos"]
        newAbInfos = []
        
        for abInfo in abInfoList:
            if server_config["assets"]["enableMods"]:
                hot_update_list["versionId"] = assetsHash
                if len(abInfo["hash"]) == 24:
                    abInfo["hash"] = assetsHash
                if abInfo["name"] not in modsList["name"]:
                    newAbInfos.append(abInfo)
            else:
                newAbInfos.append(abInfo)

        if server_config["assets"]["enableMods"]:
            for mod in modsList["mods"]:
                newAbInfos.append(mod)

        hot_update_list["abInfos"] = newAbInfos

        cachePath = './assets/cache/'
        savePath = cachePath + 'hot_update_list.json'

        if not os.path.isdir(cachePath):
            os.makedirs(cachePath)
        write_json(hot_update_list, savePath)

        with open(savePath, 'rb') as f:
            data = f.read()
        
        return Response(
            data,
            headers=headers
        )

    if os.path.exists(filePath) and not redownload:
        with open(filePath, "rb") as f:
            data = f.read()
        headers["Content-Length"] = os.path.getsize(filePath)
        
        return Response(
            data,
            headers=headers
        )

    else:
        file = requests.head(url, headers=header)
        total_size_in_bytes = int(file.headers.get('Content-length', 0))
        headers["Content-Length"] = total_size_in_bytes
            
    return Response(
        stream_with_context(downloadFile(url, filePath)),
        headers=headers
    )
