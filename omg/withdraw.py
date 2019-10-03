import base64, pyotp, requests, traceback, time

from decimal import Decimal
from block_io import BlockIo
from datetime import timedelta

from django.db import transaction
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from core.settings import BITSKINS_SECRET, BITSKINS_API_KEY, BLOCK_IO_API_KEY, BLOCK_IO_PIN_KEY

from apps.users.models import User, Withdrawal, WITHDRAW_METHODS_FLAT

block_io = BlockIo(BLOCK_IO_API_KEY, BLOCK_IO_PIN_KEY, 2)

@require_POST
@login_required
def withdraw(request):

    withdrawal = None

    with transaction.atomic():

        user = User.objects.select_for_update().get(id=request.POST.get('user_id'))
        wins = user.wins.select_for_update().filter(sold=False, ship=False, sent=False)
        method = request.POST.get('method')

        fix = {'ltc': False}

        if (user != request.user and not request.user.is_superuser) or not user.get_won_items_price() or method not in WITHDRAW_METHODS_FLAT:
            raise Http404

        last_withdrawal = Withdrawal.objects.all().first()

        if last_withdrawal and last_withdrawal.date_created + timezone.timedelta(seconds=6) > timezone.now():
            raise Http404

        withdrawal = Withdrawal.objects.create(user=user, amount=user.get_won_items_price(), method=method)

        withdrawal.wins.set(wins)

        wins.update(ship=True)

        user.save()

        if user.youtube_mode:

            withdrawal.status = 'success'
            withdrawal.save()

            time.sleep(0.3)

            withdrawal.wins.select_for_update().all().update(sent=True)

        else:

            try:

                if method == 'bitskins':

                    if withdrawal.amount < Decimal('0.15') or not user.bitskins_ltc_wallet:
                        raise Http404

                    r = requests.get('https://bitskins.com/api/v1/get_current_deposit_conversion_rate/?api_key=' + BITSKINS_API_KEY + '&network=litecoin&code=' + pyotp.TOTP(BITSKINS_SECRET).now())

                    bitskins_rate_data = r.json()
                    crypto_rate = Decimal(bitskins_rate_data['data']['price_per_litecoin_in_usd'])
                    crypto_full_amount = withdrawal.amount / crypto_rate
                    crypto_amount = str(round(crypto_full_amount, 8))  # Block.io restricts to 8 points after decimal (was established experimentally)

                    withdrawal.bitskins_rate_data = bitskins_rate_data
                    withdrawal.crypto_rate = crypto_rate
                    withdrawal.crypto_full_amount = crypto_full_amount
                    withdrawal.crypto_amount = crypto_amount
                    withdrawal.crypto_destination = user.bitskins_ltc_wallet
                    withdrawal.save()
                    
                    r = block_io.withdraw(amounts=crypto_amount, to_addresses=user.bitskins_ltc_wallet)

                    block_io_data = r

                    withdrawal.block_io_data = block_io_data
                    withdrawal.status = 'success' if block_io_data.get('status') == 'success' else 'fail'
                    withdrawal.save()

                elif method == 'opskins':

                    bhash = base64.b64encode(b'be99c0714800d50ba7328b568f9bfe:')
                    data = {'id64': user.steam_id, 'amount': int(withdrawal.amount * 100)}
                    headers = {'Content-type': 'application/json; charset=utf-8', 'authorization': 'Basic ' + bhash.decode('utf-8')}

                    r = requests.post('https://api.opskins.com/ITransactions/TransferFunds/v1/', json=data, headers=headers)
                    opskins_data = r.json()

                    withdrawal.opskins_data = opskins_data
                    withdrawal.status = 'success' if opskins_data.get('status') == 1 else 'fail'
                    withdrawal.save()

                elif method == 'skins':

                    withdrawal.delivery_date = timezone.now() + timedelta(days=8)
                    withdrawal.status = 'pending'
                    withdrawal.save()

                    fix['pending'] = True

                if withdrawal.status == 'success':

                    withdrawal.delivery_date = timezone.now()
                    withdrawal.date_delivered = timezone.now()
                    withdrawal.save()

                    withdrawal.wins.select_for_update().all().update(sent=True)

                    user.total_withdrawal += withdrawal.amount
                    user.save()

                    if user.bro:
                        user.bro.bros_withdrawal += withdrawal.amount
                        user.bro.save()

                else:

                    if method == 'bitskins':

                        error_message = withdrawal.block_io_data['data']['error_message']

                        withdrawal.delivery_date = timezone.now()
                        withdrawal.save()

                        if 'One or more destination addresses are invalid for Network=LTC.' in error_message or \
                            'Invalid value for parameter TO_ADDRESSES provided' in error_message:

                            withdrawal.wins.select_for_update().all().update(ship=False)

                            withdrawal.only_for_staff = True
                            withdrawal.save()

                            fix['ltc'] = True

                        elif 'Cannot withdraw funds without Network Fee of' in error_message:

                            withdrawal.wins.select_for_update().all().update(sent=True)

                            fix['pending'] = True

            except Exception as e:

                withdrawal.error = traceback.format_exc()
                withdrawal.save()

    if request.POST.get('admin'):
        messages.add_message(request, messages.SUCCESS, 'Check it now')
        return redirect(request.META.get('HTTP_REFERER'))

    return JsonResponse({
        'balance': user.balance,
        'delivery_date': withdrawal.delivery_date.strftime('%d %B %Y'),
        'fix': fix,
    }, status=200 if withdrawal.status == 'success' else 500)