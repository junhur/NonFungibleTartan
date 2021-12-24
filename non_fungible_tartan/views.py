import decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from PIL import Image
import os
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from non_fungible_tartan.models import NFT, Profile, Auction, Bid, Transaction, Wallet
from non_fungible_tartan.forms import (
    LoginForm,
    RegisterForm,
    CreateNFTForm,
    EditProfileForm,
    BuyingPowerForm,
)
from django.db import transaction
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime
import pytz

from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
import json
import stripe
import secrets
import string

stripe.api_key = settings.STRIPE_SECRET_KEY

GOOGLE_OAUTH_CLIENT_ID = settings.GOOGLE_OAUTH2_CLIENT_ID
NFTS_PER_PAGE = 4
NFTS_PER_ROW = 2

MONTH_DICT = {
    "1": "Jan",
    "2": "Feb",
    "3": "Mar",
    "4": "Apr",
    "5": "May",
    "6": "Jun",
    "7": "Jul",
    "8": "Aug",
    "9": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}


def home(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return render(
                request,
                "non_fungible_tartan/index.html",
                {"auctions": Auction.objects.all().filter(end_time__gt=timezone.localtime(timezone.now())).order_by('end_time')},
            )
        else:
            return render(
                request, "non_fungible_tartan/login.html", {"form": LoginForm()}
            )


@login_required
@transaction.atomic
def create_nft_action(request):
    context = {}
    if request.method == "GET":
        return render(request, "non_fungible_tartan/create_nft.html", context)

    # POST
    new_nft = NFT()
    form = CreateNFTForm(request.POST, request.FILES, instance=new_nft)
    if not form.is_valid():
        context[
            "error"
        ] = "Please make sure to include all required fields and provide valid inputs."
        return render(request, "non_fungible_tartan/create_nft.html", context)

    is_for_sale = request.POST.get("is_for_sale", False)

    try:
        if is_for_sale == "on":
            e = timezone.make_aware(
                datetime.strptime(request.POST["auctiontime"], "%Y-%m-%dT%H:%M")
            )
            c = timezone.localtime(timezone.now())
            if e <= c:
                context[
                    "error"
                ] = "Please enter an auction end date-time later than current date-time"
                return render(request, "non_fungible_tartan/create_nft.html", context)
    except:
        context["error"] = "Please enter a valid auction end date and time"
        return render(request, "non_fungible_tartan/create_nft.html", context)

    new_nft.current_owner = request.user
    new_nft.original_owner = request.user
    new_nft.create_time = timezone.now()
    new_nft.save()

    if is_for_sale == "on":
        new_auction = Auction(seller=request.user, nft=new_nft)
        new_auction.start_time = timezone.localtime(timezone.now())
        new_auction.end_time = datetime.strptime(
            request.POST["auctiontime"], "%Y-%m-%dT%H:%M"
        )
        new_auction.save()

    context["message"] = "NFT successfully created."
    return render(request, "non_fungible_tartan/create_nft.html", context)


@transaction.atomic
def google_login_action(request):
    token = request.POST["idtoken"]
    try:
        idinfo = id_token.verify_oauth2_token(token, requests.Request())
        email = idinfo["email"]
        username = email[: email.find("@")]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            letters = string.ascii_letters + string.digits
            password = "".join(secrets.choice(letters) for _ in range(20))
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=idinfo["given_name"],
                last_name=idinfo["family_name"],
            )
            new_profile = Profile(user=user, description="Introduce yourself!")
            new_profile.create_time = timezone.now()
            new_profile.save()

            new_wallet = Wallet(user=user)
            new_wallet.save()

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return HttpResponse({"success": True})
    except Exception as e:
        print(e)


def login_action(request):
    context = {}
    if request.method == "GET":
        context["form"] = LoginForm()
        return render(request, "non_fungible_tartan/login.html", context)

    form = LoginForm(request.POST)
    context["form"] = form

    if not form.is_valid():
        return render(request, "non_fungible_tartan/login.html", context)

    user = authenticate(
        username=form.cleaned_data["username"], password=form.cleaned_data["password"]
    )
    login(request, user)
    return redirect(reverse("home"))


@login_required
@transaction.atomic
def nft_details_action(request, id):
    context = {}
    nft = get_object_or_404(NFT, id=id)
    context["nft"] = nft
    context["message"] = ""
    context["auction"] = None

    for auction in Auction.objects.all():
        if auction.nft.id == nft.id:
            context["auction"] = auction

    local_create_time = timezone.localtime(nft.create_time)
    # Parse datetime from model and add it to context
    split_datetime = str(local_create_time).split("-")
    year = split_datetime[0]
    month = split_datetime[1]
    day = split_datetime[2].split(" ")[0]
    datetime_value = MONTH_DICT[month] + "-" + str(day) + "-" + str(year)
    context["datetime"] = datetime_value

    if request.method == "GET":
        return render(request, "non_fungible_tartan/nft_details.html", context)

    if (
        "minimum_bid_amount" not in request.POST
        and "bid_amount" not in request.POST
        and "auctiontime" not in request.POST
    ):
        context["message"] = "Please enter a value"
        return render(request, "non_fungible_tartan/nft_details.html", context)

    if "minimum_bid_amount" in request.POST:
        if request.POST["minimum_bid_amount"] == "":
            context["message"] = "Please enter a valid minimum bid amount"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        for c in request.POST["minimum_bid_amount"]:
            if c not in "0123456789.":
                context["message"] = "Please enter a valid minimum bid amount"
                return render(request, "non_fungible_tartan/nft_details.html", context)

        if request.POST["minimum_bid_amount"].count(".") > 1:
            context["message"] = "Please enter a valid minimum bid amount"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        if float(request.POST["minimum_bid_amount"]) <= 0:
            context["message"] = "Minimum bid amount must be greater than 0."
            return render(request, "non_fungible_tartan/nft_details.html", context)

    if "auctiontime" in request.POST:
        if request.POST["auctiontime"] == "":
            context["message"] = "Please enter a valid auction end date and time"
            return render(request, "non_fungible_tartan/nft_details.html", context)
        try:
            e = timezone.make_aware(
                datetime.strptime(request.POST["auctiontime"], "%Y-%m-%dT%H:%M")
            )
        except:
            context["message"] = "Please enter a valid auction end date and time"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        c = timezone.localtime(timezone.now())

        if e <= c:
            context[
                "message"
            ] = "Please enter an auction end date-time later than current date-time"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        nft.is_for_sale = True
        nft.asking_price = float(request.POST["minimum_bid_amount"])
        nft.save()
        new_auction = Auction(
            seller=nft.current_owner,
            nft=nft,
            start_time=timezone.now(),
            end_time=datetime.strptime(request.POST["auctiontime"], "%Y-%m-%dT%H:%M"),
        )
        new_auction.save()
        context["nft"] = nft

    if "bid_amount" in request.POST:
        if (
            request.POST["bid_amount"] == ""
            or request.POST["bid_amount"].count(".") > 1
        ):
            context["message"] = "Please enter a valid bid amount"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        for c in request.POST["bid_amount"]:
            if c not in "1234567890.":
                context["message"] = "Please enter a valid bid amount"
                return render(request, "non_fungible_tartan/nft_details.html", context)

        curr_auction = None
        for auction in Auction.objects.all():
            if auction.nft == nft:
                curr_auction = auction
                break

        highest_price = nft.asking_price
        for bid in Bid.objects.all():
            if bid.auction == curr_auction and bid.highest:
                highest_price = bid.bid_price

        if float(request.POST["bid_amount"]) <= highest_price:
            context["message"] = "Bid must be higher than highest bid and asking price"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        if (
            decimal.Decimal(request.POST["bid_amount"])
            > request.user.wallet.buying_power
        ):
            context["message"] = "Bid must be less than or equal to your buying power"
            return render(request, "non_fungible_tartan/nft_details.html", context)

        for bid in Bid.objects.all():
            if bid.auction == curr_auction and bid.highest:
                if bid.bidder == request.user:
                    context["message"] = "Cannot outbid yourself!"
                    return render(
                        request, "non_fungible_tartan/nft_details.html", context
                    )

                bid.highest = False
                bid.save()
                bid.bidder.wallet.buying_power += bid.bid_price
                bid.bidder.wallet.save()

        if Auction.objects.filter(id=curr_auction.id).exists():
            bid_price = decimal.Decimal(request.POST["bid_amount"])
            new_bid = Bid(
                bidder=request.user,
                bid_price=bid_price,
                auction=curr_auction,
                highest=True,
            )
            request.user.wallet.buying_power -= bid_price
            request.user.wallet.save()
            new_bid.save()

    return redirect(reverse("nft_details", args=[nft.id]))


@login_required
def logout_action(request):
    logout(request)
    return redirect(reverse("login"))


@transaction.atomic
def register_action(request):
    context = {}

    if request.method == "GET":
        context["form"] = RegisterForm()
        return render(request, "non_fungible_tartan/register.html", context)

    form = RegisterForm(request.POST)
    context["form"] = form

    if not form.is_valid():
        return render(request, "non_fungible_tartan/register.html", context)

    new_user = User.objects.create_user(
        username=form.cleaned_data["username"],
        password=form.cleaned_data["password"],
        email=form.cleaned_data["email"],
        first_name=form.cleaned_data["first_name"],
        last_name=form.cleaned_data["last_name"],
    )

    new_user.save()
    new_user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, new_user)

    new_profile = Profile(user=new_user, description="Introduce yourself!")
    new_profile.create_time = timezone.now()
    new_profile.save()

    new_wallet = Wallet(user=new_user)
    new_wallet.save()

    return redirect(reverse("home"))


@login_required
@transaction.atomic
def add_buying_power_action(request):
    context = {}
    if request.method == "GET":
        context["form"] = BuyingPowerForm()
        return render(request, "non_fungible_tartan/add_buying_power.html", context)
    else:
        form = BuyingPowerForm(request.POST)
        context["form"] = form
        if not form.is_valid():
            return render(request, "non_fungible_tartan/add_buying_power.html", context)

        credit_card_info = form.cleaned_data
        amount = credit_card_info["amount"]
        name = credit_card_info["name_on_card"]
        card_number = credit_card_info["card_number"]
        expiration_month = credit_card_info["expiration_date"].month
        expiration_year = credit_card_info["expiration_date"].year
        cvc = credit_card_info["cvc"]
        address = credit_card_info["address"]
        city = credit_card_info["city"]
        state = credit_card_info["state"]
        zipcode = credit_card_info["zipcode"]
        try:
            card_token = stripe.Token.create(
                card={
                    "number": card_number,
                    "exp_month": expiration_month,
                    "exp_year": expiration_year,
                    "cvc": cvc,
                    "name": name,
                    "address_line1": address,
                    "address_city": city,
                    "address_state": state,
                    "address_zip": zipcode,
                },
            )
            token_id = card_token["id"]
            charge_response = stripe.Charge.create(
                amount=amount * 100, currency="usd", source=token_id
            )

            if charge_response["captured"]:
                request.user.wallet.buying_power += amount
                request.user.wallet.save()
                context[
                    "message"
                ] = f"${amount} has been successfully added to your wallet."
            else:
                context["error"] = "Please check your information or account balance."
        except Exception as e:
            context["error"] = e.user_message

        return render(request, "non_fungible_tartan/add_buying_power.html", context)


@login_required
@transaction.atomic
def profile_action(request, user_id=None):
    context = {}
    if request.method == "GET":
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = request.user

        profile = user.profile
        form = EditProfileForm(instance=profile)
        context["profile_owner"] = user
        context["profile"] = profile
        context["form"] = form

        created_page = int(request.GET.get("created_nft_page", 1))
        created_count = user.original_owner.all().count()
        if created_count % NFTS_PER_PAGE == 0:
            created_total_pages = created_count // NFTS_PER_PAGE
        else:
            created_total_pages = created_count // NFTS_PER_PAGE + 1

        nfts_created_by_user = user.original_owner.all()[
            (created_page - 1) * NFTS_PER_PAGE : created_page * NFTS_PER_PAGE
        ]
        nfts_created_by_user = _group_nfts_by_row_count(nfts_created_by_user)
        nfts_created_by_user = list(
            map(lambda nft: _resize_image_pair(nft), nfts_created_by_user)
        )
        context["created_nft"] = nfts_created_by_user
        context["current_created_nft_page"] = created_page
        context["prev_created_nft_page"] = max(created_page - 1, 1)
        context["next_created_nft_page"] = min(created_page + 1, created_total_pages)
        if created_total_pages > 1:
            context["created_nft_pages"] = _paginate_nfts("created", created_page, user)

        currently_hold_page = int(request.GET.get("currently_hold_nft_page", 1))
        currently_held_count = user.current_owner.all().count()
        if currently_held_count % NFTS_PER_PAGE == 0:
            currently_held_total_pages = currently_held_count // NFTS_PER_PAGE
        else:
            currently_held_total_pages = currently_held_count // NFTS_PER_PAGE + 1

        currently_held_nfts = user.current_owner.all()[
            (currently_hold_page - 1)
            * NFTS_PER_PAGE : currently_hold_page
            * NFTS_PER_PAGE
        ]
        currently_held_nfts = _group_nfts_by_row_count(currently_held_nfts)
        currently_held_nfts = list(
            map(lambda nft: _resize_image_pair(nft), currently_held_nfts)
        )
        context["current_hold_nft"] = currently_held_nfts
        context["current_hold_nft_page"] = currently_hold_page
        context["prev_current_hold_nft_page"] = max(currently_hold_page - 1, 1)
        context["next_current_hold_nft_page"] = min(
            currently_hold_page + 1, currently_held_total_pages
        )
        if currently_held_total_pages > 1:
            context["current_hold_nft_pages"] = _paginate_nfts(
                "currently_hold", currently_hold_page, user
            )

        return render(request, "non_fungible_tartan/profile.html", context)
    else:
        profile = Profile.objects.get(id=request.user.id)
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        context["profile_owner"] = request.user
        context["profile"] = profile
        context["form"] = form

        if not form.is_valid():
            return render(request, "non_fungible_tartan/profile.html", context)

        profile.save()
        return redirect(reverse("profile"))


def _paginate_nfts(nft_type, current_page, user):
    if nft_type == "created":
        count = user.original_owner.all().count()
    else:
        count = user.current_owner.all().count()
    if count % NFTS_PER_PAGE == 0:
        total_pages = count // NFTS_PER_PAGE
    else:
        total_pages = count // NFTS_PER_PAGE + 1

    if current_page == 1:
        max_page = min(total_pages, 3)
        return list(range(1, max_page + 1))
    if current_page == total_pages:
        min_page = max(1, total_pages - 2)
        return list(range(min_page, total_pages + 1))
    min_page = current_page - 1
    max_page = current_page + 1

    return list(range(min_page, max_page + 1))


def _resize_image_pair(nft):
    if len(nft) == 1:
        nft[0].resized_image_path = nft[0].image.url
        nft[0].save()
        return nft
    nft_1 = nft[0]
    nft_2 = nft[1]
    if not nft_1.resized_image_path or not nft_2.resized_image_path:
        image_url_1 = nft_1.image.url
        image_url_2 = nft_2.image.url
        base_dir = str(settings.BASE_DIR)
        image_1 = Image.open(base_dir + image_url_1)
        image_2 = Image.open(base_dir + image_url_2)
        width_1, height_1 = image_1.size
        width_2, height_2 = image_2.size
        square_size = max(width_1, width_2, height_1, height_2)
        image_1_resize = True
        image_2_resize = True
        if width_1 == square_size and height_1 == square_size:
            nft_1.resized_image_path = image_url_1
            nft_1.save()
            image_1_resize = False
        if width_2 == square_size and height_2 == square_size:
            nft_2.resized_image_path = image_url_2
            nft_2.save()
            image_2_resize = False

        if not image_1_resize and not image_2_resize:
            return nft_1, nft_2

        resized_directory = settings.MEDIA_ROOT + "/resized_nft/"
        if not os.path.exists(resized_directory):
            os.makedirs(resized_directory)

        if image_1_resize:
            _resize_image(nft_1, image_1, square_size)

        if image_2_resize:
            _resize_image(nft_2, image_2, square_size)

    return [nft_1, nft_2]


def _resize_image(nft, image, square_size):
    split_path = image.filename.split("/")
    image_1_name = split_path[-1]
    resized_image_1 = image.resize((square_size, square_size), Image.ANTIALIAS)
    resized_image_1_path = f"/resized_nft/{image_1_name}"
    resized_image_1.save(
        settings.MEDIA_ROOT + resized_image_1_path, "PNG", optimized=True
    )
    nft.resized_image_path = "/media" + resized_image_1_path
    nft.save()


def _group_nfts_by_row_count(nfts):
    grouped_nfts = []
    for i in range(0, len(nfts), 2):
        group = [nfts[i]]
        if i + 1 < len(nfts):
            group.append(nfts[i + 1])
        grouped_nfts.append(group)
    return grouped_nfts


@login_required
def get_photo(request, id):
    item = get_object_or_404(NFT, id=id)

    return HttpResponse(item.image)


@login_required
@transaction.atomic
def get_details_ajax(request):
    nft = get_object_or_404(NFT, id=int(request.POST["nft_id"]))

    response_data = dict()
    response_data["time_remaining"] = "0"
    response_data["reload"] = False
    for auction in Auction.objects.all():
        if auction.nft == nft:
            if timezone.now() < auction.end_time:
                time_left = auction.end_time - timezone.now()
                days = time_left.days
                hours = int(time_left / timezone.timedelta(hours=1))
                minutes = int(time_left / timezone.timedelta(minutes=1))
                seconds = time_left.seconds
                if days >= 1:
                    if days == 1:
                        response_data["time_remaining"] = str(days) + " day"
                    else:
                        response_data["time_remaining"] = str(days) + " days"
                elif hours >= 1:
                    if hours == 1:
                        response_data["time_remaining"] = str(hours) + " hour"
                    else:
                        response_data["time_remaining"] = str(hours) + " hours"
                elif minutes >= 1:
                    if minutes == 1:
                        response_data["time_remaining"] = str(minutes) + " minute"
                    else:
                        response_data["time_remaining"] = str(minutes) + " minutes"
                elif seconds > 0:
                    if seconds == 1:
                        response_data["time_remaining"] = str(seconds) + " second"
                    else:
                        response_data["time_remaining"] = str(seconds) + " seconds"
            # AUCTION ENDED
            else:  # request.user == auction.seller:
                nft.is_for_sale = False
                for bid in Bid.objects.all():
                    # Auction is successful (there is a highest bid)
                    if bid.auction == auction and bid.highest:
                        transaction = Transaction(
                            buyer=bid.bidder,
                            sold_price=bid.bid_price,
                            seller=nft.current_owner,
                            date=timezone.now(),
                            nft=nft,
                        )
                        transaction.save()
                        nft.current_owner.wallet.buying_power += bid.bid_price
                        nft.current_owner.wallet.save()
                        nft.current_owner = bid.bidder
                        nft.save()
                        break
                nft.save()
                Bid.objects.filter(auction=auction).delete()
                auction.delete()
                response_data["reload"] = True
            break

    response_data["first_name"] = "-"
    response_data["last_name"] = ""
    response_data["highest_bid_price"] = "-"
    response_data["number_of_bids"] = "0"

    if nft.is_for_sale:
        curr_auction = Auction()
        for auction in Auction.objects.all():
            if auction.nft == nft:
                curr_auction = auction
        highest = Bid()
        bid_count = 0
        for bid in Bid.objects.all():
            if bid.auction == curr_auction:
                bid_count += 1
                if bid.highest:
                    highest = bid
        if bid_count != 0:
            response_data["first_name"] = highest.bidder.first_name
            response_data["last_name"] = highest.bidder.last_name
            response_data["highest_bid_price"] = str(highest.bid_price)
            response_data["number_of_bids"] = str(bid_count)
    else:
        response_data["reload"] = True

    response_json = json.dumps(response_data)

    response = HttpResponse(response_json, content_type="application/json")
    return response
