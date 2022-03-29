import os
import random
import sys
import time
import json

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

# rgb(200, 255, 255)
StyleSheet = """
QProgressBar {
                background-color: grey;
                color: black;
                border-style: solid;
                border-radius: 19px;
                text-align: center;
}

QProgressBar::chunk {
    background-color: rgb(200, 255, 255);
}
"""

StyleSheet_User_Pref = """
QLabel {
    font-family: Shanti;
    font-size: 12px;
    color: #FFF;                               
}

QLineEdit {
    border: 2px solid rgb(37, 39, 48);
    border-radius: 10px;
    color: #FFF;
    padding-left: 3px;
    background-color: rgb(34, 36, 44);
}

QComboBox{
        border: 2px solid rgb(37, 39, 48);
        font-size: 12px;
        color: #FFF;
        cursor: pointer;
}

QComboBox:hover{
        background: '#BC006C';
}

QListView{
        display: none;
        position: absolute;
        background: '#BC006C';
        color: #FFF;
        min-width: 10px;
        box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
}

QPushButton {
        border: 2px solid rgb(37, 39, 48);
        border-radius: 10px;
        font-size: 12px;
        color: #FFF;
}

QPushButton:hover{
        background: '#BC006C';
}       
     
QTextEdit{
        border: 2px solid rgb(37, 39, 48);
        border-radius: 10px;
        color: #FFF;
        font-family: Shanti;
        font-size: 11px;
        padding-left: 3px;
        background-color: rgb(34, 36, 44);
}            
"""

# save files and read files will go here
# function to open a new window to showcase previous games (read from)
# function to save and write new lines of games with score and game time, plus system time (write)
# can either be saved at C drive or project files, project files for now

# DIRECTORY_PATH_OF_SCORES = 'C:\GroupFiveScores'
# FILE_PATH_OF_SCORES = os.path.join(DIRECTORY_PATH_OF_SCORES, "Scores.txt")

def json_exists(nameOfFile):
    return os.path.exists(nameOfFile)

if json_exists('Scores.json'):
    print("Scores.json exists")
    pass
else:
    print("Scores.txt does not exist")
    data = {
        "scores:": [{
            'user': "root user",
            'Time Of Completion': "00:00",
            'Moves Taken': 0,
            'Score': 1000,
            'Played At': str(QDateTime.currentDateTime().toString(Qt.DefaultLocaleShortDate))
        }]
    }

    try:

        with open('Scores.json', 'w') as initialWrite:
            json.dump(data, initialWrite, indent=4)
        print("Created initial file with initial data")
    except Exception as e:
        QMessageBox.information(self, "Exception occured! Exception is:", str(e))
        # print("Exception occured! Exception is:", str(e))

WINDOW_SIZE = 900, 700
nnnn = 0 # background colour int for signals, 0 is green default colour
felt = QBrush(QColor(15, 99, 66))
USER_NAME = "root user"
VERSION_NUMBER = 1.0
VERSION_NUMBER_STR = "Version " + str(VERSION_NUMBER)
CARD_DIMENSIONS = QSize(63, 96)
CARD_RECT = QRect(0, 0, 63, 96)
CARD_SPACING_X = 110
CARD_BACK = QImage(os.path.join('Images', 'back-of-deck.png'))

DEAL_RECT = QRect(30, 30, 110, 140)

OFFSET_X = 50
OFFSET_Y = 50
WORK_STACK_Y = 200

SIDE_FACE = 0
SIDE_BACK = 1

BOUNCE_ENERGY = 0.8

# We store cards as numbers 1-13, since we only need
# to know their order for solitaire.
SUITS = ["C", "S", "H", "D"]
# Keep track of moves and foundation scores and moves scores
MOVES = 0
FOUNDATION_SCORE = 0
TOTAL_SCORE = 0
MOVE_SCORE = 0
WON_CONDITION = False

class Signals(QObject):
    complete = pyqtSignal()
    clicked = pyqtSignal()
    doubleclicked = pyqtSignal()


class HelperMonka(QObject):
     updated_score = pyqtSignal(int)
     updated_moves = pyqtSignal(int)


class Card(QGraphicsPixmapItem):

    def __init__(self, value, suit, *args, **kwargs):
        super(Card, self).__init__(*args, **kwargs)

        self.signals = Signals()
        self.helpers = HelperMonka()

        self.stack = None  # Stack this card currently is in.
        self.child = None  # Card stacked on this one (for work deck).

        # Store the value & suit of the cards internal to it.
        self.value = value
        self.suit = suit
        self.side = None

        # For end animation only.
        self.vector = None

        # Cards have no internal transparent areas, so we can use this faster method.
        self.setShapeMode(QGraphicsPixmapItem.BoundingRectShape)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.load_images()

    def load_images(self):
        self.face = QPixmap(
            os.path.join('Images/cards', '%s%s.png' % (self.value, self.suit))
        )

        self.back = QPixmap(
            os.path.join('Images', 'back-of-deck.png')
        )

    def turn_face_up(self):
        self.side = SIDE_FACE
        self.setPixmap(self.face)

    def turn_back_up(self):
        self.side = SIDE_BACK
        self.setPixmap(self.back)

    @property
    def is_face_up(self):
        return self.side == SIDE_FACE

    @property
    def color(self):
        return 'r' if self.suit in ('H', 'D') else 'b'

    def mousePressEvent(self, e):
        if not self.is_face_up and self.stack.cards[-1] == self:
            self.turn_face_up()  # We can do this without checking.
            e.accept()
            return

        if self.stack and not self.stack.is_free_card(self):
            e.ignore()
            return

        self.stack.activate()

        e.accept()

        super(Card, self).mouseReleaseEvent(e)

    def mouseReleaseEvent(self, e):
        self.stack.deactivate()

        items = self.collidingItems()
        if items:
            # Find the topmost item from a different stack:
            for item in items:
                if ((isinstance(item, Card) and item.stack != self.stack) or
                        (isinstance(item, StackBase) and item != self.stack)):

                    if item.stack.is_valid_drop(self):
                        # Remove card + all children from previous stack, add to the new.
                        # Note: the only place there will be children is on a workstack.
                        cards = self.stack.remove_card(self)
                        item.stack.add_cards(cards)
                        self.move_registered()
                        break
        # Refresh this card's stack, pulling it back if it was dropped.
        self.stack.update()

        super(Card, self).mouseReleaseEvent(e)

    def move_registered(self):
        global MOVES, MOVE_SCORE, TOTAL_SCORE, FOUNDATION_SCORE
        MOVES += 1
        MOVE_SCORE += 3
        TOTAL_SCORE = FOUNDATION_SCORE + MOVE_SCORE
        self.helpers.updated_score.emit(TOTAL_SCORE)
        self.helpers.updated_moves.emit(MOVES)


    def mouseDoubleClickEvent(self, e):
        if self.stack.is_free_card(self):
            self.signals.doubleclicked.emit()
            # self.move_registered()
            e.accept()

        super(Card, self).mouseDoubleClickEvent(e)


class StackBase(QGraphicsRectItem):

    def __init__(self, *args, **kwargs):
        super(StackBase, self).__init__(*args, **kwargs)

        self.setRect(QRectF(CARD_RECT))
        self.setZValue(-1)

        # Cards on this deck, in order.
        self.cards = []

        # Store a self ref, so the collision logic can handle cards and
        # stacks with the same approach.
        self.stack = self
        self.setup()
        self.reset()

    def setup(self):
        pass

    def reset(self):
        self.remove_all_cards()

    def update(self):
        for n, card in enumerate(self.cards):
            card.setPos(self.pos() + QPointF(n * self.offset_x, n * self.offset_y))
            card.setZValue(n)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def add_card(self, card, update=True):
        card.stack = self
        self.cards.append(card)
        if update:
            self.update()

    def add_cards(self, cards):
        for card in cards:
            self.add_card(card, update=False)
        self.update()

    def remove_card(self, card):
        card.stack = None
        self.cards.remove(card)
        self.update()

        return [card]  # Returns a list, as WorkStack must return children

    def remove_all_cards(self):
        for card in self.cards[:]:
            card.stack = None
        self.cards = []

    def is_valid_drop(self, card):

        return True

    def is_free_card(self, card):

        return False


class DeckStack(StackBase):
    offset_x = -0.2
    offset_y = -0.3

    restack_counter = 0

    def reset(self):
        super(DeckStack, self).reset()
        self.restack_counter = 0
        self.set_color(Qt.green)

    def stack_cards(self, cards):
        for card in cards:
            self.add_card(card)
            card.turn_back_up()

    def can_restack(self, n_rounds=3):
        return n_rounds is None or self.restack_counter < n_rounds - 1

    def update_stack_status(self, n_rounds):
        if not self.can_restack(n_rounds):
            self.set_color(Qt.red)
        else:
            # We only need this if players change the round number during a game.
            self.set_color(Qt.green)

    def restack(self, fromstack):
        self.restack_counter += 1

        # We need to slice as we're adding to the list, reverse to stack back
        # in the original order.
        for card in fromstack.cards[::-1]:
            fromstack.remove_card(card)
            self.add_card(card)
            card.turn_back_up()

    def take_top_card(self):
        try:
            card = self.cards[-1]
            self.remove_card(card)
            return card
        except IndexError:
            pass

    def set_color(self, color):
        color = QColor(color)
        color.setAlpha(50)
        brush = QBrush(color)
        self.setBrush(brush)
        self.setPen(QPen(Qt.NoPen))

    def is_valid_drop(self, card):
        return False


class DealStack(StackBase):
    offset_x = 20
    offset_y = 0

    spread_from = 0

    def setup(self):
        self.setPen(QPen(Qt.NoPen))
        color = QColor(Qt.black)
        color.setAlpha(50)
        brush = QBrush(color)
        self.setBrush(brush)

    def reset(self):
        super(DealStack, self).reset()
        self.spread_from = 0  # Card index to start spreading cards out.

    def is_valid_drop(self, card):
        return False

    def is_free_card(self, card):
        return card == self.cards[-1]

    def update(self):
        # Only spread the top 3 cards
        offset_x = 0
        for n, card in enumerate(self.cards):
            card.setPos(self.pos() + QPointF(offset_x, 0))
            card.setZValue(n)

            if n >= self.spread_from:
                offset_x = offset_x + self.offset_x


class WorkStack(StackBase):
    offset_x = 0
    offset_y = 15
    offset_y_back = 5

    def setup(self):
        self.setPen(QPen(Qt.NoPen))
        color = QColor(Qt.black)
        color.setAlpha(50)
        brush = QBrush(color)
        self.setBrush(brush)

    def activate(self):
        # Raise z-value of this stack so children float above all other cards.
        self.setZValue(1000)

    def deactivate(self):
        self.setZValue(-1)

    def is_valid_drop(self, card):
        if not self.cards:
            return True

        if (card.color != self.cards[-1].color and
                card.value == self.cards[-1].value - 1):
            return True

        return False

    def is_free_card(self, card):
        return card.is_face_up  # self.cards and card == self.cards[-1]

    def add_card(self, card, update=True):
        if self.cards:
            card.setParentItem(self.cards[-1])
        else:
            card.setParentItem(self)

        super(WorkStack, self).add_card(card, update=update)

    def remove_card(self, card):
        index = self.cards.index(card)
        self.cards, cards = self.cards[:index], self.cards[index:]

        for card in cards:
            # Remove card and all children, returning a list of cards removed in order.
            card.setParentItem(None)
            card.stack = None

        self.update()
        return cards

    def remove_all_cards(self):
        for card in self.cards[:]:
            card.setParentItem(None)
            card.stack = None
        self.cards = []

    def update(self):
        self.stack.setZValue(-1)  # Reset this stack the the background.
        # Only spread the top 3 cards
        offset_y = 0
        for n, card in enumerate(self.cards):
            card.setPos(QPointF(0, offset_y))

            if card.is_face_up:
                offset_y = self.offset_y
            else:
                offset_y = self.offset_y_back


# foundations
class DropStack(StackBase):
    offset_x = -0.2
    offset_y = -0.3
    suit = None
    value = 0

    def setup(self):
        self.signals = Signals()
        self.helpers = HelperMonka()
        color = QColor(Qt.blue)
        color.setAlpha(50)
        pen = QPen(color)
        pen.setWidth(5)
        self.setPen(pen)

    def reset(self):
        super(DropStack, self).reset()
        self.suit = None
        self.value = 0

    def is_valid_drop(self, card):
        if ((self.suit is None or card.suit == self.suit) and
                (card.value == self.value + 1)):
            self.register_score()
            return True

        return False

    def register_score(self):
        global FOUNDATION_SCORE, TOTAL_SCORE, MOVE_SCORE
        FOUNDATION_SCORE += 5
        TOTAL_SCORE = FOUNDATION_SCORE + MOVE_SCORE
        self.helpers.updated_score.emit(TOTAL_SCORE)


    def add_card(self, card, update=True):
        super(DropStack, self).add_card(card, update=update)
        self.suit = card.suit
        self.value = self.cards[-1].value

        if self.is_complete:
            self.signals.complete.emit()

    def remove_card(self, card):
        super(DropStack, self).remove_card(card)
        self.value = self.cards[-1].value if self.cards else 0

    @property
    def is_complete(self):
        return self.value == 13


class DealTrigger(QGraphicsRectItem):

    def __init__(self, *args, **kwargs):
        super(DealTrigger, self).__init__(*args, **kwargs)
        self.setRect(QRectF(DEAL_RECT))
        self.setZValue(1000)

        pen = QPen(Qt.NoPen)
        self.setPen(pen)

        self.signals = Signals()

    def mousePressEvent(self, e):
        self.signals.clicked.emit()


# stops user from moving cards as they fly around on win condition :p
class AnimationCover(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        super(AnimationCover, self).__init__(*args, **kwargs)
        self.setRect(QRectF(0, 0, *WINDOW_SIZE))
        self.setZValue(5000)
        pen = QPen(Qt.NoPen)
        self.setPen(pen)

    def mousePressEvent(self, e):
        e.accept()


# show rules
class HelpWindow(QDialog):
    def __init__(self, parent=None):  # parent=None
        super(HelpWindow, self).__init__()
        self.setWindowTitle("Rules")
        self.setWindowIcon(QIcon('Images/info.ico'))
        self.pixmap = QPixmap('Images/helpme.png')
        width = 800
        height = 167
        self.resize(width, height)
        self.center()
        # self.setGeometry(100, 100, width, height)
        self.label = QLabel(self)
        self.label.setPixmap(self.pixmap)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


# splashscreen
class SplashScreen(QSplashScreen):

    def __init__(self):
        super(SplashScreen, self).__init__()
        self.pxmap = QPixmap('Images/splash.png')
        self.setPixmap(self.pxmap)
        self.resize(500, 300)
        self.versionlabel = QLabel(VERSION_NUMBER_STR)
        self.versionlabel.setFont(QFont("Fantasy", 12))

        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(0, 289, 500, 11)
        self.progressBar.setStyleSheet(StyleSheet)
        # self.thread = QThread()
        # self.worker = WorkerThread()
        # self.worker.moveToThread(self.thread)
        # self.thread.started.connect(self.worker.run)
        # # self.thread.finished.connect(self.finished_worker)
        # self.worker.prog_signal.connect(self.value_of_progress_bar)
        # self.thread.start()

        self.center()
        self.oldPos = self.pos()
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.show()

    # def finished_worker(self):
    #     print("finished")
    #     user = User()
    #     user.show()
    #     self.close()

    # def value_of_progress_bar(self, i):
    #     print(i)
    #     self.progressBar.setValue(i)
    #     if i == 100:
    #         self.thread.quit()

    def progress(self):
        for i in range(100):
            time.sleep(0.02)
            self.progressBar.setValue(i)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()


    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


# Thread for Splashscreen, stops hanging the GUI
class WorkerThread(QObject):
    pass
    # prog_signal = pyqtSignal(int)
    # def run(self):
    #     for i in range(101):
    #         time.sleep(0.02)
    #         self.prog_signal.emit(i)


# user preferences and what not
class UserPreference(QDialog):
    change_colour_signal = pyqtSignal(int)

    def __init__(self):
        super(UserPreference, self).__init__()
        self.setWindowIcon(QIcon("Images/frameiconico.ico"))
        self.setWindowTitle("Preferences")
        self.setFixedSize(300, 300)
        self.setStyleSheet("background: #161219;")

        # show colour options

        combolist = ["Green", "Rose Pink", "Eggplant", "Tan"]
        self.background_combo_box = QComboBox(self)
        self.background_combo_box.setStyleSheet(StyleSheet_User_Pref)
        self.background_combo_box.addItems(combolist)
        self.background_combo_box.setGeometry(100, 30, 95, 40)
        self.background_combo_box.currentIndexChanged.connect(self.selectionchange)

        self.choose_label = QLabel("Background Color", self)
        self.choose_label.setStyleSheet(StyleSheet_User_Pref)
        self.choose_label.move(100, 10)

        self.save_preferences_button = QPushButton(self)
        self.save_preferences_button.setText("Save")
        self.save_preferences_button.setStyleSheet(StyleSheet_User_Pref)
        self.save_preferences_button.move(263, 276)
        self.save_preferences_button.clicked.connect(self.closewindow)


        self.current_combo_index(nnnn)
        self.center()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def open_highscore(self):
        pass # open window that reads the scores file

    def current_combo_index(self, i):
        self.background_combo_box.setCurrentIndex(i)

    def selectionchange(self, i):
        global nnnn
        nnnn = i
        n = i
        self.current_combo_index(n)
        self.change_colour_signal.emit(i)  # 0 green, 1 red, 2 eggplant, 3 tan

    def closewindow(self):
        self.close()


# class for highscores viewing
class UserHighscores(QDialog):

    def __init__(self):
        super(UserHighscores, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(550, 400)
        self.setStyleSheet("background: #161219;")

        self.scoreboard_text_label = QLabel("Group Five Solitaire ScoreBoard", self)
        self.scoreboard_text_label.move(200, 8)
        self.scoreboard_text_label.setStyleSheet(StyleSheet_User_Pref)


        self.highscore_text = QTextEdit(self)
        self.highscore_text.move(10,25)
        self.highscore_text.resize(530,340)
        self.highscore_text.setDisabled(True)
        self.setStyleSheet(StyleSheet_User_Pref)

        self.close_button = QPushButton(self)
        self.close_button.setStyleSheet(StyleSheet_User_Pref)
        self.close_button.setText("Close")
        self.close_button.clicked.connect(self.close_window)
        self.close_button.move(510, 375)


        self.get_score_from_json()
        self.center()
        self.oldPos = self.pos()
        self.show()

    def get_score_from_json(self):
        data_from_json = []
        with open("Scores.json", 'r') as readfile:
            users_highscores = json.load(readfile)
            # print(users_highscores)
        for row in users_highscores["scores:"]:
            userText = row['user']
            timeText = row['Time Of Completion']
            moveText = row['Moves Taken']
            scoreText = row['Score']
            playText = row['Played At']
            self.highscore_text.append(f"Player: {userText}, Time Took: {str(timeText)}, Moves Taken: {str(moveText)}, Score: {str(scoreText)}, Played At: {str(playText)}\n")


    def close_window(self):
        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # mouse press events to move the interface around without the frame of interface
    # visibile
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


class User(QDialog):

    def __init__(self):
        super(User, self).__init__()
        # self.setWindowTitle("Group 5 Solitaire")
        # self.setWindowIcon(QIcon('Images/frameiconico.ico'))
        self.icon1 = QPixmap('Images/spade-30-welcome.png')
        #self.icon2 = QPixmap('Images/frameiconico.ico')
        self.setStyleSheet("background: #161219;")
        self.setFixedSize(300,300)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.label_icon_1 = QLabel(self)
        self.label_icon_1.setPixmap(self.icon1)
        self.label_icon_1.move(60,8)
        self.label_icon_1.resize(30, 30)

        self.welcomeLabel = QLabel("Group Five Solitaire", self)
        self.welcomeLabel.setStyleSheet(StyleSheet_User_Pref)
        self.welcomeLabel.move(100, 15)

        self.label_icon_2 = QLabel(self)
        self.label_icon_2.setPixmap(self.icon1)
        self.label_icon_2.move(214, 8)
        self.label_icon_2.resize(30, 30)

        self.userNameLabel = QLabel("Player Name", self)
        self.userNameLabel.setStyleSheet(StyleSheet_User_Pref)
        self.userNameLabel.move(117, 50)

        self.userName = QLineEdit(self)
        self.userName.resize(200, 30)
        self.userName.move(50, 75)
        self.userName.setPlaceholderText("root user")
        self.userName.setStyleSheet(StyleSheet_User_Pref)

        self.whatBackground = QLabel("Background Colour", self)
        self.whatBackground.setStyleSheet(StyleSheet_User_Pref)
        self.whatBackground.move(100, 120)

        combolist = ["Green", "Rose Pink", "Eggplant", "Tan"]
        self.background_combo_box = QComboBox(self)
        self.background_combo_box.setStyleSheet(StyleSheet_User_Pref)
        self.background_combo_box.addItems(combolist)
        self.background_combo_box.setGeometry(100, 150, 95, 40)
        self.background_combo_box.currentIndexChanged.connect(self.selectionchange)


        self.button = QPushButton(self)
        self.button.setStyleSheet(StyleSheet_User_Pref)
        self.button.setText("Play!")
        self.button.move(75,210)
        self.button.resize(150,30)
        self.button.clicked.connect(self.startMainWindow)

        self.quit_button = QPushButton(self)
        self.quit_button.setStyleSheet(StyleSheet_User_Pref)
        self.quit_button.setText("Quit")
        self.quit_button.move(75, 255)
        self.quit_button.resize(150,20)
        self.quit_button.clicked.connect(self.stopApplication)


        self.center()
        self.oldPos = self.pos()
        self.show()

    def saveUserName(self):
        global USER_NAME
        if self.userName.text():
            USER_NAME = self.userName.text()
            # print("saveUserName: ", USER_NAME)
        # if no player name, it should show root user

    def selectionchange(self):
        global felt, nnnn
        n = self.background_combo_box.currentIndex()
        if n == 0:
            felt = QBrush(QColor(15, 99, 66))  # green default
        elif n == 1:
            felt = QBrush(QColor(240, 170, 158))   # red
        elif n == 2:
            felt = QBrush(QColor(22, 18, 25))   # eggplant
        else:
            felt = QBrush(QColor(166, 137, 98))     # tan??
        nnnn = n
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # mouse press events to move the interface around without the frame of interface
    # visibile
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def startMainWindow(self):
        self.saveUserName()
        main = MainWindow()
        self.close()

    def stopApplication(self):
        sys.exit()


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        global felt
        self.countup = 0
        self.stock_pile_rotation = 0


        view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(QRectF(-15, -20, *WINDOW_SIZE))  # -20 to show timer and score on load up

        #felt = QBrush(QColor(15, 99, 66))
        self.scene.setBackgroundBrush(felt)

        view.setScene(self.scene)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Timer for the win animation only.
        self.timer = QTimer()
        self.timer.setInterval(5)
        self.timer.timeout.connect(self.win_animation)

        self.animation_event_cover = AnimationCover()
        self.scene.addItem(self.animation_event_cover)

        menu = self.menuBar().addMenu("&File")

        deal_action = QAction(QIcon(os.path.join('Images', 'restartico.ico')), "Restart Game", self)
        deal_action.triggered.connect(self.restart_game)
        menu.addAction(deal_action)

        menu.addSeparator()

        option_action = QAction("User Preferences", self)
        option_action.triggered.connect(self.open_user_prefs)
        menu.addAction(option_action)

        menu.addSeparator()

        score_action = QAction("Highscores", self)
        score_action.triggered.connect(self.open_highscores)
        menu.addAction(score_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)


        optionmenu = self.menuBar().addMenu("&Options")

        deal1_action = QAction("Deal 1 Cards", self)
        deal1_action.setCheckable(True)
        deal1_action.setChecked(True)
        deal1_action.triggered.connect(lambda: self.set_deal_n(1))
        optionmenu.addAction(deal1_action)

        deal3_action = QAction("Deal 3 Cards", self)
        deal3_action.setCheckable(True)
        # deal3_action.setChecked(True)
        deal3_action.triggered.connect(lambda: self.set_deal_n(3))
        optionmenu.addAction(deal3_action)

        dealgroup = QActionGroup(self)
        dealgroup.addAction(deal1_action)
        dealgroup.addAction(deal3_action)
        dealgroup.setExclusive(True)

        optionmenu.addSeparator()

        rounds3_action = QAction(QIcon(os.path.join('Images', 'vegasico.ico')), "Vegas Mode", self)
        # rounds3_action = QAction("Vegas Mode", self)
        rounds3_action.setCheckable(True)
        # rounds3_action.setChecked(True)
        rounds3_action.triggered.connect(lambda: self.set_rounds_n(3))
        optionmenu.addAction(rounds3_action)

        # rounds5_action = QAction("5 rounds", self)
        # rounds5_action.setCheckable(True)
        # rounds5_action.triggered.connect(lambda: self.set_rounds_n(5))
        # menu.addAction(rounds5_action)

        roundsu_action = QAction("Unlimited", self)
        roundsu_action.setCheckable(True)
        roundsu_action.setChecked(True)
        roundsu_action.triggered.connect(lambda: self.set_rounds_n(None))
        optionmenu.addAction(roundsu_action)

        roundgroup = QActionGroup(self)
        roundgroup.addAction(rounds3_action)
        # roundgroup.addAction(rounds5_action)
        roundgroup.addAction(roundsu_action)
        roundgroup.setExclusive(True)


        helpmenu = self.menuBar().addMenu("&About")
        help_action = QAction(QIcon(os.path.join('Images', 'info.ico')), "Rules", self)
        help_action.triggered.connect(self.show_help)
        helpmenu.addAction(help_action)

        helpmenu.addSeparator()

        version_action = QAction(VERSION_NUMBER_STR, self)
        helpmenu.addAction(version_action)

        self.deck = []
        self.deal_n = 1  # Setting number of cards to deal each time initially
        self.rounds_n = None  # Setting number of rounds before no more rounds.

        for suit in SUITS:
            for value in range(1, 14):
                card = Card(value, suit)
                self.deck.append(card)
                self.scene.addItem(card)
                card.signals.doubleclicked.connect(lambda card=card: self.auto_drop_card(card))
                card.helpers.updated_score.connect(self.show_score)
                card.helpers.updated_moves.connect(self.show_moves)


        self.setCentralWidget(view)
        self.setFixedSize(*WINDOW_SIZE)

        self.deckstack = DeckStack()
        self.deckstack.setPos(OFFSET_X, OFFSET_Y)
        self.scene.addItem(self.deckstack)

        # Set up the working locations.
        self.works = []
        for n in range(7):
            stack = WorkStack()
            stack.setPos(OFFSET_X + CARD_SPACING_X * n, WORK_STACK_Y)
            self.scene.addItem(stack)
            self.works.append(stack)

        self.drops = []
        # Set up the foundation locations.
        for n in range(4):
            stack = DropStack()
            stack.setPos(OFFSET_X + CARD_SPACING_X * (3 + n), OFFSET_Y)
            stack.signals.complete.connect(self.check_win_condition)
            self.scene.addItem(stack)
            self.drops.append(stack)
            stack.helpers.updated_score.connect(self.show_score)

        # Add the deal location.
        self.dealstack = DealStack()
        self.dealstack.setPos(OFFSET_X + CARD_SPACING_X, OFFSET_Y)
        self.scene.addItem(self.dealstack)

        # Add the deal click-trigger.
        dealtrigger = DealTrigger()
        dealtrigger.signals.clicked.connect(self.deal)
        self.scene.addItem(dealtrigger)

        self.shuffle_and_stack()

        self.timerText = QGraphicsSimpleTextItem('00:00:00')
        self.timerText.setFont(QFont('Fantasy', 12))
        self.timerText.setBrush(QColor('white'))
        self.scene.addItem(self.timerText)
        self.timerText.setPos(830, 0)
        self.get_timer()

        self.scoreText = QGraphicsSimpleTextItem('Score:')
        self.scoreText.setFont(QFont('Fantasy', 12))
        self.scoreText.setBrush(QColor('white'))
        self.scene.addItem(self.scoreText)
        self.scoreText.setPos(325, 0)

        self.actualScore = QGraphicsSimpleTextItem("0")
        self.actualScore.setFont(QFont('Fantasy', 12))
        self.actualScore.setBrush(QColor('white'))
        self.actualScore.setPos(375, 0)
        self.scene.addItem(self.actualScore)

        self.movesLabel = QGraphicsSimpleTextItem("Moves:")
        self.movesLabel.setFont(QFont('Fabtasy', 12))
        self.movesLabel.setBrush(QColor('white'))
        self.movesLabel.setPos(523, 0)
        self.scene.addItem(self.movesLabel)

        self.actualMoves = QGraphicsSimpleTextItem("0")
        self.actualMoves.setFont(QFont('Fabtasy', 12))
        self.actualMoves.setBrush(QColor('white'))
        self.actualMoves.setPos(575, 0)
        self.scene.addItem(self.actualMoves)

        self.stockpileRotationLabel = QGraphicsSimpleTextItem("Stockpile Rotated:")
        self.stockpileRotationLabel.setFont(QFont('Fantasy', 12))
        self.stockpileRotationLabel.setBrush(QColor('white'))
        self.scene.addItem(self.stockpileRotationLabel)
        self.stockpileRotationLabel.setPos(10, 0)

        self.actualStockPileRotation = QGraphicsSimpleTextItem("0")
        self.actualStockPileRotation.setFont(QFont('Fantasy', 12))
        self.actualStockPileRotation.setBrush(QColor('white'))
        self.actualStockPileRotation.setPos(140, 0)
        self.scene.addItem(self.actualStockPileRotation)

        self.setWindowTitle("Group 5 Solitaire")
        self.setWindowIcon(QIcon('Images/frameiconico.ico'))
        self.show()


    def open_user_prefs(self):
        self.userpref = UserPreference()
        self.userpref.change_colour_signal.connect(self.change_background)

    def open_highscores(self):
        self.hh = UserHighscores()

    def change_background(self, n):
        if n == 0:
            self.scene.setBackgroundBrush(QBrush(QColor(15, 99, 66)))   # green default
        elif n == 1:
            self.scene.setBackgroundBrush(QBrush(QColor(240, 170, 158)))    # red
        elif n == 2:
            self.scene.setBackgroundBrush(QBrush(QColor(22, 18, 25)))   # eggplant
        else:
            self.scene.setBackgroundBrush(QBrush(QColor(166, 137, 98)))     # tan??

    def reset_stockpile_rotation(self):
        self.stock_pile_rotation = 0
        self.show_stockpile_rotation()

    def stockpile_rotation(self):
        self.stock_pile_rotation += 1
        self.show_stockpile_rotation()

    def show_stockpile_rotation(self):
        self.actualStockPileRotation.setText(str(self.stock_pile_rotation))

    def reset_show_score(self):
        global FOUNDATION_SCORE, MOVE_SCORE, MOVES
        MOVES = 0
        FOUNDATION_SCORE = 0
        MOVE_SCORE = 0
        self.actualScore.setText("0")
        self.actualMoves.setText("0")

    # slot
    # @QtCore.pyqtSlot()
    def show_score(self, total_score):
        ts = total_score
        # self.ts1 = score
        self.actualScore.setText(str(ts))

    def show_moves(self, moves):
        ms = moves
        self.actualMoves.setText(str(ms))

    def get_timer(self):
        self.my_qtimer = QTimer(self)
        self.my_qtimer.timeout.connect(self.timer_ticking)
        self.my_qtimer.start(1000)
        self.updateTimerDisplay()

    def reset_timer(self):
        self.countup = 0
        self.timer_ticking()
        self.updateTimerDisplay()

    def timer_ticking(self):
        self.countup += 1
        if self.countup <= 0:
            self.timer.stop()

        self.updateTimerDisplay()

    def updateTimerDisplay(self):
        text = "%02d:%02d" % (self.countup / 60, self.countup % 60)
        self.timerText.setText(text)

    def show_help(self):
        self.helpwindow = HelpWindow()

    def restart_game(self):
        global MOVES, TOTAL_SCORE, WON_CONDITION
        if WON_CONDITION:
            reply_won_btw = QMessageBox.question(self, "Restart Game", "Are you sure you want to start a new game?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply_won_btw == QMessageBox.Yes:
                self.get_timer()
                self.shuffle_and_stack()
                self.reset_show_score()
                self.reset_timer()
                self.reset_stockpile_rotation()
        else:

            reply = QMessageBox.question(self, "Restart Game", "Are you sure you want to start a new game?",
                                     QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                if MOVES > 3 or TOTAL_SCORE > 10:
                    # print("appended! restart")
                    self.append_To_Scores()
                self.shuffle_and_stack()
                self.reset_show_score()
                self.reset_timer()
                self.reset_stockpile_rotation()


    def write_json(self, datas, filename="Scores.json"):
        with open(filename, 'w') as wf:
            json.dump(datas, wf, indent=4)

    # append to Scores.json
    def append_To_Scores(self):
        global TOTAL_SCORE, MOVES, USER_NAME
        data = {
            'user': USER_NAME,
            'Time Of Completion': str(self.timerText.text()),
            'Moves Taken': str(self.actualMoves.text()),
            'Score': str(self.actualScore.text()),
            'Played At': str(QDateTime.currentDateTime().toString(Qt.DefaultLocaleShortDate))
        }

        try: # incase file gets deleted or something bad happens
            with open("Scores.json") as appendTingz:
                self.score_file = json.load(appendTingz)
                self.temp = self.score_file["scores:"]
                self.temp.append(data)
            self.write_json(self.score_file)
        except Exception as e:
            QMessageBox.information(self, "Exception occured! Exception is:", str(e))
            # print("Exception occured! Exception is:", str(e))

    def quit(self):
        global MOVES, TOTAL_SCORE, WON_CONDITION
        if WON_CONDITION:
            reply_won_btw = QMessageBox.question(self, "Quit", "Do you really want to quit?", QMessageBox.Yes | QMessageBox.No)
            if reply_won_btw == QMessageBox.Yes:
                sys.exit()
        else:
            reply = QMessageBox.question(self, "Quit And Save?", "Do you want to add your current stats to the scoreboard?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                # print("appended!")
                self.append_To_Scores()
                sys.exit()
            elif reply == QMessageBox.No:
                sys.exit()

    def set_deal_n(self, n):
        self.deal_n = n

    def set_rounds_n(self, n):
        self.rounds_n = n
        self.deckstack.update_stack_status(self.rounds_n)

    def shuffle_and_stack(self):
        # Stop any ongoing animation.

        self.timer.stop()
        self.animation_event_cover.hide()

        # Remove cards from all stacks.
        for stack in [self.deckstack, self.dealstack] + self.drops + self.works:
            stack.reset()

        random.shuffle(self.deck)

        # Deal out from the top of the deck, turning over the
        # final card on each line.
        cards = self.deck[:]
        for n, workstack in enumerate(self.works, 1):
            for a in range(n):
                card = cards.pop()
                workstack.add_card(card)
                card.turn_back_up()
                if a == n - 1:
                    card.turn_face_up()

        # Ensure removed from all other stacks here.
        self.deckstack.stack_cards(cards)

    # Method for the stack of cards, top left
    def deal(self):
        if self.deckstack.cards:
            self.dealstack.spread_from = len(self.dealstack.cards)
            for n in range(self.deal_n):
                card = self.deckstack.take_top_card()
                if card:
                    self.dealstack.add_card(card)
                    card.turn_face_up()

        elif self.deckstack.can_restack(self.rounds_n):
            self.deckstack.restack(self.dealstack)
            self.stockpile_rotation()
            self.deckstack.update_stack_status(self.rounds_n)

    def auto_drop_card(self, card):
        for stack in self.drops:
            if stack.is_valid_drop(card):
                card.stack.remove_card(card)
                stack.add_card(card)
                card.move_registered()
                break

    def check_win_condition(self):
        global WON_CONDITION
        complete = all(s.is_complete for s in self.drops)
        if complete:
            # print("You Completed the game!")
            self.my_qtimer.stop()
            WON_CONDITION = True
            self.append_To_Scores()
            # Add click-proof cover to play area.
            self.animation_event_cover.show()
            # Get the stacks of cards from the drop,stacks.
            self.timer.start()

    def win_animation(self):
        # Start off a new card
        for drop in self.drops:
            if drop.cards:
                card = drop.cards.pop()
                if card.vector is None:
                    card.vector = QPoint(-random.randint(3, 10), -random.randint(0, 10))
                    break

        for card in self.deck:
            if card.vector is not None:
                card.setPos(card.pos() + card.vector)
                card.vector += QPoint(0, 1)  # Gravity
                if card.pos().y() > WINDOW_SIZE[1] - CARD_DIMENSIONS.height():
                    # Bounce the card, losing some energy.
                    card.vector = QPoint(card.vector.x(), -max(1, int(card.vector.y() * BOUNCE_ENERGY)))
                    # Bump back up to base of screen.
                    card.setPos(card.pos().x(), WINDOW_SIZE[1] - CARD_DIMENSIONS.height())

                if card.pos().x() < - CARD_DIMENSIONS.width():
                    card.vector = None
                    # Put the card back where it started.
                    card.stack.add_card(card)


if __name__ == '__main__':
    app = QApplication([])

    splash = SplashScreen()
    splash.show()
    splash.progress()

    #window = MainWindow()
    user = User()

    # splash.finish(window)
    splash.finish(user)
    app.exec_()
