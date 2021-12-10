import os
import pathlib
import shutil

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


def download_comic(dir_name, img_name, num):
    comic_download_url = "https://xkcd.com/{}/info.0.json".format(num)

    response = requests.get(comic_download_url)
    response.raise_for_status()
    comic_response = response.json()
    img_url = comic_response["img"]
    comic_alt = comic_response["alt"]
    comic_title = comic_response["title"]

    response = requests.get(img_url)
    response.raise_for_status()

    with open(os.path.join(dir_name, img_name), "wb") as file:
        file.write(response.content)

    return f"{comic_title}\n\n{comic_alt}"


def upload_img(basic_params, endpoint, dir_name, img_name, group_id):
    params = {
        **basic_params,
        "group_id": group_id
    }

    response = requests.get(endpoint.format("photos.getWallUploadServer"), params=params)
    response.raise_for_status()
    upload_url = response.json()["response"]["upload_url"]

    with open(os.path.join(dir_name, img_name), 'rb') as file:
        url = upload_url
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        return response.json()


def save_wall_photo(basic_params, upload_img_response, endpoint, group_id):
    params = {
        **basic_params,
        **upload_img_response,
        "group_id": group_id
    }

    response = requests.get(endpoint.format("photos.saveWallPhoto"), params=params)
    response.raise_for_status()
    saved_img_response = response.json()
    img_owner_id = saved_img_response["response"][0]["owner_id"]
    img_media_id = saved_img_response["response"][0]["id"]

    return img_owner_id, img_media_id


def post_img(basic_params, endpoint, owner_id, media_id, msg, group_id):
    params = {
        **basic_params,
        "owner_id": f'-{group_id}',
        "from_group": 1,
        "message": msg,
        "attachments": f"photo{owner_id}_{media_id}"
    }

    response = requests.post(endpoint.format("wall.post"), data=params)
    response.raise_for_status()

    shutil.rmtree('images', ignore_errors=False, onerror=None)



if __name__ == "__main__":
    load_dotenv()

    api_version = "5.131"
    vk_endpoint = "https://api.vk.com/method/{}"
    vk_group_id = os.environ["VK_GROUP_ID"]

    basic_params = {
        "access_token": os.environ["VK_ACCESS_TOKEN"],
        "v": api_version,
    }

    dir_name = "images"
    img_name = "comic.png"
    pathlib.Path(dir_name).mkdir(exist_ok=True)

    comic_msg = download_comic(dir_name, img_name, get_random_comic_num())
    upload_img_response = upload_img(basic_params, vk_endpoint, dir_name, img_name, vk_group_id)
    img_owner_id, img_media_id = save_wall_photo(basic_params, upload_img_response, vk_endpoint, vk_group_id)
    post_img(basic_params, vk_endpoint, img_owner_id, img_media_id, comic_msg, vk_group_id)
