from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from django.conf import settings

from core.models import Booking, Wallet



