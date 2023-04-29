import mysql.connector


def run_query(query, host, user, password, database):
    mydb = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    mycursor = mydb.cursor()
    mycursor.execute(query)
    result = mycursor.fetchall()
    mydb.commit()
    mydb.close()
    return result
