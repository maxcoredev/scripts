import time
import aiohttp
import asyncio


url = 'https://amp-api.apps.apple.com/v1/catalog/ru/apps/1065803457/reviews'

payload = {
    'l': 'ru',
    'offset': offset,
    'platform': 'web',
    'additionalPlatforms': 'appletv,ipad,iphone,mac'
}


async def fetch(session, offset):

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


def get_total_pages_count():
    """Функция, запрашивает
       https://amp-api.apps.apple.com/v1/catalog/ru/apps/1065803457/reviews
       с параметром offset, равным, к примеру 100000,
       и, методом бинарного поиска, ищет страницу,
       у которой в ответе нет параметра "next"

       Эта страница и является последней. Возвращаем её номер
       """
    return 5210


async def main():
    """Функция реализует асинхронные запросы ко всем страницам с отзывами,
       сохраняет значения (предположительно, в базу)"""

    token = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IldlYlBsYXlLaWQifQ.eyJpc3MiOiJBTVBXZWJQbGF5IiwiaWF0IjoxNTc5NjM3MzI0LCJleHAiOjE1OTUxODkzMjR9.SCgFvMtDJmpfGBYGjJ9ss9aloYssX7HYq0eI-xyQssNruaVLI_wXLWPDUtigBXDQrwVCPariPfcvOLvEn067lg'
    headers = {'Authorization': 'Bearer ' + token}

    total_pages_count = get_total_pages_count()
    offsets = range(0, total_pages_count + 10, 10)
    
    tasks = []

    async with aiohttp.ClientSession(headers=headers) as session:
        for offset in offsets:
            task = asyncio.create_task(fetch(session, offset))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f'Выполнено за: {end - start}')