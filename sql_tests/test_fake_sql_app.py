import pymysql
from time import sleep
import pytest


@pytest.mark.skip(reason="Still TODO")
def test_data_is_inputted(docker_compose_sql):
    sleep(10)  # wait while we initialise a server
    connection = pymysql.connect(
        host="127.0.0.1", user="root", passwd="password", port=3306
    )
    mycursor = connection.cursor()
    db_name = "mydatabase"
    mycursor.execute(f"CREATE DATABASE {db_name}")
    sleep(1)
    mycursor.execute("SHOW DATABASES")
    results = mycursor.fetchall()

    assert db_name in [item[0] for item in results]
