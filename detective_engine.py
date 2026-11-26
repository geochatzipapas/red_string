"""Κοινή μηχανή για τα παιχνίδια ντετέκτιβ (PySide6).
Δεν τρέχει μόνη της: τη χρησιμοποιούν τα game_*.py με την συνάρτηση run(GAME).
"""
import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                               QGraphicsItem, QGraphicsLineItem, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox,
                               QDialog, QFormLayout, QLineEdit, QDialogButtonBox)
from PySide6.QtGui import QColor, QPen, QFont, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer

W, H = 250, 170
T = {}  # θέμα (ορίζεται από το GAME)


def base_dir():
    """Φάκελος αποθήκευσης προόδου: δίπλα στο .py ή δίπλα στο εκτελέσιμο (PyInstaller)."""
    if getattr(sys, "frozen", False):
        b = Path(sys.executable).resolve().parent
        if sys.platform == "darwin" and b.name == "MacOS":
            b = b.parents[2]
        return b
    return Path(__file__).resolve().parent


def fmt(sec):
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


class Card(QGraphicsItem):
    def __init__(self, cid, title, text, pos, interro=False):
        super().__init__()
        self.cid, self.title, self.text = cid, title, text
        self.interro = interro
        self.penalized = False
        self.links = []
        self._moved = False
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(pos)
        self.setZValue(1)

    def boundingRect(self):
        return QRectF(-4, -4, W + 12, H + 12)

    def pin(self):
        return self.pos() + QPointF(W / 2, 8)

    def paint(self, p, option, widget=None):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 110))
        p.drawRoundedRect(QRectF(4, 5, W, H), 6, 6)
        scene = self.scene()
        hot = scene is not None and scene.first is self
        i = self.interro
        accent = QColor(T["i_accent"] if i else T["accent"])
        edge = QColor(T["i_edge"] if i else T["edge"])
        p.setBrush(QColor(T["i_card"] if i else T["card"]))
        p.setPen(QPen(accent if hot else edge, 3 if hot else 1.5))
        p.drawRoundedRect(QRectF(0, 0, W, H), 6, 6)
        f = QFont(T["font"], 10)
        f.setBold(True)
        p.setFont(f)
        p.setPen(accent)
        p.drawText(QRectF(12, 18, W - 24, 22), Qt.AlignmentFlag.AlignLeft, T["bullet"] + self.title)
        f.setBold(False)
        f.setPointSize(9)
        p.setFont(f)
        p.setPen(QColor(T["text"]))
        bottom = 72 if i else 56
        p.drawText(QRectF(12, 46, W - 24, H - bottom),
                   Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, self.text)
        if i:
            f.setPointSize(8)
            p.setFont(f)
            p.setPen(accent)
            tag = ("ΑΝΑΚΡΙΣΗ · ποινή εφαρμόστηκε" if self.penalized
                   else f"ΑΝΑΚΡΙΣΗ · -{T['penalty']}″ αν χρησιμοποιηθεί")
            p.drawText(QRectF(12, H - 24, W - 24, 18), Qt.AlignmentFlag.AlignLeft, tag)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(T["string"]))
        p.drawEllipse(QPointF(W / 2, 8), 6, 6)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._moved = True
            for l in self.links:
                l.update_pos()
        return super().itemChange(change, value)

    def mousePressEvent(self, e):
        self._moved = False
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if not self._moved and self.scene():
            self.scene().card_clicked(self)


class String(QGraphicsLineItem):
    def __init__(self, a, b):
        super().__init__()
        self.a, self.b = a, b
        self.setPen(QPen(QColor(T["string"]), 3))
        self.setZValue(2)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        a.links.append(self)
        b.links.append(self)
        self.update_pos()

    def update_pos(self):
        pa, pb = self.a.pin(), self.b.pin()
        self.setLine(pa.x(), pa.y(), pb.x(), pb.y())


def slot(i):
    return QPointF(25 + (i % 4) * 265, 25 + (i // 4) * 188)


class Board(QGraphicsScene):
    def __init__(self, on_change, on_penalty):
        super().__init__(0, 0, 1100, 790)
        self.on_change = on_change
        self.on_penalty = on_penalty
        self.connect_mode = False
        self.first = None
        self.strings = {}

    def load(self, case):
        self.clear()
        self.strings = {}
        self.first = None
        for i, (cid, title, text) in enumerate(case["cards"]):
            self.addItem(Card(cid, title, text, slot(i)))
        self.on_change()

    def add_interro(self, cid, title, text, n):
        self.addItem(Card(cid, title, text, slot(12 + n), True))
        self.update()

    def drawBackground(self, p, rect):
        p.fillRect(rect, QColor(T["bg"]))
        c = QColor(T["grid"])
        p.setPen(QPen(c, 1))
        for x in range(0, int(self.width()) + 1, 40):
            p.drawLine(x, 0, x, int(self.height()))
        for y in range(0, int(self.height()) + 1, 40):
            p.drawLine(0, y, int(self.width()), y)

    def card_clicked(self, card):
        if not self.connect_mode:
            return
        penalties = 0
        if self.first is None:
            self.first = card
        elif self.first is card:
            self.first = None
        else:
            key = frozenset({self.first.cid, card.cid})
            if key in self.strings:
                s = self.strings.pop(key)
                s.a.links.remove(s)
                s.b.links.remove(s)
                self.removeItem(s)
            else:
                for c in (self.first, card):
                    if c.interro and not c.penalized:
                        c.penalized = True
                        penalties += 1
                s = String(self.first, card)
                self.strings[key] = s
                self.addItem(s)
            self.first = None
        self.update()
        self.on_change()
        if penalties:
            self.on_penalty(penalties)


class Window(QMainWindow):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.cases = game["cases"]
        self.clues = game["clues"]
        self.penalty = game["penalty"]
        self.progress = base_dir() / game["progress"]
        self.setWindowTitle(game["window"])
        self.resize(1500, 860)
        self.setStyleSheet(
            f"QMainWindow, QWidget {{ background:{T['panel']}; color:{T['panel_text']}; }}"
            f"QPushButton {{ background:{T['btn']}; color:{T['btn_text']}; border:1px solid {T['edge']};"
            f" padding:6px; border-radius:4px; }}"
            f"QPushButton:checked {{ background:{T.get('panel_accent', T['accent'])}; color:{T['panel']}; }}"
            f"QComboBox, QLineEdit {{ background:{T['btn']}; color:{T['btn_text']}; padding:4px; }}")
        self.state = {"solved": [False] * 5, "final_unlocked": False, "best": [0] * 5}
        self.load_state()
        self.current = 0
        self.attempts = 0
        self.remaining = 0
        self.running = False
        self.paused = False
        self.asked = []
        self.board = Board(self.refresh, self.apply_penalty)
        view = QGraphicsView(self.board)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setStyleSheet("border:0;")

        panel = QWidget()
        panel.setFixedWidth(350)
        lay = QVBoxLayout(panel)
        head = QLabel(game["name"])
        head.setWordWrap(True)
        head.setStyleSheet(f"font-size:16px;font-weight:bold;color:{T.get('panel_accent', T['accent'])};")
        self.case_combo = QComboBox()
        self.case_combo.addItems([c["title"] for c in self.cases])
        self.timer_lbl = QLabel()
        tf = QFont(T["font"], 26)
        tf.setBold(True)
        self.timer_lbl.setFont(tf)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet(f"color:{T.get('panel_status', T['i_accent'])};")
        self.brief = QLabel()
        self.brief.setWordWrap(True)
        self.btn = QPushButton("Σύνδεση: ΚΛΕΙΣΤΗ")
        self.btn.setCheckable(True)
        self.btn.toggled.connect(self.toggle)
        self.info = QLabel()
        self.q_combo = QComboBox()
        ask_btn = QPushButton("Ανάκριση (ξεκλειδώνει κάρτα)")
        ask_btn.clicked.connect(self.ask)
        self.combo = QComboBox()
        accuse = QPushButton("Κατηγορώ!")
        accuse.clicked.connect(self.accuse)
        self.notes = QLabel()
        self.notes.setWordWrap(True)
        self.notes.setStyleSheet(f"color:{T.get('panel_accent', T['accent'])};")
        for w in (head, self.case_combo, self.timer_lbl, self.status, self.brief, self.btn,
                  self.info, QLabel("Ανακρίσεις (η χρήση τους κοστίζει χρόνο):"),
                  self.q_combo, ask_btn, QLabel("Ποιος είναι ο ένοχος;"), self.combo,
                  accuse, self.notes):
            lay.addWidget(w)
        lay.addStretch()

        root = QWidget()
        h = QHBoxLayout(root)
        h.addWidget(view, 1)
        h.addWidget(panel)
        self.setCentralWidget(root)

        self.case_combo.currentIndexChanged.connect(self.on_case_changed)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.tick)
        self.clock.start(1000)
        self.set_case(0)

    # ---------- βοηθητικά ----------
    def say(self, kind, title, text):
        self.paused = True
        try:
            getattr(QMessageBox, kind)(self, title, text)
        finally:
            self.paused = False

    def load_state(self):
        try:
            data = json.loads(self.progress.read_text(encoding="utf-8"))
            if len(data.get("solved", [])) == 5:
                self.state.update(data)
        except Exception:
            pass
        if len(self.state.get("best", [])) != 5:
            self.state["best"] = [0] * 5

    def save_state(self):
        try:
            self.progress.write_text(json.dumps(self.state), encoding="utf-8")
        except Exception:
            pass

    def unlocked(self, i):
        if i == 0:
            return True
        if i < 4:
            return self.state["solved"][i - 1]
        return self.state["final_unlocked"]

    def refresh_menu(self):
        self.case_combo.blockSignals(True)
        for i, c in enumerate(self.cases):
            mark = "✔ " if self.state["solved"][i] else ("• " if self.unlocked(i) else "🔒 ")
            self.case_combo.setItemText(i, mark + c["title"])
        self.case_combo.setCurrentIndex(self.current)
        self.case_combo.blockSignals(False)
        lines = [f"Υπόθεση {i + 1}: {self.clues[i]}" for i in range(4) if self.state["solved"][i]]
        text = ("Στοιχεία που έχεις βρει:\n" + "\n".join(lines)) if lines else "Δεν έχεις βρει στοιχεία ακόμα."
        recs = [f"Υπόθεση {i + 1}: {fmt(t)}" for i, t in enumerate(self.state["best"]) if t > 0]
        if recs:
            text += "\n\nΡεκόρ (χρόνος που περίσσεψε):\n" + "\n".join(recs)
        self.notes.setText(text)

    # ---------- χρονόμετρο ----------
    def update_clock(self):
        color = "#ff4d4d" if self.remaining < 180 else T.get("panel_accent", T["accent"])
        self.timer_lbl.setStyleSheet(f"color:{color};")
        self.timer_lbl.setText("⏱ " + fmt(self.remaining))

    def tick(self):
        if not self.running or self.paused:
            return
        self.remaining -= 1
        self.update_clock()
        if self.remaining <= 0:
            self.running = False
            QTimer.singleShot(0, self.timeout)

    def apply_penalty(self, n):
        if not self.running:
            return
        self.remaining -= self.penalty * n
        self.status.setText(f"Ποινή χρόνου: -{self.penalty * n}″ (χρησιμοποίησες κάρτα ανάκρισης).")
        self.update_clock()
        if self.remaining <= 0:
            self.running = False
            QTimer.singleShot(0, self.timeout)

    def timeout(self):
        self.say("warning", "Λήξη χρόνου", "Ο χρόνος τελείωσε. Η υπόθεση ξαναρχίζει από την αρχή.")
        self.set_case(self.current)

    # ---------- μενού ----------
    def on_case_changed(self, i):
        if i == self.current:
            return
        if self.unlocked(i):
            self.set_case(i)
            return
        self.refresh_menu()
        if i < 4:
            self.say("information", "Κλειδωμένη", f"Λύσε πρώτα την υπόθεση {i}.")
        elif not all(self.state["solved"][:4]):
            self.say("information", "Κλειδωμένη",
                     "Η τελική υπόθεση ανοίγει όταν λύσεις τις 4 πρώτες και βάλεις τα στοιχεία τους.")
        elif self.ask_clues():
            self.state["final_unlocked"] = True
            self.save_state()
            self.set_case(4)
        else:
            self.say("warning", "Λάθος στοιχεία", "Τα στοιχεία δεν ταιριάζουν. Ξαναδές τις κάρτες των υποθέσεων.")

    def ask_clues(self):
        self.paused = True
        try:
            dlg = QDialog(self)
            dlg.setWindowTitle("Στοιχεία προηγούμενων υποθέσεων")
            form = QFormLayout(dlg)
            edits = []
            for i in range(4):
                e = QLineEdit()
                edits.append(e)
                form.addRow(f"Στοιχείο υπόθεσης {i + 1}", e)
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            bb.accepted.connect(dlg.accept)
            bb.rejected.connect(dlg.reject)
            form.addRow(bb)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return False
            return all(e.text().strip().upper() == self.clues[i] for i, e in enumerate(edits))
        finally:
            self.paused = False

    def set_case(self, i):
        self.current = i
        self.case = self.cases[i]
        self.attempts = 0
        self.brief.setText(self.case["brief"])
        self.status.setText("")
        self.combo.clear()
        self.combo.addItems(self.case["suspects"])
        self.q_combo.clear()
        for q in self.case["interro"]:
            self.q_combo.addItem(f"{self.case['suspects'][q['s']].split(' (')[0]}: {q['q']}")
        self.asked = [False] * len(self.case["interro"])
        self.btn.setChecked(False)
        self.board.load(self.case)
        self.remaining = self.game["limits"][i]
        self.running = True
        self.update_clock()
        self.refresh_menu()

    def toggle(self, on):
        self.board.connect_mode = on
        self.board.first = None
        self.btn.setText("Σύνδεση: ΑΝΟΙΧΤΗ (κλικ σε 2 κάρτες)" if on else "Σύνδεση: ΚΛΕΙΣΤΗ")
        self.board.update()

    def refresh(self):
        self.info.setText(f"Νήματα στον πίνακα: {len(self.board.strings)}")

    # ---------- ανάκριση ----------
    def ask(self):
        k = self.q_combo.currentIndex()
        if k < 0 or self.asked[k] or not self.running:
            return
        n = sum(self.asked)
        self.asked[k] = True
        cid, title, text = self.case["interro"][k]["card"]
        self.board.add_interro(cid, title, text, n)
        self.q_combo.model().item(k).setEnabled(False)
        self.status.setText(f"Νέα κάρτα ανάκρισης στην κάτω σειρά του πίνακα. "
                            f"Αν τη συνδέσεις με νήμα, χάνεις {self.penalty}″.")

    # ---------- κατηγορία ----------
    def accuse(self):
        if not self.running:
            return
        c = self.case
        strings = set(self.board.strings.keys())
        key = {frozenset(k) for k in c["key_links"]}
        ok = {frozenset(k) for k in c["ok_links"]}
        wrong = [s for s in strings
                 if s not in key and s not in ok and not any(x.startswith("Q") for x in s)]
        good = (self.combo.currentIndex() == c["culprit"] and key <= strings and len(wrong) <= 1)
        if not good:
            self.attempts += 1
            msg = "Η δικογραφία δεν στέκει. Έλεγξε ξανά ένοχο, αποδείξεις και περιττές συνδέσεις."
            if self.attempts >= 3:
                msg += "\n\nΥπόδειξη: " + c["hint"]
            self.say("warning", "Απόρριψη", msg)
            return
        self.running = False
        first_time = not self.state["solved"][self.current]
        self.state["solved"][self.current] = True
        prev = self.state["best"][self.current]
        new_record = self.remaining > prev
        if new_record:
            self.state["best"][self.current] = self.remaining
        self.save_state()
        msg = "Υπόθεση λύθηκε!\n\n" + c["epilogue"]
        msg += f"\n\nΧρόνος που περίσσεψε: {fmt(self.remaining)}"
        if new_record:
            msg += "  (νέο ρεκόρ!)"
        if self.current < 4 and first_time:
            msg += f"\n\nΝέο στοιχείο στο σημειωματάριο: {self.clues[self.current]}"
        if self.current < 3:
            msg += f"\n\nΞεκλείδωσε η υπόθεση {self.current + 2}."
        elif self.current == 3:
            msg += "\n\nΈχεις και τα 4 στοιχεία. Επίλεξε την υπόθεση 5 από το μενού και γράψε τα."
        self.say("information", "Απόφαση", msg)
        self.refresh_menu()


def run(game):
    T.clear()
    T.update(game["theme"])
    T["penalty"] = game["penalty"]
    app = QApplication(sys.argv)
    w = Window(game)
    w.show()
    sys.exit(app.exec())
