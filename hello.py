import tornado.ioloop
import tornado.web
import uuid
import json
import pymysql
from pymongo import MongoClient
from datetime import datetime

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, World")

class ClientHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            self.write({'status': 200, 'clientes': self.get_all_clients()})
        except Exception as exc:
            print("Error occurred during data retrieving")
            self.write({'status': 500, 'error': exc})

    def post(self):
        try:
            body = json.loads(self.request.body)
            nome = body["nome"]
            if not nome:
                self.write({'msg': 'Nome obrigatorio', 'status': 400})
            self.insert_into_clients(nome)
            self.write({'msg': 'Inserido', 'status': 200})
        except Exception as exc:
            print('Exception occurred during insert %s ' %exc)
            self.write({'msg': 'Error', 'status': 500})

    def get_all_clients(self):
        try:
            db = pymysql.connect("10.20.0.5", "root", "admin", "db")
            cursor = db.cursor()
            cursor.execute("SELECT * FROM Cliente")
            intercept = LogIntercepterController()
            intercept.record_logs('cursor.fetchall()')

            return cursor.fetchall()
        except Exception as exc:
            print("Exception occurred during retrieving data " %exc)
            db.rollback()
        finally:
            db.close()
    
    def insert_into_clients(self, nome):
        try:
            db = pymysql.connect("10.20.0.5", "root", "admin", "db")
            cursor = db.cursor()
            query = "INSERT INTO Cliente(Nome) VALUES ('%s')" % (nome)
            cursor.execute(query)
            db.commit()
        except Exception as exc:
            print(exc)
            db.rollback()
        finally:
            db.close()

class UUIDHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({'uuid': str(uuid.uuid4())})

class LogHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(self.get_logs())
    
    def get_logs(self):
        log_intercepter = LogIntercepterController()
        
        return log_intercepter.get_recorded_logs()

class Intercept(object):
    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            def new_func(*args, **kwargs):
                print('before calling %s' %attr.__name__)
                result = attr(*args, **kwargs)
                print('done calling %s' %attr.__name__)
                return result
            return new_func
        else:
            return attr

class LogIntercepterController(Intercept):
    def record_logs(self, data):
        client = MongoClient('localhost', 27017)
        db = client['client-facade']
        collection = db['client-facade']

        myData = {'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data': data}
        print(myData)
        x = collection.insert_one(dict(myData))
        print(x.inserted_id)

    def get_recorded_logs(self):
        client = MongoClient('localhost', 27017)
        db = client['client-facade']
        collection = db['client-facade']
        cursor = collection.find().sort('data', -1)
        rows = []
        for row in cursor:
            rows.append(row)
            print(row)
        
        return json.dumps(rows, default=str)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/client", ClientHandler),
        (r"/logs", LogHandler),
        (r"/uuid", UUIDHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()