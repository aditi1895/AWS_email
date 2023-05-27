from flask import Flask, render_template
from constants import *
app = Flask(__name__)


from flask import render_template, request
from helper import upload_file_to_s3, update_table

# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# # function to check file extension
# def allowed_file(filename):
#     return '.' in filename and \
#         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")

def home():
    print("Hello, World!")
    return render_template('form.html')

@app.route("/upload", methods=["POST"])
def create():

    print('request form {}'.format(request.form))
    # check whether an input field with name 'user_file' exist
    if 'Email Addresses' not in request.form.keys() or len(request.form['Email Addresses']) == 0:
        return 'No Email Addresses in request text'

    if 'user_file' not in request.files:
        return "No user_file key in request.files" 
        #redirect(url_for('new'))

    # after confirm 'user_file' exist, get the file from input
    file = request.files['user_file']
    emails = request.form['Email Addresses']
    print('emails {}'.format(emails))

    # check whether a file is selected
    if file.filename == '':
        print('No selected file')
        return "No selected file"

    if file:
        output = upload_file_to_s3(file) 
        
        # if upload success,will return file name of uploaded file
        if output:
            filepath = 'https://s3.us-east-2.amazonaws.com/'+AWS_BUCKET_NAME+'/'+output
            print(filepath)
            resp = update_table(filepath, emails)
            print("table item updated {}".format(resp))
            print('Upload completed')
            print('Output {}'.format(output))
            return "Upload Completed" 

        # upload failed, redirect to upload page
        else:
            print("Unable to upload, try again")
            return "Unable to upload, try again" 
        
    else:
        print("File not present.")
        return "File not present."

    

if __name__ == "__main__":

    app.run(debug=True)