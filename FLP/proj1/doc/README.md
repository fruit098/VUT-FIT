# FLP(2021) 1.Project: rv-2-rka
 Project aim is to parse regular expression into extended finite-state machine. The format of input and output is specified in the assigment.

# Build
Use the `make` command in order to compile the project via ghc, the compilation should result in binary file named `rv-2-rka`.

# Run
Binary file can be run as follows:
`./rv-2-rka (-i|-t) [file]` 
The `-i` flag will result in printing the internal representation of regex on the stdout. The `-t` flag will result in printing the extended finite-state machine that is acpeting same language as input regex. In case of missing file the stdin is read.

# Description

Firstly, the whitespace characters are removed from the input string, then the string is parsed via Parsec library into the Regex datatype that reflects the non-terminals in regex parsing rules.
These are the parsing rules for regular expression.

`
--regex -> term regexRest
--regexRest ->  '+' term regexRest | endOfRules
--term -> factor termRest
--termRest -> factor termRest | endOfRules
--factor -> atom | atom '*'
--atom -> '(' regex ')' | character | endOfRules
--character -> 'a' | 'b' | 'c' | ... | 'z' | '#'
`

In case the input is not parsed, the entered regex is consider invalid.
Otherwise, the Regex datatype is constructed and can be used for printing or transformed into the extended finite-state machine(EFSM).
The main idea of the transformation from regex into the EFSM is taken from TIN [scripts](http://www.fit.vutbr.cz/study/courses/TIN/public/Texty/TIN-studijni-text.pdf), starting the page 42. 

The source code logic is divided into the files:
* Main.hs: The main module responsible for parsing the arguments and reading the input from file/stdin and calling other function defined in Regex.hs. 
* Regex.hs: The module that takes care of parsing the string with help of Parsec into Regex datatype and then transforms it into the EFSM.
* FiniteMachine.hs: This module exposes EFSM datatype and operation that can be done on it as for example the union, intersection and creation from given character.
modules where are used but I like it more this way. 
