#!/usr/bin/env python
# coding=utf-8


from flask import Flask
# from flask import make_response
from flask import request
from flask import render_template

# import requests
# import json
import MySQLdb

app = Flask(__name__)


@app.route('/', methods=['GET'])
def racine():

    return render_template('index.html')


@app.route('/init', methods=['POST'])
def init():

    try:
        conn = MySQLdb.connect(host="mysql", user="root", passwd="Ensibs56")
        cursor = conn.cursor()
        cursor.execute('DROP DATABASE IF EXISTS test')
        cursor.execute('CREATE DATABASE test')
        cursor.execute('USE test')
        cursor.execute('CREATE TABLE individuals (lastname varchar(50), firstname varchar(50))')
        cursor.execute("INSERT INTO individuals VALUES ('Lagaffe', 'Gaston')")
        cursor.execute("INSERT INTO individuals VALUES ('Gouigoux', 'Jean-Philippe')")
        conn.commit()
        conn.close()

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])

    return "Database 'test' initialized with dummy individuals"


@app.route('/data', methods=['GET'])
def data():

    try:
        conn = MySQLdb.connect(host="mysql", user="root", passwd="Ensibs56", db="test")
        cursor = conn.cursor()

        name = request.args['restriction']
        if request.args.has_key('securemode') and request.args['securemode'] == 'on':
            cursor.execute("SELECT * FROM individuals WHERE lastname = %s", (name,))
        else:
            # Liste de mots-clés interdits
            forbidden = ["SELECT", "ORDER", "FROM", "WHERE", "UNION", "JOIN", "LIMIT"]

            # Méthode isalpha, retourne Tru si la chaine est composée entièrement de
            # caractères alphabétiques
            if name.isalpha() and name.upper() not in forbidden:
                # Ancienne requete SQL à laquelle on ajoute "LIMIT 1"
                # cursor.execute("SELECT * FROM individuals WHERE lastname = '%s'" % name)
                # Si l'attaquant parvient à déjouer nos filtres, il ne sera pas en mesure
                # d'obtenir plus d'un champ à la fois
                cursor.execute("SELECT * FROM individuals WHERE lastname = '%s' LIMIT 1" % name)
            else:
                # Redirection vers No Item Found. De cette manière l'attaquant ne pourra
                # pas identifier d'injection
                cursor.countdown = 0

            if cursor.rowcount > 0:
                return render_template('results.html', cursor=cursor)
            else:
                return "no item found"

    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])

if __name__ == '__main__':
    app.run(host='0.0.0.0')
