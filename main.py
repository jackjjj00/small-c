# main.py
print("=== 偵測到 main.py 開始執行 ===")
import os
import importlib.util
from memory import SystemMemory
from symtable import SymbolTable
from repl import REPL

# --- 核心修正：動態載入當前目錄下的 custom builtins.py，避免與 Python 標準庫衝突 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
builtins_path = os.path.join(current_dir, "builtins.py")

# 建立模組規格並載入
spec = importlib.util.spec_from_file_location("custom_builtins", builtins_path)
custom_builtins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(custom_builtins)

# 取得你寫的 BuildINFunction 類別
BuildINFunction = custom_builtins.BuildINFunction
# -------------------------------------------------------------------------

def main():
    memory = SystemMemory()
    symtable = SymbolTable()
    builtin = BuildINFunction(memory)
    repl = REPL(memory, symtable, builtin)
    repl.start()

if __name__ == "__main__":
    main()