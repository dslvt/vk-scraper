import requests
import time
import re
from urllib.parse import unquote
import os
import shutil
import progressbar
import pickle
from dotenv import dotenv_values


reg_ex = r'[\w-]+.(jpg|png|txt|jpeg)'


class VKWrapper:

    def __init__(self, token, group_id):
        '''
        :param token: VK Token
        :param group_id: Group id
        '''
        if not token:
            raise ValueError("No `token` specified")

        self.group_id = group_id

        self.version = "5.131"
        self.token = token

        self.api_url = "https://api.vk.com/method/{{}}?access_token={}&v={}" \
            .format(self.token, self.version)

    def execute_api(self, method, params):
        try:
            result = requests.get(self.api_url.format(
                method), params=params).json()
            return result
        except:
            raise ValueError("Response is not correct!")


def calculate(count):
    count_array = []
    max_val = 100
    offset = 0

    while not count == 0:
        if count >= max_val:
            count_array.append([max_val, offset])
            offset += max_val
            count -= max_val
        else:
            count_array.append([count, offset])
            count -= count

    return count_array


def get_posts(vk_api, count, offset=None):
    counts = calculate(count)
    links = []
    bar = progressbar.ProgressBar(maxval=len(counts), widgets=[
        f'Downloading {len(links)} posts: ',
        progressbar.Bar(marker='#', left='[', right=']', fill='.'),
        progressbar.Percentage(),
    ]).start()

    for i, count in enumerate(counts):
        params = {
            'owner_id': vk_api.group_id * -1,
            'count': count[0],
            'filter': 'owner'
        }

        bar.update(i)
        if offset:
            params['offset'] = offset + count[1]
        else:
            params['offset'] = count[1]

        res = vk_api.execute_api("wall.get", params)
        links.append(res)

        time.sleep(5)

    return links


if __name__ == "__main__":
    group_id = dotenv_values('.env')['GROUP_ID']
    if not group_id:
        print("Group id is not presented")
        exit()
    elif not group_id.isdigit():
        raise ValueError("Group id is not integer")
    else:
        group_id = int(group_id)

    offset = 0
    if offset and not offset.isdigit():
        raise ValueError("Offset is not integer")
    elif offset:
        offset = int(offset)

    count = input("Enter count of posts with images parse\n")
    if not count:
        print("Count is not presented")
        exit()
    elif not count.isdigit():
        raise ValueError("Count is not integer")
    else:
        count = int(count)

    vk_api = VKWrapper(dotenv_values(".env")['VK_TOKEN'], group_id)
    posts = get_posts(vk_api, count, offset)
    with open('posts.pkl', 'wb') as f:
        pickle.dump(posts, f)
    print("Thanks for using that program!")
