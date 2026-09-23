import subprocess


def run_script(
    commands: list[str],
    db_filename: str,
    check: bool = True,
) -> list[str]:
    process = subprocess.Popen(
        ["./db", db_filename],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    for command in commands:
        try:
            process.stdin.write(command + "\n")
            process.stdin.flush()
        except BrokenPipeError:
            break

    try:
        process.stdin.close()
    except BrokenPipeError:
        pass

    stdout = process.stdout.read()
    stderr = process.stderr.read()

    process.wait()

    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode,
            process.args,
            output=stdout,
            stderr=stderr,
        )

    return stdout.splitlines()


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
        "LEAF_NODE_HEADER_SIZE: 14",
        "LEAF_NODE_CELL_SIZE: 297",
        "LEAF_NODE_SPACE_FOR_CELLS: 4082",
        "LEAF_NODE_MAX_CELLS: 13",
        "db > ",
    ]


def test_prints_an_error_message_if_there_is_a_duplicate_id(tmp_path):
    db_file = tmp_path / "mydb.db"

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


def test_insert_into_internal_node(tmp_path):
    db_file = tmp_path / "test.db"

    script = [
        *[f"insert {i} user{i} person{i}@example.com" for i in range(1, 15)],
        "insert 15 user15 person15@example.com",
        ".exit",
    ]

    result = run_script(
        script,
        str(db_file),
    )

    assert result[-2:] == [
        "db > Executed.",
        "db > ",
    ]


def test_prints_all_rows_in_a_multi_level_tree(tmp_path):
    db_file = tmp_path / "test.db"

    script = [
        *[f"insert {i} user{i} person{i}@example.com" for i in range(1, 16)],
        "select",
        ".exit",
    ]

    result = run_script(script, str(db_file))

    assert result[15:] == [
        "db > (1, user1, person1@example.com)",
        "(2, user2, person2@example.com)",
        "(3, user3, person3@example.com)",
        "(4, user4, person4@example.com)",
        "(5, user5, person5@example.com)",
        "(6, user6, person6@example.com)",
        "(7, user7, person7@example.com)",
        "(8, user8, person8@example.com)",
        "(9, user9, person9@example.com)",
        "(10, user10, person10@example.com)",
        "(11, user11, person11@example.com)",
        "(12, user12, person12@example.com)",
        "(13, user13, person13@example.com)",
        "(14, user14, person14@example.com)",
        "(15, user15, person15@example.com)",
        "Executed.",
        "db > ",
    ]
