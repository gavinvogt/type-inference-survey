# Overview
This repository contains my Python implementations of topics discussed in
my literary survey of type inference. It can infer the types of functions written in &mu;ML, which is defined below.

## `type-inference/`

This folder contains an implementation of Wand's algorithm in the `type_inference.py` file. It parses the function definitions written in &mu;ML files in `tests/` using the parser code defined in `microml/`. It annotates the AST with types, generates the appropriate type equations, and unifies them using the `unify` procedure defined in `type_unification.py`.

## `unification/`

This folder contains various implementations of unification from the papers by Robinson (1965) and Martelli & Montanari (1982).


<!-- <table>
<tr>
  <td>&lt;program&gt;</td>
  <td>::=</td>
  <td><span style="color:magenta">{</span> &lt;statement&gt; <span style="color:magenta">}</span></td>
</tr>

<tr>
  <td>&lt;statement&gt;</td>
  <td>::=</td>
  <td><span style="color:magenta">(</span> &lt;func_def&gt; <span style="color:magenta">|</span> &lt;expr&gt; <span style="color:magenta">)</span> ;
  </td>
</tr>

<tr>
</tr>
</table> -->

# &mu;ML

&mu;ML is a basic subset of ML. It contains *if* and *let* expressions, anonymous *fn* functions, and operators such as `+` and `<`. It is used as a toy functional language for performing type inference.

## EBNF Syntax

```
<program>    ::=  { <func_def> }
<func_def>   ::=  "fun" <ID> <params> "=" <expr>;
<params>     ::=  { <ID> }
<expr>       ::=  <if_expr> | <let_expr> | <fn_expr> | <expr0>
<if_expr>    ::=  "if" <expr> "then" <expr> "else" <expr>
<let_expr>   ::=  "let" <ID> "=" <expr> "in" <expr>
<fn_expr>    ::=  "fn" <params> "=>" <expr>
<expr0>      ::=  <expr1> { "or" <expr1> }
<expr1>      ::=  <expr2> { "and" <expr2> }
<expr2>      ::=  <expr3> [ ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) <expr3> ]
<expr3>      ::=  <expr4> [ ( "+" | "-" ) <expr4> ]
<expr4>      ::=  <expr5> [ ( "*" | "/" ) <expr5> ]
<expr5>      ::=  { "-" | "not" } <expr6>
<expr6>      ::=  <int> | <real> | <bool> | <ID> | "(" [ <expr> ] ")" | <func_call>
<func_call>  ::=  <expr6> { <expr6> }
```

## Example
```
fun fib n = if n == 1 then 1
    else if n == 2 then 1
    else fib(n - 2) + fib(n - 1);

fun f = let addTwo = fn x => x + 2
    in addTwo 5;
```