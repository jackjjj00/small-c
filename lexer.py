from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: object
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type!r}, {self.value!r}, line={self.line}, col={self.col})"


KEYWORDS = {
    "int", "char", "void",
    "if", "else", "while", "for", "do",
    "break", "continue", "return",
    "switch", "case", "default",
}

# 優先匹配的多字元運算子
MULTI_OPS = [
    "==", "!=", "<=", ">=",
    "&&", "||",
    "<<", ">>",
    "+=", "-=", "*=", "/=", "%=",
    "++", "--",
]

# 後續匹配的單字元運算子
SINGLE_OPS = set("{}[]();,+-*/%<>=!~&|^#:")

ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "\\": "\\",
    "'": "'",
    '"': '"',
}


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def current(self) -> str:
        if self.i >= len(self.source):
            return "\0"
        return self.source[self.i]

    def peek(self, n: int = 1) -> str:
        j = self.i + n
        if j >= len(self.source):
            return "\0"
        return self.source[j]

    def advance(self) -> str:
        ch = self.current()
        self.i += 1

        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        return ch

    def add(self, token_type: str, value: object, line: int, col: int):
        self.tokens.append(Token(token_type, value, line, col))

    def tokenize(self) -> list[Token]:
        while self.current() != "\0":
            ch = self.current()

            # 1. 處理空白與換行
            if ch.isspace():
                self.advance()
                continue

            # 2. 處理單行註解 //
            if ch == "/" and self.peek() == "/":
                self.skip_line_comment()
                continue

            # 3. 處理區塊註解 /* ... */
            if ch == "/" and self.peek() == "*":
                self.skip_block_comment()
                continue

            # 4. 處理標識符或關鍵字
            if ch.isalpha() or ch == "_":
                self.read_identifier_or_keyword()
                continue

            # 5. 處理數字字面量 (支援 10 進位與 16 進位)
            if ch.isdigit():
                self.read_number()
                continue

            # 6. 處理字串 "..."
            if ch == '"':
                self.read_string()
                continue

            # 7. 處理字元 '...'
            if ch == "'":
                self.read_char()
                continue

            # 8. 優先處理「多字元」運算子 (例如 +=, ==)
            matched = False
            for op in MULTI_OPS:
                if self.source.startswith(op, self.i):
                    line, col = self.line, self.col
                    for _ in op:
                        self.advance()
                    self.add("OP", op, line, col)
                    matched = True
                    break

            if matched:
                continue

            # 9. 最後處理「單字元」運算子 (例如 +, =)
            if ch in SINGLE_OPS:
                line, col = self.line, self.col
                self.advance()
                self.add("OP", ch, line, col)
                continue

            raise LexerError(f"Unexpected character {ch!r} at line {self.line}, col {self.col}")

        # 檔案結尾
        self.add("EOF", "", self.line, self.col)
        return self.tokens

    def skip_line_comment(self):
        while self.current() not in ("\n", "\0"):
            self.advance()

    def skip_block_comment(self):
        start_line, start_col = self.line, self.col

        self.advance()  # 跳過 '/'
        self.advance()  # 跳過 '*'

        while True:
            if self.current() == "\0":
                raise LexerError(f"Unterminated block comment at line {start_line}, col {start_col}")

            if self.current() == "*" and self.peek() == "/":
                self.advance()  # 跳過 '*'
                self.advance()  # 跳過 '/'
                break

            self.advance()

    def read_identifier_or_keyword(self):
        line, col = self.line, self.col
        start = self.i

        while self.current().isalnum() or self.current() == "_":
            self.advance()

        text = self.source[start:self.i]

        if text in KEYWORDS:
            self.add("KEYWORD", text, line, col)
        else:
            self.add("IDENT", text, line, col)

    def read_number(self):
        line, col = self.line, self.col

        # 16 進位處理 (如 0x10)
        if self.current() == "0" and self.peek().lower() == "x":
            self.advance()  # 跳過 '0'
            self.advance()  # 跳過 'x'
            start = self.i

            while self.current().isdigit() or self.current().lower() in "abcdef":
                self.advance()

            if start == self.i:
                raise LexerError(f"Invalid hex literal at line {line}, col {col}")

            text = self.source[start:self.i]
            # 修正：type 改為 "NUMBER"，value 直接存整數，與其他數字一致
            self.add("NUMBER", int(text, 16), line, col)
            return

        # 10 進位處理
        start = self.i
        while self.current().isdigit():
            self.advance()

        text = self.source[start:self.i]
        self.add("NUMBER", int(text), line, col)

    def read_string(self):
        line, col = self.line, self.col
        self.advance()  # 開頭雙引號
        chars = []

        while self.current() != '"':
            if self.current() == "\0" or self.current() == "\n":
                raise LexerError(f"Unterminated string at line {line}, col {col}")

            if self.current() == "\\":
                self.advance()
                esc = self.current()
                chars.append(ESCAPES.get(esc, esc))
                self.advance()
            else:
                chars.append(self.advance())

        self.advance()  # 結尾雙引號
        self.add("STRING", "".join(chars), line, col)

    def read_char(self):
        line, col = self.line, self.col
        self.advance()  # 開頭單引號

        if self.current() == "\\":
            self.advance()
            esc = self.current()
            ch = ESCAPES.get(esc, esc)
            self.advance()
        else:
            ch = self.advance()

        if self.current() != "'":
            raise LexerError(f"Invalid char literal at line {line}, col {col}")

        self.advance()  # 結尾單引號
        # 修正：type 改為 "CHAR"（原本就是），value 存 ord() 整數，讓 Parser 直接當數字用
        self.add("CHAR", ord(ch), line, col)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()