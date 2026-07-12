import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd


def load_db(db_path: str = "data/Chinook.db") -> sqlite3.Connection:
    """
    Load the SQLite database and return a connection.

    Args:
        db_path: Path to the SQLite database file. Defaults to "data/Chinook.db"

    Returns:
        sqlite3.Connection: Active database connection

    Raises:
        FileNotFoundError: If the database file doesn't exist
        sqlite3.Error: If there's an error connecting to the database
    """
    db_file = Path(db_path)
    if not db_file.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            "Please run setup.sh first to create the database."
        )

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Error connecting to database: {e}")


def query_db(
    conn: sqlite3.Connection,
    query: str,
    params: Optional[tuple] = None,
    return_as_df: bool = True,
) -> List[Dict[str, Any]] | pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame or list of dictionaries.

    Args:
        conn: Active SQLite database connection
        query: SQL query string to execute
        params: Optional tuple of parameters for parameterized queries
        return_as_df: If True, return pandas DataFrame; if False, return list of dicts

    Returns:
        pd.DataFrame or List[Dict[str, Any]]: Query results

    Raises:
        sqlite3.Error: If there's an error executing the query
    """
    try:
        if return_as_df:
            return pd.read_sql_query(query, conn, params=params)
        else:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Error executing query: {e}")


def get_schema(conn: sqlite3.Connection) -> Dict[str, List[Dict[str, str]]]:
    """
    Get the database schema including all tables and their columns.

    Args:
        conn: Active SQLite database connection

    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary mapping table names to their column info
    """
    schema = {}

    tables = query_db(
        conn,
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
        return_as_df=False,
    )

    for table in tables:
        table_name = table["name"]
        columns = query_db(conn, f"PRAGMA table_info({table_name})", return_as_df=False)
        schema[table_name] = columns

    return schema


def print_table_schema(
    conn: sqlite3.Connection, table_name: Optional[str] = None
) -> None:
    """
    Print a formatted view of the database schema.

    Args:
        conn: Active SQLite database connection
        table_name: Optional specific table name to display. If None, shows all tables.
    """
    schema = get_schema(conn)

    if table_name:
        if table_name not in schema:
            print(f"Error: Table '{table_name}' not found in database.")
            print(f"Available tables: {', '.join(schema.keys())}")
            return
        tables_to_print = {table_name: schema[table_name]}
    else:
        tables_to_print = schema

    print("\n" + "=" * 100)
    print(f"DATABASE SCHEMA - {len(schema)} tables")
    print("=" * 100)

    if not table_name:
        print("\nTables:")
        for i, tbl in enumerate(schema.keys(), 1):
            print(f"  {i}. {tbl}")
        print()

    for tbl_name, columns in tables_to_print.items():
        print("\n" + "-" * 100)
        print(f"Table: {tbl_name} ({len(columns)} columns)")
        print("-" * 100)
        print(f"{'Column':<30} {'Type':<20} {'Nullable':<12} {'PK':<5} {'Default':<15}")
        print("-" * 100)

        for col in columns:
            nullable = "NULL" if col["notnull"] == 0 else "NOT NULL"
            pk = "Y" if col["pk"] > 0 else ""
            default = str(col["dflt_value"]) if col["dflt_value"] is not None else ""
            print(
                f"{col['name']:<30} {col['type']:<20} {nullable:<12} {pk:<5} {default:<15}"
            )

    print("=" * 100 + "\n")
