import pymysql.cursors

def obtenerconexion():
   try:
       connection = pymysql.connect(
           host='localhost', user='root', password='',
           database='botica_sistema',
           cursorclass=pymysql.cursors.DictCursor)
       return connection
   except:
       raise
