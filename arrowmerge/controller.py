from PyQt6.QtCore import QObject
from PyQt6.QtGui import QColor, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QTextEdit, QFileDialog

class DiffController(QObject):
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view
        
        # Connections
        self.view.left_edit.textChanged.connect(self.on_text_changed)
        self.view.right_edit.textChanged.connect(self.on_text_changed)
        self.view.merge_requested.connect(self.perform_merge)
        self.view.action_refresh.triggered.connect(self.force_refresh)
        
        self.view.action_open_left.triggered.connect(lambda: self.open_file('left'))
        self.view.action_open_right.triggered.connect(lambda: self.open_file('right'))
        self.view.action_save_left.triggered.connect(lambda: self.save_file('left'))
        self.view.action_save_right.triggered.connect(lambda: self.save_file('right'))
        
        self.view.action_next_diff.triggered.connect(self.next_diff)
        self.view.action_prev_diff.triggered.connect(self.prev_diff)
        
        self.is_updating = False

    def open_file(self, side):
        path, _ = QFileDialog.getOpenFileName(self.view, f"Open {side} file")
        if path:
            try:
                self.model.load_file(path, side)
                # Model update does NOT trigger textChanged automatically if we just set internal strings,
                # BUT set_left_text updates internal state. We need to update the View.
                if side == 'left':
                    self.view.left_edit.setPlainText(self.model.get_left_text())
                else:
                    self.view.right_edit.setPlainText(self.model.get_right_text())
            except Exception as e:
                print(f"Error opening file: {e}")

    def save_file(self, side):
        path, _ = QFileDialog.getSaveFileName(self.view, f"Save {side} file")
        if path:
            try:
                self.model.save_file(path, side)
            except Exception as e:
                print(f"Error saving file: {e}")
                
    def next_diff(self):
        # Determine current line from left editor cursor
        cursor = self.view.left_edit.textCursor()
        current_line = cursor.blockNumber()
        
        diff_rows = self.model.get_diff_lines()
        target_row = None
        
        # Find first row > current_line that is not equal
        for row in diff_rows:
            if row['type'] == 'equal': continue
            
            # Use left_index if available, else right_index (mapped loosely)
            # We want to scroll both but we track position mostly by left for simplicity or whichever exists
            l_idx = row['left_index']
            
            # If it's an insert, l_idx is None. We iterate rows. 
            # We just need a row index higher than current "position" in diff list could be tricky.
            # Simpler: Find the first diff row that appears AFTER the current cursor position.
            
            # Let's map current file line to diff row index
            # This is hard because multiple diff rows might map to same line or gaps.
            # Instead, just find the first diff row where the line number is greater than current_line.
            
            if l_idx is not None and l_idx > current_line:
                target_row = row
                break
            elif l_idx is None:
                # Insert: check right index? 
                # If we are only looking at left cursor, skipping inserts might happen if we solely rely on left line.
                # Better approach: Iterate all non-equal rows, find one that is "after" current view.
                # But "after" is ambiguous if we only check left cursor.
                # Let's just iterate and find the first one with l_idx > current_line
                # If l_idx is None (pure insert), we check if the PREVIOUS row had l_idx <= current_line.
                pass
                
        # Robust Next:
        # 1. Get all non-equal rows
        # 2. Find the one that has a line number > current cursor.
        #    If row is 'insert' (no left line), we estimate its position based on surrounding rows.
        
        # Simplest working version: Move to next non-equal row based on Left Line Number.
        # If 'insert', we can't easily jump based on left cursor unless we track 'virtual' position.
        # For now, let's just jump to next diff that has a left_line > current.
        
        for row in diff_rows:
            if row['type'] == 'equal': continue
            if row['left_index'] is not None and row['left_index'] > current_line:
                self.scroll_to_row(row)
                return
                
    def prev_diff(self):
        cursor = self.view.left_edit.textCursor()
        current_line = cursor.blockNumber()
        
        diff_rows = self.model.get_diff_lines()
        target_row = None
        
        # Search backwards
        for row in reversed(diff_rows):
            if row['type'] == 'equal': continue
            if row['left_index'] is not None and row['left_index'] < current_line:
                self.scroll_to_row(row)
                return

    def scroll_to_row(self, row):
        l_idx = row['left_index']
        r_idx = row['right_index']
        
        if l_idx is not None:
             cursor = self.get_line_cursor(self.view.left_edit, l_idx)
             self.view.left_edit.setTextCursor(cursor)
             self.view.left_edit.ensureCursorVisible()
             
        if r_idx is not None:
             cursor = self.get_line_cursor(self.view.right_edit, r_idx)
             self.view.right_edit.setTextCursor(cursor)
             self.view.right_edit.ensureCursorVisible()

    def on_text_changed(self):
        if self.is_updating:
            return
            
        left_txt = self.view.left_edit.toPlainText()
        right_txt = self.view.right_edit.toPlainText()
        
        self.model.set_left_text(left_txt)
        self.model.set_right_text(right_txt)
        self.model.calculate_diff()
        
        # Update View with latest diff rows for context menu logic
        self.view.set_diff_rows(self.model.get_diff_lines())
        
        self.update_highlights()

    def force_refresh(self):
        self.on_text_changed()

    def update_highlights(self):
        self.is_updating = True
        
        diff_rows = self.model.get_diff_lines()
        
        left_selections = []
        right_selections = []
        
        bg_red = QColor("#FFCCCC")
        bg_green = QColor("#CCFFCC")
        bg_mod_left = QColor("#FFFF99") 
        bg_mod_right = QColor("#FFFF99")
        
        # We need to map diff_rows to selections
        for row in diff_rows:
            type = row['type']
            
            if type == 'replace':
                l_idx = row['left_index']
                r_idx = row['right_index']
                
                # Highlight whole line background
                sel_l = QTextEdit.ExtraSelection()
                sel_l.format.setBackground(bg_mod_left)
                sel_l.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel_l.cursor = self.get_line_cursor(self.view.left_edit, l_idx)
                left_selections.append(sel_l)

                sel_r = QTextEdit.ExtraSelection()
                sel_r.format.setBackground(bg_mod_right)
                sel_r.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel_r.cursor = self.get_line_cursor(self.view.right_edit, r_idx)
                right_selections.append(sel_r)
                
                # Intra-line diff highlighting
                ops = row['intra_diffs']
                
                for op, i1, i2, j1, j2 in ops:
                    if op == 'delete' or op == 'replace':
                        cursor = self.get_line_cursor(self.view.left_edit, l_idx)
                        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, i1)
                        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, i2 - i1)
                        sel_intra = QTextEdit.ExtraSelection()
                        sel_intra.format.setBackground(QColor("#FF8888"))
                        sel_intra.cursor = cursor
                        left_selections.append(sel_intra)
                        
                    if op == 'insert' or op == 'replace':
                        cursor = self.get_line_cursor(self.view.right_edit, r_idx)
                        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, j1)
                        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, j2 - j1)
                        sel_intra = QTextEdit.ExtraSelection()
                        sel_intra.format.setBackground(QColor("#88FF88"))
                        sel_intra.cursor = cursor
                        right_selections.append(sel_intra)

            elif type == 'delete':
                l_idx = row['left_index']
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(bg_red)
                sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel.cursor = self.get_line_cursor(self.view.left_edit, l_idx)
                left_selections.append(sel)
                
            elif type == 'insert':
                r_idx = row['right_index']
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(bg_green)
                sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel.cursor = self.get_line_cursor(self.view.right_edit, r_idx)
                right_selections.append(sel)

        self.view.left_edit.setExtraSelections(left_selections)
        self.view.right_edit.setExtraSelections(right_selections)
        
        self.is_updating = False

    def get_line_cursor(self, editor, line_num):
        doc = editor.document()
        # Find block by line number
        block = doc.findBlockByNumber(line_num)
        cursor = QTextCursor(block)
        return cursor
        
    def perform_merge(self, pane, action, line_num, opcode_index):
        # Find which Diff Row involves this line
        rows = self.model.get_diff_lines()
        target_row_index = -1
        
        for i, row in enumerate(rows):
            if pane == 'left' and row['left_index'] == line_num:
                target_row_index = i
                break
            elif pane == 'right' and row['right_index'] == line_num:
                target_row_index = i
                break
        
        if target_row_index == -1:
            print("Could not find matching diff row for line", line_num)
            return

        self.is_updating = True 
        
        if opcode_index != -1:
            # Intra-line merge
            self.model.merge_intra_line(target_row_index, opcode_index, action)
        else:
            # Full line merge
            if action == 'push_to_right': # Left -> Right
                self.model.merge_left_to_right(target_row_index)
            elif action == 'pull_to_left': # Right -> Left
                self.model.merge_right_to_left(target_row_index)
            
        # Update text in View
        self.view.left_edit.setPlainText(self.model.get_left_text())
        self.view.right_edit.setPlainText(self.model.get_right_text())
        
        self.is_updating = False
        
        # Trigger recalc
        self.on_text_changed()
