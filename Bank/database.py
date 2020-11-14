import sqlite3
from datetime import datetime
import pathlib

BASE_PATH = pathlib.Path(__file__).parent.absolute()
BANK_DB = f'{BASE_PATH}/bank_db.sqlite3'


class Database():
    """Database Helper class"""
    def __init__(self):
        self.conn = None

    def connect(self, filename):
        """ Connect the databse handler to a databse """
        self.conn = sqlite3.connect(filename)
        self.conn.row_factory = self.dict_factory
        #enable foreign keys
        self.execQuery('PRAGMA foreign_keys = ON;')

    def insert(self,tableName,data):
        """ Inserts data in the form of a dictionary into a table """
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(tableName, columns, placeholders)
        cur = self.execQuery(sql, data.values())
        self.conn.commit()
        return cur

    def update(self, tableName, data, id_name, id_value):
        counter = 0
        max = len(data)
        update_fields = ''
        for k, v in data.items():
            counter += 1
            if counter == max:
                update_fields += f'{k} = {v}'
            else:
                update_fields += f'{k} = {v},'
        sql = f'UPDATE {tableName} SET {update_fields} WHERE {id_name} = {id_value};'
        cur = self.execQuery(sql)
        self.conn.commit()
        return cur

    def delete(self, table_name, id_name, id_value):
        sql = f'DELETE FROM {table_name} WHERE {id_name} = {id_value};'
        self.execQuery(sql)
        self.conn.commit()

    def execQuery(self, query, data=None):
        """ Execute a query on the database """
        cur = self.conn.cursor()
        if data:
            cur.execute(query, tuple(data))
        else:
            cur.execute(query)
        return cur

    def close(self):
        """ Closes the connection to the database """
        self.conn.close()

    def dict_factory(self,cursor, row):
        """ Used to return rows as dictionary"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

def main():
    db = Database()
    db.connect(BANK_DB)
    
    # Usage
    '''
    data = {
        "UserId" : "userid4",
        "CreatedAt" : datetime.now().microsecond
    }
    db.insert('BankUser', data)
    print(db.execQuery("SELECT * FROM BankUser").fetchone())

'''

    db.close()


if __name__ == '__main__': 
    main()