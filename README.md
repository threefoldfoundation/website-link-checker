<h1> Link Checker </h1>

<h2> Table of Contents </h2>

- [Introduction](#introduction)
- [How the Python Program Exits](#how-the-python-program-exits)
- [Python Program Arguments](#python-program-arguments)

***

## Introduction

This is a Python program that calls muffet on a whole website and filters errors. 

## How the Python Program Exits

Exits with error code 1 if at least one error is found, as specified with --errors
flag. Otherwise exits with code 0.

## Python Program Arguments

* url
  * The URL to scan. Please include https:// or http://. (e.g. https://google.com)
* -h, --help            
  * show this help message and exit
* -e ERRORS [ERRORS ...], --errors ERRORS [ERRORS ...]
  * Specify one, many or all error codes to be filtered (e.g. -e 404, -e 403 404, -e all). Use -e all to show all errors.
* -w WARNINGS [WARNINGS ...], --warnings WARNINGS [WARNINGS ...]
  * Specify one, many or all error codes to be filtered as warnings (e.g. -w 404, -w 403 404, -w all). Use -w all to show all warnings.