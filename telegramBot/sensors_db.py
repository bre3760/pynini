from mysql.connector import connect, Error
import json
import requests

class SensorsDB():
    def __init__(self, data):
        self.host = data["host"]
        self.user = data["user"]
        self.password = data["password"]
        self.nameDB = data["nameDB"]
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
        # sql = '''CREATE TABLE CO2(
        #    TIMESTAMP timestamp(0),
        #    VALUE float,
        #    TYPE char(50)
        # )'''
        #
        # self.cursor.execute(sql)

        # sql = '''CREATE TABLE best(
        #    TYPOLOGY char(50),
        #    TEMPERATURE float,
        #    CO2 float,
        #    HUMIDITY float,
        #    INFO char(254)
        # )'''
        #
        # self.cursor.execute(sql)

        # sql = ''' INSERT INTO best (TYPOLOGY, TEMPERATURE, CO2, HUMIDITY, INFO) values (%s,%s,%s,%s,%s)'''
        # self.cursor.execute(sql,['Standard', 28.0, 2.0, 25.0, 'https://www.allrecipes.com/recipe/20066/traditional-white-bread/'])
        # self.mydb.commit()

        #return self.cursor
    #mycursor.execute("CREATE DATABASE sensors_data")
    #mycursor.execute("DELETE mydatabase")
    #mycursor.execute("SHOW DATABASES")


if __name__ == "__main__":

    data = requests.get("http://localhost:9090/db")
    mydb = SensorsDB(json.loads(data.text))
    mydb.start()
    print(mydb.cursor)