class Version:
    """Offline build: no update check, no outbound traffic."""

    def __init__(self, userSettings, main_app):
        self.main_app = main_app
        self.version = "1.4.4"
        self.new_version = ""
        self.update = self._disabled_text()

    def _disabled_text(self):
        return self.main_app.text_content["help_menu"]["about_settings"]["version_check_update_text"]["disabled"]

    def checkVersion(self):
        return self._disabled_text()

    def refresh_locale_text(self):
        self.update = self._disabled_text()
