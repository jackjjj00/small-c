# Small-C 互動式解譯器

## 專題簡介

本專題使用 Python 實作一個 Small-C 互動式解譯器。使用者可以在 `sc>` 環境中直接輸入程式碼，也可以用 `APPEND` 建立多行程式，再透過 `RUN` 執行。

---

## 執行環境

- Python 3.10 以上
- Windows / macOS / Linux 皆可執行

---

## 檔案結構

```text
main.py           程式進入點
repl.py           互動式指令環境
lexer.py          詞法分析器
parser.py         語法分析器
interpreter.py    執行引擎
symtable.py       符號表管理
memory.py         記憶體與指標模型
builtins.py       內建函式
test_a.sc         測試程式
README.md         專案說明
```

---

## 執行方式

```powershell
cd D:\smallc_final_spec_version\smallc_final_spec_version
python main.py
```

啟動後會看到：

```text
sc>
```

---

## 支援的互動指令

```text
ABOUT
HELP
APPEND
LIST
EDIT
DELETE
INSERT
CHECK
RUN
SAVE
LOAD
NEW
TRACE ON / TRACE OFF
VARS
FUNCS
CLEAR
QUIT / EXIT
```

---

## 支援的 Small-C 功能

- `int`、`char`
- 變數宣告與指定
- 算術、關係、邏輯、位元運算
- `if / else`
- `while`、`for`、`do while`
- `break`、`continue`
- 一維陣列
- 指標 `&`、`*`
- 函式定義與呼叫
- 遞迴
- `#define` 常數
- 註解
- 基本錯誤處理

---

## 內建函式

```text
printf
strlen
strcpy
strcat
strcmp
atoi
itoa
abs
max
min
pow
sqrt
rand
srand
```

---

## 測試方式

進入解譯器後輸入：

```text
LOAD test_a.sc
RUN
```

預期輸出：

```text
Original: 64 25 12 22 11 90 45 33
Max = 90
Min = 11
Sum = 302
Avg = 37
Sorted:   11 12 22 25 33 45 64 90
Program exited with return value 0.
```

---

## 操作範例

```c
int x = 25;
int y = -18;
printf("abs(%d) = %d\n", y, abs(y));
```

輸出：

```text
abs(-18) = 18
```

---

## 目前限制

本專題是 Small-C 教學版解譯器，並非完整 C 編譯器，因此不支援：

```text
float
double
struct
union
enum
typedef
多維陣列
完整標準 C 函式庫
```

---

## 作者資訊

```text
作者：TODO
課程：系統軟體 System Software
學期：Spring 2026
專題名稱：Small-C 互動式解譯器
```
# small-c
