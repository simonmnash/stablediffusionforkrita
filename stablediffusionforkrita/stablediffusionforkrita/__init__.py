from krita import *
#from stablediffusionforkrita import StableDiffusionExtension

from PyQt5.QtWidgets import QDialog, QTextEdit, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QByteArray
from urllib import request, parse
import json
from krita import *

HOST = "127.0.0.1"
PORT = "8000"
#signal_name = pyqtSignal(bool, name='signalName')

def current_selection_pixel_data():
    d = Krita.instance().activeDocument()
    current_selection = d.selection()
    x = current_selection.x()
    y = current_selection.y()
    w = current_selection.width()
    h = current_selection.height()
    w = min([w, 512])
    h = min([h, 512])
    w = w - (w % 64)
    h = h - (h % 64)
    pixel_data = d.pixelData(x, y, w , h)
    return x, y, w, h, pixel_data


class StableDiffusionExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        open_prompt = window.createAction("QueueStableDiffusionAction", "StableDiffusion", "tools/scripts")
        open_prompt.triggered.connect(self.queue_request)
    
    def queue_request(self):
        x, y, w, h, pixel_data = current_selection_pixel_data()
        image = QImage(pixel_data, w, h, QImage.Format_RGB32)
        pix_map = QPixmap.fromImage(image)

        newDialog = QDialog()
        layout = QHBoxLayout()
        text_edit = QTextEdit()
        label = QLabel()
        label.setPixmap(pix_map)
        
        newButton = QPushButton("Generate")
        newButton.clicked.connect(self.send_request)
        newButton.clicked.connect(newDialog.accept)
        layout.addWidget(label)
        layout.addWidget(text_edit)
        layout.addWidget(newButton)

        newDialog.setWindowTitle("GenerateImage")
        newDialog.setLayout(layout) 
        newDialog.exec_()

    def send_request(self, prompt="test"):
        d = Krita.instance().activeDocument()
        x, y, w, h, pixel_data = current_selection_pixel_data()
        API_KEY = ''

        data = json.dumps({'prompt': prompt, 'width': w, 'height': h}).encode('utf8')
        req = request.Request("""http://127.0.0.1:8000/prompt_to_image""", data=data)
        req.add_header('x-api-key', API_KEY)
        req.add_header("Content-Type", "application/json")
        contents = request.urlopen(req, timeout=1000000000)
        with open("temporary_file.png", "wb") as f:
            f.write(contents.read())
        new_paint_layer = d.createNode("TEST", "paintLayer")
        new_file_layer = d.createFileLayer("test", "temporary_file.png", None)
        new_file_layer.move(x, y)
        root = d.rootNode()
        child_nodes = root.childNodes()
        root.addChildNode(new_paint_layer, child_nodes[0]) 
        root.addChildNode(new_file_layer, child_nodes[0])
        new_paint_layer.mergeDown()
        d.refreshProjection()


Krita.instance().addExtension(StableDiffusionExtension(Krita.instance()))