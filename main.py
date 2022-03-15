import os

import mobile
from mrun import MRun
from dbconfig import DBConfig

from flask import Flask, request
from flask_jwt import JWT
from werkzeug.security import safe_str_cmp
import mysql.connector as mysql
import json
from datetime import datetime
import hashlib
import bcrypt

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from mobile import mobile_blueprint

from sqlalchemy import create_engine

from flask import Blueprint


import logging


app = Flask(__name__)
CORS(app)
app.register_blueprint(mobile_blueprint)

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)




dbObj = DBConfig()
db = dbObj.connect()
def __init__(self):
    self.data = dict()


MRun = MRun()


# engine = create_engine('mysql://root:dhe123!@#@202.67.10.238/ntmc_ccntmc')
# connection = engine.connect()
# metadata = db.MetaData()
# apps_video_banner = db.Table('apps_video_banner', metadata, autoload=True, autoload_with=engine)
# app_link_banner = db.Table('app_linkS_banner', metadata, autoload=True, autoload_with=engine)


@app.route('/test')
def test():
    ret = MRun.get_polda_no_cc()
    return ret






@app.route('/login_user', methods=["POST"])
def login_user():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    res = authenticate_user(username, password)
    return res




@app.route('/simpan_user', methods=["POST"])
def simpan_user():
    username = request.json.get('username')
    password = request.json.get('password')
    level_user = request.json.get('level_user')
    satwil_id = request.json.get('satwil')
    polda_id = request.json.get('polda')

    cursor = db.cursor(dictionary=True)
    query = "SELECT username,password FROM user WHERE username = %s"
    cursor.execute(query, (username,))
    record = cursor.fetchall()
    valid = 0

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)

    if (len(record) > 0):
        valid = 2
    else:
        valid = 1
        query = "INSERT INTO user (username, password, level_user, satwil_id, polda_id " \
                ") " \
                "VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (username, hashed,level_user,satwil_id, polda_id,))
        db.commit()
    res = dict()
    res['valid'] = valid
    cursor.close()
    return res


@app.route('/warga_reg', methods=["POST"])
def warga_reg():
    email = request.json.get('email')
    passwd = request.json.get('pass')
    name = request.json.get('name')
    ktp = request.json.get('ktp')
    ktppic = request.json.get('ktppic')
    detail = request.json.get('detail')
    hp = request.json.get('hp')
    address = request.json.get('alamat')
    cursor = db.cursor(dictionary=True)
    query = "SELECT id_user_mobile,password FROM user_mobile WHERE email = %s"
    cursor.execute(query, (email,))
    record = cursor.fetchall()
    valid = 0

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(passwd.encode(), salt)

    if (len(record) > 0):
        valid = 2
    else:
        valid = 1
        query = "INSERT INTO user_mobile (nama, ktp, ktppic, email, password, " \
                "telepon, alamat, user_status) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (name, ktp,ktppic,email, hashed, hp, address, 1,))
        db.commit()
    res = dict()
    res['valid'] = valid
    cursor.close()
    return res

def authenticate_user(username, password):
    cursor = db.cursor(dictionary=True)
    query = "SELECT iduser,username,password, level_user, satwil_id, polda_id FROM user WHERE username = %s"
    cursor.execute(query, (username,))
    record = cursor.fetchall()
    cursor.close()
    level_user = ''
    satwil = ''
    polda = ''
    valid = 0
    if (len(record) > 0):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)

        if bcrypt.checkpw(password.encode(), (record[0]['password']).encode()):
            valid = 1
            token = username
            access_token = create_access_token(identity=username)
            name = record[0]['username']
            level_user = record[0]['level_user']
            satwil = record[0]['satwil_id']
            polda = record[0]['polda_id']

            return jsonify(token=access_token, name=name, level_user=level_user, satwil=satwil, polda=polda,valid=valid)

        else:
            valid = 2
            token = ""
            name = ""
    else:
        valid = 2
        token = ""
        name = ""
    res = dict()
    res['valid'] = valid
    res['username'] = name
    res['level_user'] = level_user
    res['satwil'] = satwil
    res['polda'] = polda
    res['token'] = token

    return res





@app.route('/datatable', methods=["POST"])
@jwt_required()
def datatable():
    level_user = request.json.get('level_user')
    polda = request.json.get('polda')
    satwil = request.json.get('satwil')
    start = request.json.get('start')
    limit = request.json.get('limit')
    cursor = db.cursor(dictionary=True)
    res = dict()

    if (level_user == 'superadmin'):
        query = "SELECT no_pengaduan,nama_pelapor,work_order.satwil_id, satwil.satwil,sub_kategori_id,subkategori.sub_kategori,tgl_kontak,tgl_close,status,status_detail.keterangan,idworkorder FROM work_order " \
                "LEFT JOIN satwil ON satwil.idsatwil = work_order.satwil_id " \
                "LEFT JOIN status_detail ON status_detail.idstatus = work_order.status " \
                "LEFT JOIN user ON user.iduser = work_order.user_id " \
                "LEFT JOIN subkategori ON subkategori.idsubkategori = work_order.sub_kategori_id LIMIT %s, %s"
        cursor.execute(query, (start, limit,))
        record = cursor.fetchall()
        res = record
    elif (level_user == 'spv'):
        query = "SELECT no_pengaduan,nama_pelapor,work_order.satwil_id,satwil.satwil,sub_kategori_id,subkategori.sub_kategori,tgl_kontak,tgl_close,status,status_detail.keterangan,idworkorder FROM work_order " \
                "LEFT JOIN satwil ON satwil.idsatwil = work_order.satwil_id " \
                "LEFT JOIN status_detail ON status_detail.idstatus = work_order.status " \
                "LEFT JOIN polda ON polda.idpolda = satwil.polda_id " \
                "LEFT JOIN user ON user.iduser = work_order.user_id " \
                "LEFT JOIN subkategori ON subkategori.idsubkategori = work_order.sub_kategori_id " \
                "WHERE polda.idpolda = %s LIMIT %s, %s "
        cursor.execute(query, (polda, start, limit, ))
        record = cursor.fetchall()
        res = record
    else:
        query = "SELECT no_pengaduan,nama_pelapor,work_order.satwil_id,satwil.satwil,sub_kategori_id,subkategori.sub_kategori,tgl_kontak,tgl_close,status,status_detail.keterangan,idworkorder FROM work_order " \
                "LEFT JOIN satwil ON satwil.idsatwil = work_order.satwil_id " \
                "LEFT JOIN status_detail ON status_detail.idstatus = work_order.status " \
                "LEFT JOIN user ON user.iduser = work_order.user_id " \
                "LEFT JOIN subkategori ON subkategori.idsubkategori = work_order.sub_kategori_id " \
                "WHERE work_order.satwil_id = %s LIMIT %s, %s "
        cursor.execute(query, (satwil, start, limit, ))
        record = cursor.fetchall()
        res = record
    cursor.close()
    return jsonify(res)




# Protect a route with jwt_required, which will kick out requests
# without a valid JWT present.
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


if __name__ == "__main__":
    app.run(ssl_context='adhoc', debug=True)

# if __name__ == "__main__":
#     app.run(ssl_context=('cert.pem', 'key.pem'))
