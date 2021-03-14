from mysql.connector import connect, Error

class SensorsDB():
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "pynini"
        self.nameDB = "mydatabase"
        #self.cursor = {}

    def start(self):
        try:
            with connect(
                host=self.host,
                user=self.user,
                password=self.password
            ) as connection:
                print(connection)
        except Error as e:
            print(e)

        self.mydb = connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.nameDB
        )

        self.cursor = self.mydb.cursor()
        #return self.cursor
    #mycursor.execute("CREATE DATABASE sensors_data")
    #mycursor.execute("DELETE mydatabase")
    #mycursor.execute("SHOW DATABASES")

        #self.cursor.execute("DROP TABLE IF EXISTS CO2")
        # sql = '''CREATE TABLE CO2(
        #    TIMESTAMP timestamp(0),
        #    VALUE float
        # )'''
        # self.cursor.execute(sql)


if __name__ == "__main__":
    mydb = SensorsDB()
    mydb.start()
    print(mydb.cursor)