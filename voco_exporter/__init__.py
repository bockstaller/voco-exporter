from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.0.0"


class PluginApp(PluginConfig):
    name = "voco_exporter"
    verbose_name = "voco exporter"

    class PretixPluginMeta:
        name = gettext_lazy("voco exporter")
        author = "Lukas Bockstaller"
        description = gettext_lazy("Short description")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = "voco_exporter.PluginApp"
