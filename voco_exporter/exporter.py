from datetime import date
from dateutil.relativedelta import relativedelta
from django_scopes import scope
from pretix.base.exporter import ListExporter
from pretix.base.models.items import Item
from pretix.base.models.orders import Order, QuestionAnswer


class GroupExporter(ListExporter):
    identifier = "voco-groupexporter"
    verbose_name = "roverVOCO Gruppeninfos"

    def get_filename(self):
        return "{}_groups".format(self.event.slug)

    def iterate_list(self, form_data):
        headers = ["Order Code", "Reiseart", "Bereich", "Auftakt", "Diözese"]

        headers.append("Anzahl Proj.")
        headers.append("Anzahl Proj. TN ü18")
        headers.append("Anzahl Proj. TN u18")
        headers.append("Anzahl Proj. TN u16")
        headers.append("Anzahl Proj. Leiter*innen")
        headers.append("Anzahl Nachz.")
        headers.append("Anzahl Nachz. TN ü18")
        headers.append("Anzahl Nachz. TN u18")
        headers.append("Anzahl Nachz. TN u16")
        headers.append("Anzahl Nachz. Leiter*innen")

        yield headers

        gruppeninfo = Item.objects.filter(id=30)
        gruppeninfo_nachz = Item.objects.filter(id=56)
        tn = Item.objects.filter(id__in=[27, 28, 31])
        nz = Item.objects.filter(id__in=[45, 51, 53])
        leiter = Item.objects.filter(id__in=[27, 31, 51, 53])

        dioezese_id = "C3YKTN77"
        reiseart_id = "TRWSCC8E"
        bereich_id = "AEYPGRNG"
        geb_date_id = "EQ3HTNKC"

        cut_off_date = date(year=2021, month=4, day=10)

        with scope(event=self.event):

            os = (
                Order.objects.exclude(status=Order.STATUS_CANCELED)
                .filter(event=self.event)
                .all()
            )
            for o in os:
                proj, projue18, proju18, proju16, projl = 0, 0, 0, 0, 0
                nachz, nachzue18, nachzu18, nachzu16, nachzl = 0, 0, 0, 0, 0
                reiseart, bereich, auftakt, dioezese = "", "", "", ""

                for p in o.all_positions.all():
                    if p.canceled:
                        continue

                    try:
                        dioezese = p.answers.get(
                            question__identifier=dioezese_id
                        ).answer
                    except QuestionAnswer.DoesNotExist:
                        pass

                    if p.item in gruppeninfo:
                        try:
                            reiseart = p.answers.get(
                                question__identifier=reiseart_id
                            ).answer

                        except QuestionAnswer.DoesNotExist:
                            pass

                        if dioezese in [
                            "Eichstätt",
                            "Passau",
                            "Bamberg",
                            "Augsburg",
                            "Würzburg",
                            "Regensburg",
                            "München - Freising",
                        ]:
                            auftakt = "Süd"
                        if dioezese in [
                            "Aachen",
                            "Paderborn",
                            "Essen",
                            "Münster",
                            "Köln",
                        ]:
                            auftakt = "West"
                        if dioezese in [
                            "Freiburg",
                            "Fulda",
                            "Limburg",
                            "Mainz",
                            "Rottenburg-Stuttgart",
                            "Speyer",
                            "Trier",
                        ]:
                            auftakt = "Mitte"
                        if dioezese in [
                            "Erfurt",
                            "Magdeburg",
                            "Berlin",
                            "Osnabrück",
                            "Hildesheim",
                            "Hamburg",
                        ]:
                            auftakt = "Nord-Ost"

                        try:
                            bereich = p.answers.get(
                                question__identifier=bereich_id
                            ).answer
                        except QuestionAnswer.DoesNotExist:
                            pass

                    elif (p.item in gruppeninfo_nachz) & (reiseart == ""):
                        reiseart = "Nachzügler"

                    else:
                        c = 1
                        ue18, u16, u18, leader = 0, 0, 0, 0

                        if p.item in leiter:
                            leader = 1
                        else:
                            try:
                                datum = date.fromisoformat(
                                    p.answers.get(
                                        question__identifier=geb_date_id
                                    ).answer
                                )
                                age = relativedelta(cut_off_date, datum).years
                                if age > 18:
                                    ue18 = 1
                                elif age < 16:
                                    u16 = 1
                                else:
                                    u18 = 1
                            except QuestionAnswer.DoesNotExist:
                                u18 = 1

                        if p.item in tn:
                            projue18 += ue18
                            proju18 += u18
                            proju16 += u16
                            projl += leader
                            proj += c

                        if p.item in nz:
                            nachzue18 += ue18
                            nachzu18 += u18
                            nachzu16 += u16
                            nachzl += leader
                            nachz += c

                assert sum([nachz, proj]) == sum(
                    [
                        nachzue18,
                        nachzu18,
                        nachzu16,
                        nachzl,
                        projue18,
                        proju18,
                        proju16,
                        projl,
                    ]
                )

                yield [
                    o.code,
                    reiseart,
                    bereich,
                    auftakt,
                    dioezese,
                    proj,
                    projue18,
                    proju18,
                    proju16,
                    projl,
                    nachz,
                    nachzue18,
                    nachzu18,
                    nachzu16,
                    nachzl,
                ]
