# Register your receivers here
from django.dispatch import receiver
from pretix.base.signals import register_data_exporters


@receiver(register_data_exporters, dispatch_uid="voco_groupexporter")
def register_group_exporter(sender, **kwargs):
    from .exporter import GroupExporter

    return GroupExporter


@receiver(register_data_exporters, dispatch_uid="voco_dhlexporter")
def register_dhl_exporter(sender, **kwargs):
    from .exporter import DHLExporter

    return DHLExporter


@receiver(register_data_exporters, dispatch_uid="voco_postexporter")
def register_post_exporter(sender, **kwargs):
    from .exporter import PostExporter

    return PostExporter
