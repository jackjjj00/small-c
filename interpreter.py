# ============================================================
# 控制流例外
# ============================================================

class BreakException(Exception): pass
class ContinueException(Exception): pass
class ReturnException(Exception):
    def __init__(self, value=None):
        self.value = value


# ============================================================
# Interpreter
# ============================================================

class Interpreter:
    def __init__(self, memory, symtable, builtins):
        self.memory = memory
        self.symtable = symtable
        self.builtins = builtins

    def visit(self, node):
        if node is None:
            return None

        node_type = type(node).__name__

        # ── 字面量 ──────────────────────────────────────────────
        if node_type == 'NumberNode':
            return node.value

        elif node_type == 'HexNode':
            return node.value

        # ── 一元運算 ─────────────────────────────────────────────
        elif node_type == 'UnaryOpNode':
            val = self.visit(node.expr)
            op = node.op.value
            if op == '-':  return -val
            elif op == '!': return 1 if val == 0 else 0
            elif op == '~': return ~val

        # ── 二元運算 ─────────────────────────────────────────────
        elif node_type == 'BinOpNode':
            left_val  = self.visit(node.left)
            right_val = self.visit(node.right)
            op = node.op.value
            if op == '+':   return left_val + right_val
            elif op == '-': return left_val - right_val
            elif op == '*': return left_val * right_val
            elif op == '/':
                if right_val == 0: raise RuntimeError("Runtime error: division by zero")
                return int(left_val / right_val)
            elif op == '%':
                if right_val == 0: raise RuntimeError("Runtime error: division by zero")
                return left_val % right_val
            elif op == '&':  return left_val & right_val
            elif op == '|':  return left_val | right_val
            elif op == '^':  return left_val ^ right_val
            elif op == '<<': return left_val << right_val
            elif op == '>>': return left_val >> right_val
            elif op == '>':  return 1 if left_val > right_val else 0
            elif op == '<':  return 1 if left_val < right_val else 0
            elif op == '==': return 1 if left_val == right_val else 0
            elif op == '!=': return 1 if left_val != right_val else 0
            elif op == '>=': return 1 if left_val >= right_val else 0
            elif op == '<=': return 1 if left_val <= right_val else 0
            elif op == '&&': return 1 if (left_val and right_val) else 0
            elif op == '||': return 1 if (left_val or right_val) else 0

        # ── 字串字面量 ───────────────────────────────────────────
        elif node_type == 'StringNode':
            str_len = len(node.value) + 1
            addr = self.memory.allocate(str_len)
            self.builtins.write_str(addr, node.value)
            return addr

        # ── 讀取變數 ─────────────────────────────────────────────
        elif node_type == 'VarNode':
            symbol = self.symtable.lookup(node.name)
            # 陣列名稱 = 第一個元素的位址（C 語義）
            if symbol.is_array:
                return symbol.address
            if symbol.data_type == 'char' and not symbol.is_pointer:
                return self.memory.read_char(symbol.address)
            return self.memory.read_int(symbol.address)

        # ── 陣列/字串讀取 arr[i] ─────────────────────────────────
        elif node_type == 'ArrayAccessNode':
            symbol = self.symtable.lookup(node.name)
            idx = self.visit(node.index_expr)
            # 越界檢查（只對陣列，不對指標）
            if symbol.is_array and symbol.array_size is not None and (idx < 0 or idx >= symbol.array_size):
                raise RuntimeError(
                    f"Runtime error: array index out of bounds (index {idx}, size {symbol.array_size})")
            # 指標 → 先讀取存的位址；陣列 → 直接用 symbol.address
            if symbol.is_pointer:
                base_addr = self.memory.read_int(symbol.address)
            else:
                base_addr = symbol.address
            elem_size = 1 if symbol.data_type == 'char' else 4
            elem_addr = base_addr + idx * elem_size
            if symbol.data_type == 'char' and not symbol.is_pointer:
                return self.memory.read_char(elem_addr)
            return self.memory.read_int(elem_addr)

        # ── 取址 &x ──────────────────────────────────────────────
        elif node_type == 'AddrOfNode':
            symbol = self.symtable.lookup(node.var_name)
            return symbol.address  # 回傳整數位址

        # ── 解參考讀取 *p ────────────────────────────────────────
        elif node_type == 'DerefNode':
            addr = self.visit(node.expr)
            return self.memory.read_int(addr)

        # ── 變數宣告 ─────────────────────────────────────────────
        elif node_type == 'VarDeclNode':
            if node.array_size is not None:
                # 陣列宣告
                count = self.visit(node.array_size)
                elem_size = 1 if node.data_type == 'char' else 4
                total = count * elem_size
                addr = self.memory.allocate(total)
                self.symtable.add_symbol(
                    node.name, node.data_type, addr,
                    size=total, is_array=1, array_size=count)
            else:
                # 一般變數或指標
                size = 4  # 指標也用 4 bytes 存位址
                addr = self.memory.allocate(size)
                self.symtable.add_symbol(
                    node.name, node.data_type, addr, size=size,
                    is_pointer=1 if node.is_pointer else 0)
                if node.init_expr is not None:
                    val = self.visit(node.init_expr)
                    if node.data_type == 'char' and not node.is_pointer:
                        self.memory.write_char(addr, val)
                    else:
                        self.memory.write_int(addr, val)
            return None

        # ── 一般賦值 ─────────────────────────────────────────────
        elif node_type == 'AssignNode':
            symbol = self.symtable.lookup(node.var_name)
            val = self.visit(node.expr)
            if symbol.data_type == 'char' and not symbol.is_pointer:
                self.memory.write_char(symbol.address, val)
            else:
                self.memory.write_int(symbol.address, val)
            return val

        # ── 陣列元素賦值 arr[i] = expr ───────────────────────────
        elif node_type == 'ArrayAssignNode':
            symbol = self.symtable.lookup(node.name)
            idx = self.visit(node.index_expr)
            # 越界檢查（只對陣列，不對指標）
            if symbol.is_array and symbol.array_size is not None and (idx < 0 or idx >= symbol.array_size):
                raise RuntimeError(
                    f"Runtime error: array index out of bounds (index {idx}, size {symbol.array_size})")
            val = self.visit(node.expr)
            # 指標 → 先讀取存的位址；陣列 → 直接用 symbol.address
            if symbol.is_pointer:
                base_addr = self.memory.read_int(symbol.address)
            else:
                base_addr = symbol.address
            elem_size = 1 if symbol.data_type == 'char' else 4
            elem_addr = base_addr + idx * elem_size
            if symbol.data_type == 'char' and not symbol.is_pointer:
                self.memory.write_char(elem_addr, val)
            else:
                self.memory.write_int(elem_addr, val)
            return val

        # ── 解參考賦值 *p = expr ─────────────────────────────────
        elif node_type == 'DerefAssignNode':
            addr = self.visit(node.ptr_expr)
            val = self.visit(node.expr)
            self.memory.write_int(addr, val)
            return val

        # ── 複合賦值 ─────────────────────────────────────────────
        elif node_type == 'CompoundAssignNode':
            symbol = self.symtable.lookup(node.var_name)
            if symbol.data_type == 'char' and not symbol.is_pointer:
                old_val = self.memory.read_char(symbol.address)
            else:
                old_val = self.memory.read_int(symbol.address)
            rhs = self.visit(node.expr)
            op = node.op.value if hasattr(node.op, 'value') else node.op
            if op == '+=':    new_val = old_val + rhs
            elif op == '-=':  new_val = old_val - rhs
            elif op == '*=':  new_val = old_val * rhs
            elif op == '/=':
                if rhs == 0: raise RuntimeError("Runtime error: division by zero")
                new_val = int(old_val / rhs)
            elif op == '%=':
                if rhs == 0: raise RuntimeError("Runtime error: division by zero")
                new_val = old_val % rhs
            elif op == '&=':   new_val = old_val & rhs
            elif op == '|=':   new_val = old_val | rhs
            elif op == '^=':   new_val = old_val ^ rhs
            elif op == '<<=':  new_val = old_val << rhs
            elif op == '>>=':  new_val = old_val >> rhs
            else:
                raise RuntimeError(f"Runtime error: Unknown compound operator '{op}'")
            if symbol.data_type == 'char' and not symbol.is_pointer:
                self.memory.write_char(symbol.address, new_val)
            else:
                self.memory.write_int(symbol.address, new_val)
            return new_val

        # ── 後綴 i++ / i-- ───────────────────────────────────────
        elif node_type == 'PostfixOpNode':
            symbol = self.symtable.lookup(node.var_name)
            if symbol.data_type == 'char' and not symbol.is_pointer:
                old_val = self.memory.read_char(symbol.address)
            else:
                old_val = self.memory.read_int(symbol.address)
            new_val = old_val + 1 if node.op == '++' else old_val - 1
            if symbol.data_type == 'char' and not symbol.is_pointer:
                self.memory.write_char(symbol.address, new_val)
            else:
                self.memory.write_int(symbol.address, new_val)
            return old_val

        # ── 函式呼叫 ─────────────────────────────────────────────
        elif node_type == 'FuncCallNode':
            args_vals = [self.visit(arg) for arg in node.args]
            if node.func_name in self.symtable.functions:
                return self._call_user_func(node.func_name, args_vals)
            if hasattr(self.builtins, node.func_name):
                func = getattr(self.builtins, node.func_name)
                if node.func_name == 'printf':
                    self.builtins.printf(args_vals[0], *args_vals[1:])
                    return 0
                else:
                    return func(*args_vals)
            raise RuntimeError(f"Runtime error: Unknown function '{node.func_name}'")

        # ── 函式定義 ─────────────────────────────────────────────
        elif node_type == 'FuncDefNode':
            self.symtable.functions[node.name] = node
            return None

        # ── 區塊 ────────────────────────────────────────────────
        elif node_type == 'BlockNode':
            self.symtable.enter_block()
            result = None
            try:
                for stmt in node.statements:
                    result = self.visit(stmt)
            finally:
                self.symtable.exit_block()
            return result

        # ── return ───────────────────────────────────────────────
        elif node_type == 'ReturnNode':
            val = self.visit(node.expr) if node.expr is not None else None
            raise ReturnException(val)

        # ── break / continue ─────────────────────────────────────
        elif node_type == 'BreakNode':    raise BreakException()
        elif node_type == 'ContinueNode': raise ContinueException()

        # ── if / else ────────────────────────────────────────────
        elif node_type == 'IfNode':
            cond = self.visit(node.condition)
            if cond:    return self.visit(node.then_block)
            elif node.else_block: return self.visit(node.else_block)
            return None

        # ── switch ───────────────────────────────────────────────
        elif node_type == 'SwitchNode':
            switch_val = self.visit(node.expr)
            matched = False
            try:
                for case_val_node, stmts in node.cases:
                    if not matched and self.visit(case_val_node) == switch_val:
                        matched = True
                    if matched:
                        for s in stmts: self.visit(s)
                if not matched and node.default_stmts:
                    for s in node.default_stmts: self.visit(s)
            except BreakException:
                pass
            return None

        # ── while ────────────────────────────────────────────────
        elif node_type == 'WhileNode':
            while self.visit(node.condition):
                try:    self.visit(node.body)
                except BreakException:    break
                except ContinueException: continue
            return None

        # ── do...while ───────────────────────────────────────────
        elif node_type == 'DoWhileNode':
            while True:
                try:    self.visit(node.body)
                except BreakException:    break
                except ContinueException: pass
                if not self.visit(node.condition): break
            return None

        # ── for ──────────────────────────────────────────────────
        elif node_type == 'ForNode':
            self.visit(node.init)
            while True:
                if node.condition is not None and not self.visit(node.condition): break
                try:    self.visit(node.body)
                except BreakException:    break
                except ContinueException: pass
                if node.update: self.visit(node.update)
            return None

        raise RuntimeError(f"Runtime error: Unknown AST node type '{node_type}'")

    # ── 使用者自定義函式 ─────────────────────────────────────────
    def _call_user_func(self, func_name, args_vals):
        func_node = self.symtable.functions[func_name]
        self.symtable.enter_function()
        for (p_type, p_name, p_is_ptr), p_val in zip(func_node.params, args_vals):
            size = 4
            addr = self.memory.allocate(size)
            self.symtable.add_symbol(p_name, p_type, addr, size=size,
                                     is_pointer=1 if p_is_ptr else 0)
            self.memory.write_int(addr, p_val)
        ret_val = None
        try:
            self.visit(func_node.body)
        except ReturnException as e:
            ret_val = e.value
        finally:
            self.symtable.exit_function()
        return ret_val