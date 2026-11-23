"""
Unit tests for Language Detection module.
"""
import pytest
from core.language_detector import detect_language

def test_extension_detection():
    assert detect_language("script.py", "")[0] == "python"
    assert detect_language("App.java", "")[0] == "java"
    assert detect_language("main.c", "")[0] == "c"
    assert detect_language("server.cpp", "")[0] == "cpp"
    assert detect_language("client.js", "")[0] == "javascript"

def test_manual_override():
    lang, conf, _ = detect_language("unknown.txt", "some code", "java")
    assert lang == "java"
    assert conf == 1.0

def test_heuristic_python():
    code = """
def calculate_sum(a, b):
    # Sum elements
    return a + b
"""
    lang, conf, _ = detect_language("", code)
    assert lang == "python"

def test_heuristic_java():
    code = """
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
"""
    lang, conf, _ = detect_language("", code)
    assert lang == "java"

def test_heuristic_c():
    code = """
#include <stdio.h>
#include <stdlib.h>
int main() {
    printf("Test");
    return 0;
}
"""
    lang, conf, _ = detect_language("", code)
    assert lang == "c"
