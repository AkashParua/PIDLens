import sys
from PyQt6.QtWidgets import QApplication

from pidlens.config import APP_NAME, ORG_NAME
from pidlens.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
