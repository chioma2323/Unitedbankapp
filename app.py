from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from werkzeug.security import generate_password_hash,check_password_hash
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = '12345vchvcjhb'

login_manger = LoginManager()
login_manger.init_app(app)
login_manger.login_view = "login"

# Your database models and routes here...
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

def generate_account_number():
    return str(random.randint(1000000000,9999999999))

db = SQLAlchemy(app)

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    fullname = db.Column(db.String(100),nullable =False)
    phone = db.Column(db.String(20), nullable =False)
    email = db.Column(db.String(120), nullable =False)
    password = db.Column(db.String(200), nullable = False)

    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    balance = db.Column(db.Float, default=0.0)
    acc_no = db.Column(db.String(10), unique=True, nullable=False, default=generate_account_number)

class Transaction(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    type = db.Column(db.String(10), nullable = False)
    account = db.Column(db.Float,nullable= False)
    description = db.Column(db.String(100), nullable= False)
    timestamp = db.Column(db.DateTime,nullable =False,default= datetime.utcnow)


with app.app_context():
    db.create_all()

# we have to load all users by thier id
@login_manger.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Registration logic
    if request.method== "POST":
        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        password = request.form.get("password")
        email = request.form.get("email")
        password =generate_password_hash(password)

        if User.query.filter_by(email=email).first():
            flash("email already registered. please log in," 'danger')
            return redirect(url_for("login"))
        
        new_user = User(fullname=fullname,phone=phone,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registeration Successful", 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("login successful", 'success')
            return redirect(url_for("dashboard"))
        else:
            flash("invaid username or password", 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Dashboard logic
    user = current_user
    transactions= Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).all()
    return render_template('dashboard.html',user=user,transactions=transactions)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    # Deposit logic
    user = current_user
    if request.method == "POST":
        amount= float(request.form.get("amount"))
        description = request.form.get("description")

        if amount<= 50:
            flash("deposite amount must be more than 50",'danger')
            return redirect(url_for('deposit'))
        user.balance += amount
        txn = Transaction(user_id=user.id, type= 'deposit', account=amount, description=description)
        db.session.add(txn)
        db.session.commit()
        flash("deposit successful",'success')
        return redirect(url_for('dashboard'))
    return render_template('deposit.html',user=user)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    # Withdraw logic
    user = current_user
    if request.method =="POST":
        amount = float(request.form.get('amount'))
        description = request.form.get('description')

        if amount <= 50:
            flash("withdrawal amount must be greater than 50", 'danger')
            return redirect(url_for('withdraw'))
        
        if amount > user.balance:
            flash("Insufficent balance", 'danger')
             
        user.balance -= amount

        txn = Transaction(user_id = user.id, type = 'withdraw', account= amount, description = description)
        db.session.add(txn)
        db.session.commit()
        flash('withdrawal successful',"success")
        return redirect (url_for("dashboard"))
    return render_template('withdraw.html')
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    user = current_user
    if request.method == "POST":
        recipient_acc_no = request.form.get("recipient")
        amount = float(request.form.get("amount"))
        description = request.form.get("description")

        recipient = User.query.filter_by(acc_no=recipient_acc_no).first()

        if not recipient:
            flash('Recipient account number not found.', 'danger')
            return redirect(url_for('transfer'))

        if amount <= 50:
            flash('Transfer amount must be greater than ₦50.', 'danger')
            return redirect(url_for('transfer'))

        if amount > user.balance:
            flash('Insufficient balance for this transfer.', 'danger')
            return redirect(url_for('transfer'))

        user.balance -= amount
        recipient.balance += amount

        txn_sender = Transaction(user_id=user.id, type='transfer', account=amount, description=f'Transfer to {recipient.fullname} ({recipient.acc_no}): {description}')
        txn_recipient = Transaction(user_id=recipient.id, type='transfer', account=amount, description=f'Transfer from {user.fullname} ({user.acc_no}): {description}')
        db.session.add(txn_sender)
        db.session.add(txn_recipient)
        db.session.commit()
        flash('Transfer successful!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('transfer.html', user=user)

@app.route('/logout')
def logout():
    
    flash('You have been logged out.', 'info')
    logout_user()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")