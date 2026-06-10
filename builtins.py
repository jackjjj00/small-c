# builtins.py
import math
import sys
import random


class BuildINFunction:
    def __init__(self, memory):
        self.memory = memory

    # ============================================================
    # 字串輔助（供內部使用）
    # ============================================================

    def read_str(self, addr):
        """從記憶體位址讀取以 null 結尾的字串"""
        chars = []
        while True:
            ch = self.memory.read_char(addr)
            if ch == 0:
                break
            chars.append(chr(ch))
            addr += 1
        return "".join(chars)

    def write_str(self, addr, s_string):
        """把 Python 字串寫入記憶體（含結尾 null byte）"""
        for char in s_string:
            self.memory.write_char(addr, ord(char))
            addr += 1
        self.memory.write_char(addr, 0)

    # ============================================================
    # I/O 函式
    # ============================================================

    def putchar(self, ch):
        sys.stdout.write(chr(int(ch)))
        sys.stdout.flush()
        return int(ch)

    def getchar(self):
        char = sys.stdin.read(1)
        if not char:
            return -1
        return ord(char)

    def puts(self, str_ptr):
        """puts：印出字串並換行"""
        print(self.read_str(str_ptr))
        return 1

    def printf(self, fmt_ptr, *args):
        """
        支援格式：%d %c %x %s %%
        回傳印出的字元數（與 C 標準一致）
        """
        fmt_str = self.read_str(fmt_ptr)
        result = []
        arg_idx = 0
        i = 0
        while i < len(fmt_str):
            if fmt_str[i] == '%' and i + 1 < len(fmt_str):
                spec = fmt_str[i + 1]
                if spec == '%':
                    result.append('%')
                elif arg_idx < len(args):
                    val = args[arg_idx]
                    arg_idx += 1
                    if spec == 'd':
                        result.append(str(int(val)))
                    elif spec == 'c':
                        result.append(chr(int(val) & 0xFF))
                    elif spec == 'x':
                        result.append(hex(int(val))[2:])
                    elif spec == 'X':
                        result.append(hex(int(val))[2:].upper())
                    elif spec == 's':
                        result.append(self.read_str(val))
                    else:
                        # 未知格式符，原樣保留
                        result.append(f'%{spec}')
                        arg_idx -= 1
                i += 2
            else:
                result.append(fmt_str[i])
                i += 1
        output = "".join(result)
        sys.stdout.write(output)
        sys.stdout.flush()
        return len(output)

    def scanf(self, fmt_ptr, *addr_args):
        """
        支援格式：%d %c
        從 stdin 讀取一行，以空白分割後依序寫入對應記憶體位址。
        回傳成功讀取的項目數。
        """
        fmt_str = self.read_str(fmt_ptr)
        try:
            user_inputs = input().split()
        except EOFError:
            return -1   # EOF

        arg_idx = 0
        i = 0
        while i < len(fmt_str) and arg_idx < len(user_inputs) and arg_idx < len(addr_args):
            if fmt_str[i] == '%' and i + 1 < len(fmt_str):
                spec = fmt_str[i + 1]
                val_str = user_inputs[arg_idx]
                addr = addr_args[arg_idx]
                if spec == 'd':
                    try:
                        self.memory.write_int(addr, int(val_str))
                    except ValueError:
                        break
                    arg_idx += 1
                elif spec == 'c':
                    self.memory.write_char(addr, ord(val_str[0]))
                    arg_idx += 1
                i += 2
            else:
                i += 1
        return arg_idx

    # ============================================================
    # 字串函式
    # ============================================================

    def strlen(self, str_ptr):
        return len(self.read_str(str_ptr))

    def strcpy(self, dest_ptr, src_ptr):
        src_str = self.read_str(src_ptr)
        self.write_str(dest_ptr, src_str)
        return dest_ptr

    def strcmp(self, s1_ptr, s2_ptr):
        s1 = self.read_str(s1_ptr)
        s2 = self.read_str(s2_ptr)
        if s1 < s2:   return -1
        elif s1 > s2: return 1
        return 0

    def strcat(self, dest_ptr, src_ptr):
        dest_str = self.read_str(dest_ptr)
        src_str = self.read_str(src_ptr)
        self.write_str(dest_ptr, dest_str + src_str)
        return dest_ptr

    def atoi(self, str_ptr):
        s = self.read_str(str_ptr).strip()
        try:
            return int(s)
        except ValueError:
            return 0

    def itoa(self, value, str_ptr):
        """把整數轉成字串寫入記憶體"""
        self.write_str(str_ptr, str(int(value)))
        return str_ptr

    # ============================================================
    # 數學函式
    # ============================================================

    def abs(self, x):
        return abs(int(x))

    def max(self, a, b):
        return a if a > b else b

    def min(self, a, b):
        return a if a < b else b

    def pow(self, base, exp):
        exp = int(exp)
        if exp < 0:  return 0
        if exp == 0: return 1
        return int(math.pow(int(base), exp))

    def sqrt(self, x):
        x = int(x)
        if x < 0:
            raise RuntimeError("Runtime error: sqrt() argument must be non-negative.")
        return int(math.sqrt(x))

    def mod(self, a, b):
        b = int(b)
        if b == 0:
            raise RuntimeError("Runtime error: division by zero.")
        return int(a) % b

    # ============================================================
    # 亂數
    # ============================================================

    def rand(self):
        """回傳 0 ~ 32767 的亂數（與 C 的 rand() 相符）"""
        return random.randint(0, 32767)

    def srand(self, seed):
        """設定亂數種子"""
        random.seed(int(seed))
        return 0

    # ============================================================
    # 程式控制
    # ============================================================

    def exit(self, code):
        print(f"\nProgram exited with return value {int(code)}.")
        sys.exit(int(code))