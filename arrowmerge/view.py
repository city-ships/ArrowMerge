from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QLabel, QSplitter, QToolBar, QMenu)
from PyQt6.QtGui import QAction, QColor, QTextCursor, QTextCharFormat, QPainter, QTextFormat
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from .highlighter import LatexHighlighter

class MenuLabelBuilder:
    @staticmethod
    def get_label(direction, scope):
        """
        Returns the label for the context menu action.
        direction: 'push' (Left->Right) or 'pull' (Right->Left)
        scope: 'word' or 'line'
        """
        arrow = ""
        action_text = ""
        
        if direction == 'push':
            # Previous (Left) -> Changed (Right)
            arrow = "⮕"
            if scope == 'word':
                action_text = "Copy to Changed Text (Word)"
            else:
                action_text = "Copy to Changed Text (Line)"
        elif direction == 'pull':
            # Changed (Right) -> Previous (Left)
            arrow = "⬅"
            if scope == 'word':
                action_text = "Revert to Previous Text (Word)"
            else:
                action_text = "Revert to Previous Text (Line)"
                
        return f"{action_text}  {arrow}"

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        font = self.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self.setFont(font)
        
        # Apply Syntax Highlighting
        self.highlighter = LatexHighlighter(self.document())

class DiffWindow(QMainWindow):
    merge_requested = pyqtSignal(str, str, int, int) # pane, action, line_num, opcode_index

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Diff & Merge Tool")
        self.resize(1200, 800)

        # Main Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.action_refresh = QAction("Refresh Diff", self)
        toolbar.addAction(self.action_refresh)
        
        toolbar.addSeparator()
        self.action_prev_diff = QAction("Previous Diff", self)
        self.action_next_diff = QAction("Next Diff", self)
        toolbar.addAction(self.action_prev_diff)
        toolbar.addAction(self.action_next_diff)

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        self.action_open_left = QAction("Open Previous File...", self)
        self.action_open_right = QAction("Open Changed File...", self)
        self.action_save_left = QAction("Save Previous File...", self)
        self.action_save_right = QAction("Save Changed File...", self)
        
        file_menu.addAction(self.action_open_left)
        file_menu.addAction(self.action_open_right)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save_left)
        file_menu.addAction(self.action_save_right)

        # Splitter for editors
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.left_edit = CodeEditor()
        self.right_edit = CodeEditor()
        
        # Labels
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Previous Text (Original)  ⮕"))
        left_layout.addWidget(self.left_edit)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("⬅  Changed Text (Modified)"))
        right_layout.addWidget(self.right_edit)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 600])
        
        layout.addWidget(splitter)
        
        # Merge Actions (ContextMenu)
        self.left_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.left_edit.customContextMenuRequested.connect(self.show_left_context_menu)
        
        self.right_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.right_edit.customContextMenuRequested.connect(self.show_right_context_menu)

        # Sync scrolling
        self.left_edit.verticalScrollBar().valueChanged.connect(self.sync_scroll_left_to_right)
        self.right_edit.verticalScrollBar().valueChanged.connect(self.sync_scroll_right_to_left)
        self._scrolling = False
        
        self.diff_rows = [] 

    def set_diff_rows(self, rows):
        self.diff_rows = rows

    def sync_scroll_left_to_right(self, value):
        if self._scrolling: return
        self._scrolling = True
        self.right_edit.verticalScrollBar().setValue(value)
        self._scrolling = False

    def sync_scroll_right_to_left(self, value):
        if self._scrolling: return
        self._scrolling = True
        self.left_edit.verticalScrollBar().setValue(value)
        self._scrolling = False

    def get_opcode_at_cursor(self, pane, block_num, column):
        # Find the row corresponding to this block_num
        target_row = None
        for row in self.diff_rows:
            if pane == 'left' and row['left_index'] == block_num:
                target_row = row
                break
            elif pane == 'right' and row['right_index'] == block_num:
                target_row = row
                break
        
        if not target_row or not target_row.get('intra_diffs'):
            return -1
            
        # Check opcodes
        # ops = [(op, i1, i2, j1, j2), ...]
        for i, (op, i1, i2, j1, j2) in enumerate(target_row['intra_diffs']):
            if pane == 'left':
                # Check intersection with [i1, i2)
                # Note: 'replace' usually means i1!=i2 and j1!=j2. 
                # 'delete' means i1!=i2. 'insert' means j1!=j2.
                if i1 <= column < i2:
                    if op in ('delete', 'replace'):
                        return i
            elif pane == 'right':
                if j1 <= column < j2:
                    if op in ('insert', 'replace'):
                        return i
        return -1

    def show_left_context_menu(self, pos):
        menu = self.left_edit.createStandardContextMenu()
        menu.addSeparator()
        
        cursor = self.left_edit.cursorForPosition(pos)
        block_num = cursor.blockNumber()
        column = cursor.positionInBlock()
        
        # Check for intra-line merge
        opcode_index = self.get_opcode_at_cursor('left', block_num, column)
        
        if opcode_index != -1:
            label = MenuLabelBuilder.get_label('push', 'word')
            action_word = QAction(label, self)
            action_word.triggered.connect(lambda: self.merge_requested.emit('left', 'push_to_right', block_num, opcode_index))
            menu.addAction(action_word)
        
        label_line = MenuLabelBuilder.get_label('push', 'line')
        action_push = QAction(label_line, self)
        action_push.triggered.connect(lambda: self.merge_requested.emit('left', 'push_to_right', block_num, -1))
        menu.addAction(action_push)
        
        menu.exec(self.left_edit.mapToGlobal(pos))

    def show_right_context_menu(self, pos):
        menu = self.right_edit.createStandardContextMenu()
        menu.addSeparator()

        cursor = self.right_edit.cursorForPosition(pos)
        block_num = cursor.blockNumber()
        column = cursor.positionInBlock()
        
        # Check for intra-line merge
        opcode_index = self.get_opcode_at_cursor('right', block_num, column)
        
        if opcode_index != -1:
            label = MenuLabelBuilder.get_label('pull', 'word')
            action_word = QAction(label, self)
            action_word.triggered.connect(lambda: self.merge_requested.emit('right', 'pull_to_left', block_num, opcode_index))
            menu.addAction(action_word)
        
        label_line = MenuLabelBuilder.get_label('pull', 'line')
        action_pull = QAction(label_line, self)
        action_pull.triggered.connect(lambda: self.merge_requested.emit('right', 'pull_to_left', block_num, -1))
        menu.addAction(action_pull)
        
        menu.exec(self.right_edit.mapToGlobal(pos))
