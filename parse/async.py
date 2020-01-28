import time
import asyncio
import aiohttp
import requests


token = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IldlYlBsYXlLaWQifQ.eyJpc3MiOiJBTVBXZWJQbGF5IiwiaWF0IjoxNTc5NjM3MzI0LCJleHAiOjE1OTUxODkzMjR9.SCgFvMtDJmpfGBYGjJ9ss9aloYssX7HYq0eI-xyQssNruaVLI_wXLWPDUtigBXDQrwVCPariPfcvOLvEn067lg'

headers = {'Authorization': 'Bearer ' + token}

url = 'https://amp-api.apps.apple.com/v1/catalog/ru/apps/1065803457/reviews'

payload = {
    'l': 'ru',
    'offset': None,
    'platform': 'web',
    'additionalPlatforms': 'appletv,ipad,iphone,mac'
}


def get_last_offset():
    """Поиск последнего значения "offset" (можно понимать, как номер последней страницы)"""

    min_page = 1
    max_page = 10000
    cur_page = max_page
    multiplier = 10

    def search_last_offset():

        nonlocal min_page, max_page, cur_page

        payload['offset'] = cur_page * multiplier

        result = requests.get(url, params=payload, headers=headers)

        if not result:
            max_page = cur_page
        else:
            min_page = cur_page

        cur_page = min_page + int((max_page - min_page) / 2)

        if min_page != cur_page:
            return search_last_offset()
        else:
            return cur_page * multiplier

    return search_last_offset()


async def fetch(session, offset):

    payload['offset'] = offset

    async with session.get(url, params=payload) as response:

        data = await response.json()

        for review in data['data']:

            attributes = review['attributes']

            # Записываем содержимое attributes в базу

            print(attributes['rating'])
            print(attributes['userName'])
            print(attributes['title'])
            print(attributes['date'])
            print(attributes['review'])
            print(attributes['isEdited'])
            
            if attributes.get('developerResponse'):
                print(attributes.get('developerResponse')['modified'])
                print(attributes.get('developerResponse')['body'])


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        offsets = range(0, get_last_offset() + 10, 10)
        awaitables = [fetch(session, offset) for offset in offsets]
        await asyncio.gather(*awaitables)


if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f'Выполнено за: {end - start}')
