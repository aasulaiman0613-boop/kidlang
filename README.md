KidLang

KidLang is a small programming language built to teach how programming actually works.

It is designed for learning logic, structure, and problem solving without overwhelming syntax or hidden behavior.

KidLang does not try to replace Python.
It prepares you for Python by teaching the foundations clearly and explicitly.

Why KidLang exists

Many beginners struggle not because programming is hard, but because too much happens behind the scenes.

KidLang removes that confusion.

KidLang is:

Explicit instead of magical

Strict instead of forgiving

Small instead of complex

Educational instead of clever

Nothing happens unless you write it.
Mistakes are explained, not punished.

Who KidLang is for

KidLang is designed for:

Children learning programming for the first time

Teenagers who want to understand logic 

Adults who want a clean introduction to programming

Teachers who need a safe and controlled learning environment

What you can do with KidLang

With KidLang, you can:

Print messages

Ask the user questions

Store values in variables

Do math

Make decisions with if and else

Repeat actions with loops

See programs run step by step

Understand how programs actually execute

Quick start
Using the KidLang IDE (Windows)

Download the latest release

Open the dist folder

Double click the KidLang IDE executable

Write your code and press Run

Output appears in the black output panel

If your program asks for input, a small input box will appear.

No installation is required.

Using the command line
python kidlang.py example.kid

Example program
let name = ask("What is your name? ")
say("Hello " + name)

let x = 1
while x <= 5 do
  say(x)
  x = x + 1
end

How KidLang works (simple explanation)

Every KidLang program follows these steps:

Your code is read line by line

Each word and symbol is understood

A structure is built from your code

That structure is executed step by step

This is how real programming languages work internally.

Language basics
Comments

Comments are ignored by the language and are only for humans.

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
score = score + 1


You must create a variable before using it.
If you forget, KidLang explains how to fix the mistake.

User input

Use ask to get text from the user.

let name = ask("What is your name? ")
say("Hello " + name)


ask always returns text.

Numbers and math

KidLang supports standard math operators:

+ - * /

let x = 2 + 3 * 4
say(x)


Result:

14


Parentheses work as expected.

let y = (2 + 3) * 4
say(y)

True, false, and null

KidLang includes:

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

Use while to repeat actions until a condition becomes false.

let x = 1

while x <= 5 do
  say(x)
  x = x + 1
end


Make sure the condition changes inside the loop so it can stop.

Repeat loops (beginner friendly)

Use repeat when you know how many times something should run.

repeat 3 times
  say("Hello")
end


This is one of the easiest ways to learn loops.

Step mode (learning feature)

The KidLang IDE includes Step mode.

When Step mode is enabled:

The program pauses before each statement

You see what will run next

You see current variable values

This helps learners understand execution order and logic.

Errors that teach

KidLang error messages are written to help you learn.

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

This makes it safe for learning and classroom use.

What KidLang does not include (yet)

These features are intentionally not included:

User defined functions

Classes or objects

Lists or dictionaries

Imports or modules

This keeps the focus on fundamentals.

Learning path suggestion

Learn say and let

Learn math

Learn if and else

Learn repeat

Learn while

Use Step mode to understand execution

After this, Python will feel much easier.
