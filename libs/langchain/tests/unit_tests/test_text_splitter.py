"""Test text splitting functionality."""
import random
import re
import string
from pathlib import Path
from typing import Any, List

import pytest
from langchain_core.documents import Document

from langchain.text_splitter import (
    CharacterTextSplitter,
    HTMLHeaderTextSplitter,
    Language,
    MarkdownHeaderTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
    RecursiveJsonSplitter,
    TextSplitter,
    Tokenizer,
    split_text_on_tokens,
)

FAKE_PYTHON_TEXT = """
class Foo:

    def bar():


def foo():

def testing_func():

def bar():
"""


def test_character_text_splitter() -> None:
    """Test splitting by character count."""
    text = "foo bar baz 123"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=7, chunk_overlap=3)
    output = splitter.split_text(text)
    expected_output = ["foo bar", "bar baz", "baz 123"]
    assert output == expected_output


def test_character_text_splitter_empty_doc() -> None:
    """Test splitting by character count doesn't create empty documents."""
    text = "foo  bar"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=2, chunk_overlap=0)
    output = splitter.split_text(text)
    expected_output = ["foo", "bar"]
    assert output == expected_output


def test_character_text_splitter_separtor_empty_doc() -> None:
    """Test edge cases are separators."""
    text = "f b"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=2, chunk_overlap=0)
    output = splitter.split_text(text)
    expected_output = ["f", "b"]
    assert output == expected_output


def test_character_text_splitter_long() -> None:
    """Test splitting by character count on long words."""
    text = "foo bar baz a a"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=3, chunk_overlap=1)
    output = splitter.split_text(text)
    expected_output = ["foo", "bar", "baz", "a a"]
    assert output == expected_output


def test_character_text_splitter_short_words_first() -> None:
    """Test splitting by character count when shorter words are first."""
    text = "a a foo bar baz"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=3, chunk_overlap=1)
    output = splitter.split_text(text)
    expected_output = ["a a", "foo", "bar", "baz"]
    assert output == expected_output


def test_character_text_splitter_longer_words() -> None:
    """Test splitting by characters when splits not found easily."""
    text = "foo bar baz 123"
    splitter = CharacterTextSplitter(separator=" ", chunk_size=1, chunk_overlap=1)
    output = splitter.split_text(text)
    expected_output = ["foo", "bar", "baz", "123"]
    assert output == expected_output


@pytest.mark.parametrize(
    "separator, is_separator_regex", [(re.escape("."), True), (".", False)]
)
def test_character_text_splitter_keep_separator_regex(
    separator: str, is_separator_regex: bool
) -> None:
    """Test splitting by characters while keeping the separator
    that is a regex special character.
    """
    text = "foo.bar.baz.123"
    splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size=1,
        chunk_overlap=0,
        keep_separator=True,
        is_separator_regex=is_separator_regex,
    )
    output = splitter.split_text(text)
    expected_output = ["foo", ".bar", ".baz", ".123"]
    assert output == expected_output


@pytest.mark.parametrize(
    "separator, is_separator_regex", [(re.escape("."), True), (".", False)]
)
def test_character_text_splitter_discard_separator_regex(
    separator: str, is_separator_regex: bool
) -> None:
    """Test splitting by characters discarding the separator
    that is a regex special character."""
    text = "foo.bar.baz.123"
    splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size=1,
        chunk_overlap=0,
        keep_separator=False,
        is_separator_regex=is_separator_regex,
    )
    output = splitter.split_text(text)
    expected_output = ["foo", "bar", "baz", "123"]
    assert output == expected_output


def test_character_text_splitting_args() -> None:
    """Test invalid arguments."""
    with pytest.raises(ValueError):
        CharacterTextSplitter(chunk_size=2, chunk_overlap=4)


def test_merge_splits() -> None:
    """Test merging splits with a given separator."""
    splitter = CharacterTextSplitter(separator=" ", chunk_size=9, chunk_overlap=2)
    splits = ["foo", "bar", "baz"]
    expected_output = ["foo bar", "baz"]
    output = splitter._merge_splits(splits, separator=" ")
    assert output == expected_output


def test_create_documents() -> None:
    """Test create documents method."""
    texts = ["foo bar", "baz"]
    splitter = CharacterTextSplitter(separator=" ", chunk_size=3, chunk_overlap=0)
    docs = splitter.create_documents(texts)
    expected_docs = [
        Document(page_content="foo"),
        Document(page_content="bar"),
        Document(page_content="baz"),
    ]
    assert docs == expected_docs


def test_create_documents_with_metadata() -> None:
    """Test create documents with metadata method."""
    texts = ["foo bar", "baz"]
    splitter = CharacterTextSplitter(separator=" ", chunk_size=3, chunk_overlap=0)
    docs = splitter.create_documents(texts, [{"source": "1"}, {"source": "2"}])
    expected_docs = [
        Document(page_content="foo", metadata={"source": "1"}),
        Document(page_content="bar", metadata={"source": "1"}),
        Document(page_content="baz", metadata={"source": "2"}),
    ]
    assert docs == expected_docs


@pytest.mark.parametrize(
    "splitter, text, expected_docs",
    [
        (
            CharacterTextSplitter(
                separator=" ", chunk_size=7, chunk_overlap=3, add_start_index=True
            ),
            "foo bar baz 123",
            [
                Document(page_content="foo bar", metadata={"start_index": 0}),
                Document(page_content="bar baz", metadata={"start_index": 4}),
                Document(page_content="baz 123", metadata={"start_index": 8}),
            ],
        ),
        (
            RecursiveCharacterTextSplitter(
                chunk_size=6,
                chunk_overlap=0,
                separators=["\n\n", "\n", " ", ""],
                add_start_index=True,
            ),
            "w1 w1 w1 w1 w1 w1 w1 w1 w1",
            [
                Document(page_content="w1 w1", metadata={"start_index": 0}),
                Document(page_content="w1 w1", metadata={"start_index": 6}),
                Document(page_content="w1 w1", metadata={"start_index": 12}),
                Document(page_content="w1 w1", metadata={"start_index": 18}),
                Document(page_content="w1", metadata={"start_index": 24}),
            ],
        ),
    ],
)
def test_create_documents_with_start_index(
    splitter: TextSplitter, text: str, expected_docs: List[Document]
) -> None:
    """Test create documents method."""
    docs = splitter.create_documents([text])
    assert docs == expected_docs
    for doc in docs:
        s_i = doc.metadata["start_index"]
        assert text[s_i : s_i + len(doc.page_content)] == doc.page_content


def test_metadata_not_shallow() -> None:
    """Test that metadatas are not shallow."""
    texts = ["foo bar"]
    splitter = CharacterTextSplitter(separator=" ", chunk_size=3, chunk_overlap=0)
    docs = splitter.create_documents(texts, [{"source": "1"}])
    expected_docs = [
        Document(page_content="foo", metadata={"source": "1"}),
        Document(page_content="bar", metadata={"source": "1"}),
    ]
    assert docs == expected_docs
    docs[0].metadata["foo"] = 1
    assert docs[0].metadata == {"source": "1", "foo": 1}
    assert docs[1].metadata == {"source": "1"}


def test_iterative_text_splitter_keep_separator() -> None:
    chunk_size = 5
    output = __test_iterative_text_splitter(chunk_size=chunk_size, keep_separator=True)

    assert output == [
        "....5",
        "X..3",
        "Y...4",
        "X....5",
        "Y...",
    ]


def test_iterative_text_splitter_discard_separator() -> None:
    chunk_size = 5
    output = __test_iterative_text_splitter(chunk_size=chunk_size, keep_separator=False)

    assert output == [
        "....5",
        "..3",
        "...4",
        "....5",
        "...",
    ]


def __test_iterative_text_splitter(chunk_size: int, keep_separator: bool) -> List[str]:
    chunk_size += 1 if keep_separator else 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=0,
        separators=["X", "Y"],
        keep_separator=keep_separator,
    )
    text = "....5X..3Y...4X....5Y..."
    output = splitter.split_text(text)
    for chunk in output:
        assert len(chunk) <= chunk_size, f"Chunk is larger than {chunk_size}"
    return output


def test_iterative_text_splitter() -> None:
    """Test iterative text splitter."""
    text = """Hi.\n\nI'm Harrison.\n\nHow? Are? You?\nOkay then f f f f.
This is a weird text to write, but gotta test the splittingggg some how.

Bye!\n\n-H."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=1)
    output = splitter.split_text(text)
    expected_output = [
        "Hi.",
        "I'm",
        "Harrison.",
        "How? Are?",
        "You?",
        "Okay then",
        "f f f f.",
        "This is a",
        "weird",
        "text to",
        "write,",
        "but gotta",
        "test the",
        "splitting",
        "gggg",
        "some how.",
        "Bye!",
        "-H.",
    ]
    assert output == expected_output


def test_split_documents() -> None:
    """Test split_documents."""
    splitter = CharacterTextSplitter(separator="", chunk_size=1, chunk_overlap=0)
    docs = [
        Document(page_content="foo", metadata={"source": "1"}),
        Document(page_content="bar", metadata={"source": "2"}),
        Document(page_content="baz", metadata={"source": "1"}),
    ]
    expected_output = [
        Document(page_content="f", metadata={"source": "1"}),
        Document(page_content="o", metadata={"source": "1"}),
        Document(page_content="o", metadata={"source": "1"}),
        Document(page_content="b", metadata={"source": "2"}),
        Document(page_content="a", metadata={"source": "2"}),
        Document(page_content="r", metadata={"source": "2"}),
        Document(page_content="b", metadata={"source": "1"}),
        Document(page_content="a", metadata={"source": "1"}),
        Document(page_content="z", metadata={"source": "1"}),
    ]
    assert splitter.split_documents(docs) == expected_output


def test_python_text_splitter() -> None:
    splitter = PythonCodeTextSplitter(chunk_size=30, chunk_overlap=0)
    splits = splitter.split_text(FAKE_PYTHON_TEXT)
    split_0 = """class Foo:\n\n    def bar():"""
    split_1 = """def foo():"""
    split_2 = """def testing_func():"""
    split_3 = """def bar():"""
    expected_splits = [split_0, split_1, split_2, split_3]
    assert splits == expected_splits


CHUNK_SIZE = 16


def test_python_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.PYTHON, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
def hello_world():
    print("Hello, World!")

# Call the function
hello_world()
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "def",
        "hello_world():",
        'print("Hello,',
        'World!")',
        "# Call the",
        "function",
        "hello_world()",
    ]


def test_golang_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.GO, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
package main

import "fmt"

func helloWorld() {
    fmt.Println("Hello, World!")
}

func main() {
    helloWorld()
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "package main",
        'import "fmt"',
        "func",
        "helloWorld() {",
        'fmt.Println("He',
        "llo,",
        'World!")',
        "}",
        "func main() {",
        "helloWorld()",
        "}",
    ]


def test_rst_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.RST, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
Sample Document
===============

Section
-------

This is the content of the section.

Lists
-----

- Item 1
- Item 2
- Item 3

Comment
*******
Not a comment

.. This is a comment
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "Sample Document",
        "===============",
        "Section",
        "-------",
        "This is the",
        "content of the",
        "section.",
        "Lists",
        "-----",
        "- Item 1",
        "- Item 2",
        "- Item 3",
        "Comment",
        "*******",
        "Not a comment",
        ".. This is a",
        "comment",
    ]
    # Special test for special characters
    code = "harry\n***\nbabylon is"
    chunks = splitter.split_text(code)
    assert chunks == ["harry", "***\nbabylon is"]


def test_proto_file_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.PROTO, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
syntax = "proto3";

package example;

message Person {
    string name = 1;
    int32 age = 2;
    repeated string hobbies = 3;
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "syntax =",
        '"proto3";',
        "package",
        "example;",
        "message Person",
        "{",
        "string name",
        "= 1;",
        "int32 age =",
        "2;",
        "repeated",
        "string hobbies",
        "= 3;",
        "}",
    ]


def test_javascript_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.JS, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
function helloWorld() {
  console.log("Hello, World!");
}

// Call the function
helloWorld();
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "function",
        "helloWorld() {",
        'console.log("He',
        "llo,",
        'World!");',
        "}",
        "// Call the",
        "function",
        "helloWorld();",
    ]


def test_cobol_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.COBOL, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
IDENTIFICATION DIVISION.
PROGRAM-ID. HelloWorld.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 GREETING           PIC X(12)   VALUE 'Hello, World!'.
PROCEDURE DIVISION.
DISPLAY GREETING.
STOP RUN.
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "IDENTIFICATION",
        "DIVISION.",
        "PROGRAM-ID.",
        "HelloWorld.",
        "DATA DIVISION.",
        "WORKING-STORAGE",
        "SECTION.",
        "01 GREETING",
        "PIC X(12)",
        "VALUE 'Hello,",
        "World!'.",
        "PROCEDURE",
        "DIVISION.",
        "DISPLAY",
        "GREETING.",
        "STOP RUN.",
    ]


def test_typescript_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.TS, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
function helloWorld(): void {
  console.log("Hello, World!");
}

// Call the function
helloWorld();
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "function",
        "helloWorld():",
        "void {",
        'console.log("He',
        "llo,",
        'World!");',
        "}",
        "// Call the",
        "function",
        "helloWorld();",
    ]


def test_java_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.JAVA, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "public class",
        "HelloWorld {",
        "public",
        "static void",
        "main(String[]",
        "args) {",
        "System.out.prin",
        'tln("Hello,',
        'World!");',
        "}\n}",
    ]


def test_kotlin_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.KOTLIN, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
class HelloWorld {
    companion object {
        @JvmStatic
        fun main(args: Array<String>) {
            println("Hello, World!")
        }
    }
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "class",
        "HelloWorld {",
        "companion",
        "object {",
        "@JvmStatic",
        "fun",
        "main(args:",
        "Array<String>)",
        "{",
        'println("Hello,',
        'World!")',
        "}\n    }",
        "}",
    ]


def test_csharp_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.CSHARP, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
using System;
class Program
{
    static void Main()
    {
        int age = 30; // Change the age value as needed

        // Categorize the age without any console output
        if (age < 18)
        {
            // Age is under 18
        }
        else if (age >= 18 && age < 65)
        {
            // Age is an adult
        }
        else
        {
            // Age is a senior citizen
        }
    }
}
    """

    chunks = splitter.split_text(code)
    assert chunks == [
        "using System;",
        "class Program\n{",
        "static void",
        "Main()",
        "{",
        "int age",
        "= 30; // Change",
        "the age value",
        "as needed",
        "//",
        "Categorize the",
        "age without any",
        "console output",
        "if (age",
        "< 18)",
        "{",
        "//",
        "Age is under 18",
        "}",
        "else if",
        "(age >= 18 &&",
        "age < 65)",
        "{",
        "//",
        "Age is an adult",
        "}",
        "else",
        "{",
        "//",
        "Age is a senior",
        "citizen",
        "}\n    }",
        "}",
    ]


def test_cpp_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.CPP, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "#include",
        "<iostream>",
        "int main() {",
        "std::cout",
        '<< "Hello,',
        'World!" <<',
        "std::endl;",
        "return 0;\n}",
    ]


def test_scala_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.SCALA, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
object HelloWorld {
  def main(args: Array[String]): Unit = {
    println("Hello, World!")
  }
}
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "object",
        "HelloWorld {",
        "def",
        "main(args:",
        "Array[String]):",
        "Unit = {",
        'println("Hello,',
        'World!")',
        "}\n}",
    ]


def test_ruby_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.RUBY, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
def hello_world
  puts "Hello, World!"
end

hello_world
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "def hello_world",
        'puts "Hello,',
        'World!"',
        "end",
        "hello_world",
    ]


def test_php_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.PHP, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
<?php
function hello_world() {
    echo "Hello, World!";
}

hello_world();
?>
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "<?php",
        "function",
        "hello_world() {",
        "echo",
        '"Hello,',
        'World!";',
        "}",
        "hello_world();",
        "?>",
    ]


def test_swift_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.SWIFT, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
func helloWorld() {
    print("Hello, World!")
}

helloWorld()
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "func",
        "helloWorld() {",
        'print("Hello,',
        'World!")',
        "}",
        "helloWorld()",
    ]


def test_rust_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.RUST, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
fn main() {
    println!("Hello, World!");
}
    """
    chunks = splitter.split_text(code)
    assert chunks == ["fn main() {", 'println!("Hello', ",", 'World!");', "}"]


def test_markdown_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.MARKDOWN, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
# Sample Document

## Section

This is the content of the section.

## Lists

- Item 1
- Item 2
- Item 3

### Horizontal lines

***********
____________
-------------------

#### Code blocks
```
This is a code block

# sample code
a = 1
b = 2
```
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "# Sample",
        "Document",
        "## Section",
        "This is the",
        "content of the",
        "section.",
        "## Lists",
        "- Item 1",
        "- Item 2",
        "- Item 3",
        "### Horizontal",
        "lines",
        "***********",
        "____________",
        "---------------",
        "----",
        "#### Code",
        "blocks",
        "```",
        "This is a code",
        "block",
        "# sample code",
        "a = 1\nb = 2",
        "```",
    ]
    # Special test for special characters
    code = "harry\n***\nbabylon is"
    chunks = splitter.split_text(code)
    assert chunks == ["harry", "***\nbabylon is"]


def test_latex_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.LATEX, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """
Hi Harrison!
\\chapter{1}
"""
    chunks = splitter.split_text(code)
    assert chunks == ["Hi Harrison!", "\\chapter{1}"]


def test_html_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.HTML, chunk_size=60, chunk_overlap=0
    )
    code = """
<h1>Sample Document</h1>
    <h2>Section</h2>
        <p id="1234">Reference content.</p>

    <h2>Lists</h2>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>

        <h3>A block</h3>
            <div class="amazing">
                <p>Some text</p>
                <p>Some more text</p>
            </div>
    """
    chunks = splitter.split_text(code)
    assert chunks == [
        "<h1>Sample Document</h1>\n    <h2>Section</h2>",
        '<p id="1234">Reference content.</p>',
        "<h2>Lists</h2>\n        <ul>",
        "<li>Item 1</li>\n            <li>Item 2</li>",
        "<li>Item 3</li>\n        </ul>",
        "<h3>A block</h3>",
        '<div class="amazing">',
        "<p>Some text</p>",
        "<p>Some more text</p>\n            </div>",
    ]


def test_md_header_text_splitter_1() -> None:
    """Test markdown splitter by header: Case 1."""

    markdown_document = (
        "# Foo\n\n"
        "    ## Bar\n\n"
        "Hi this is Jim\n\n"
        "Hi this is Joe\n\n"
        " ## Baz\n\n"
        " Hi this is Molly"
    )
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    output = markdown_splitter.split_text(markdown_document)
    expected_output = [
        Document(
            page_content="Hi this is Jim  \nHi this is Joe",
            metadata={"Header 1": "Foo", "Header 2": "Bar"},
        ),
        Document(
            page_content="Hi this is Molly",
            metadata={"Header 1": "Foo", "Header 2": "Baz"},
        ),
    ]
    assert output == expected_output


def test_md_header_text_splitter_2() -> None:
    """Test markdown splitter by header: Case 2."""
    markdown_document = (
        "# Foo\n\n"
        "    ## Bar\n\n"
        "Hi this is Jim\n\n"
        "Hi this is Joe\n\n"
        " ### Boo \n\n"
        " Hi this is Lance \n\n"
        " ## Baz\n\n"
        " Hi this is Molly"
    )

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    output = markdown_splitter.split_text(markdown_document)
    expected_output = [
        Document(
            page_content="Hi this is Jim  \nHi this is Joe",
            metadata={"Header 1": "Foo", "Header 2": "Bar"},
        ),
        Document(
            page_content="Hi this is Lance",
            metadata={"Header 1": "Foo", "Header 2": "Bar", "Header 3": "Boo"},
        ),
        Document(
            page_content="Hi this is Molly",
            metadata={"Header 1": "Foo", "Header 2": "Baz"},
        ),
    ]
    assert output == expected_output


def test_md_header_text_splitter_3() -> None:
    """Test markdown splitter by header: Case 3."""

    markdown_document = (
        "# Foo\n\n"
        "    ## Bar\n\n"
        "Hi this is Jim\n\n"
        "Hi this is Joe\n\n"
        " ### Boo \n\n"
        " Hi this is Lance \n\n"
        " #### Bim \n\n"
        " Hi this is John \n\n"
        " ## Baz\n\n"
        " Hi this is Molly"
    )

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    output = markdown_splitter.split_text(markdown_document)

    expected_output = [
        Document(
            page_content="Hi this is Jim  \nHi this is Joe",
            metadata={"Header 1": "Foo", "Header 2": "Bar"},
        ),
        Document(
            page_content="Hi this is Lance",
            metadata={"Header 1": "Foo", "Header 2": "Bar", "Header 3": "Boo"},
        ),
        Document(
            page_content="Hi this is John",
            metadata={
                "Header 1": "Foo",
                "Header 2": "Bar",
                "Header 3": "Boo",
                "Header 4": "Bim",
            },
        ),
        Document(
            page_content="Hi this is Molly",
            metadata={"Header 1": "Foo", "Header 2": "Baz"},
        ),
    ]

    assert output == expected_output


def test_md_header_text_splitter_preserve_headers_1() -> None:
    """Test markdown splitter by header: Preserve Headers."""

    markdown_document = (
        "# Foo\n\n"
        "    ## Bat\n\n"
        "Hi this is Jim\n\n"
        "Hi Joe\n\n"
        "## Baz\n\n"
        "# Bar\n\n"
        "This is Alice\n\n"
        "This is Bob"
    )
    headers_to_split_on = [
        ("#", "Header 1"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    output = markdown_splitter.split_text(markdown_document)
    expected_output = [
        Document(
            page_content="# Foo  \n## Bat  \nHi this is Jim  \nHi Joe  \n## Baz",
            metadata={"Header 1": "Foo"},
        ),
        Document(
            page_content="# Bar  \nThis is Alice  \nThis is Bob",
            metadata={"Header 1": "Bar"},
        ),
    ]
    assert output == expected_output


def test_md_header_text_splitter_preserve_headers_2() -> None:
    """Test markdown splitter by header: Preserve Headers."""

    markdown_document = (
        "# Foo\n\n"
        "    ## Bar\n\n"
        "Hi this is Jim\n\n"
        "Hi this is Joe\n\n"
        "### Boo \n\n"
        "Hi this is Lance\n\n"
        "## Baz\n\n"
        "Hi this is Molly\n"
        "    ## Buz\n"
        "# Bop"
    )
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    output = markdown_splitter.split_text(markdown_document)
    expected_output = [
        Document(
            page_content="# Foo  \n## Bar  \nHi this is Jim  \nHi this is Joe",
            metadata={"Header 1": "Foo", "Header 2": "Bar"},
        ),
        Document(
            page_content="### Boo  \nHi this is Lance",
            metadata={"Header 1": "Foo", "Header 2": "Bar", "Header 3": "Boo"},
        ),
        Document(
            page_content="## Baz  \nHi this is Molly",
            metadata={"Header 1": "Foo", "Header 2": "Baz"},
        ),
        Document(
            page_content="## Buz",
            metadata={"Header 1": "Foo", "Header 2": "Buz"},
        ),
        Document(page_content="# Bop", metadata={"Header 1": "Bop"}),
    ]
    assert output == expected_output


@pytest.mark.parametrize("fence", [("```"), ("~~~")])
def test_md_header_text_splitter_fenced_code_block(fence: str) -> None:
    """Test markdown splitter by header: Fenced code block."""

    markdown_document = (
        "# This is a Header\n\n"
        f"{fence}\n"
        "foo()\n"
        "# Not a header\n"
        "bar()\n"
        f"{fence}"
    )

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    output = markdown_splitter.split_text(markdown_document)

    expected_output = [
        Document(
            page_content=f"{fence}\nfoo()\n# Not a header\nbar()\n{fence}",
            metadata={"Header 1": "This is a Header"},
        ),
    ]

    assert output == expected_output


@pytest.mark.parametrize(["fence", "other_fence"], [("```", "~~~"), ("~~~", "```")])
def test_md_header_text_splitter_fenced_code_block_interleaved(
    fence: str, other_fence: str
) -> None:
    """Test markdown splitter by header: Interleaved fenced code block."""

    markdown_document = (
        "# This is a Header\n\n"
        f"{fence}\n"
        "foo\n"
        "# Not a header\n"
        f"{other_fence}\n"
        "# Not a header\n"
        f"{fence}"
    )

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )
    output = markdown_splitter.split_text(markdown_document)

    expected_output = [
        Document(
            page_content=(
                f"{fence}\nfoo\n# Not a header\n{other_fence}\n# Not a header\n{fence}"
            ),
            metadata={"Header 1": "This is a Header"},
        ),
    ]

    assert output == expected_output


def test_solidity_code_splitter() -> None:
    splitter = RecursiveCharacterTextSplitter.from_language(
        Language.SOL, chunk_size=CHUNK_SIZE, chunk_overlap=0
    )
    code = """pragma solidity ^0.8.20;
  contract HelloWorld {
    function add(uint a, uint b) pure public returns(uint) {
      return  a + b;
    }
  }
  """
    chunks = splitter.split_text(code)
    assert chunks == [
        "pragma solidity",
        "^0.8.20;",
        "contract",
        "HelloWorld {",
        "function",
        "add(uint a,",
        "uint b) pure",
        "public",
        "returns(uint) {",
        "return  a",
        "+ b;",
        "}\n  }",
    ]


@pytest.mark.requires("lxml")
def test_html_header_text_splitter(tmp_path: Path) -> None:
    splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2")]
    )

    content = """
<h1>Sample Document</h1>
    <h2>Section</h2>
        <p id="1234">Reference content.</p>

    <h2>Lists</h2>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>

        <h3>A block</h3>
            <div class="amazing">
                <p>Some text</p>
                <p>Some more text</p>
            </div>
    """

    docs = splitter.split_text(content)
    expected = [
        Document(
            page_content="Reference content.",
            metadata={"Header 1": "Sample Document", "Header 2": "Section"},
        ),
        Document(
            page_content="Item 1 Item 2 Item 3  \nSome text  \nSome more text",
            metadata={"Header 1": "Sample Document", "Header 2": "Lists"},
        ),
    ]
    assert docs == expected

    with open(tmp_path / "doc.html", "w") as tmp:
        tmp.write(content)
    docs_from_file = splitter.split_text_from_file(tmp_path / "doc.html")

    assert docs_from_file == expected


def test_split_text_on_tokens() -> None:
    """Test splitting by tokens per chunk."""
    text = "foo bar baz 123"

    tokenizer = Tokenizer(
        chunk_overlap=3,
        tokens_per_chunk=7,
        decode=(lambda it: "".join(chr(i) for i in it)),
        encode=(lambda it: [ord(c) for c in it]),
    )
    output = split_text_on_tokens(text=text, tokenizer=tokenizer)
    expected_output = ["foo bar", "bar baz", "baz 123"]
    assert output == expected_output


def test_split_json() -> None:
    """Test json text splitter"""
    max_chunk = 800
    splitter = RecursiveJsonSplitter(max_chunk_size=max_chunk)

    def random_val() -> str:
        return "".join(random.choices(string.ascii_letters, k=random.randint(4, 12)))

    test_data: Any = {
        "val0": random_val(),
        "val1": {f"val1{i}": random_val() for i in range(100)},
    }
    test_data["val1"]["val16"] = {f"val16{i}": random_val() for i in range(100)}

    # uses create_docs and split_text
    docs = splitter.create_documents(texts=[test_data])

    output = [len(doc.page_content) < max_chunk * 1.05 for doc in docs]
    expected_output = [True for doc in docs]
    assert output == expected_output


def test_split_json_with_lists() -> None:
    """Test json text splitter with list conversion"""
    max_chunk = 800
    splitter = RecursiveJsonSplitter(max_chunk_size=max_chunk)

    def random_val() -> str:
        return "".join(random.choices(string.ascii_letters, k=random.randint(4, 12)))

    test_data: Any = {
        "val0": random_val(),
        "val1": {f"val1{i}": random_val() for i in range(100)},
    }
    test_data["val1"]["val16"] = {f"val16{i}": random_val() for i in range(100)}

    test_data_list: Any = {"testPreprocessing": [test_data]}

    # test text splitter
    texts = splitter.split_text(json_data=test_data)
    texts_list = splitter.split_text(json_data=test_data_list, convert_lists=True)

    assert len(texts_list) >= len(texts)
