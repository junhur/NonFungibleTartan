from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.


class NFT(models.Model):
    image = models.ImageField(blank=True, upload_to="nft/", null=True)
    resized_image_path = models.CharField(max_length=300, blank=True)
    is_for_sale = models.BooleanField()
    asking_price = models.DecimalField(max_digits=50, decimal_places=2)
    create_time = models.DateTimeField()
    current_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="current_owner"
    )
    original_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="original_owner"
    )
    previous_owners = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="previous_owners", null=True
    )
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500)


class Auction(models.Model):
    seller = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="auction_seller"
    )
    nft = models.ForeignKey(NFT, on_delete=models.PROTECT, related_name="auction_nft")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.PROTECT)
    bid_price = models.DecimalField(max_digits=50, decimal_places=2)
    highest = models.BooleanField()
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)


class Transaction(models.Model):
    buyer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="transaction_buyer"
    )
    seller = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="transaction_seller"
    )
    date = models.DateTimeField()
    sold_price = models.DecimalField(max_digits=50, decimal_places=2)
    nft = models.ForeignKey(
        NFT, on_delete=models.PROTECT, related_name="transaction_nft"
    )


class Profile(models.Model):
    user = models.OneToOneField(User, default=None, on_delete=models.PROTECT)
    picture = models.FileField(
        upload_to="profiles/", default=f"no_preview_available.jpeg"
    )
    description = models.TextField()
    create_time = models.DateTimeField()


class Wallet(models.Model):
    user = models.OneToOneField(User, default=None, on_delete=models.PROTECT)
    buying_power = models.DecimalField(max_digits=50, decimal_places=2, default=0.0)
