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


def parse_images_from_post(posts):
    links = []
    for post in posts['response']['items']:
        if not post.get("attachments", None):
            continue
        for att in post['attachments']:
            if not att['type'] == "photo":
                continue

            if "sizes" in att['photo']:
                m_s_ind = -1
                m_s_wid = 0

                for i, size in enumerate(att['photo']["sizes"]):
                    if size["width"] > m_s_wid:
                        m_s_wid = size["width"]
                        m_s_ind = i

                link = att['photo']["sizes"][m_s_ind]["url"]
                links.append(link)
            elif "url" in att['photo']:
                link = att['photo']['url']
                links.append(link)

    return links


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


def download_images(name, links):
    print(f"Start downloading {len(links)} images. Wait plz!\n")
    bar = progressbar.ProgressBar(maxval=len(links), widgets=[
        f'Downloading {len(links)} images: ',
        progressbar.Bar(marker='#', left='[', right=']', fill='.'),
        progressbar.Percentage(),
    ]).start()

    if not os.path.exists(f"output/"):
        os.makedirs(f"output/")

    l = 0
    for url in links:
        l += 1
        bar.update(l)
        result = re.search(reg_ex, url)
        if result:
            g = result.group(0)
        else:
            continue

        img_bytes = requests.get(url, stream=True)
        try:
            if not os.path.exists(f"output/{name}/"):
                os.makedirs(f"output/{name}")

            with open(f"output/{name}/{g}", 'wb') as f:
                img_bytes.raw.decode_content = True
                shutil.copyfileobj(img_bytes.raw, f)
        except Exception as e:
            print(f"ERROR: {e}")

    bar.finish()


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

    count = input("Enter count of posts to parse\n")
    if not count:
        print("Count is not presented")
        exit()
    elif not count.isdigit():
        raise ValueError("Count is not integer")
    else:
        count = int(count)

    is_image_need = input('Do I need to download images?\n')
    is_image_need = is_image_need in ('Yes', 'y', 'yes')

    vk_api = VKWrapper(dotenv_values(".env")['VK_TOKEN'], group_id)
    posts = get_posts(vk_api, count, offset)
    with open(f"output/{dotenv_values('.env')['GROUP_ID']}.pkl", 'wb') as f:
        pickle.dump(posts, f)

    if is_image_need:
        links = []
        for post in posts:
            l = parse_images_from_post(post)
            for li in l:
                links.append(li)

        download_images(str(vk_api.group_id), links)

    print("Thanks for using that program!")
