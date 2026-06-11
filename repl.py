# repl.py
import sys
import os
import re
import lexer
from parser import Parser
from interpreter import Interpreter

EXPR_NODE_TYPES = ('BinOpNode', 'UnaryOpNode', 'NumberNode', 'HexNode')

HELP_TEXT = """
Available commands:
  HELP                  顯示此說明
  NEW                   清除緩衝區、記憶體、符號表與巨集表
  CLEAR                 同 NEW
  APPEND                進入附加模式，輸入 '.' 結束
  LIST                  列出緩衝區所有程式行
  EDIT <n> <code>       修改緩衝區第 n 行
  DELETE <n>            刪除緩衝區第 n 行
  RUN                   執行緩衝區內所有程式
  SAVE <filename>       將緩衝區存入檔案
  LOAD <filename>       從檔案載入程式到緩衝區
  FUNCTION              列出目前已定義的函式
  TRACE ON|OFF          開啟或關閉 Debug 追蹤模式
  QUIT / EXIT           離開直譯器
"""


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

        # 若這段程式碼定義了 main，自動呼叫後移除，避免下次重複執行
        if 'main' in self.symtable.functions:
            interp._call_user_func('main', [])
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

                # ── 空行處理 ─────────────────────────────────────
                if not line.strip():
                    if self._brace_depth > 0:
                        self._pending_lines.append(line)
                    continue

                # ── 累積模式中不解析指令 ──────────────────────────
                if self._brace_depth == 0:
                    if self._handle_define(line):
                        continue

                    cmd_parts = line.split()
                    main_cmd = cmd_parts[0].upper()

                    # ── QUIT / EXIT ───────────────────────────────
                    if main_cmd in ("QUIT", "EXIT"):
                        print("Goodbye.")
                        break

                    # ── HELP ─────────────────────────────────────
                    elif main_cmd == "HELP":
                        print(HELP_TEXT)
                        continue

                    # ── NEW / CLEAR ───────────────────────────────
                    elif main_cmd in ("NEW", "CLEAR"):
                        self.buffer = [""]
                        self.memory.reset()
                        self.symtable.reset()
                        self._pending_lines = []
                        self._brace_depth = 0
                        self._defines = {}
                        print("All cleared.")
                        continue

                    # ── APPEND ────────────────────────────────────
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

                    # ── LIST ──────────────────────────────────────
                    elif main_cmd == "LIST":
                        if len(self.buffer) <= 1:
                            print("Buffer is empty.")
                        else:
                            for idx in range(1, len(self.buffer)):
                                print(f"  {idx}: {self.buffer[idx]}")
                        continue

                    # ── EDIT <n> <code> ───────────────────────────
                    elif main_cmd == "EDIT":
                        if len(cmd_parts) < 3:
                            print("Usage: EDIT <line_number> <new_code>")
                        else:
                            try:
                                n = int(cmd_parts[1])
                                new_code = " ".join(cmd_parts[2:])
                                if 1 <= n < len(self.buffer):
                                    self.buffer[n] = new_code
                                    print(f"Line {n} updated.")
                                else:
                                    print(f"Error: Line {n} does not exist.")
                            except ValueError:
                                print("Error: Line number must be an integer.")
                        continue

                    # ── DELETE <n> ────────────────────────────────
                    elif main_cmd == "DELETE":
                        if len(cmd_parts) < 2:
                            print("Usage: DELETE <line_number>")
                        else:
                            try:
                                n = int(cmd_parts[1])
                                if 1 <= n < len(self.buffer):
                                    removed = self.buffer.pop(n)
                                    print(f"Line {n} deleted: {removed}")
                                else:
                                    print(f"Error: Line {n} does not exist.")
                            except ValueError:
                                print("Error: Line number must be an integer.")
                        continue

                    # ── RUN ───────────────────────────────────────
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

                    # ── SAVE <filename> ───────────────────────────
                    elif main_cmd == "SAVE":
                        if len(cmd_parts) < 2:
                            print("Usage: SAVE <filename>")
                        else:
                            filename = cmd_parts[1]
                            if len(self.buffer) <= 1:
                                print("Buffer is empty, nothing to save.")
                            else:
                                try:
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        f.write("\n".join(self.buffer[1:]))
                                    print(f"Saved to '{filename}' ({len(self.buffer)-1} lines).")
                                except Exception as e:
                                    print(f"Error saving file: {e}")
                        continue

                    # ── LOAD <filename> ───────────────────────────
                    elif main_cmd == "LOAD":
                        if len(cmd_parts) < 2:
                            print("Usage: LOAD <filename>")
                        else:
                            filename = cmd_parts[1]
                            if not os.path.exists(filename):
                                print(f"Error: File '{filename}' not found.")
                            else:
                                try:
                                    with open(filename, 'r', encoding='utf-8') as f:
                                        lines = f.read().splitlines()
                                    self.buffer = [""] + lines
                                    print(f"Loaded '{filename}' ({len(lines)} lines). Use RUN to execute.")
                                except Exception as e:
                                    print(f"Error loading file: {e}")
                        continue

                    # ── FUNCTION ──────────────────────────────────
                    elif main_cmd == "FUNCTION":
                        if not self.symtable.functions:
                            print("No user-defined functions.")
                        else:
                            print("Defined functions:")
                            for fname, fnode in self.symtable.functions.items():
                                params = ", ".join(
                                    f"{p[0]}{'*' if p[2] else ''} {p[1]}"
                                    for p in fnode.params
                                )
                                print(f"  {fnode.return_type} {fname}({params})")
                        continue

                    # ── TRACE ON / OFF ────────────────────────────
                    elif main_cmd == "TRACE":
                        if len(cmd_parts) > 1 and cmd_parts[1].upper() == "ON":
                            self.trace_mode = True
                            print("Trace mode enabled.")
                        elif len(cmd_parts) > 1 and cmd_parts[1].upper() == "OFF":
                            self.trace_mode = False
                            print("Trace mode disabled.")
                        else:
                            print("Usage: TRACE ON | TRACE OFF")
                        continue

                # ── 大括號計數，決定是否累積 ──────────────────────
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