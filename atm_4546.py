from flask import Flask,render_template,request,session,redirect,url_for
import mysql.connector
import  re
from datetime import timedelta


atm_o=Flask(__name__)
atm_o.secret_key="my secret key"
db_connctr=mysql.connector.connect(host="localhost",user="root",password="YOUR_PASSWORD",database="atm_4546")
cursr=db_connctr.cursor()  #cursor point

atm_o.permanent_session_lifetime=timedelta(minutes=5)

@atm_o.route("/")
def welcome():
    if  "username" in session:
        return  redirect(url_for("home"))
    elif "ac_no" in session:
        return redirect(url_for("pin")) 
    return render_template("welcome.html")

@atm_o.route("/ac_details",methods=["GET","POST"])
def ac_no():
    if session:
        return redirect(url_for("home"))
       
    if request.method=="POST":
        ac_no=request.form["ac_no"]  #1234 1234 1234
        pattern=r"^\d{4} \d{4} \d{4}$"
        if not re.match(pattern,ac_no):
            return render_template("account.html",info="*plz enter valid ac_no \n like XXXX XXXX XXXX ")
        else:
            cursr.execute("""select ac_no,pin from user_data where ac_no=%s;""",(ac_no,))

            data=cursr.fetchone() #
            if data:
                session.permanent=True
                session["ac_no"]=data[0]
                session["pin"]=data[1]

                return  redirect(url_for("pin"))
            else:

               return render_template("account.html",info="* The ac_no is un-identified  ")



    return render_template("account.html")

@atm_o.route("/pin",methods=["GET","POST"])
def pin():  
    if  "ac_no" not in session:
        return  redirect(url_for("ac_no"))
    elif "username" in session:
        return redirect(url_for("home")) 
    
    if request.method=="POST":
        if request.form["password"]=="password":
            acc_no=session.get("ac_no")
            pin=request.form["pin"]
            if int(pin)== int(session.get("pin")):
                cursr.execute(""" select u_name from user_data where ac_no=%s;""",(acc_no,))
                data=cursr.fetchone()
                session["username"]=data[0]
                
                return redirect(url_for("home"))
            else :
                return render_template("pin.html",info="*incorrect pin")


    return render_template("pin.html")

@atm_o.route("/home")
def home():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    
    return render_template("home.html",username=session.get("username"))

@atm_o.route("/check_balance")
def check_balance():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    ac_no=session.get("ac_no")
    cursr.execute("""select balance from user_data where ac_no=%s; """,(ac_no,))
    data=cursr.fetchone()
    if data:
        return render_template("balance.html",username=session.get("username"),balance=data[0])



@atm_o.route("/desposite" , methods=["GET","POST"])
def deposite():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    type="deposite"
    if request.method == "POST":
        ac_no=session.get("ac_no")
        d_amount=request.form["d_amount"]
        cursr.execute("""select balance from user_data where ac_no=%s;""",(ac_no,))
        b_amount=cursr.fetchone()
        b_balance=b_amount[0]


        cursr.execute(""" update user_data  set balance = balance + %s where ac_no=%s;""",(d_amount,ac_no))
        db_connctr.commit()

        cursr.execute("""select balance from user_data where ac_no=%s; """,(ac_no,))
        data=cursr.fetchone()
        
        cursr.execute("""insert into transactions(ac_no,transaction,transaction_amount,b_balance,a_balance) values(%s,%s,%s,%s,%s);""",(ac_no,type,d_amount,b_balance,data[0]))
        db_connctr.commit()

        return redirect(url_for("deposite_success"))


    return render_template("deposite.html")

@atm_o.route("/deposite_success")
def deposite_success():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    
    ac_no=session.get("ac_no")
    cursr.execute("""select balance from user_data where ac_no=%s; """,(ac_no,))
    data=cursr.fetchone()


    return render_template(
        "notification_d.html",username=session.get("username"),balance=data[0])




@atm_o.route("/withdraw",methods=["GET","POST"])
def withdraw():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    
    ac_no=session.get("ac_no")
    cursr.execute(""" select pin from user_data where ac_no=%s;""",(ac_no,))
    data=cursr.fetchone()
    
    
    if request.method=="POST":
        w_pin=request.form["w_pin"]
        

        if int(w_pin)==int(data[0]):

            return render_template("withdrawl_amount.html")
        else:
            return render_template("w_pin.html",info="wrong pin entered")

    
    return render_template("w_pin.html")

@atm_o.route("/withdraw_amount",methods=["GET","POST"])
def withdraw_amount():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    type="withdraw"
    ac_no=session.get("ac_no")
    cursr.execute(""" select balance from user_data where ac_no=%s;""",(ac_no,))
    data=cursr.fetchone()
    if request.method=="POST" and request.form["w_form"] == "w_form" :
        w_amount=request.form["w_amount"]

        if float(w_amount) <= float(data[0]):
            cursr.execute("""select balance from user_data where ac_no=%s;""",(ac_no,))
            b_amount=cursr.fetchone()
            b_balance=b_amount[0]

            cursr.execute(""" update user_data set balance=balance-%s where ac_no=%s;""",(w_amount,ac_no))
            db_connctr.commit()

            cursr.execute(""" select balance from user_data where ac_no=%s;""",(ac_no,))
            u_balance=cursr.fetchone()
            session["w_amount"]=w_amount
            session["balance"]=u_balance[0]

            cursr.execute("""insert into transactions(ac_no,transaction,transaction_amount,b_balance,a_balance) values(%s,%s,%s,%s,%s);""",(ac_no,type,w_amount,b_balance,u_balance[0]))
            db_connctr.commit()
            return redirect(url_for("withdraw_success"))
        else:
            return render_template("withdrawl_amount.html",info="* insufficient funds ")
        
@atm_o.route("/withdraw_success")
def withdraw_success():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))

    return render_template(
        "notification_w.html",username=session.get("username"),w_amount=session.get("w_amount"),balance=session.get("balance"))

    
@atm_o.route("/update_pin",methods=["get","post"])
def change_pin():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    ac_no=session.get("ac_no")
    cursr.execute(""" select pin from user_data where ac_no=%s;""",(ac_no,))
    data=cursr.fetchone()

    if request.method=="POST":
         if request.form["c_pin"]=="c_pin":
             ch_pin=request.form["ch_pin"]
             if int(ch_pin)==int(data[0]):
                 
                 return render_template("n_pin.html")
             else:
                 return render_template("u_pin.html",info="*wrong pin entered")
             


    return render_template("u_pin.html")

    
@atm_o.route("/update_pin2",methods=["get","post"])
def  change_pin2():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    ac_no=session.get("ac_no")

    
    if request.form["u_pin"]=="u_pin":
             pin1=request.form["ch_pin1"]
             pin2=request.form["ch_pin2"]
             if pin1==pin2:
                 cursr.execute("""update user_data set pin=%s  where ac_no=%s;""",(pin2,ac_no))
                 db_connctr.commit()
                 session.clear()
                 return render_template("account.html",info="*password updated sucessfully plz login with new pin")
             
             else:
                 return render_template("n_pin.html",info="* not same values in both ")
                 
             
@atm_o.route("/bank_statement")   
def bank_statement():
    if "ac_no" not in session:
        return redirect(url_for("ac_no"))
    
    elif "username" not in session:
        return redirect(url_for("pin"))
    ac_no=session.get("ac_no")

    ac_no=session.get("ac_no")
    cursr.execute(""" select * from transactions where ac_no=%s;""",(ac_no,))
    data=cursr.fetchall()
    cursr.execute(""" select sum(b_balance),sum(a_balance) from transactions where ac_no=%s;""",(ac_no,))
    balances=cursr.fetchone()
    sum_b_balance=balances[0]
    sum_a_balance=balances[1]
    return render_template("bank_statement.html",username=session.get("username"),
                        data=data,sum_b_balance=sum_b_balance,sum_a_balance=sum_a_balance , ac_no="XXXX XXXX "+str(ac_no)[-4:] )




@atm_o.route("/logout")
def logout():
    if "username" not in session:
        return  redirect(url_for("ac_no"))

    session.clear()
    return redirect(url_for("welcome"))

  



if __name__=="__main__":
    atm_o.run(debug=True,port=5003)