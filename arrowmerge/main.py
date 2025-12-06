import sys
from PyQt6.QtWidgets import QApplication
from .model import DiffModel
from .view import DiffWindow
from .controller import DiffController

def main():
    app = QApplication(sys.argv)
    
    # MVC setup
    model = DiffModel()
    view = DiffWindow()
    controller = DiffController(model, view)
    
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
