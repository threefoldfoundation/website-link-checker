<h1> Link Checker </h1>

<h2> Table of Contents </h2>

- [Introduction](#introduction)
- [How the Python Program Exits](#how-the-python-program-exits)
- [Python Program Arguments](#python-program-arguments)
- [How to Use the Python Program](#how-to-use-the-python-program)

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

## How to Use the Python Program

* Clone the repository
  * ```
    git clone https://github.com/threefoldfoundation/website-link-checker
    ```
* Change directory
  * ```
    cd website-link-checker
    ```
* Run the program (e.g. with threefold.io, displaying 404 errors and 403 warnings)
  * ```
    python website-link-checker.py https://threefold.io -e 404 -w 403
    ```

> Note: It can take a couple of minutes to run if the website has a lot of URLs.