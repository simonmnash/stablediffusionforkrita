from krita import *
from PyQt5.QtWidgets import QDialog, QTextEdit, QPushButton, QHBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QByteArray
from urllib import request, parse
import json
from krita import *
import os
from PIL import Image
from io import BytesIO

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
        
        t2iButton = QPushButton("Text To Image")
        t2iButton.clicked.connect((lambda x: self.send_request(prompt=text_edit.toPlainText(), endpoint="prompt_to_image")))
        t2iButton.clicked.connect(newDialog.accept)

        i2iButton = QPushButton("Image To Image")
        i2iButton.clicked.connect((lambda x: self.send_request(prompt=text_edit.toPlainText(), endpoint="image_to_image")))
        i2iButton.clicked.connect(newDialog.accept)


        layout.addWidget(label)
        layout.addWidget(text_edit)
        layout.addWidget(t2iButton)

        newDialog.setWindowTitle("GenerateImage")
        newDialog.setLayout(layout) 
        newDialog.exec_()

    def send_request(self, prompt="test", endpoint="prompt_to_image"):
        d = Krita.instance().activeDocument()
        x, y, w, h, pixel_data = current_selection_pixel_data()
        API_KEY = ''
        data = json.dumps({'prompt': prompt, 'width': w, 'height': h}).encode('utf8')
        if endpoint=="prompt_to_image":
            req = request.Request("""http://127.0.0.1:8000/prompt_to_image""", data=data)
        elif endpoint=="image_to_image":
            req = request.Request("""http://127.0.0.1:8000/image_to_image""", data=data, files=("selection", pixel_data))
        req.add_header('x-api-key', API_KEY)
        req.add_header("Content-Type", "application/json")
        contents = request.urlopen(req, timeout=1000000000)
        with open("temporary_file.png", "wb") as f:
            f.write(contents.read())
        with Image.open("temporary_file.png") as f:
            bytearray = QByteArray(f.convert('RGBA').tobytes())
        new_paint_layer = d.createNode("TEST", "paintLayer")
        new_paint_layer.setPixelData(bytearray, x, y, w, h)
        root = d.rootNode()
        child_nodes = root.childNodes()
        root.addChildNode(new_paint_layer, child_nodes[-1])
        d.refreshProjection()



Krita.instance().addExtension(StableDiffusionExtension(Krita.instance()))