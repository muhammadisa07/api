from flask import Flask, make_response, jsonify
from flask_restx import Resource, Api, reqparse
from flask_cors import  CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)
api = Api(app)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@127.0.0.1:3306/capstone"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY] = 'whateveryouwant'
db = SQLAlchemy(app)

class Users(db.Model):
    id       = db.Column(db.Integer(), primary_key=True, nullable=False)
    firstname     = db.Column(db.String(30), nullable=False)
    lastname     = db.Column(db.String(30), nullable=False)
    email    = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    createdAt = db.Column(db.Date)
    updatedAt = db.Column(db.Date)

#parserRegister
regParser = reqparse.RequestParser()
regParser.add_argument('firstname', type=str, help='firstname', location='json', required=True)
regParser.add_argument('lastname', type=str, help='lastname', location='json', required=True)
regParser.add_argument('email', type=str, help='Email', location='json', required=True)
regParser.add_argument('password', type=str, help='Password', location='json', required=True)
regParser.add_argument('confirm_password', type=str, help='Confirm Password', location='json', required=True)


@api.route('/register')
class Registration(Resource):
    @api.expect(regParser)
    def post(self):
        # BEGIN: Get request parameters.
        args        = regParser.parse_args()
        firstname   = args['firstname']
        lastname    = args['lastname']
        email       = args['email']
        password    = args['password']
        password2  = args['confirm_password']
        is_verified = False

        # cek confirm password
        if password != password2:
            return {
                'messege': 'Password tidak cocok'
            }, 400

        #cek email sudah terdaftar
        user = db.session.execute(db.select(Users).filter_by(email=email)).first()
        if user:
            return "Email sudah terpakai silahkan coba lagi menggunakan email lain"
        user          = Users()
        user.firstname    = firstname
        user.lastname     = lastname
        user.email    = email
        user.password = generate_password_hash(password)
        user.is_verified = is_verified
        db.session.add(user)
        db.session.commit()
        return {'message': 'Registrasi Berhasil'}, 201

logParser = reqparse.RequestParser()
logParser.add_argument('email', type=str, help='Email', location='json', required=True)
logParser.add_argument('password', type=str, help='Password', location='json', required=True)

@api.route('/login')
class LogIn(Resource):
    @api.expect(logParser)
    def post(self):
        args        = logParser.parse_args()
        email       = args['email']
        password    = args['password']
        # cek jika kolom email dan password tidak terisi
        if not email or not password:
            return {
                'message': 'Email Dan Password Harus Diisi'
            }, 400
        #cek email sudah ada
        user = db.session.execute(
            db.select(Users).filter_by(email=email)).first()
        if not user:
            return {
                'message': 'Email / Password Salah'
            }, 400
        else:
            user = user[0]
        #cek password
        if check_password_hash(user.password, password):
            if user.is_verified == True:
                token= jwt.encode({
                        "user_id":user.id,
                        "user_email":user.email,
                        "exp": datetime.utcnow() + timedelta(days= 1)
                },app.config['SECRET_KEY'],algorithm="HS256")
                return {'message' : 'Login Berhasil',
                        'token' : token
                        },200
            else:
                return {'message' : 'Email Belum Diverifikasi ,Silahka verifikasikan terlebih dahulu '},401
        else:
            return {
                'message': 'Email / Password Salah'
            }, 400

def decodetoken(jwtToken):
    decode_result = jwt.decode(
               jwtToken,
               app.config['SECRET_KEY'],
               algorithms = ['HS256'],
            )
    return decode_result

authParser = reqparse.RequestParser()
authParser.add_argument('Authorization', type=str, help='Authorization', location='headers', required=True)
@api.route('/user')
class DetailUser(Resource):
       @api.expect(authParser)
       def get(self):
        args = authParser.parse_args()
        bearerAuth  = args['Authorization']
        try:
            jwtToken    = bearerAuth[7:]
            token = decodetoken(jwtToken)
            user =  db.session.execute(db.select(Users).filter_by(email=token['user_email'])).first()
            user = user[0]
            data = {
                'firstname' : user.firstname,
                'lastname' : user.lastname,
                'email' : user.email
            }
        except:
            return {
                'message' : 'Token Tidak valid,Silahkan Login Terlebih Dahulu!'
            }, 401

        return data, 200

editParser = reqparse.RequestParser()
editParser.add_argument('firstname', type=str, help='Firstname', location='json', required=True)
editParser.add_argument('lastname', type=str, help='Lastname', location='json', required=True)
editParser.add_argument('Authorization', type=str, help='Authorization', location='headers', required=True)
@api.route('/edituser')
class EditUser(Resource):
       @api.expect(editParser)
       def put(self):
        args = editParser.parse_args()
        bearerAuth  = args['Authorization']
        firstname = args['firstname']
        lastname = args['lastname']
        datenow =  datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        try:
            jwtToken    = bearerAuth[7:]
            token = decodetoken(jwtToken)
            user = Users.query.filter_by(email=token.get('user_email')).first()
            user.firstname = firstname
            user.lastname = lastname
            user.updatedAt = datenow
            db.session.commit()
        except:
            return {
                'message' : 'Token Tidak valid,Silahkan Login Terlebih Dahulu!'
            }, 401
        return {'message' : 'Update User Sukses'}, 200

if __name__ == '__main__':
    app.run(ssl_context='adhoc', debug=True)
