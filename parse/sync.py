import time
import requests


token = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IldlYlBsYXlLaWQifQ.eyJpc3MiOiJBTVBXZWJQbGF5IiwiaWF0IjoxNTc5NjM3MzI0LCJleHAiOjE1OTUxODkzMjR9.SCgFvMtDJmpfGBYGjJ9ss9aloYssX7HYq0eI-xyQssNruaVLI_wXLWPDUtigBXDQrwVCPariPfcvOLvEn067lg'

headers = {'Authorization': 'Bearer ' + token}

url = 'https://amp-api.apps.apple.com/v1/catalog/ru/apps/1065803457/reviews'

payload = {
    'l': 'ru',
    'offset': 10,
    'platform': 'web',
    'additionalPlatforms': 'appletv,ipad,iphone,mac'
}


def main():

    while True:

        response = requests.get(url, params=payload, headers=headers)

        for review in response.json()['data']:
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

        if response.json().get('next'):
            payload['offset'] += 10
        else:
            break


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(f'Выполнено за: {end - start}')