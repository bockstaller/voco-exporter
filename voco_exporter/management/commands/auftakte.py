import decimal
from django.core.management.base import BaseCommand
from django.db.models import Q
from django_scopes import scope
from pretix.base.models.event import Event

from pretix.base.models.orders import (
    QuestionAnswer,
    Order,
    OrderPayment,
    OrderPosition,
    Item,
)
from pretix.base.models.organizer import Organizer
from pretix.base.services.invoices import generate_invoice, invoice_qualified
from decimal import Decimal
from pprint import pprint


class MultiplePaymentsException(Exception):
    pass


class Command(BaseCommand):
    diocese_id = "C3YKTN77"
    project_mode_id = "TRWSCC8E"

    abschluss = 1

    projekt_unbekannt = 6
    projekt_blindbooking = 7
    projekt_individualreise = 8

    auftakte = {
        "Eichstätt": 3,
        "Passau": 3,
        "Bamberg": 3,
        "Augsburg": 3,
        "Würzburg": 3,
        "Regensburg": 3,
        "München - Freising": 3,
        "Erfurt": 5,
        "Magdeburg": 5,
        "Berlin": 5,
        "Osnabrück": 5,
        "Hildesheim": 5,
        "Hamburg": 5,
        "Aachen": 4,
        "Paderborn": 4,
        "Essen": 4,
        "Münster": 4,
        "Köln": 4,
        "Freiburg": 2,
        "Fulda": 2,
        "Limburg": 2,
        "Mainz": 2,
        "Rottenburg-Stuttgart": 2,
        "Speyer": 2,
        "Trier": 2,
    }

    help = "Weißt Gruppen ihrem Auftakt zu"

    def add_arguments(self, parser):
        parser.add_argument("organizer_slug", type=str)
        parser.add_argument("event_slug", type=str)
        parser.add_argument("--clean", action="store_true")

    def handle(self, *args, **options):
        o_slug = options["organizer_slug"]
        e_slug = options["event_slug"]

        o = Organizer.objects.filter(slug__iexact=o_slug).first()

        unhandled = []

        with scope(organizer=o):

            e: Event = Event.objects.filter(slug__iexact=e_slug).first()

            o: Order

            for o in e.orders.filter(status=Order.STATUS_PAID):
                try:
                    print(o.code)

                    if options["clean"]:
                        o.eventpart_set.clear()

                    diocese = (
                        QuestionAnswer.objects.filter(
                            question__identifier=self.diocese_id
                        )
                        .filter(orderposition__order=o)
                        .filter(orderposition__canceled=False)
                        .get()
                        .answer
                    )
                    print(diocese)
                    auftakt_id = self.auftakte[diocese]
                    o.eventpart_set.add(auftakt_id)

                    project = (
                        QuestionAnswer.objects.filter(
                            question__identifier=self.project_mode_id
                        )
                        .filter(orderposition__order=o)
                        .filter(orderposition__canceled=False)
                        .get()
                        .answer
                    )
                    print(project)

                    if project == "Individualreise":
                        o.eventpart_set.add(self.projekt_individualreise)
                    elif project == "Blind Booking":
                        o.eventpart_set.add(self.projekt_blindbooking)
                    else:
                        o.eventpart_set.add(self.projekt_unbekannt)

                    o.eventpart_set.add(self.abschluss)

                    o.save()
                except Exception as e:
                    unhandled.append((o.code, e))

            pprint(unhandled)
