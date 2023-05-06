import mysql.connector


class QueryError(Exception):
    pass


def run_query(query, host, user, password, database):
    try:
        mydb = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        cursor = mydb.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        mydb.commit()
        mydb.close()
        return result
    except mysql.connector.Error as error:
        raise QueryError(str(error))