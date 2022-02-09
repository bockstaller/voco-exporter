from datetime import date
from dateutil.relativedelta import relativedelta
from django_scopes import scope
from pretix.base.exporter import ListExporter
from pretix.base.models.items import Item
from pretix.base.models.orders import Order, QuestionAnswer
from enum import Enum


class GroupExporter(ListExporter):
    identifier = "voco-groupexporter"
    verbose_name = "roverVOCO Gruppeninfos"

    def get_filename(self):
        return "{}_groups".format(self.event.slug)

    def iterate_list(self, form_data):
        headers = ["Order Code", "Reiseart", "Bereich", "Auftakt", "Diözese"]

        headers.append("Anzahl Proj.")
        headers.append("Anzahl Proj. TN ü27")
        headers.append("Anzahl Proj. TN u27")
        headers.append("Anzahl Proj. TN u18")
        headers.append("Anzahl Proj. TN u16")
        headers.append("Anzahl Proj. Leiter*innen")
        headers.append("Anzahl Nachz.")
        headers.append("Anzahl Nachz. TN ü27")
        headers.append("Anzahl Nachz. TN u27")
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
                proj, projue27, proju27, proju18, proju16, projl = 0, 0, 0, 0, 0, 0
                nachz, nachzue27, nachzu27, nachzu18, nachzu16, nachzl = (
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                )
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
                        u16, u18, u27, ue27, leader = 0, 0, 0, 0, 0

                        if p.item in leiter:
                            leader = 1

                        try:
                            datum = date.fromisoformat(
                                p.answers.get(question__identifier=geb_date_id).answer
                            )
                            age = relativedelta(cut_off_date, datum).years

                            if age >= 27:
                                ue27 = 1
                            elif age > 18 & age < 27:
                                u27 = 1
                            elif age < 16:
                                u16 = 1
                            else:
                                u18 = 1
                        except QuestionAnswer.DoesNotExist:
                            u18 = 1

                        if p.item in tn:
                            projue27 += ue27
                            proju27 += u27
                            proju18 += u18
                            proju16 += u16
                            projl += leader
                            proj += c

                        if p.item in nz:
                            nachzue27 += ue27
                            nachzu27 += u27
                            nachzu18 += u18
                            nachzu16 += u16
                            nachzl += leader
                            nachz += c

                assert sum([nachz, proj]) == sum(
                    [
                        projue27,
                        proju27,
                        nachzu18,
                        nachzu16,
                        nachzue27,
                        nachzu27,
                        proju18,
                        proju16,
                    ]
                )

                yield [
                    o.code,
                    reiseart,
                    bereich,
                    auftakt,
                    dioezese,
                    proj,
                    projue27,
                    proju27,
                    proju18,
                    proju16,
                    projl,
                    nachz,
                    nachzue27,
                    nachzu27,
                    nachzu18,
                    nachzu16,
                    nachzl,
                ]


class Sizes(Enum):
    Maxibrief = "Maxibrief"
    Paeckchen_S = "PAECKS.DEU"
    Paeckchen_M = "PAECK.DEU"
    Packet_2KG = "PAK02.DEU"
    Packet_5KG = "PAK05.DEU"
    Packet_10KG = "PAK10.DEU"
    Packet_31KG = "PAK31.DEU"


class DHLExporter(ListExporter):
    identifier = "voco-dhlexporter"
    verbose_name = "roverVOCO DHL"

    def get_filename(self):
        return "{}_dhl".format(self.event.slug)

    def iterate_list(self, form_data):
        headers = ["Order Code"]

        headers.append("Anzahl Proj.")
        headers.append("Anzahl Nachz.")
        headers.append("SEND_NAME1")
        headers.append("SEND_NAME2")
        headers.append("SEND_STREET")
        headers.append("SEND_HOUSENUMBER")
        headers.append("SEND_PLZ")
        headers.append("SEND_CITY")
        headers.append("SEND_COUNTRY")
        headers.append("RECV_NAME1")
        headers.append("RECV_NAME2")
        headers.append("RECV_STREET")
        headers.append("RECV_HOUSENUMBER")
        headers.append("RECV_PLZ")
        headers.append("RECV_CITY")
        headers.append("RECV_COUNTRY")
        headers.append("PRODUCT")
        headers.append("COUPON")
        headers.append("SEND_EMAIL")

        yield headers

        tn = Item.objects.filter(id__in=[27, 28, 31])
        nz = Item.objects.filter(id__in=[45, 51, 53])
        gruppenleiter = Item.objects.filter(id__in=[27, 51])

        data = [
            ("W7N8FX3M", "RECV_STREET"),
            ("JGCZN9CQ", "RECV_HOUSENUMBER"),
            ("NETUFAER", "RECV_PLZ"),
            ("DXARB8KL", "RECV_CITY"),
        ]

        with scope(event=self.event):

            os = (
                Order.objects.exclude(status=Order.STATUS_CANCELED)
                .filter(event=self.event)
                .all()
            )
            for o in os:
                proj = 0
                nachz = 0

                d = {
                    "SEND_NAME1": "Marvin Anselm",
                    "SEND_NAME2": "Bundesamt Sankt Georg e.V.",
                    "SEND_STREET": "Martinstraße",
                    "SEND_HOUSENUMBER": "2",
                    "SEND_PLZ": "41472",
                    "SEND_CITY": "Neuss (Holzheim)",
                    "SEND_COUNTRY": "DEU",
                    "RECV_NAME1": "",
                    "RECV_NAME2": "",
                    "RECV_STREET": "",
                    "RECV_HOUSENUMBER": "",
                    "RECV_PLZ": "",
                    "RECV_CITY": "",
                    "RECV_COUNTRY": "DEU",
                    "PRODUCT": "",
                    "COUPON": "",
                    "SEND_EMAIL": "LUKAS.BOCKSTALLER@POSTEO.DE",
                }

                product, coupon = "", ""

                for p in o.all_positions.all():
                    if p.canceled:
                        continue

                    if p.item in gruppenleiter:
                        d["RECV_NAME1"] = p.attendee_name_cached

                        for key, var in data:
                            try:
                                d[var] = p.answers.get(question__identifier=key).answer

                            except QuestionAnswer.DoesNotExist:
                                pass

                    if p.item in tn:
                        proj += 1

                    if p.item in nz:
                        nachz += 1

                if sum([proj, nachz]) > 28:
                    d["PRODUCT"] = Sizes.Packet_10KG.value

                if sum([proj, nachz]) <= 28:
                    d["PRODUCT"] = Sizes.Packet_5KG.value

                if sum([proj, nachz]) <= 13:
                    d["PRODUCT"] = Sizes.Paeckchen_S.value

                if sum([proj, nachz]) <= 6:
                    d["PRODUCT"] = Sizes.Maxibrief.value
                    continue

                yield [
                    o.code,
                    proj,
                    nachz,
                ] + list(d.values())


class PostExporter(ListExporter):
    identifier = "voco-postexporter"
    verbose_name = "roverVOCO POST"

    def get_filename(self):
        return "{}_post".format(self.event.slug)

    def iterate_list(self, form_data):

        headers = ["Anzahl Proj."]
        headers.append("Anzahl Nachz.")
        headers.append("NAME")
        headers.append("ZUSATZ")
        headers.append("STRASSE")
        headers.append("NUMMER")
        headers.append("PLZ")
        headers.append("STADT")
        headers.append("LAND")
        headers.append("ADRESS_TYP")
        headers.append("REFERENZ")

        yield headers

        tn = Item.objects.filter(id__in=[27, 28, 31])
        nz = Item.objects.filter(id__in=[45, 51, 53])
        gruppenleiter = Item.objects.filter(id__in=[27, 51])

        data = [
            ("W7N8FX3M", "STRASSE"),
            ("JGCZN9CQ", "NUMMER"),
            ("NETUFAER", "PLZ"),
            ("DXARB8KL", "STADT"),
        ]

        with scope(event=self.event):

            os = (
                Order.objects.exclude(status=Order.STATUS_CANCELED)
                .filter(event=self.event)
                .all()
            )
            for o in os:
                proj = 0
                nachz = 0

                d = {
                    "NAME": "",
                    "ZUSATZ": "",
                    "STRASSE": "",
                    "NUMMER": "",
                    "PLZ": "",
                    "STADT": "",
                    "LAND": "DEU",
                    "ADRESS_TYP": "HOUSE",
                    "REFERENZ": o.code,
                }

                product, coupon = "", ""

                for p in o.all_positions.all():
                    if p.canceled:
                        continue

                    if p.item in gruppenleiter:
                        d["NAME"] = p.attendee_name_cached

                        for key, var in data:
                            try:
                                d[var] = p.answers.get(question__identifier=key).answer

                            except QuestionAnswer.DoesNotExist:
                                pass

                    if p.item in tn:
                        proj += 1

                    if p.item in nz:
                        nachz += 1

                if sum([proj, nachz]) > 6:
                    continue

                yield [
                    proj,
                    nachz,
                ] + list(d.values())
