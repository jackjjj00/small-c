# repl.py
import sys
import re
import lexer
from parser import Parser
from interpreter import Interpreter

EXPR_NODE_TYPES = ('BinOpNode', 'UnaryOpNode', 'NumberNode', 'HexNode')


class REPL:
    def __init__(self, memory, symtable, builtins):
        self.memory = memory
        self.symtable = symtable
        self.builtins = builtins
        self.buffer = [""]
        self.trace_mode = False
        self._pending_lines = []
        self._brace_depth = 0
        self._defines = {}

    # ============================================================
    # #define 預處理
    # ============================================================

    def _handle_define(self, line: str) -> bool:
        stripped = line.strip()
        m = re.match(r'^#\s*define\s+([A-Za-z_]\w*)\s*(.*)', stripped)
        if m:
            name = m.group(1)
            value = m.group(2).strip() or '1'
            self._defines[name] = value
            return True
        if stripped.startswith('#'):
            return True
        return False

    def _apply_defines(self, code: str) -> str:
        for name, value in self._defines.items():
            code = re.sub(r'\b' + re.escape(name) + r'\b', value, code)
        return code

    # ============================================================
    # 大括號計數（跳過字串、字元、// 註解）
    # ============================================================

    @staticmethod
    def _count_braces(line: str) -> int:
        depth = 0
        in_str = False
        in_char = False
        i = 0
        while i < len(line):
            ch = line[i]
            if not in_str and not in_char and ch == '/' and i + 1 < len(line) and line[i+1] == '/':
                break
            if (in_str or in_char) and ch == '\\':
                i += 2
                continue
            if ch == '"' and not in_char:
                in_str = not in_str
            elif ch == "'" and not in_str:
                in_char = not in_char
            elif not in_str and not in_char:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
            i += 1
        return depth

    # ============================================================
    # 執行一段程式碼（自動呼叫 main）
    # ============================================================

    def _execute(self, code: str):
        code = self._apply_defines(code)

        if self.trace_mode:
            print(f"\n[Debug] 準備執行:\n{code}")

        tokens = lexer.tokenize(code)

        if not tokens or (len(tokens) == 1 and tokens[0].type == 'EOF'):
            return

        if self.trace_mode:
            print(f"[Debug] Tokens: {tokens}")

        parser_obj = Parser(tokens)
        stmts = parser_obj.parse_program()

        if self.trace_mode:
            for s in stmts:
                print(f"[Debug] AST: {type(s).__name__}")

        interp = Interpreter(self.memory, self.symtable, self.builtins)

        for ast_root in stmts:
            result = interp.visit(ast_root)
            if result is not None and type(ast_root).__name__ in EXPR_NODE_TYPES:
                print(result)

        # 若這段程式碼定義了 main，且 main 尚未被呼叫，自動呼叫
        if 'main' in self.symtable.functions:
            interp._call_user_func('main', [])
            # 呼叫完後從函式表移除，避免下次又重複呼叫
            del self.symtable.functions['main']

    # ============================================================
    # REPL 主迴圈
    # ============================================================

    def start(self):
        print("Small-C Interactive Interpreter v3.0")
        print("System Software Final Project, 2026")
        print("Type 'HELP' for a list of commands.\n")

        while True:
            try:
                prompt = ("  " * self._brace_depth + ".. ") if self._brace_depth > 0 else "sc> "
                line = input(prompt)

                if not line.strip():
                    if self._brace_depth > 0:
                        self._pending_lines.append(line)
                    continue

                if self._brace_depth == 0:
                    if self._handle_define(line):
                        continue

                    cmd_parts = line.split()
                    main_cmd = cmd_parts[0].upper()

                    if main_cmd in ("QUIT", "EXIT"):
                        print("Goodbye.")
                        break

                    elif main_cmd == "NEW":
                        self.buffer = [""]
                        self.memory.reset()
                        self.symtable.reset()
                        self._pending_lines = []
                        self._brace_depth = 0
                        self._defines = {}
                        print("All cleared.")
                        continue

                    elif main_cmd == "APPEND":
                        print("Entering append mode. Type '.' on a blank line to exit.")
                        current_line_num = len(self.buffer)
                        while True:
                            sub_line = input(f"{current_line_num}> ")
                            if sub_line.strip() == ".":
                                break
                            self.buffer.append(sub_line)
                            current_line_num += 1
                        continue

                    elif main_cmd == "LIST":
                        if len(self.buffer) <= 1:
                            print("Buffer is empty.")
                        else:
                            for idx in range(1, len(self.buffer)):
                                print(f"  {idx}: {self.buffer[idx]}")
                        continue

                    elif main_cmd == "RUN":
                        if len(self.buffer) <= 1:
                            print("Buffer is empty.")
                        else:
                            code = "\n".join(self.buffer[1:])
                            try:
                                self._execute(code)
                            except Exception as e:
                                print(e)
                        continue

                    elif main_cmd == "TRACE":
                        if len(cmd_parts) > 1 and cmd_parts[1].upper() == "ON":
                            self.trace_mode = True
                            print("Trace mode enabled.")
                        elif len(cmd_parts) > 1 and cmd_parts[1].upper() == "OFF":
                            self.trace_mode = False
                            print("Trace mode disabled.")
                        continue

                delta = self._count_braces(line)

                if self._brace_depth > 0 or delta > 0:
                    self._pending_lines.append(line)
                    self._brace_depth += delta
                    if self._brace_depth == 0:
                        code = "\n".join(self._pending_lines)
                        self._pending_lines = []
                        try:
                            self._execute(code)
                        except Exception as e:
                            print(e)
                else:
                    try:
                        self._execute(line)
                    except Exception as e:
                        print(e)

            except KeyboardInterrupt:
                if self._brace_depth > 0:
                    print("\n[已取消多行輸入]")
                    self._pending_lines = []
                    self._brace_depth = 0
                else:
                    print("\nUse 'QUIT' or 'EXIT' to exit.")
            except EOFError:
                print("\nGoodbye.")
                break