# Lisp Interpreter — Final Project for MIT 6.101: Fundamentals of Programming

This is a complete Python-based interpreter for a Scheme-like Lisp dialect, built as the **final project for MIT 6.101 (Fundamentals of Programming)**. The interpreter parses and evaluates Scheme expressions, handles user-defined functions, and supports special forms like `let`, `set!`, and `del`.

## 🧠 Features

- Full support for:
  - Arithmetic and boolean operations
  - Proper lists using `cons`, `car`, `cdr`, `list`, and `append`
  - Logical constructs: `if`, `and`, `or`, `begin`
  - Lexical scoping and user-defined functions via `define` and `lambda`
  - Variable mutation and deletion with `set!` and `del`
  - Scoped variable declarations using `let`
- Custom error classes for robust debugging
- REPL interface and `.scm` file loader

## ✅ Completed Milestones

- ✅ Parsing and tokenization
- ✅ Recursive evaluation
- ✅ Support for built-in and user-defined functions
- ✅ Custom special forms
- ✅ Passes all MIT 6.101 test cases, including edge cases and deep nesting



```bash
python3 lab.py test_inputs/your_file.scm
