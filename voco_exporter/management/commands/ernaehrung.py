import decimal
from django.core.management.base import BaseCommand
from django.db.models import Q

from django_scopes import scope
from pretix.base.models.event import Event
from pretix.base.models.invoices import Invoice
from pretix.base.models.orders import (
    QuestionAnswer,
    Question,
)
from pretix.base.models.organizer import Organizer
from pretix.base.services.invoices import generate_invoice, invoice_qualified
from decimal import Decimal


class Command(BaseCommand):
    help = "Assigns Ernährungsthings"

    def add_arguments(self, parser):
        parser.add_argument("organizer_slug", type=str)
        parser.add_argument("a_codes_file", type=str)
        parser.add_argument("sonder_codes_file", type=str)

    def handle(self, *args, **options):
        a_order_codes = []
        sonder_codes = []

        with open(options["a_codes_file"]) as file:
            a_order_codes = file.read().splitlines()

        with open(options["sonder_codes_file"]) as file:
            sonder_codes = file.read().splitlines()

        print(a_order_codes)

        print(sonder_codes)

        o_slug = options["organizer_slug"]

        print(f"{len(a_order_codes)} order codes loaded")
        print(f"{len(sonder_codes)} sonder codes loaded")

        a_regulaer = "KNmTsdXtmD9jnO69uAo9e9ElXDoNpigO.A_regulaCC88r.png"
        b_regulaer = "LGFtQ4pECFZWNvMkNdFEPee0FaD9lR2T.B_regulaCC88r.png"
        a_sonder = "rW0to5YnEzPLkuMOgiKjfLMESSra4znp.A_sonder.png"
        b_sonder = "OJSSqAHLg4KgJReepYgixRrN23FYAVAq.B_sonder.png"

        frage_id = "W37CTRKW"

        o: Organizer = Organizer.objects.filter(slug__iexact=o_slug).first()

        with scope(organizer=o):

            qas = []

            e: Event
            for e in o.events.all():
                print(e.name)
                try:
                    q = Question.objects.get(identifier=frage_id, event=e)
                except Question.DoesNotExist:
                    continue

                qa_del = QuestionAnswer.objects.filter(question=q).delete()
                for order in e.orders.all():
                    if order.code in a_order_codes:
                        print(f"{order.code} Group A")
                        for op in order.positions.all():
                            if op.pseudonymization_id in sonder_codes:
                                qa = QuestionAnswer(
                                    orderposition=op,
                                    question=q,
                                    answer="A_sonder.png",
                                    file=f"cachedfiles/answers/{o.slug}/{e.slug}/{a_sonder}",
                                )
                                qas.append(qa)
                                print(f"{op.pseudonymization_id} special diet")
                            else:
                                qa = QuestionAnswer(
                                    orderposition=op,
                                    question=q,
                                    answer="A_regulaer.png",
                                    file=f"cachedfiles/answers/{o.slug}/{e.slug}/{a_regulaer}",
                                )
                                qas.append(qa)
                    else:
                        print(f"{order.code} Group B")
                        for op in order.positions.all():
                            if op.pseudonymization_id in sonder_codes:
                                qa = QuestionAnswer(
                                    orderposition=op,
                                    question=q,
                                    answer="B_sonder.png",
                                    file=f"cachedfiles/answers/{o.slug}/{e.slug}/{b_sonder}",
                                )
                                qas.append(qa)
                                print(f"{op.pseudonymization_id} special diet")

                            else:
                                qa = QuestionAnswer(
                                    orderposition=op,
                                    question=q,
                                    answer="B_regulaer.png",
                                    file=f"cachedfiles/answers/{o.slug}/{e.slug}/{b_regulaer}",
                                )
                                qas.append(qa)

            QuestionAnswer.objects.bulk_create(qas)
