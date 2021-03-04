# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from dataclasses import dataclass, field
from typing import Tuple, Dict
from time import sleep
import keyboard
import mouse
from PIL import Image
import pyscreenshot as ImageGrab
from operator import itemgetter
import numpy as np
import hitherdither
import os

# TODO https://github.com/hbldh/hitherdither
# TODO check of afbeelding bestaat
# TODO maak color pallete preview of een grid of geef het een scrollbar
# TODO scaling en dither menu toepassen en verbinden
# TODO transparantie toevoegen
# TODO ook als png of bmp opslaan zodat je geen artifacts krijgt
# TODO before drawing have a popup which states the estimated drawing time, amount of dots and amount of colors and have user confirm


def grab_color() -> Tuple[Tuple[int, int, int], Tuple[int, int]]:
    """
    returns a list with a tuple containing the RGB value of the most
     present color around the mouse and the position at the time of measurement
    """
    pos = mouse.get_position()
    m = 2
    rect = (pos[0] - m, pos[1] - m, pos[0] + m, pos[1] + m)

    img = ImageGrab.grab(rect)
    colors = img.getcolors()
    most_common = max(colors, key=itemgetter(1))[1]

    return most_common, pos


class QPaletteButton(QtWidgets.QPushButton):
    def __init__(self, rgb_color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24, 24))

        self.rgb_color = rgb_color
        self.color = '#{:02x}{:02x}{:02x}'.format(*rgb_color)
        # self.setEnabled(False)
        self.setStyleSheet("border :1px solid ;background-color: %s;" %
                           self.color)


@dataclass
class img_file():
    filename: str
    # max size is actualy the width of the image but i did not update this yet
    max_size: int
    qpix: QtGui.QPixmap = field(init=False, default=None)
    qpix_scaled: QtGui.QPixmap = field(init=False, default=None)
    aspect_ratio: float = field(init=False, default=None)
    width: int = field(init=False, default=None)
    height: int = field(init=False, default=None)

    def __post_init__(self):
        self.qpix = QtGui.QPixmap(self.filename)
        self.width, self.heigth = self.qpix.width(), self.qpix.height()
        self.aspect_ratio = self.width / self.heigth
        self.generate_scaled()

    def generate_scaled(self):
        # if self.width == self.heigth:
        #     self.qpix_scaled = self.qpix.scaled(self.max_size, self.max_size)
        # elif self.width > self.heigth:
        #     # self.qpix_scaled = self.qpix.scaled(
        #     #     self.max_size,
        #     #     int(1 / self.aspect_ratio * self.max_size),
        #     #     transformMode=QtCore.Qt.FastTransformation)
        #     self.qpix_scaled = self.qpix.scaled(
        #         self.max_size,
        #         int(1 / self.aspect_ratio * self.max_size),
        #         transformMode=QtCore.Qt.SmoothTransformation)
        self.qpix_scaled = self.qpix.scaled(
            self.max_size,
            int(1 / self.aspect_ratio * self.max_size),
            transformMode=QtCore.Qt.SmoothTransformation)
        # else:
        # self.qpix_scaled = self.qpix.scaled(
        #     int(self.aspect_ratio * self.max_size),
        #     self.max_size,
        #     transformMode=QtCore.Qt.FastTransformation)
        # self.qpix_scaled = self.qpix.scaled(
        #     int(self.aspect_ratio * self.max_size),
        #     self.max_size,
        #     transformMode=QtCore.Qt.SmoothTransformation)

    def update_size(self, new_max_size: int):
        self.max_size = int(new_max_size)
        self.generate_scaled()


class FloatingPreview(QtWidgets.QWidget):
    def __init__(self, input_img: img_file, opacity: int):
        super().__init__()

        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.setStyleSheet("QMainWindow {background: transparent;}\n"
                           "QToolTip {\n"
                           "    color: #ffffff;\n"
                           "    background-color: rgba(227, 29, 35, 160);\n"
                           "    border: 1px solid rgb(40, 40, 40);\n"
                           "    border-radius: 2px;\n"
                           "}")
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.m_original_input_image = input_img
        self.m_label = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.m_label.setPixmap(self.m_original_input_image.qpix)
        self.dragPos = QtCore.QPoint()
        self.m_label.mouseMoveEvent = self.mouseMoveEvent

        self.change_opacity(opacity)

        lay = QtWidgets.QVBoxLayout(self)
        # lay.addWidget(self.m_slider)
        lay.addWidget(self.m_label)

    def change_opacity(self, opacity):
        self.opacity = opacity * 0.01
        self.__update_opacity()

    def __update_opacity(self):
        new_pix = QtGui.QPixmap(self.m_original_input_image.qpix_scaled.size())
        new_pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(new_pix)
        painter.setOpacity(self.opacity)
        painter.drawPixmap(QtCore.QPoint(),
                           self.m_original_input_image.qpix_scaled)
        painter.end()
        self.m_label.setPixmap(new_pix)

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()

    def update_image(self):
        # self.m_label.setPixmap(self.m_original_input_image.qpix_scaled)
        self.__update_opacity()

    def resize_window(self, new_size_width: int):
        # print(
        #     new_size_width,
        #     int(1 / self.m_original_input_image.aspect_ratio * new_size_width))
        # self.resize(
        #     new_size_width,
        #     int(1 / self.m_original_input_image.aspect_ratio * new_size_width))
        self.m_original_input_image.update_size(new_size_width)
        self.resize(1, 1)
        self.update_image()
        # print()
        # print("pos", self.dragPos)
        # print("x", self.dragPos.x())
        # print("y", self.dragPos.y())
        # print("left", self.geometry().left())
        # print("top", self.geometry().top())
        # print("right", self.geometry().right())
        # print("bottom", self.geometry().bottom())
        # print("label left", self.m_label.geometry().left())
        # print("label top", self.m_label.geometry().top())
        # print("label right", self.m_label.geometry().right())
        # print("label bottom", self.m_label.geometry().bottom())
        # print()


class DrawingWorker(QtCore.QThread):
    # send int between 0 and 100 to assign percentage of done
    progress_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        QtCore.QThread.__init__(self)

    def start_drawing(self, drawing_domain: Tuple[int, int, int,
                                                  int], color_palette: dict,
                      output_img: img_file, home: Tuple[int, int],
                      drawing_speed: float, waiting_speed: float):
        self.drawing_domain = drawing_domain
        self.color_palette_dict = color_palette
        self.qpix_input_image: img_file = output_img
        # self.resize_method = resize_method
        self.home = home
        self.drawing_speed = drawing_speed
        self.waiting_speed = waiting_speed
        # TODO
        self.background_color = (255, 255, 255)

        self.resize_resample = {
            "NEAREST": Image.NEAREST,
            "BOX": Image.BOX,
            "BILINEAR": Image.BILINEAR,
            "HAMMING": Image.HAMMING,
            "BICUBIC": Image.BICUBIC,
            "LANCZOS": Image.LANCZOS
        }

        # first we map the pixels to each color in the pallete
        self.generate_que()
        self.draw_with_mouse()

    def generate_que(self):
        self.que = {}

        for color in self.color_palette_dict.keys():
            self.que[color] = []

        print("now generating que")
        self.img = Image.open(self.qpix_input_image.filename)

        # if the image has transparency replace that transparency
        # TODO make a function for this
        if self.img.mode != "RGB":
            png = self.img.convert('RGBA')
            background = Image.new('RGBA', png.size, (255, 255, 255))

            alpha_composite = Image.alpha_composite(background, png)
            self.img = alpha_composite.convert('RGB')

        self.img = np.array(self.img)

        # itterate over pixels and add color to que
        for y in range(self.img.shape[1] - 1):
            if y % 10 == 0:
                self.progress_signal.emit(int(100 / self.img.shape[1] * y))
            for x in range(self.img.shape[0] - 1):
                color = tuple(self.img[x, y])
                self.que[color].append((x, y))

        self.progress_signal.emit(100)

    def draw_with_mouse(self):
        self.progress_signal.emit(0)
        print("starting drawing")
        colors_placed = 0
        prev_percent = 0
        for i in list(self.color_palette_dict.keys()):
            if i == self.background_color:
                continue

            # print(i)

            # sleep(0.2)
            x, y = self.home
            mouse.move(x, y)
            # sleep(0.15)
            sleep(self.waiting_speed)
            mouse.click()
            sleep(self.waiting_speed)
            # sleep(1)
            # select the color
            x, y = self.color_palette_dict[i]
            print("color = ", i, "@", x, y)
            mouse.move(x, y)
            sleep(self.waiting_speed)
            # sleep(0.15)
            mouse.click()
            sleep(self.waiting_speed)
            # sleep(0.15)

            for j in self.que[i]:
                # update progrssbar
                if not colors_placed % 40:
                    curr_precent = int(colors_placed * 100 /
                                       (self.img.shape[1] * self.img.shape[0]))
                    if curr_precent > prev_percent:
                        prev_percent = curr_precent
                        # sleep(0.2)
                        # self.progress_signal.emit(curr_precent)
                        # sleep(0.2)
                if keyboard.is_pressed("escape") or keyboard.is_pressed(
                        "shift"):
                    self.progress_signal.emit(0)
                    return

                y, x = j
                mouse.move(
                    self.drawing_domain[0] + x *
                    (self.drawing_domain[2] - self.drawing_domain[0]) /
                    self.img.shape[0], self.drawing_domain[1] + y *
                    (self.drawing_domain[3] - self.drawing_domain[1]) /
                    self.img.shape[1])
                # mouse.move(200 + x * 4, 400 + y * 4)
                # sleep(0.0000005)
                sleep(self.drawing_speed)
                mouse.click()
                sleep(self.drawing_speed)
                # sleep(0.0000005)
                colors_placed += 1
        self.progress_signal.emit(100)


class FloydWorker(QtCore.QThread):
    output_name_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.color_pallette_dict: dict = {(1, 1, 1): (0, 0)}

        # self.qpix_input_image: img_file = None

        self.image_name = None
        self.size = None
        self.resize_method: str = None
        # self.dither_method: str = "Floyd-Steinberg"
        self.dither_method: str = None

        self.resize_resample = {
            "NEAREST": Image.NEAREST,
            "BOX": Image.BOX,
            "BILINEAR": Image.BILINEAR,
            "HAMMING": Image.HAMMING,
            "BICUBIC": Image.BICUBIC,
            "LANCZOS": Image.LANCZOS
        }

        self.error_diffusion_dithering = [
            "Floyd-Steinberg", "Jarvis-Judice-Ninke", "Stucki", "Burkes",
            "Sierra3", "Sierra2", "Sierra-2-4A", "Atkinson"
        ]
        self.ordered_dither_functions = {
            "Yliluoma":
            hitherdither.ordered.yliluoma.yliluomas_1_ordered_dithering,
            "Bayer matrix":
            hitherdither.ordered.bayer.bayer_dithering,
            "Cluster dot matrix":
            hitherdither.ordered.cluster.cluster_dot_dithering
        }

    def run(self):
        print("starting pre-processing")
        # we want to change the output format to png
        intermediate_filename = self.image_name.split("/")[-1]
        intermediate_filename_parts = intermediate_filename.split(".")
        intermediate_filename = '.'.join(
            intermediate_filename_parts[:-1]) + ".png"
        self.output_file_name = "./output/" + intermediate_filename

        if not isinstance(self.image_name, str):
            raise TypeError("filename must excist")

        self.hither_palette = hitherdither.palette.Palette(
            list(self.color_pallette_dict.keys()))
        # print(list(self.color_pallette_dict.keys()))

        img = Image.open(self.image_name).resize(
            self.size, self.resize_resample[self.resize_method])
        # img.show()

        # if the image is a png the transparancy needs to be removed
        # TODO make the background color custom adjustable
        # TODO add support for other image modes
        if img.mode != "RGB":
            png = img.convert('RGBA')
            background = Image.new('RGBA', png.size, (255, 255, 255))

            alpha_composite = Image.alpha_composite(background, png)
            img = alpha_composite.convert('RGB')

        print("starting processing")
        if self.dither_method in self.error_diffusion_dithering:
            print(img, self.hither_palette, self.dither_method)
            img_dithered = hitherdither.diffusion.error_diffusion_dithering(
                img, self.hither_palette, self.dither_method)
        elif self.dither_method == "Yliluoma":
            img_dithered = self.ordered_dither_functions[self.dither_method](
                img, self.hither_palette)
        else:
            img_dithered = self.ordered_dither_functions[self.dither_method](
                img, self.hither_palette, thresholds=1)

        # img_dithered.show()

        # TODO dit is nog overbodig
        if img_dithered.mode != 'RGB':
            img_dithered = img_dithered.convert('RGB')

        # img_dithered.show()

        try:
            os.makedirs("./output")
        except FileExistsError:
            pass

        # TODO the image always needs to be saved as a png
        try:
            img_dithered.save(self.output_file_name)
        except PermissionError as error:
            tmp = str(error)
            print("het ging fout", tmp)
            return
            # tmp = str(error)
            # print("het ging fout")
            # QtWidgets.QMessageBox.about(
            #     self, tmp,
            #     "Waarschijnlijk heeft python geen toegang tot de output map")

            # tmp = str(error)

            # error_dialog = QtWidgets.QMessageBox(QtWidgets.QMainWindow)
            # error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
            # error_dialog.setText("permission error")
            # error_dialog.setInformativeText(
            #     tmp +
            #     "\nWaarschijnlijk heeft python geen toegang tot de output map")
            # error_dialog.setWindowTitle("Error")
            # error_dialog.exec_()

        self.output_name_signal.emit(self.output_file_name)
        print("done")


class ColorWorker(QtCore.QThread):
    # used to communicate color
    color_signal = QtCore.pyqtSignal(tuple)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.keep_looking = True
        # moet een int zijn :(
        self.short_sleep_time = 1  # s

    # run method gets called when we start the thread
    def run(self):
        self.keep_looking = True
        while self.keep_looking:
            if keyboard.is_pressed("shift"):
                # scrllock is misschien ook nice
                color, position = grab_color()
                self.color_signal.emit((color, position))
                QtCore.QThread.sleep(self.short_sleep_time)
            if keyboard.is_pressed("ctrl"):
                print(mouse.get_position())

    def stop(self):
        self.keep_looking = False


class HomeWorker(QtCore.QThread):
    # used to communicate color
    home_signal = QtCore.pyqtSignal(tuple)

    def __init__(self):
        QtCore.QThread.__init__(self)
        self.keep_looking = True
        self.short_sleep_time = 1  # s

    # run method gets called when we start the thread
    def run(self):
        self.keep_looking = True
        while self.keep_looking:
            if keyboard.is_pressed("shift"):
                # scrllock is misschien ook nice
                pos = mouse.get_position()
                self.home_signal.emit(pos)
                QtCore.QThread.sleep(self.short_sleep_time)

    def stop(self):
        self.keep_looking = False


class Ui_Image_drawer(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui_Image_drawer, self).__init__()
        # super().__init__()
        # print((self))
        # print(type(self))

        # define defaults
        self.DEFAULT_IMG_MENU_SIZE = 180
        self.DEFAULT_INPUT_IMG = img_file("./sources/eend.png",
                                          self.DEFAULT_IMG_MENU_SIZE)
        self.DEFAULT_OUTPUT_IMG = img_file("./sources/eend_out.png",
                                           self.DEFAULT_IMG_MENU_SIZE)
        self.DEFAULT_WINDOW_SIZE = (430, 700)
        self.DEFAULT_OUTPUT_IMG_SIZE = (40, 40)
        self.DEFAULT_SCALE_METHOD = "NEAREST"
        self.DEFAULT_DITHER_METHOD = "Floyd-Steinberg"
        self.DEFAULT_HOME = (0, 0)
        self.DEFAULT_PREVIEW_OPACITY = 80

        # drawing speeds in seconds
        self.AVAILABLE_DRAWING_SPEEDS = [
            0.0001, 0.000005, 0.000001, 0.0000005, 0.0000002
        ]
        self.DEFAULT_DRAWING_SPEED_IDX = 2
        self.drawing_speed = self.AVAILABLE_DRAWING_SPEEDS[
            self.DEFAULT_DRAWING_SPEED_IDX]
        # waiting speeds in seconds
        self.AVAILABLE_WAITING_SPEEDS = [0.000001, 0.15, 1, 4]
        self.DEFAULT_WAITING_SPEED_IDX = 1
        self.waiting_speed = self.AVAILABLE_WAITING_SPEEDS[
            self.DEFAULT_WAITING_SPEED_IDX]
        # file types which we let the user input
        self.ACCEPTED_FILETYPES = ["jpg", "png", "bmp"]

        self.img_menu_size = self.DEFAULT_IMG_MENU_SIZE
        self.input_img = self.DEFAULT_INPUT_IMG
        self.output_img = self.DEFAULT_OUTPUT_IMG
        self.output_img_size = self.DEFAULT_OUTPUT_IMG_SIZE
        self.scale_method = self.DEFAULT_SCALE_METHOD
        self.dither_method = self.DEFAULT_DITHER_METHOD
        self.home = self.DEFAULT_HOME

        self.color_pallette = {}
        self.palette_preview_button_list = []

        # which colors have been added to preview of the color_palette
        self.drawn_palette_colors = []

        self.floating_image_preview_window = FloatingPreview(
            img_file(self.output_img.filename, self.output_img_size[1]),
            self.DEFAULT_PREVIEW_OPACITY)

        icon = QtGui.QIcon("./sources/icon.png")
        # icon.addPixmap(QtGui.QPixmap("./sources/eend.png"),
        #                QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.setWindowIcon(icon)

    def UI_setup(self, Image_drawer):
        self.UI_window(Image_drawer)
        self.img_dwr = Image_drawer
        # self.img_dwr.closeEvent.

        self.init_thread()

        self.UI_vertical_layout()

        Image_drawer.setCentralWidget(self.centralwidget)

        self.UI_menubar()
        Image_drawer.setMenuBar(self.menubar)

        # self.update_input_image()
        self.retranslateUi(Image_drawer)
        QtCore.QMetaObject.connectSlotsByName(Image_drawer)

    def UI_window(self, Image_drawer):
        Image_drawer.resize(*self.DEFAULT_WINDOW_SIZE)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            Image_drawer.sizePolicy().hasHeightForWidth())
        Image_drawer.setSizePolicy(sizePolicy)
        self.centralwidget = QtWidgets.QWidget(Image_drawer)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)

        # self.setWindowTitle("image-plotter")

    def UI_vertical_layout(self):
        self.veticalLayout_outer = QtWidgets.QVBoxLayout(self.centralwidget)
        self.veticalLayout_outer.setSizeConstraint(
            QtWidgets.QLayout.SetMinimumSize)

        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumWidth(self.DEFAULT_WINDOW_SIZE[0])
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Raised)

        self.veticalLayout_outer.addWidget(self.scrollArea)

        self.veticalLayout_inner = QtWidgets.QVBoxLayout(self.centralwidget)

        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.veticalLayout_inner)
        self.scrollArea.setWidget(self.main_widget)

        # self.veticalLayout_inner.setSizeConstraint(
        #     QtWidgets.QLayout.SetMaximumSize)
        self.veticalLayout_inner.setSizeConstraint(
            QtWidgets.QLayout.SetMinimumSize)

        # voor de afbeelding grootte double spinbox
        self.UI_img_menu_size()
        self.veticalLayout_inner.addLayout(self.gridLayout_menu_img_size)

        # schijdingslijn
        self.line_img_menu_size = QtWidgets.QFrame(self.centralwidget)
        self.line_img_menu_size.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_img_menu_size.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.veticalLayout_inner.addWidget(self.line_img_menu_size)

        self.UI_grid_layout_1()
        self.veticalLayout_inner.addLayout(self.gridLayout_1)

        self.line_pallete = QtWidgets.QFrame(self.centralwidget)
        self.line_pallete.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_pallete.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.veticalLayout_inner.addWidget(self.line_pallete)

        self.label_color_pallete = QtWidgets.QLabel(self.centralwidget)
        self.veticalLayout_inner.addWidget(self.label_color_pallete)

        self.UI_colorboxes()
        self.veticalLayout_inner.addLayout(self.horizontalLayout_colorboxes)

        self.UI_vertical_layout_drawing_speed()
        self.veticalLayout_inner.addLayout(self.verticalLayout_drawing_speed)

        self.UI_vertical_layout_waiting_speed()
        self.veticalLayout_inner.addLayout(self.verticalLayout_waiting_speed)

        self.line_13 = QtWidgets.QFrame(self.centralwidget)
        self.line_13.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_13.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.veticalLayout_inner.addWidget(self.line_13)
        '''origineer zou hier een progressbar komen maar dat is niet meer zo handig gezien ik nu een library gebruik voor het ditheren
        wellicht kan hier later nog de progressie van het tekenen worden weergeven. Maar dit zou ook net zo goed bovenaan de ui kunnen gebeuren'''
        self.label_progress = QtWidgets.QLabel(self.centralwidget)
        self.label_progress.setAlignment(QtCore.Qt.AlignCenter)
        self.veticalLayout_inner.addWidget(self.label_progress)

        self.progressBar_main = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar_main.setMaximum(100)
        self.progressBar_main.setProperty("value", 0)
        self.veticalLayout_inner.addWidget(self.progressBar_main)

        # self.progressBar_secondary = QtWidgets.QProgressBar(self.centralwidget)
        # self.progressBar_secondary.setProperty("value", 0)
        # self.veticalLayout_inner.addWidget(self.progressBar_secondary)

        spacerItem6 = QtWidgets.QSpacerItem(20, 40,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.veticalLayout_inner.addItem(spacerItem6)

    def UI_grid_layout_1(self):
        self.gridLayout_1 = QtWidgets.QGridLayout()
        self.gridLayout_1.setHorizontalSpacing(6)

        self.pushButton_generate_output = QtWidgets.QPushButton(
            self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pushButton_generate_output.sizePolicy().hasHeightForWidth())
        self.pushButton_generate_output.setSizePolicy(sizePolicy)
        self.pushButton_generate_output.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_generate_output.clicked.connect(self.floyd)
        self.gridLayout_1.addWidget(self.pushButton_generate_output, 7, 0, 1,
                                    1)

        self.checkBox_display_image_placing = QtWidgets.QCheckBox(
            self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBox_display_image_placing.
                                     sizePolicy().hasHeightForWidth())
        self.checkBox_display_image_placing.setSizePolicy(sizePolicy)
        self.checkBox_display_image_placing.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_display_image_placing.toggled.connect(
            self.show_hide_floating_placer)
        self.gridLayout_1.addWidget(self.checkBox_display_image_placing, 7, 2,
                                    1, 1)

        self.UI_pixmap_output_image()
        self.gridLayout_1.addWidget(self.label_pixmap_output_image, 4, 2, 1, 1)

        self.label_input_image = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_1.addWidget(self.label_input_image, 3, 0, 1, 1)

        self.label_output_image = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_1.addWidget(self.label_output_image, 3, 2, 1, 1)

        self.UI_pixmap_input_image()
        self.gridLayout_1.addWidget(self.label_pixmap_input_image, 4, 0, 1, 1)

        self.line_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_1.addWidget(self.line_3, 7, 1, 1, 1)

        self.line_4 = QtWidgets.QFrame(self.centralwidget)
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_1.addWidget(self.line_4, 8, 1, 1, 1)

        self.pushButton_start_drawing = QtWidgets.QPushButton(
            self.centralwidget)
        self.pushButton_start_drawing.setEnabled(True)
        self.pushButton_start_drawing.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton_start_drawing.clicked.connect(self.draw_output)
        self.gridLayout_1.addWidget(self.pushButton_start_drawing, 8, 0, 1, 1)

        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_1.addWidget(self.line_2, 5, 1, 1, 1)

        self.gridLayout_input_color_and_set_home = QtWidgets.QGridLayout()
        self.checkBox_input_colors = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_input_colors.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.gridLayout_input_color_and_set_home.addWidget(
            self.checkBox_input_colors, 0, 0, 1, 1)
        self.checkBox_input_colors.toggled.connect(self.load_pallete)

        self.checkBox_set_home = QtWidgets.QRadioButton(self.centralwidget)
        self.checkBox_set_home.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.checkBox_set_home.toggled.connect(self.define_home)
        self.gridLayout_input_color_and_set_home.addWidget(
            self.checkBox_set_home, 0, 1, 1, 1)

        self.spinBox_input_colors = QtWidgets.QSpinBox(self.centralwidget)
        self.spinBox_input_colors.setReadOnly(True)
        self.spinBox_input_colors.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_input_colors.setMaximum(16581375)
        self.gridLayout_input_color_and_set_home.addWidget(
            self.spinBox_input_colors, 1, 0, 1, 1)

        self.progressBar_home_set = QtWidgets.QProgressBar(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.progressBar_home_set.sizePolicy().hasHeightForWidth())
        self.progressBar_home_set.setSizePolicy(sizePolicy)
        self.progressBar_home_set.setMaximum(1)
        self.progressBar_home_set.setProperty("value", 0)
        self.progressBar_home_set.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar_home_set.setTextVisible(False)
        self.gridLayout_input_color_and_set_home.addWidget(
            self.progressBar_home_set, 1, 1, 1, 1)

        self.gridLayout_1.addLayout(self.gridLayout_input_color_and_set_home,
                                    8, 2, 1, 1)

        self.verticalLayout_output_size = QtWidgets.QVBoxLayout()
        self.line_5 = QtWidgets.QFrame(self.centralwidget)
        self.line_5.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_output_size.addWidget(self.line_5)

        self.gridLayout_floating_preview = QtWidgets.QGridLayout()

        self.label_output_size = QtWidgets.QLabel(self.centralwidget)
        self.label_output_size.setAlignment(QtCore.Qt.AlignCenter)
        # self.verticalLayout_output_size.addWidget(self.label_output_size)
        self.gridLayout_floating_preview.addWidget(self.label_output_size, 0,
                                                   0)

        self.dial_output_size = QtWidgets.QDial(self.centralwidget)
        self.dial_output_size.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.dial_output_size.setMinimum(1)
        self.dial_output_size.setMaximum(801)
        self.dial_output_size.setProperty("value", 99)
        self.dial_output_size.setTracking(True)
        self.dial_output_size.setOrientation(QtCore.Qt.Horizontal)
        self.dial_output_size.valueChanged.connect(self.resize_floating_placer)
        # self.verticalLayout_output_size.addWidget(self.dial_output_size)
        self.gridLayout_floating_preview.addWidget(self.dial_output_size, 1, 0)

        self.label_output_opacity = QtWidgets.QLabel(self.centralwidget)
        # self.verticalLayout_output_size.addWidget(self.label_output_size)
        self.label_output_opacity.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_floating_preview.addWidget(self.label_output_opacity,
                                                   0, 1)

        self.dial_output_opacity = QtWidgets.QDial(self.centralwidget)
        self.dial_output_opacity.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.dial_output_opacity.setMinimum(0)
        self.dial_output_opacity.setMaximum(100)
        self.dial_output_opacity.setProperty("value",
                                             self.DEFAULT_PREVIEW_OPACITY)
        self.dial_output_opacity.setTracking(True)
        self.dial_output_opacity.valueChanged.connect(
            self.opacity_floating_placer)
        self.dial_output_opacity.setOrientation(QtCore.Qt.Horizontal)
        # self.verticalLayout_output_size.addWidget(self.dial_output_size)
        self.gridLayout_floating_preview.addWidget(self.dial_output_opacity, 1,
                                                   1)

        self.verticalLayout_output_size.addLayout(
            self.gridLayout_floating_preview)

        self.line_6 = QtWidgets.QFrame(self.centralwidget)
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_output_size.addWidget(self.line_6)

        self.gridLayout_1.addLayout(self.verticalLayout_output_size, 5, 2, 1,
                                    1)
        self.verticalLayout_output_resolution = QtWidgets.QVBoxLayout()
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_output_resolution.addWidget(self.line)

        self.label_output_resolution = QtWidgets.QLabel(self.centralwidget)
        self.verticalLayout_output_resolution.addWidget(
            self.label_output_resolution)

        self.label_output_resolution_x = QtWidgets.QLabel(self.centralwidget)
        self.verticalLayout_output_resolution.addWidget(
            self.label_output_resolution_x)

        self.spinBox_output_resolution_x = QtWidgets.QSpinBox(
            self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.spinBox_output_resolution_x.sizePolicy().hasHeightForWidth())
        self.spinBox_output_resolution_x.setSizePolicy(sizePolicy)
        self.spinBox_output_resolution_x.setMinimum(1)
        self.spinBox_output_resolution_x.setMaximum(600)
        self.spinBox_output_resolution_x.setProperty("value",
                                                     self.output_img_size[0])
        self.spinBox_output_resolution_x.valueChanged.connect(
            self.update_output_resolution)
        self.verticalLayout_output_resolution.addWidget(
            self.spinBox_output_resolution_x)

        self.label_output_resolution_y = QtWidgets.QLabel(self.centralwidget)
        self.verticalLayout_output_resolution.addWidget(
            self.label_output_resolution_y)

        self.spinBox_output_resolution_y = QtWidgets.QSpinBox(
            self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.spinBox_output_resolution_y.sizePolicy().hasHeightForWidth())
        self.spinBox_output_resolution_y.setSizePolicy(sizePolicy)
        self.spinBox_output_resolution_y.setMinimum(1)
        self.spinBox_output_resolution_y.setReadOnly(True)
        self.spinBox_output_resolution_y.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinBox_output_resolution_y.setMaximum(6000)
        self.spinBox_output_resolution_y.setProperty("value",
                                                     self.output_img_size[1])
        self.verticalLayout_output_resolution.addWidget(
            self.spinBox_output_resolution_y)

        self.line_7 = QtWidgets.QFrame(self.centralwidget)
        self.line_7.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_7.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_output_resolution.addWidget(self.line_7)
        self.gridLayout_1.addLayout(self.verticalLayout_output_resolution, 5,
                                    0, 1, 1)

    def UI_img_menu_size(self):
        self.gridLayout_menu_img_size = QtWidgets.QGridLayout()

        self.doubleSpinBox_afbeelding_menu_grootte = QtWidgets.QDoubleSpinBox(
            self.centralwidget)
        self.doubleSpinBox_afbeelding_menu_grootte.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
            | QtCore.Qt.AlignVCenter)
        self.doubleSpinBox_afbeelding_menu_grootte.setDecimals(0)
        self.doubleSpinBox_afbeelding_menu_grootte.setMinimum(1.0)
        self.doubleSpinBox_afbeelding_menu_grootte.setMaximum(501.0)
        self.doubleSpinBox_afbeelding_menu_grootte.setSingleStep(20.0)
        self.doubleSpinBox_afbeelding_menu_grootte.setProperty(
            "value", self.img_menu_size)
        self.doubleSpinBox_afbeelding_menu_grootte.valueChanged.connect(
            self.update_menu_img)
        self.gridLayout_menu_img_size.addWidget(
            self.doubleSpinBox_afbeelding_menu_grootte, 0, 0)

        self.label_afbeelding_menu_grootte = QtWidgets.QLabel(
            self.centralwidget)
        self.gridLayout_menu_img_size.addWidget(
            self.label_afbeelding_menu_grootte, 0, 1)

        self.comboBox_dither_method = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_dither_method.addItems([
            "Floyd-Steinberg", "Yliluoma", "Jarvis-Judice-Ninke", "Stucki",
            "Burkes", "Sierra3", "Sierra2", "Sierra-2-4A", "Atkinson",
            "Bayer matrix", "Cluster dot matrix"
        ])
        self.comboBox_dither_method.setCurrentText(self.DEFAULT_DITHER_METHOD)
        self.comboBox_dither_method.activated[str].connect(
            self.assign_dither_method)
        self.gridLayout_menu_img_size.addWidget(self.comboBox_dither_method, 1,
                                                0)

        self.label_dither_method = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_menu_img_size.addWidget(self.label_dither_method, 1, 1)

        self.comboBox_scale_method = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_scale_method.addItems(
            ["NEAREST", "BOX", "BILINEAR", "HAMMING", "BICUBIC", "LANCZOS"])
        self.comboBox_scale_method.setCurrentText(self.DEFAULT_SCALE_METHOD)
        self.comboBox_scale_method.activated[str].connect(
            self.assign_scale_method)
        self.gridLayout_menu_img_size.addWidget(self.comboBox_scale_method, 2,
                                                0)

        self.label_scale_method = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_menu_img_size.addWidget(self.label_scale_method, 2, 1)

    def UI_pixmap_input_image(self):
        self.label_pixmap_input_image = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_pixmap_input_image.sizePolicy().hasHeightForWidth())
        self.label_pixmap_input_image.setSizePolicy(sizePolicy)
        self.label_pixmap_input_image.setAlignment(QtCore.Qt.AlignCenter)
        self.label_pixmap_input_image.setFrameShape(QtWidgets.QFrame.Panel)
        self.label_pixmap_input_image.setPixmap(self.input_img.qpix_scaled)

    def UI_pixmap_output_image(self):
        self.label_pixmap_output_image = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_pixmap_output_image.sizePolicy().hasHeightForWidth())
        self.label_pixmap_output_image.setSizePolicy(sizePolicy)
        self.label_pixmap_output_image.setAlignment(QtCore.Qt.AlignCenter)
        self.label_pixmap_output_image.setFrameShape(QtWidgets.QFrame.Box)
        self.label_pixmap_output_image.setPixmap(self.output_img.qpix_scaled)

    def update_menu_img(self):
        self.img_menu_size = self.doubleSpinBox_afbeelding_menu_grootte.value()

        self.input_img.update_size(self.img_menu_size)
        self.label_pixmap_input_image.setPixmap(self.input_img.qpix_scaled)

        self.output_img.update_size(self.img_menu_size)
        self.label_pixmap_output_image.setPixmap(self.output_img.qpix_scaled)

        # resize app venster
        # self.img_dwr.resize(*self.DEFAULT_WINDOW_SIZE)

    def UI_vertical_layout_drawing_speed(self):
        self.verticalLayout_drawing_speed = QtWidgets.QVBoxLayout()
        self.line_drawing_speed_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_drawing_speed_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_drawing_speed_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_drawing_speed.addWidget(self.line_drawing_speed_3)

        self.label_drawing_speed_0 = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_drawing_speed_0.sizePolicy().hasHeightForWidth())
        self.label_drawing_speed_0.setSizePolicy(sizePolicy)
        self.verticalLayout_drawing_speed.addWidget(self.label_drawing_speed_0)

        self.horizontalSlider_drawing_speed = QtWidgets.QSlider(
            self.centralwidget)
        self.horizontalSlider_drawing_speed.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.horizontalSlider_drawing_speed.setMinimum(0)
        self.horizontalSlider_drawing_speed.setMaximum(
            len(self.AVAILABLE_DRAWING_SPEEDS) - 1)
        self.horizontalSlider_drawing_speed.setValue(
            self.DEFAULT_DRAWING_SPEED_IDX)
        self.horizontalSlider_drawing_speed.setPageStep(1)
        self.horizontalSlider_drawing_speed.setOrientation(
            QtCore.Qt.Horizontal)
        self.horizontalSlider_drawing_speed.setInvertedAppearance(False)
        self.horizontalSlider_drawing_speed.setInvertedControls(False)
        self.horizontalSlider_drawing_speed.setTickPosition(
            QtWidgets.QSlider.TicksBelow)
        self.horizontalSlider_drawing_speed.setTickInterval(1)
        self.horizontalSlider_drawing_speed.valueChanged.connect(
            self.update_drawing_speed)
        self.verticalLayout_drawing_speed.addWidget(
            self.horizontalSlider_drawing_speed)

        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.label_drawing_speed_1 = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_drawing_speed_1.sizePolicy().hasHeightForWidth())
        self.label_drawing_speed_1.setSizePolicy(sizePolicy)
        self.label_drawing_speed_1.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.label_drawing_speed_1.setTextFormat(QtCore.Qt.AutoText)
        self.label_drawing_speed_1.setAlignment(QtCore.Qt.AlignLeading
                                                | QtCore.Qt.AlignLeft
                                                | QtCore.Qt.AlignVCenter)
        self.label_drawing_speed_1.setTextInteractionFlags(
            QtCore.Qt.NoTextInteraction)
        self.horizontalLayout_4.addWidget(self.label_drawing_speed_1)

        spacerItem = QtWidgets.QSpacerItem(33, 20,
                                           QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.line_drawing_speed_1 = QtWidgets.QFrame(self.centralwidget)
        self.line_drawing_speed_1.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_drawing_speed_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.horizontalLayout_4.addWidget(self.line_drawing_speed_1)

        spacerItem1 = QtWidgets.QSpacerItem(40, 20,
                                            QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.label_drawing_speed_2 = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_drawing_speed_2.sizePolicy().hasHeightForWidth())
        self.label_drawing_speed_2.setSizePolicy(sizePolicy)
        self.label_drawing_speed_2.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_4.addWidget(self.label_drawing_speed_2)

        spacerItem2 = QtWidgets.QSpacerItem(55, 20,
                                            QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.line_drawing_speed_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_drawing_speed_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_drawing_speed_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.horizontalLayout_4.addWidget(self.line_drawing_speed_2)

        spacerItem3 = QtWidgets.QSpacerItem(40, 20,
                                            QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.label_drawing_speed_3 = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.label_drawing_speed_3.sizePolicy().hasHeightForWidth())
        self.label_drawing_speed_3.setSizePolicy(sizePolicy)
        self.label_drawing_speed_3.setAlignment(QtCore.Qt.AlignRight
                                                | QtCore.Qt.AlignTrailing
                                                | QtCore.Qt.AlignVCenter)
        self.horizontalLayout_4.addWidget(self.label_drawing_speed_3)

        self.verticalLayout_drawing_speed.addLayout(self.horizontalLayout_4)

    def UI_vertical_layout_waiting_speed(self):
        self.verticalLayout_waiting_speed = QtWidgets.QVBoxLayout()
        self.line_12 = QtWidgets.QFrame(self.centralwidget)
        self.line_12.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_12.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.verticalLayout_waiting_speed.addWidget(self.line_12)

        self.label_waiting_speed_0 = QtWidgets.QLabel(self.centralwidget)
        self.verticalLayout_waiting_speed.addWidget(self.label_waiting_speed_0)

        self.horizontalSlider_waiting_speed = QtWidgets.QSlider(
            self.centralwidget)
        self.horizontalSlider_waiting_speed.setMinimum(0)
        self.horizontalSlider_waiting_speed.setMaximum(
            len(self.AVAILABLE_WAITING_SPEEDS) - 1)
        self.horizontalSlider_waiting_speed.setValue(
            self.DEFAULT_WAITING_SPEED_IDX)
        self.horizontalSlider_waiting_speed.setPageStep(1)
        self.horizontalSlider_waiting_speed.setOrientation(
            QtCore.Qt.Horizontal)
        self.horizontalSlider_waiting_speed.setTickPosition(
            QtWidgets.QSlider.TicksBelow)
        self.horizontalSlider_waiting_speed.setTickInterval(1)
        self.horizontalSlider_waiting_speed.valueChanged.connect(
            self.update_waiting_speed)
        self.verticalLayout_waiting_speed.addWidget(
            self.horizontalSlider_waiting_speed)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.label_waiting_speed_1 = QtWidgets.QLabel(self.centralwidget)
        self.horizontalLayout.addWidget(self.label_waiting_speed_1)

        # spacerItem4 = QtWidgets.QSpacerItem(40, 20,
        #                                     QtWidgets.QSizePolicy.Expanding,
        #                                     QtWidgets.QSizePolicy.Minimum)
        # self.horizontalLayout.addItem(spacerItem4)
        # self.line_11 = QtWidgets.QFrame(self.centralwidget)
        # self.line_11.setFrameShape(QtWidgets.QFrame.VLine)
        # self.line_11.setFrameShadow(QtWidgets.QFrame.Sunken)
        # self.horizontalLayout.addWidget(self.line_11)

        spacerItem5 = QtWidgets.QSpacerItem(40, 20,
                                            QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem5)
        self.label_waiting_speed_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_waiting_speed_2.setAlignment(QtCore.Qt.AlignRight
                                                | QtCore.Qt.AlignTrailing
                                                | QtCore.Qt.AlignVCenter)
        self.horizontalLayout.addWidget(self.label_waiting_speed_2)

        self.verticalLayout_waiting_speed.addLayout(self.horizontalLayout)

    def UI_colorboxes(self):
        self.horizontalLayout_colorboxes = QtWidgets.QHBoxLayout(
            self.centralwidget)

    def add_colorbox(self, rgb_color):
        b = QPaletteButton(rgb_color)
        b.clicked.connect(self.destroy_preview_palette_box)
        self.palette_preview_button_list.append(b)
        # self.drawn_palette_colors.append(hex_color)
        self.horizontalLayout_colorboxes.addWidget(b)

    def destroy_preview_palette_box(self):
        button = self.sender()
        # remove the color from the palette
        del self.color_pallette[button.rgb_color]
        button.deleteLater()
        self.palette_preview_button_list.remove(button)
        self.spinBox_input_colors.setValue(len(self.color_pallette.keys()))
        # for button in self.palette_preview_button_list:
        #     # if the button is pressed
        #     if button.down():
        #         # remove the color from the palette
        #         del self.color_pallette[button.rgb_color]
        #         button.deleteLater()
        #         self.palette_preview_button_list.remove(button)

    def UI_menubar(self):
        self.menubar = QtWidgets.QMenuBar(Image_drawer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 549, 21))
        self.menuFiles = QtWidgets.QMenu(self.menubar)

        self.actionLoad_input = QtWidgets.QAction(Image_drawer)
        self.actionLoad_input.setCheckable(False)
        self.actionLoad_input.setShortcutContext(QtCore.Qt.WindowShortcut)
        self.actionLoad_input.triggered.connect(self.open_file_dialog)
        self.menuFiles.addAction(self.actionLoad_input)

        self.actionSave_output = QtWidgets.QAction(Image_drawer)
        self.actionSave_output.setShortcutVisibleInContextMenu(False)
        self.actionSave_output.triggered.connect(self.save_file_dialog)
        self.menuFiles.addAction(self.actionSave_output)

        self.menubar.addAction(self.menuFiles.menuAction())

    def retranslateUi(self, Image_drawer):
        _translate = QtCore.QCoreApplication.translate
        Image_drawer.setWindowTitle(_translate("Image_drawer",
                                               "image-plotter"))
        self.pushButton_generate_output.setText(
            _translate("Image_drawer", "Generate output"))
        self.checkBox_display_image_placing.setText(
            _translate("Image_drawer", "Display image placing preview"))
        # self.label_pixmap_output_image.setText(
        #     _translate("Image_drawer", "Output image"))
        self.label_input_image.setText(_translate("Image_drawer", "Input"))
        self.label_output_image.setText(
            _translate("Image_drawer", "Output (approx)"))
        self.label_afbeelding_menu_grootte.setText(
            _translate("Image_drawer", "Menu image size (px)"))
        self.label_dither_method.setText(
            _translate("Image_drawer", "Color quantization method"))
        self.label_scale_method.setText(
            _translate("Image_drawer", "Image scaling method"))
        # self.label_pixmap_input_image.setText(
        #     _translate("Image_drawer", "Input image"))
        self.pushButton_start_drawing.setText(
            _translate("Image_drawer", "Start drawing"))
        self.checkBox_input_colors.setText(
            _translate("Image_drawer", "Input colors"))
        self.checkBox_set_home.setText(_translate("Image_drawer", "Set home"))
        self.progressBar_home_set.setFormat(_translate("Image_drawer", "%p%"))
        self.label_output_size.setText(
            _translate("Image_drawer", "Preview size"))
        self.label_output_opacity.setText(
            _translate("Image_drawer", "Preview opacity"))
        self.label_output_resolution.setText(
            _translate("Image_drawer", "Output resolution"))
        self.label_output_resolution_x.setText(
            _translate("Image_drawer", "x (px)"))
        self.label_output_resolution_y.setText(
            _translate("Image_drawer", "y (px)"))
        self.label_drawing_speed_0.setText(
            _translate("Image_drawer", "Drawing speed"))
        self.label_drawing_speed_1.setText(
            _translate("Image_drawer", "Slow and steady"))
        self.label_drawing_speed_2.setText(
            _translate("Image_drawer", "I trust my computer"))
        self.label_drawing_speed_3.setText(_translate("Image_drawer", "Zoom"))
        self.label_waiting_speed_0.setText(
            _translate("Image_drawer", "Waiting speed"))
        self.label_waiting_speed_1.setText(_translate("Image_drawer", "Short"))
        self.label_waiting_speed_2.setText(_translate("Image_drawer", " Long"))
        # self.label_progress.setText(_translate("Image_drawer", "Progress"))
        self.label_color_pallete.setText(
            _translate("Image_drawer", "Color pallete preview:"))
        self.menuFiles.setTitle(_translate("Image_drawer", "Files"))
        self.actionSave_output.setText(
            _translate("Image_drawer", "Save output file"))
        self.actionLoad_input.setText(
            _translate("Image_drawer", "Load input file"))

    def init_thread(self):
        self.pallete_thread = ColorWorker()
        self.pallete_thread.color_signal.connect(self.add_color_to_pallete)

        self.floyd_thread = FloydWorker()
        self.floyd_thread.output_name_signal.connect(self.process_floyd)

        self.drawing_thread = DrawingWorker()
        self.drawing_thread.progress_signal.connect(
            self.update_progressBar_main)

        self.home_thread = HomeWorker()
        self.home_thread.home_signal.connect(self.update_home_pos)

    def update_output_resolution(self):
        value = int(self.spinBox_output_resolution_x.value())
        self.output_img_size = (value,
                                int(self.output_img_size[1] /
                                    self.output_img_size[0] * value))
        self.spinBox_output_resolution_y.setProperty("value",
                                                     self.output_img_size[1])

    def update_progressBar_main(self, percentage: int):
        self.progressBar_main.setProperty("value", int(percentage))

    def update_home_pos(self, pos):
        self.progressBar_home_set.setProperty("value", 1)
        self.home = pos

    def update_drawing_speed(self):
        self.drawing_speed = self.AVAILABLE_DRAWING_SPEEDS[
            self.horizontalSlider_drawing_speed.value()]

    def update_waiting_speed(self):
        self.waiting_speed = self.AVAILABLE_WAITING_SPEEDS[
            self.horizontalSlider_waiting_speed.value()]

    def show_hide_floating_placer(self):
        if self.checkBox_display_image_placing.isChecked():
            self.floating_image_preview_window.show()
        else:
            self.floating_image_preview_window.hide()

    def resize_floating_placer(self):
        self.floating_image_preview_window.resize_window(
            int(self.dial_output_size.value()))

    def opacity_floating_placer(self):
        self.floating_image_preview_window.change_opacity(
            int(self.dial_output_opacity.value()))

    def open_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        # there is an option to not use the native dialog
        # options |= QFileDialog.DontUseNativeDialog
        self.input_fileName, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            f"Image Files ({' '.join(['*.'+x for x in self.ACCEPTED_FILETYPES])});;All Files (*);;{';;'.join([f'{x} (*.{x})' for x in self.ACCEPTED_FILETYPES])}",
            options=options)

        try:
            if self.input_fileName[-3:] == "svg":
                print("Ik heb geen implementatie voor svg. ")
                QtWidgets.QMessageBox.about(
                    self, "Helaas",
                    "Ik heb nog geen implementatie voor svg bestanden")
                return
        except AttributeError as error:
            tmp = str(error)
            print("het ging fout")
            QtWidgets.QMessageBox.about(
                self, tmp, "Je afbeelding is waarschijnlijk niet mooi genoeg")

        # if no file was selected return
        if not self.input_fileName:
            return

        # change input image to selected image
        self.input_img = img_file(self.input_fileName, self.img_menu_size)
        self.update_menu_img()

    def save_file_dialog(self):
        print("to be implemented")
        options = QtWidgets.QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "QFileDialog.getSaveFileName()",
            "",
            "All Files (*);;Text Files (*.txt)",
            options=options)
        if fileName:
            print(fileName)

    def assign_dither_method(self):
        self.dither_method = self.comboBox_dither_method.currentText()

    def assign_scale_method(self):
        self.scale_method = self.comboBox_scale_method.currentText()

    def load_pallete(self):
        if self.checkBox_input_colors.isChecked():
            # Start Button action:
            self.pallete_thread.start()
        else:
            self.pallete_thread.keep_looking = False
            # self.update_colorboxes()

    def define_home(self):
        if self.checkBox_set_home.isChecked():
            # Start Button action:
            self.home_thread.start()
        else:
            self.home_thread.keep_looking = False

    def add_color_to_pallete(self, data: tuple):
        color, position = data
        if color not in self.color_pallette:
            self.add_colorbox(color)
            # self.spinBox_input_colors.setValue(
            #     self.spinBox_input_colors.value() + 1)
            # self.spinBox_input_colors.setValue(len(self.color_pallette.keys())+1)
        self.color_pallette[color] = position
        self.spinBox_input_colors.setValue(len(self.color_pallette.keys()))
        print("toegevoegd:", data)
        # print(self.color_pallette)

    def empty_palette_error(self):
        # error_dialog = QtWidgets.QErrorMessage(self)
        error_dialog = QtWidgets.QMessageBox(self)
        error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.setText("Error")
        error_dialog.setInformativeText(
            'There are no colors in the colorpalette')
        error_dialog.setWindowTitle("Error")
        error_dialog.exec_()
        # error_dialog.showMessage('There are no colors in the color palette')
        # QtWidgets.QMessageBox.about(
        #     self, "whoops", "There are no colors in the color palette")

    def floyd(self):
        if len(self.color_pallette) == 0:
            self.empty_palette_error()
            return

        self.checkBox_input_colors.setChecked(QtCore.Qt.Unchecked)
        self.load_pallete()

        # print(self.color_pallette)
        self.floyd_thread.color_pallette_dict = self.color_pallette
        self.floyd_thread.resize_method = self.scale_method
        self.floyd_thread.dither_method = self.dither_method
        # self.floyd_thread.qpix_input_image = self.self.input_img
        self.floyd_thread.image_name = self.input_img.filename
        self.floyd_thread.size = self.output_img_size
        self.floyd_thread.start()

    def process_floyd(self, outfile_name: str):
        del self.output_img
        self.output_img = img_file(outfile_name, self.img_menu_size)
        self.update_menu_img()

        self.floating_image_preview_window.m_original_input_image.qpix = self.output_img.qpix
        self.floating_image_preview_window.m_original_input_image.generate_scaled(
        )
        self.floating_image_preview_window.update_image()

    def draw_output(self):
        geom_window = self.floating_image_preview_window.geometry()
        win_x, win_y = geom_window.left(), geom_window.top()
        geom_img = self.floating_image_preview_window.m_label.geometry()
        img_x, img_y, img_x2, img_y2 = geom_img.left(), geom_img.top(
        ), geom_img.right(), geom_img.bottom()
        drawing_domain = (win_x + img_x, win_y + img_y, win_x + img_x2,
                          win_y + img_y2)

        # print(f"drawing domain {drawing_domain}")
        # print("hier moet nog een resize method worden toegevoegd")
        self.checkBox_display_image_placing.setChecked(QtCore.Qt.Unchecked)
        self.show_hide_floating_placer()

        self.drawing_thread.start_drawing(drawing_domain, self.color_pallette,
                                          self.output_img, self.home,
                                          self.drawing_speed,
                                          self.waiting_speed)

    def onClose(self, event):
        '''called when the main window is closed
        '''
        self.floating_image_preview_window.close()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Image_drawer = QtWidgets.QMainWindow()
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("./sources/eend.png"), QtGui.QIcon.Selected,
                   QtGui.QIcon.On)
    # self.setWindowIcon(icon)
    Image_drawer.setWindowIcon(icon)

    ui = Ui_Image_drawer()

    Image_drawer.closeEvent = ui.onClose

    ui.UI_setup(Image_drawer)

    Image_drawer.show()
    sys.exit(app.exec_())
