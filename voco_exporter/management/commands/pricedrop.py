import decimal
from django.core.management.base import BaseCommand
from django.db.models import Q
from django_scopes import scope
from pretix.base.models.event import Event
from pretix.base.models.invoices import Invoice
from pretix.base.models.orders import (
    CartPosition,
    Order,
    OrderPayment,
    OrderPosition,
    Item,
)
from pretix.base.models.organizer import Organizer
from pretix.base.services.invoices import generate_invoice, invoice_qualified
from decimal import Decimal


class MultiplePaymentsException(Exception):
    pass


class Command(BaseCommand):
    help = "Reduces prices"

    def add_arguments(self, parser):
        parser.add_argument("organizer_slug", type=str)
        parser.add_argument("event_slug", type=str)
        parser.add_argument("--dry-run", action="store_true")

    def reduce_items(self, event: Event, dry_run: bool):
        self.stdout.write(self.style.SUCCESS(f"Changing Items"))
        items = []
        i: Item
        for i in event.items.all():
            i.original_price = i.default_price
            i.default_price = self.new_price(i.default_price)
            items.append(i)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"Writing item changes"))
            Item.objects.bulk_update(items, ["default_price", "original_price"])

    def check_for_multiple_payments(self, event: Event):
        o: Order
        for o in event.orders.all():
            conf_payments = [
                payment.full_id
                for payment in o.payments.all()
                if payment.state == OrderPayment.PAYMENT_STATE_CONFIRMED
            ]
            if len(conf_payments) > 1:
                self.stdout.write(
                    self.style.ERROR(f"Multiple Payments for order: {o.code}")
                )

                raise MultiplePaymentsException()

        self.stdout.write(self.style.SUCCESS(f"No multiple payments found."))

    def reduce_orders(self, event: Event, dry_run: bool):
        o: Order
        for o in event.orders.all():
            self.stdout.write(self.style.SUCCESS(f"Starting order: {o.code}"))
            if o.status == o.STATUS_CANCELED:
                self.stdout.write(
                    self.style.SUCCESS(f"Order: {o.code} canceled, continue")
                )
                continue

            p: OrderPosition
            price = Decimal("0")
            for p in o.positions.all():
                old_price = p.price
                p.price = self.new_price(old_price)
                price += p.price

                if not dry_run:
                    p.save()

                self.stdout.write(
                    self.style.NOTICE(f"Reduced position from {old_price} to {p.price}")
                )

            o.total = price

            if not dry_run:
                o.save()

            if o.payments:
                payed_sum = sum(
                    [
                        payment.amount
                        if payment.state == OrderPayment.PAYMENT_STATE_CONFIRMED
                        else 0
                        for payment in o.payments.all()
                    ]
                )
                if price < payed_sum:
                    payment = o.payments.last()
                    reduction = payed_sum - price

                    if not dry_run:
                        payment.amount = o.payments.last().amount - reduction
                        payment.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Reduced Payment for {o.code} by {reduction} from {payed_sum}"
                        )
                    )

    def new_price(self, price: Decimal) -> Decimal:
        if price == Decimal("250.00"):
            return Decimal("210.00")
        elif price == Decimal("170.00"):
            return Decimal("145.00")
        return price

    def reduce_cart_positions(self, event: Event, dry_run: bool, price: Decimal):
        cps: CartPosition
        cps_updates = []
        cps = CartPosition.objects.filter(price=price).all()
        self.stdout.write(self.style.SUCCESS(f"Modifying {len(cps)} cartpositions"))
        for c in cps:
            c.price = self.new_price(c.price)
            c.price_before_voucher = c.price
            cps_updates.append(c)
        count = 0
        if not dry_run:
            count = CartPosition.objects.bulk_update(
                cps_updates, ["price", "price_before_voucher"]
            )
        self.stdout.write(self.style.SUCCESS(f"Updated {count} cartpositions"))

    def handle(self, *args, **options):
        o_slug = options["organizer_slug"]
        e_slug = options["event_slug"]

        if dry_run := options["dry_run"]:
            self.stdout.write(self.style.WARNING("Running Dry Run"))

        o = Organizer.objects.filter(slug__iexact=o_slug).first()

        with scope(organizer=o):

            e: Event = Event.objects.filter(slug__iexact=e_slug).first()

            self.check_for_multiple_payments(e)
            self.reduce_items(e, dry_run)
            self.reduce_orders(e, dry_run)
            self.reduce_cart_positions(e, dry_run, Decimal("250.00"))
            self.reduce_cart_positions(e, dry_run, Decimal("170.00"))
