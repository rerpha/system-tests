import pymysql
from time import sleep
import pytest


def test_data_is_inputted(docker_compose_sql):
    sleep(20)  # wait while we initialise a server
    connection = pymysql.connect(host="*", user="root", passwd="example")
    mycursor = connection.cursor()
    db_name = "mydatabase"

    # Simulates a an application interacting with a database.
    mycursor.execute(f"CREATE DATABASE {db_name}")
    sleep(1)
    mycursor.execute("SHOW DATABASES")
    results = mycursor.fetchall()

    assert db_name in [item[0] for item in results]
