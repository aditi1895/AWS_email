import imp
from flask import Flask, request, render_template, flash
from utils.constansts import *
from utils.helper_functions import *
# from tkinter import messagebox

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/', methods=['GET'])
def login_page():
    return render_template('login_form.html')

@app.route('/home', methods=['GET', 'POST'])
def home_page():
    print("request form {}" .format(request.form))
    if 'Username' not in request.form.keys():
        flash("No Username provided")
        return render_template('login_form.html')
    elif "Password" not in request.form.keys():
        flash("No password provided")
        return render_template("login_form.html")
    elif request.form['Password'].strip().split() == ""  or request.form['Username'].strip().split() == "":
        flash("Username or Password can't be empty")
        return render_template("login_form.html")
    
    Key_to_scan = {"Username": {'S': request.form['Username']}}
    print('key to scan {} table {}'.format(Key_to_scan, LOGIN_TABLE))
    db_response = get_item_from_db(Key_to_scan, LOGIN_TABLE)
    if db_response:
        if 'Item' in db_response:
            item = db_response['Item']
            if item["Password"]['S'] == request.form["Password"]:
                flash("Signed in successfully!")
                return(render_template("upload_form.html"))
            else:
                flash("Invalid Password!")
                return(render_template("login_form.html"))
        else:
            flash("Invalid Username!")
            return(render_template("login_form.html"))
    else:
        flash("Invalid Username or Password!")
        return(render_template("login_form.html"))

@app.route('/form', methods=['GET'])
def form_page():
    return render_template("upload_form.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if "upload_file" not in request.files:
        flash("No file uploaded")
        return(render_template("upload_form.html"))
    
    if "Email" not in request.form.keys():
        flash("Email Addresses are not provided")
        return(render_template("upload_form.html"))
    else:
        Emails = request.form["Email"].strip().split(';')
        Emails = [Email.strip() for Email in Emails]
        if len(Emails) > 5:
            flash("Only 5 Email Addresses are allowed!")
            return(render_template("upload_form.html"))
        for Email in Emails:
            print('Email', Email)
            
            if not validate_email(Email):
                flash("Email Address is not in correct format!")
                return(render_template("upload_form.html"))
        
    Uploaded_file = request.files['upload_file']
    response_s3 = put_object_in_s3(Uploaded_file)
    print('put object in s3!')
    if response_s3:
        Key_for_db = create_item_payload(Emails, response_s3)
        response_db = put_item_in_db(Key_for_db, TABLE)
        if response_db:
            flash("Table updated Successfully!")
        else:
            flash("Dynamodb table updation ran into some issue!")
            return(render_template("upload_form.html"))
    return render_template("success.html")

if __name__ == '__main__':
    app.run(debug=True)