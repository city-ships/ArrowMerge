import difflib

class DiffModel:
    def __init__(self):
        self.left_text = ""
        self.right_text = ""
        self.left_lines = []
        self.right_lines = []
        self.diff_rows = []

    def set_left_text(self, text):
        self.left_text = text
        self.left_lines = text.splitlines()

    def set_right_text(self, text):
        self.right_text = text
        self.right_lines = text.splitlines()

    def load_file(self, path, side):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            if side == 'left':
                self.set_left_text(text)
            elif side == 'right':
                self.set_right_text(text)
        except Exception as e:
            # In a real app we might propagate this or handle gracefully
            raise e

    def save_file(self, path, side):
        try:
            text = ""
            if side == 'left':
                text = self.get_left_text()
            elif side == 'right':
                text = self.get_right_text()
                
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            raise e

    def get_left_text(self):
        return "\n".join(self.left_lines)

    def get_right_text(self):
        return "\n".join(self.right_lines)

    def calculate_diff(self):
        # difflib.SequenceMatcher to compare lines
        matcher = difflib.SequenceMatcher(None, self.left_lines, self.right_lines)
        self.diff_rows = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    self.diff_rows.append({
                        'type': 'equal',
                        'left_line': self.left_lines[i1 + k],
                        'right_line': self.right_lines[j1 + k],
                        'left_index': i1 + k,
                        'right_index': j1 + k,
                        'intra_diffs': [] 
                    })
            elif tag == 'replace':
                len_left = i2 - i1
                len_right = j2 - j1
                min_len = min(len_left, len_right)
                
                # Aligned replacements
                for k in range(min_len):
                    l_line = self.left_lines[i1 + k]
                    r_line = self.right_lines[j1 + k]
                    
                    # Compute intra-line diffs immediately
                    ops = self.compute_intra_line_diff(l_line, r_line)
                    
                    self.diff_rows.append({
                        'type': 'replace',
                        'left_line': l_line,
                        'right_line': r_line,
                        'left_index': i1 + k,
                        'right_index': j1 + k,
                        'intra_diffs': ops
                    })
                
                # Excess left (treated as delete)
                if len_left > min_len:
                    for k in range(min_len, len_left):
                        self.diff_rows.append({
                            'type': 'delete',
                            'left_line': self.left_lines[i1 + k],
                            'right_line': None,
                            'left_index': i1 + k,
                            'right_index': None,
                            'intra_diffs': []
                        })
                # Excess right (treated as insert)
                elif len_right > min_len:
                    for k in range(min_len, len_right):
                        self.diff_rows.append({
                            'type': 'insert',
                            'left_line': None,
                            'right_line': self.right_lines[j1 + k],
                            'left_index': None,
                            'right_index': j1 + k,
                            'intra_diffs': []
                        })
                        
            elif tag == 'delete':
                for k in range(i2 - i1):
                    self.diff_rows.append({
                        'type': 'delete',
                        'left_line': self.left_lines[i1 + k],
                        'right_line': None,
                        'left_index': i1 + k,
                        'right_index': None,
                        'intra_diffs': []
                    })
            elif tag == 'insert':
                for k in range(j2 - j1):
                    self.diff_rows.append({
                        'type': 'insert',
                        'left_line': None,
                        'right_line': self.right_lines[j1 + k],
                        'left_index': None,
                        'right_index': j1 + k,
                        'intra_diffs': []
                    })

    def get_diff_lines(self):
        return self.diff_rows

    def compute_intra_line_diff(self, text1, text2):
        s = difflib.SequenceMatcher(None, text1, text2)
        return s.get_opcodes()

    def merge_right_to_left(self, row_index):
        if row_index < 0 or row_index >= len(self.diff_rows):
            return

        row = self.diff_rows[row_index]
        l_idx = row['left_index']
        r_idx = row['right_index']
        
        if row['type'] == 'replace':
            self.left_lines[l_idx] = self.right_lines[r_idx]
        elif row['type'] == 'insert':
            insert_pos = 0
            found_anchor = False
            for i in range(row_index - 1, -1, -1):
                if self.diff_rows[i]['left_index'] is not None:
                    insert_pos = self.diff_rows[i]['left_index'] + 1
                    found_anchor = True
                    break
            self.left_lines.insert(insert_pos, self.right_lines[r_idx])
            
        elif row['type'] == 'delete':
            del self.left_lines[l_idx]

        self.calculate_diff()

    def merge_left_to_right(self, row_index):
        if row_index < 0 or row_index >= len(self.diff_rows):
            return

        row = self.diff_rows[row_index]
        l_idx = row['left_index']
        r_idx = row['right_index']

        if row['type'] == 'replace':
            self.right_lines[r_idx] = self.left_lines[l_idx]
        elif row['type'] == 'delete':
             insert_pos = 0
             found_anchor = False
             for i in range(row_index - 1, -1, -1):
                if self.diff_rows[i]['right_index'] is not None:
                    insert_pos = self.diff_rows[i]['right_index'] + 1
                    found_anchor = True
                    break
             self.right_lines.insert(insert_pos, self.left_lines[l_idx])
        elif row['type'] == 'insert':
            del self.right_lines[r_idx]
            
        self.calculate_diff()
        
    def merge_intra_line(self, row_index, opcode_index, direction):
        if row_index < 0 or row_index >= len(self.diff_rows):
            return
            
        row = self.diff_rows[row_index]
        if row['type'] != 'replace': 
            # Can only do intra-line merge on replace rows (where both lines exist)
            return
            
        ops = row['intra_diffs']
        if opcode_index < 0 or opcode_index >= len(ops):
            return
            
        op, i1, i2, j1, j2 = ops[opcode_index]
        
        # We need to apply this specific change to the target
        # If direction='pull' (Right->Left), we want Left to take Right's segment
        # If direction='push' (Left->Right), we want Right to take Left's segment
        
        if direction == 'pull_to_left': # Make Left match Right for this segment
            # Target is Left Line
            # We replace left_line[i1:i2] with right_line[j1:j2]
            original_left = self.left_lines[row['left_index']]
            replacement = self.right_lines[row['right_index']][j1:j2]
            new_left = original_left[:i1] + replacement + original_left[i2:]
            self.left_lines[row['left_index']] = new_left
            
        elif direction == 'push_to_right': # Make Right match Left for this segment
            # Target is Right Line
            # We replace right_line[j1:j2] with left_line[i1:i2]
            original_right = self.right_lines[row['right_index']]
            replacement = self.left_lines[row['left_index']][i1:i2]
            new_right = original_right[:j1] + replacement + original_right[j2:]
            self.right_lines[row['right_index']] = new_right
            
        self.calculate_diff()
