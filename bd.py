import pymysql.cursors

def obtenerconexion():
   try:
       connection = pymysql.connect(
           host='localhost', user='root', password='',
           database='elHueco',
           cursorclass=pymysql.cursors.DictCursor)
       return connection
   except:
       raise
