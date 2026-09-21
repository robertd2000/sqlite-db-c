import subprocess


def run_script(
    commands: list[str],
    db_filename: str,
    check: bool = True,
) -> list[str]:
    result = subprocess.run(
        ["./db", db_filename],
        input="\n".join(commands) + "\n",
        text=True,
        capture_output=True,
        check=check,
    )

    return result.stdout.splitlines()


def test_inserts_and_retrieves_a_row(tmp_path):
    db_file = tmp_path / "test.db"

    result = run_script(
        [
            "insert 1 user1 person1@example.com",
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > Executed.",
        "db > (1, user1, person1@example.com)",
        "Executed.",
        "db > ",
    ]


def test_allows_inserting_strings_that_are_the_maximum_length(tmp_path):
    db_file = tmp_path / "test.db"

    long_username = "a" * 32
    long_email = "a" * 255

    result = run_script(
        [
            f"insert 1 {long_username} {long_email}",
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > Executed.",
        f"db > (1, {long_username}, {long_email})",
        "Executed.",
        "db > ",
    ]


def test_prints_error_message_if_strings_are_too_long(tmp_path):
    db_file = tmp_path / "test.db"

    long_username = "a" * 33
    long_email = "a" * 256

    result = run_script(
        [
            f"insert 1 {long_username} {long_email}",
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > String is too long.",
        "db > Executed.",
        "db > ",
    ]


def test_prints_an_error_message_if_id_is_negative(tmp_path):
    db_file = tmp_path / "test.db"

    result = run_script(
        [
            "insert -1 cstack foo@bar.com",
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > ID must be positive.",
        "db > Executed.",
        "db > ",
    ]


def test_keeps_data_after_closing_connection(tmp_path):
    db_file = tmp_path / "mydb.db"

    result1 = run_script(
        [
            "insert 1 cstack foo@bar.com",
            "insert 2 voltorb volty@example.com",
            ".exit",
        ],
        str(db_file),
    )

    assert result1 == [
        "db > Executed.",
        "db > Executed.",
        "db > ",
    ]

    result2 = run_script(
        [
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result2 == [
        "db > (1, cstack, foo@bar.com)",
        "(2, voltorb, volty@example.com)",
        "Executed.",
        "db > ",
    ]


def test_allows_printing_out_the_structure_of_a_one_node_btree(tmp_path):
    db_file = tmp_path / "test.db"

    result = run_script(
        [
            "insert 3 user3 person3@example.com",
            "insert 1 user1 person1@example.com",
            "insert 2 user2 person2@example.com",
            ".btree",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > Executed.",
        "db > Executed.",
        "db > Executed.",
        "db > Tree:",
        "- leaf (size 3)",
        "  - 1",
        "  - 2",
        "  - 3",
        "db > ",
    ]


def test_prints_constants(tmp_path):
    db_file = tmp_path / "test.db"

    result = run_script(
        [
            ".constants",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > Constants:",
        "ROW_SIZE: 293",
        "COMMON_NODE_HEADER_SIZE: 6",
        "LEAF_NODE_HEADER_SIZE: 10",
        "LEAF_NODE_CELL_SIZE: 297",
        "LEAF_NODE_SPACE_FOR_CELLS: 4086",
        "LEAF_NODE_MAX_CELLS: 13",
        "db > ",
    ]


def test_prints_an_error_message_if_there_is_a_duplicate_id(tmp_path):
    db_file = tmp_path / "test.db"

    result = run_script(
        [
            "insert 1 user1 person1@example.com",
            "insert 1 user1 person1@example.com",
            "select",
            ".exit",
        ],
        str(db_file),
    )

    assert result == [
        "db > Executed.",
        "db > Error: Duplicate key.",
        "db > (1, user1, person1@example.com)",
        "Executed.",
        "db > ",
    ]


def test_allows_printing_out_the_structure_of_a_3_leaf_node_btree(tmp_path):
    db_file = tmp_path / "test.db"

    script = [
        *[f"insert {i} user{i} person{i}@example.com" for i in range(1, 15)],
        ".btree",
        ".exit",
    ]

    result = run_script(script, str(db_file))

    assert result == [
        *["db > Executed."] * 14,
        "db > Tree:",
        "- internal (size 1)",
        "  - leaf (size 7)",
        "    - 1",
        "    - 2",
        "    - 3",
        "    - 4",
        "    - 5",
        "    - 6",
        "    - 7",
        "  - key 7",
        "  - leaf (size 7)",
        "    - 8",
        "    - 9",
        "    - 10",
        "    - 11",
        "    - 12",
        "    - 13",
        "    - 14",
        "db > ",
    ]


def test_insert_into_internal_node_is_not_implemented_yet(tmp_path):
    db_file = tmp_path / "test.db"

    script = [
        *[f"insert {i} user{i} person{i}@example.com" for i in range(1, 15)],
        "insert 15 user15 person15@example.com",
    ]

    result = run_script(
        script,
        str(db_file),
        check=False,
    )

    assert result[-1] == "db > Need to implement searching an internal node"
