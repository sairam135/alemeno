from django.shortcuts import render, redirect
from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.db import connection
from django.contrib import messages
import bcrypt
import hashlib
import sys
import base64
from datetime import datetime
from datetime import date
from django.http import HttpResponse
from django.template.loader import get_template
import smtplib
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.utils.crypto import get_random_string


def index(request):
    if request.session.get('email') != None:
        email = request.session.get('email')
        userId = request.session.get('userId')
        role = request.session.get('role')
        return redirect('index')    
    else:
        return render(request, 'admins/index.html')

def register(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        gender = request.POST.get('gender')
        email = request.POST.get('email')
        mobileno= request.POST.get('mobileno')
        password = request.POST.get('password')
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email = %s""", [email])
        row = cursor.fetchall()
        if cursor.rowcount == 0:
            request.session['firstname'] = firstname
            request.session['lastname'] = lastname
            request.session['gender'] = gender
            request.session['email'] = email
            request.session['password'] = password
            request.session['mobileno'] = mobileno
            otp = get_random_string(6, allowed_chars='0123456789')
            request.session['otp'] = otp
            send_mail(subject='{} is your Alemeno OTP'.format(otp), message='Enter otp to Verify your email.Note that this otp will only be active for 10 minutes.', from_email='alemenohealth@gmail.com', recipient_list=[email], fail_silently=True,
                      html_message="<h2>Please enter the below OTP to complete your verification.Note that this OTP will only be active for 10 minutes.</h2><br><h2>{}</h2>".format(otp))
            request.session['otp_is_active'] = True
            messages.success(
                request, 'OTP sent to your email please check your inbox!!')
            return redirect('verify_email')
        else:
            messages.success(
                request, 'User with the entered email already exists please login to continue!!!')
            return redirect('login')

    else:
        return render(request, 'admins/register.html')


def verify_email(request):
    if request.session.get('otp_is_active'):
        if request.method == 'POST':
            entered_otp = request.POST.get('otp')
            cursor = connection.cursor()
            if request.session.get('otp') != None:
                generated_otp= request.session.get('otp')
                if generated_otp == entered_otp:
                    firstname = request.session.get('firstname')
                    lastname = request.session.get('lastname')
                    email = request.session.get('email')
                    gender = request.session.get('gender')
                    mobile_number = request.session.get('mobileno')
                    password = request.session.get('password')
                    hashed_password = bcrypt.hashpw(password.encode(
                        'utf8'), bcrypt.gensalt(rounds=12))
                    cursor.execute("""INSERT INTO admins(firstname,lastname,gender,mobileno,email,password) VALUES (%s,%s,%s,%s,%s,%s)""", (
                        firstname, lastname, gender,mobile_number, email, hashed_password))
                    messages.success(
                        request, 'Emial verification successful!! Please login to continue')
                    return redirect('login')
                else:
                    messages.success(request, 'Invalid otp try again!!')
                    return redirect('verify_email')

            else:
                messages.success(request, 'Register before email verification!!')
                return redirect('register')
        else:
            return render(request, 'admins/verify_email.html')
    else:
        return render(request, 'admins/error.html')






def login(request):
    request.session.flush()
    request.session.clear_expired()
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email= %s""", [email])
        row = cursor.fetchall()
        if cursor.rowcount == 1:
            database_password = row[0][5]
            adminId = row[0][1]
            if bcrypt.checkpw(password.encode('utf8'), database_password.encode('utf8')):

                request.session['adminId'] = row[0][1]
                messages.success(request, 'Login successful!!')
                request.session['email'] = email
                return redirect('home')
            else:
                messages.success(
                    request, 'Incorrect password please try again!!')
                return render(request, 'admins/login.html')
        else:
            messages.success(
                request, 'Account does not exist with the entered credentials!! Register to create an account')
            return render(request, 'admins/login.html')
    else:
        return render(request, 'admins/login.html')



def logout(request):
    request.session.flush()
    request.session.clear_expired()
    return render(request,'admins/logout.html')

def home(request):
    adminId = request.session.get('adminId')
    email = request.session.get('email')
    if request.session.get('email')!=None:
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email= %s""", [email])
        row = cursor.fetchall()
        data = {
            'firstname': row[0][0],
            'lastname': row[0][2],
            'adminId': row[0][1],
        }

        return render(request, 'admins/home.html', data)
    else:
        return render(request, 'admins/error.html')


def add_kids(request):
    adminId = request.session.get('adminId')
    email = request.session.get('email')
    if request.session.get('email')!=None:
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email= %s""", [email])
        row = cursor.fetchall()
        data = {
            'firstname': row[0][0],
            'lastname': row[0][2],
            'adminId': row[0][1],
        }
        if request.method == "POST":
            kid_name = request.POST.get('kid_name')
            kid_age = request.POST.get('kid_age')
            parent_phone_number = request.POST.get('parent_phone_number')
            parent_email = request.POST.get('parent_email')
            image_url= request.POST.get('image_url')
            food_group= request.POST.get('food_group')
            admin_name=data['firstname']+" "+data['lastname']
            cursor.execute("""INSERT INTO kids(name,age,parent_phone,parent_email) VALUES (%s,%s,%s,%s)""", (
                        kid_name,int(kid_age),parent_phone_number,parent_email))
            kid_id=cursor.lastrowid
            now=datetime.now()
            date_time=now.strftime("%Y-%m-%d %H:%M:%S")
            if food_group=='Unknown':
                cursor.execute("""INSERT INTO images(url,food_group,is_approved,approved_by,created_on,updated_on,kid_id) VALUES (%s,%s,%s,%s,%s,%s,%s)""", (
                            image_url,food_group,'Yes',admin_name,date_time,date_time,kid_id))                
                send_mail(subject='Food in Image', message='Image does not cantain food', from_email='alemenohealth@gmail.com', recipient_list=[parent_email], fail_silently=True,
                            html_message="<p>Dear Parent,</p><p>This is to kindly inform you that your kid's Food Image Url does not contain any food.Please resolve this issue at the earliest.</p><p>Regards</p><p>Alemeno</p>")
            else:
                cursor.execute("""INSERT INTO images(url,food_group,is_approved,approved_by,created_on,updated_on,kid_id) VALUES (%s,%s,%s,%s,%s,%s,%s)""", (
                            image_url,food_group,'Yes',admin_name,date_time,date_time,kid_id))
            messages.success(
                request, 'Kids details are added successfully!!')
            return redirect('home')
           
        else:
            return render(request, 'admins/add_kids.html',data)
    else:
        return render(request, 'admins/error.html')

def kids(request):
    adminId=request.session.get('adminId')
    email=request.session.get('email')   
    if request.session.get('email')!=None:
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email= %s""", [email])
        row = cursor.fetchall()
        firstname=row[0][0]
        lastname=row[0][2]
        name_filter= request.GET.get('name')
        if name_filter==None:
            cursor.execute("""SELECT kids.kid_id,image_id,name,age  FROM kids JOIN images ON kids.kid_id = images.kid_id """)
        else:
            cursor.execute("""SELECT kids.kid_id,image_id,name,age  FROM kids JOIN images ON kids.kid_id = images.kid_id  WHERE name=%s""",[name_filter])
        row = cursor.fetchall()
        kids_details=[]
        count= cursor.rowcount
        if count!=0:
            for n in range(count):
                kids_details.append({
                'kid_id':row[n][0],
                'name':row[n][2],
                'age':row[n][3],
                'image_id':row[n][1]
            })
            data={
            'kids_details':kids_details,
            'name_filter':name_filter,
            'adminId':adminId,
            'email':email,
            'firstname':firstname,
            'lastname':lastname
            }
        else:
            data={
            'kids_details':None,
            'name_filter':name_filter,
            'adminId':adminId,
            'email':email,
            'firstname':firstname,
            'lastname':lastname
                }
        return render(request,'admins/kids.html',data)
    else:
        return render(request,'admins/error.html')

def update_images(request,id):
    adminId = request.session.get('adminId')
    email = request.session.get('email')
    if request.session.get('email')!=None:
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM admins WHERE email= %s""", [email])
        row = cursor.fetchall()
        firstname=row[0][0]
        lastname=row[0][2]
        adminId=row[0][1]
        cursor.execute("""SELECT parent_email,url,approved_by,created_on,updated_on,food_group  FROM kids JOIN images ON kids.kid_id = images.kid_id WHERE image_id=%s """,[id]) 
        row = cursor.fetchall()
        parent_email=row[0][0]
        created_on=row[0][3]
        updated_on=row[0][4]
        data = {
            'firstname': firstname,
            'lastname': lastname,
            'adminId': adminId,
            'url':row[0][1],
            'approved_by':row[0][2],
            'group':row[0][5],
            'updated_on':updated_on.strftime("%b %d, %Y, %I:%M %p"),
            'created_date':created_on.strftime("%Y-%m-%d"),
            'created_time':created_on.strftime("%H:%M:%S")
        }
        if request.method == "POST":
            image_url= request.POST.get('image_url')
            food_group= request.POST.get('food_group')
            admin_name=data['firstname']+" "+data['lastname']
            now=datetime.now()
            date_time=now.strftime("%Y-%m-%d %H:%M:%S")
            if food_group=='Unknown':
                cursor.execute("""UPDATE images SET url=%s,food_group=%s,is_approved=%s,approved_by=%s,updated_on=%s WHERE image_id=%s""", (
                        image_url,food_group,'Yes',admin_name,date_time,int(id)))     
                send_mail(subject='Food in Image', message='Image does not cantain food', from_email='alemenohealth@gmail.com', recipient_list=[parent_email], fail_silently=True,
                            html_message="<p>Dear Parent,</p><p>This is to kindly inform you that your kid's Food Image Url does not contain any food.Please resolve this issue at the earliest.</p><p>Regards</p><p>Alemeno</p>")       
            else:
                 cursor.execute("""UPDATE images SET url=%s,food_group=%s,is_approved=%s,approved_by=%s,updated_on=%s WHERE image_id=%s""", (
                        image_url,food_group,'Yes',admin_name,date_time,int(id)))
            messages.success(
                request, 'Image is updated successfully!!')
            return redirect('home')
           
        else:
            return render(request, 'admins/update_images.html',data)
    else:
        return render(request, 'admins/error.html')
