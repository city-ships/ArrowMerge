from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class LatexHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Formats
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0033cc")) # Blue for commands
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080")) # Gray for comments
        comment_format.setFontItalic(True)
        
        math_format = QTextCharFormat()
        math_format.setForeground(QColor("#006600")) # Green for math

        # Rules
        # 1. LaTeX Commands: \whatever
        self.highlighting_rules.append((QRegularExpression(r"\\[a-zA-Z]+"), keyword_format))
        
        # 2. Math: $...$ (simplistic single line)
        self.highlighting_rules.append((QRegularExpression(r"\$.*?\$"), math_format))
        
        # 3. Comments: % ... (captured till end of line)
        self.highlighting_rules.append((QRegularExpression(r"%.*"), comment_format))

    def highlightBlock(self, text):
        try:
            for pattern, format in self.highlighting_rules:
                match_iterator = pattern.globalMatch(text)
                while match_iterator.hasNext():
                    match = match_iterator.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), format)
        except Exception:
            # Robustness: Do not crash on highlighting errors
            pass
