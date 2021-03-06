import os
import pathlib
import shutil

import bcolors
import requests

from dotenv import load_dotenv
from random import randint


def get_random_comic_num():
    latest_comic_url = "https://xkcd.com/info.0.json"
    response = requests.get(latest_comic_url)
    response.raise_for_status()
    latest_comic_num = response.json()["num"]
    random_comic_num = randint(1, latest_comic_num)

    return random_comic_num


def check_vk_response(response):
    if "error" in response:
        error_msg = f'Code:{response["error"]["error_code"]} --' \
                    f'{response["error"]["error_msg"]}'
        raise requests.HTTPError(error_msg)
    return response


def download_file(dir_name, img_name, url):
    response = requests.get(url)
    response.raise_for_status()
    with open(os.path.join(dir_name, img_name), "wb") as file:
        file.write(response.content)


def download_comic(dir_name, img_name, num):
    comic_download_url = "https://xkcd.com/{}/info.0.json".format(num)

    response = requests.get(comic_download_url)
    response.raise_for_status()
    comic_response = response.json()
    img_url = comic_response["img"]
    comic_alt = comic_response["alt"]
    comic_title = comic_response["title"]

    download_file(dir_name, img_name, img_url)
    return f"{comic_title}\n\n{comic_alt}"


def get_upload_url(endpoint, group_id, access_token, api_version="5.131"):
    params = {
        "access_token": access_token,
        "v": api_version,
        "group_id": group_id
    }
    response = requests.get(endpoint.format("photos.getWallUploadServer"),
                            params=params)
    response.raise_for_status()
    upload_url_response = response.json()
    check_vk_response(upload_url_response)
    upload_url = upload_url_response["response"]["upload_url"]
    return upload_url


def upload_img(upload_url, dir_name, img_name):
    with open(os.path.join(dir_name, img_name), 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
    response.raise_for_status()
    upload_img_response = response.json()
    server = upload_img_response["server"]
    photo = upload_img_response["photo"]
    img_hash = upload_img_response["hash"]
    if photo == "[]":
        raise requests.HTTPError("Photo not uploaded")
    return server, photo, img_hash


def save_wall_photo(server, photo, img_hash, endpoint, group_id,
                    access_token, api_version="5.131"):
    params = {
        "server": server,
        "photo": photo,
        "hash": img_hash,
        "access_token": access_token,
        "v": api_version,
        "group_id": group_id
    }

    response = requests.get(endpoint.format("photos.saveWallPhoto"),
                            params=params)
    response.raise_for_status()
    saved_img_response = response.json()
    check_vk_response(saved_img_response)
    img_owner_id = saved_img_response["response"][0]["owner_id"]
    img_media_id = saved_img_response["response"][0]["id"]

    return img_owner_id, img_media_id


def post_img(endpoint, owner_id, media_id, msg, group_id,
             access_token, api_version="5.131"):
    params = {
        "access_token": access_token,
        "v": api_version,
        "owner_id": f'-{group_id}',
        "from_group": 1,
        "message": msg,
        "attachments": f"photo{owner_id}_{media_id}"
    }

    response = requests.post(endpoint.format("wall.post"), data=params)
    response.raise_for_status()
    check_vk_response(response.json())


if __name__ == "__main__":
    load_dotenv()

    vk_endpoint = "https://api.vk.com/method/{}"
    vk_group_id = os.environ["VK_GROUP_ID"]
    access_token = os.environ["VK_ACCESS_TOKEN"]

    dir_name = "images"
    img_name = "comic.png"
    pathlib.Path(dir_name).mkdir(exist_ok=True)

    try:
        comic_msg = download_comic(dir_name, img_name, get_random_comic_num())
        upload_url = get_upload_url(vk_endpoint, vk_group_id, access_token)
        upload_server, upload_photo, upload_hash = upload_img(
            upload_url,
            dir_name,
            img_name
        )
        img_owner_id, img_media_id = save_wall_photo(
            upload_server,
            upload_photo,
            upload_hash,
            vk_endpoint,
            vk_group_id,
            access_token
        )
        post_img(
            vk_endpoint,
            img_owner_id,
            img_media_id,
            comic_msg,
            vk_group_id,
            access_token
        )
    except requests.HTTPError as error:
        print(f"{bcolors.ERR}ERROR: {error}")
    except requests.exceptions.RequestException as error:
        print(f"{bcolors.ERR}ERROR: {error}")
    finally:
        shutil.rmtree(dir_name, ignore_errors=False, onerror=None)
