import sys, datetime, tornado, requests, json, os

from steampy import guard
from steampy.client import SteamClient, Asset
from steampy.utils import merge_items_with_descriptions_from_inventory
from steampy.models import TradeOfferState

from tornado import web, ioloop, escape

from core import settings


class GameOptions:

    from collections import namedtuple

    PredefinedOptions = namedtuple('PredefinedOptions', ['app_id', 'context_id'])

    DOTA2 = PredefinedOptions('570', '2')
    CS = PredefinedOptions('730', '2')
    TF2 = PredefinedOptions('440', '2')
    PUBG = PredefinedOptions('578080', '2')
    H1Z1 = PredefinedOptions('433850', '2')

    def __init__(self, app_id: str, context_id: str) -> None:
        self.app_id = app_id
        self.context_id = context_id

class Bot:

    def __init__(self):
        self.steam_name = sys.argv[1]  # python bot.py name
        self.steam_password = sys.argv[2]
        self.steam_guard = sys.argv[3]
        self.proxies = sys.argv[4]
        self.port = sys.argv[5]
        self.client = SteamClient(sys.argv[6])
        self.game = GameOptions.DOTA2

    def get_my_inventory(self, merge=True):  # Костыльный прокси-метод, из-за кривой реализации метода в библиотеке. Всегда возвращает объект

        try:
            response = self.client._session.get('http://steamcommunity.com/my/inventory/json/570/2/')
            if response.status_code == 200:
                json_response = response.json()
                if json_response.get('success'):
                    if isinstance(json_response.get('rgInventory'), dict):
                        if merge:
                            return merge_items_with_descriptions_from_inventory(json_response, self.game)
                        else:
                            return json_response['rgInventory']
                    else:
                        return {}
                else:
                    return {}
        except Exception as e:
            self.say(e)
            tornado.ioloop.IOLoop.instance().stop()
            sys.exit()

    def say(self, message, write=None):
        print('{0} {1}: {2}'.format(str(datetime.datetime.now().strftime(':%S' if settings.SERVER == 'prod' else '%H:%M:%S')), self.steam_name, str(message)), flush=True)
        if write: write.write(message)

    def api(self, method):
        return '{0}://{1}/{2}/'.format(settings.PROTOCOL, settings.ABSOLUTE_URL, method)

    def login(self):  # Proxy check: self.client._session.get('https://api.ipify.org?format=json').json()

        self.say('Logging ...')
        self.client.login(self.steam_name, self.steam_password, self.steam_guard)
        self.say('Successfully logged in.')


    def make_offer(self, task, asset_ids, steam_id, trade_url, message):

        exception = None

        my_asset = [Asset(item, bot.game) for item in asset_ids]

        try:
            offer = bot.client.make_offer_with_url(my_asset, [], trade_url, message)
        except Exception as e:  # Session lost
            self.say('{0}: Exception while {1}.'.format(task, e))
            exception = e
            return {'exception': e, 'task': task}
        else:
            if not offer.get('success'):
                self.say('{0}: SteamError while {1}. {2}'.format(steam_id, task, offer))
            else:
                self.say('{0}: Success while {1}.'.format(steam_id, task))
            offer['task'] = task
            return offer
        finally:
            if exception:
                tornado.ioloop.IOLoop.instance().stop()
                sys.exit()


# API Methods


class GetTradeOffers(web.RequestHandler):
    def get(self):
        self.write(bot.client.get_trade_offers())


class GetMyInventory(web.RequestHandler):  # Дёргаем и обрабатываем http://steamcommunity.com/my/inventory/json/730/2/
    def get(self, merge):
        self.write(bot.get_my_inventory(json.loads(merge)))


class GetSession(web.RequestHandler):
    def get(self):
        self.write(guard.generate_one_time_code(bot.client.steam_guard['shared_secret']))


# Admin Steam Methods


class TransferItems(web.RequestHandler):

    def post(self):

        bot.say('Someone requested transfer_items ...')

        data = escape.json_decode(self.request.body)

        inventory = bot.get_my_inventory(merge=True)

        items_asset_ids = [k for k, v in inventory.items() if 'R8 Revolver | Bone Mask' not in v['market_name']]

        my_asset = [Asset(item, bot.game) for item in items_asset_ids]

        result = bot.client.make_offer_with_url(my_asset, [], data['bot_trade_url'], 'Hey, bro!')

        self.write(result)


class IsItemOnBot(web.RequestHandler):
    def get(self, asset_id):

        inventory = bot.get_my_inventory(merge=False)
        inventory_asset_ids = [k for k, v in inventory.items()]

        self.write('Yes' if asset_id in inventory_asset_ids else 'No')


class AffectOffer(web.RequestHandler):
    def get(self, action, order_id):
        method = 'bot.client.{0}_trade_offer(str({1}))'.format(action, order_id)
        bot.say('Someone requested {}'.format(method))
        self.write(eval(method))


class AcceptAllOffers(web.RequestHandler):

    def is_donation(self, offer):
        return offer.get('items_to_receive') \
               and not offer.get('items_to_give') \
               and offer['trade_offer_state'] == TradeOfferState.Active \
               and not offer['is_our_offer']

    def get(self):
        offers = bot.client.get_trade_offers()['response']['trade_offers_received']
        response = ''
        for offer in offers:
            if self.is_donation(offer):
                try:
                    offer_id = offer['tradeofferid']
                    num_accepted_items = len(offer['items_to_receive'])
                    bot.client.accept_trade_offer(offer_id)
                    response = 'Accepted trade offer {}. Got {} items \n'.format(offer_id, num_accepted_items)
                    bot.say('Got {}'.format(offer_id))
                except Exception as e:
                    bot.say(e)

        self.write(response) if response else self.write('Nothing to accept')


# Withdraw Steam Methods


class MakeOffer(web.RequestHandler):
    def post(self):
        data = escape.json_decode(self.request.body)
        self.write(bot.make_offer('delivering', data['asset_ids'], data['steam_id'], data['trade_url'], data['message']))


class Withdraw(web.RequestHandler):

    def post(self):

        data = escape.json_decode(self.request.body)

        bot.say('User {0} requested withdraw. Sending to Courier ...'.format(data['user_steam_id']))

        offer_to_courier = bot.make_offer('sending', data['asset_ids'], data['courier_steam_id'], data['courier_trade_url'], 'Hey!')

        if not offer_to_courier.get('success'):
            bot.say(offer_to_courier)
            self.write(offer_to_courier)
        else:

            offer_to_courier_id = offer_to_courier.get('tradeofferid')

            bot.say('Courier got trade offer. Resending to {} ...'.format(data['user_steam_id']))

            try:
                response = requests.post('http://127.0.0.1:{0}/resend/'.format(data['courier_port']), data=json.dumps({
                    'offer_id'  : offer_to_courier_id,
                    'steam_id'  : data['user_steam_id'],
                    'trade_url' : data['user_trade_url'],
                    'message'   : data['message']
                }))
            except Exception as e:  # ConnectionError
                bot.client.cancel_trade_offer(offer_to_courier_id)
                bot.say('Courier probably got ConnectionError. Trade offer should be canceled.')
                self.write({'exception': str(e), 'task': 'resending'})
            else:
                try:
                    text = response.json()
                    if text.get('exception') or text.get('strError'):
                        bot.client.cancel_trade_offer(offer_to_courier_id)
                except ValueError:
                    pass
                finally:
                    self.write(response.text)


class WithdrawNew(web.RequestHandler):

    def post(self):

        data = escape.json_decode(self.request.body)

        bot.say('{0} ({1}) requested withdraw...'.format(data['user_steam_name'], data['user_steam_id']))

        asset_ids, offer = {'asset_ids': data['asset_ids']}, {}

        try:
            offer = bot.client.make_offer_with_url([Asset(item, bot.game) for item in data['asset_ids']], [], data['user_trade_url'], 'Hey')
        except Exception as e:  # Session lost
            bot.say('{0} ({1}) got Exception on withdraw'.format(data['user_steam_name'], data['user_steam_id']))
            offer = {'delivering': e}
        finally:
            bot.say('{0} ({1}) result: {2}'.format(data['user_steam_name'], data['user_steam_id'], offer))
            requests.post(bot.api('withdraw/ipn'), data=dict(offer, **asset_ids))  # {**offer, **asset_ids}
            if offer.get('delivering'):
                tornado.ioloop.IOLoop.instance().stop()
                sys.exit()


class Hello(web.RequestHandler):
    def get(self):
        self.write('Hello!')

class Resend(web.RequestHandler):

    def post(self):

        data = escape.json_decode(self.request.body)

        exception = None

        try:
            bot.client.accept_trade_offer(data['offer_id'])
        except Exception as e:  # Потеря сессии
            exception = e
            self.write({'exception': str(e), 'task': 'accepting'})
        else:

            # Иногда нет ключа assets_received
            trade_items = bot.client.get_trade_history(max_trades=1, start_after_tradeid=data['offer_id'])['response']['trades'][0]['assets_received']

            new_asset_ids = [item['new_assetid'] for item in trade_items]

            offer_to_user = bot.make_offer('delivering', new_asset_ids, data['steam_id'], data['trade_url'], data['message'])

            offer_to_user['items'] = trade_items

            self.write(offer_to_user)

        finally:
            if exception:
                tornado.ioloop.IOLoop.instance().stop()
                sys.exit()


class Check(web.RequestHandler):
    def post(self):
        data = escape.json_decode(self.request.body)
        bot.say('Check requested ...')

        inventory = bot.get_my_inventory(merge=True)
        asset_ids = [k for k, v in inventory.items() if 'R8 Revolver | Bone Mask' in v['market_name']]

        if asset_ids:

            try:
                offer = bot.client.make_offer_with_url([Asset(item, bot.game) for item in asset_ids], [], data['user_trade_url'], 'Hey')
            except Exception as e:  # Session lost
                bot.say('Check Exception: {}'.format(e))
                offer = {'exception': e}
            finally:
                bot.say('Check result: {}'.format(offer))
                self.write(offer)
                if offer.get('exception'):
                    tornado.ioloop.IOLoop.instance().stop()
                    sys.exit()


def make_app():
    return web.Application([

        # API Methods

        (r'/get_trade_offers/',         GetTradeOffers),  # Session lost not possible only there
        (r'/get_my_inventory/([^/]+)/', GetMyInventory),
        (r'/get_session/',              GetSession),

        # Admin Steam Methods

        (r'/transfer_items/',               TransferItems),
        (r'/is_item_on_bot/([^/]+)/',       IsItemOnBot),
        (r'/affect_offer/([^/]+)/([^/]+)/', AffectOffer),
        (r'/accept_all_offers/',            AcceptAllOffers),
        (r'/check/',                        Check),
        (r'/hello/',                        Hello),

        # Withdraw Steam Methods
        
        (r'/make_offer/',   MakeOffer),
        (r'/withdraw/',     Withdraw),
        (r'/resend/',       Resend),
        (r'/withdraw/new/', WithdrawNew),

    ], debug=False)


if __name__ == '__main__':

    bot = Bot()
    bot.login()

    app = make_app()
    app.listen(bot.port, address='127.0.0.1')

    ioloop.IOLoop.current().start()