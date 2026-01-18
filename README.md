KidLang

A small programming language made for learning how to think like a programmer

What is KidLang

KidLang is a beginner friendly programming language designed to teach logic, structure, and problem solving without overwhelming syntax.

It was built to feel simple like Python and Luau, but stricter and clearer so learners understand what is really happening.

KidLang is not meant to replace Python.
It is meant to teach the foundations so moving to Python later feels natural.

Who KidLang is for

KidLang is designed for:

Children learning programming for the first time

Teenagers who want to understand logic, not just copy code

Adults who want a clean and simple introduction

Teachers who want a safe, controlled learning environment


What you can do with KidLang

With KidLang, you can:

Print messages

Ask the user questions

Store values in variables

Do math

Make decisions with if / else

Repeat actions with loops

See step by step execution

Learn how programs actually run

How KidLang works (simple explanation)

Every KidLang program goes through these steps:

Your code is read line by line

The language understands each word and symbol

It builds a structure of what you meant

It runs that structure step by step

This is how real programming languages work internally.

Running KidLang

If you are using the KidLang IDE app:

Open the kidlang file

go to dist

and double click on the exe or pin it to taskbar

once the app is opened write your code and press run and see the output in the black box

If your program asks a question, a small input box will appear.

You do not need to install anything else.

The KidLang language guide
Comments

Comments are ignored by the language. They are for humans.

# This is a comment
-- This is also a comment

Printing output

Use say to print text or values.

say("Hello")
say(1, 2, "three")


Output:

Hello
1 2 three

Variables

Create a variable using let.

let score = 0


Update an existing variable like this:

score = score + 1


Important rule:
You must create a variable before using it.
If you forget, KidLang explains how to fix it.

Asking the user for input

Use ask to get text from the user.

let name = ask("What is your name? ")
say("Hello " + name)


ask always returns text.

Numbers and math

Supported math operators:

+ add

- subtract

* multiply

/ divide

Examples:

let x = 2 + 3 * 4
say(x)


Result:

14


Parentheses work as expected.

let y = (2 + 3) * 4
say(y)

Strings

Strings are text inside quotes.

say("Hello world")


You can combine text and numbers using +.

let age = 10
say("Age: " + age)

True, false, and null

KidLang supports:

true
false
null


These are used in conditions and logic.

If and else

Use if to make decisions.

let score = 80

if score >= 60 then
  say("Pass")
else
  say("Fail")
end


Rules:

then starts the block

end always closes the block

While loops

Use while when something should repeat until a condition becomes false.

let x = 1

while x <= 5 do
  say(x)
  x = x + 1
end


Be careful to change the variable inside the loop so it can stop.

KidLang protects against infinite loops.

Repeat loops (very beginner friendly)

Use repeat when you know how many times something should run.

repeat 3 times
  say("Hello")
end


This is one of the easiest ways to learn loops.

Step mode (learning feature)

In the IDE, you can enable Step mode.

When Step mode is on:

The program pauses before each statement

You can see what is about to run

You can see current variable values

This is extremely useful for learning how programs execute.

Errors that teach

KidLang errors are written to help you learn, not to scare you.

Example:

You used 'x' before creating it.
Fix: write `let x = ...` first.


The goal is to explain what went wrong and how to fix it.

Safety rules

KidLang is intentionally limited.

It cannot:

Access files

Access the internet

Modify your computer

Run system commands

This makes it safe for learning.

What KidLang does not include (yet)

These features are intentionally not included:

User defined functions

Classes or objects

Lists or dictionaries

Imports or modules

This keeps the language focused on fundamentals.

Why KidLang is different

KidLang is:

Explicit instead of magical

Strict instead of forgiving

Small instead of complex

Educational instead of clever

It is designed to teach how programming really works.

Folder structure (for developers)

If you explore the source code:

kidlang/
  kid_lexer.py
  parser.py
  ast_nodes.py
  interpreter.py
  kidlang.py
  kidlang_ide.py
  tests/


Each file has a clear responsibility.

Learning path suggestion

Learn say and let

Learn math

Learn if / else

Learn repeat

Learn while

Use Step mode to understand execution

After this, Python will feel much easier.

Final note

KidLang was built to remove fear from programming.

If something feels confusing, slow down, read the code, and step through it.

Programming is not about typing fast.
It is about thinking clearly.
