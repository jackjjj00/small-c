class Symbol:
    def __init__(self, name, data_type, address, size=1, is_array=0, is_pointer=0, array_size=None):
        self.name = name
        self.data_type = data_type
        self.address = address
        self.size = size
        self.is_array = is_array
        self.is_pointer = is_pointer
        self.array_size = array_size  # 陣列元素個數（非 None 表示是陣列）


class SymbolTable:
    def __init__(self):
        self.global_scope = {}
        # scope_stack：每個元素是一個 dict，代表一層 local scope
        # 空 stack 表示目前在全域
        self.scope_stack = []
        self.functions = {}

    # ── 函式呼叫進入 / 離開 ──────────────────────────────────────
    def enter_function(self):
        """進入函式時 push 一個新的 scope（支援遞迴）"""
        self.scope_stack.append({})

    def exit_function(self):
        """離開函式時 pop scope"""
        if self.scope_stack:
            self.scope_stack.pop()

    # ── Block scope 進入 / 離開（用於 while/for body 等）──────────
    def enter_block(self):
        """進入 { } block 時 push 一個新的 scope"""
        self.scope_stack.append({})

    def exit_block(self):
        """離開 block 時 pop scope"""
        if self.scope_stack:
            self.scope_stack.pop()

    # ── 查詢目前的 local scope（最頂層）───────────────────────────
    @property
    def local_scope(self):
        return self.scope_stack[-1] if self.scope_stack else None

    # ── 新增符號 ─────────────────────────────────────────────────
    def add_symbol(self, name, data_type, address, size=1, is_array=0, is_pointer=0, array_size=None):
        cur_scope = self.local_scope if self.local_scope is not None else self.global_scope
        if name in cur_scope:
            raise RuntimeError(f"Semantic error: Variable '{name}' already declared in this scope.")
        symbol = Symbol(name, data_type, address, size, is_array, is_pointer, array_size)
        cur_scope[name] = symbol
        return symbol

    # ── 查找符號（由內到外逐層查詢）─────────────────────────────
    def lookup(self, name):
        # 從最頂層 scope 向下找
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        if name in self.global_scope:
            return self.global_scope[name]
        raise RuntimeError(f"Semantic error: Variable '{name}' is undeclared.")

    # ── 重置 ─────────────────────────────────────────────────────
    def reset(self):
        self.global_scope = {}
        self.scope_stack = []
        self.functions = {}