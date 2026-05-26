import pymysql.cursors
from flask import jsonify

def obtenerconexion():
   try:
       connection = pymysql.connect(
           host='localhost', user='root', password='',
           database='tottus_sgi',
           cursorclass=pymysql.cursors.DictCursor)
       return connection
   except:
       raise




























