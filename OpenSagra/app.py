from configparser import ConfigParser
config = ConfigParser()
config.read("settings/config.ini")
dbconfig = config["DATABASE"]

import utils
plates = utils.load_plates("settings/plates.json")

from datetime import date, timedelta
import calendar
my_date = date.today()

from flask import Flask, flash, url_for, render_template, redirect, request, session
app = Flask(__name__)
app.secret_key = config["APP"]["SECRET_KEY"]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=int(config["APP"]["PERMANENT_SESSION_LIFETIME"]))
app.config["MYSQL_DATABASE_HOST"] = dbconfig["MYSQL_DATABASE_HOST"]
app.config["MYSQL_DATABASE_PORT"] = int(dbconfig["MYSQL_DATABASE_PORT"])
app.config["MYSQL_DATABASE_USER"] = dbconfig["MYSQL_DATABASE_USER"]
app.config["MYSQL_DATABASE_PASSWORD"] = dbconfig["MYSQL_DATABASE_PASSWORD"]
app.config["MYSQL_DATABASE_DB"] = dbconfig["MYSQL_DATABASE_DB"]

from dbManager import dbManager
from hashlib import md5

db = dbManager(app)
db.load_from_file("database.sql")
db.add_default_admin()
db.load_json("settings/location.json")
db.load_ingredients("settings/ingredients.json")
db.load_list(plates)

@app.route("/")
def index():
    return render_template(
        "index.html", 
        plates=utils.filter_plates(
            calendar.day_name[my_date.weekday()].lower(),
            plates
        )
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/admin", methods=["POST", "GET"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = md5(request.form["password"].encode()).hexdigest()
        if db.get_by_username_role_password(username, "admin", password):
            session["username"] = username
            session["auth"] = True
            session.permanent = True
        elif db.get_by_username_role_password(username, "cashier", password):
            session["username"] = username
            session["cashier"] = True
            session.permanent = True
            return redirect(url_for("cashier"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("login"))
    if "auth" in session:
        args = (
            db.get_by_role("admin"), 
            db.get_by_role("cashier")
        )
        return render_template("admin.html", args=args)
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/admin/add", methods=["POST", "GET"])
def admin_addadmin():
    if request.method == "POST":
        if request.form["password_check"] == request.form["password"]:
            db.insert_admin(request.form["username"], request.form["role"], request.form["password"])
        else:
            flash("Passwords did not match.")
        return redirect(url_for("admin"))
    return redirect(url_for("index"))

@app.route("/admin/remove/<int:id>", methods=["POST", "GET"])
def admin_remove(id):
    if session["auth"]:
        db.delete_from_admin(id, session["username"])
        return redirect(url_for("admin"))
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/cashier")
def cashier():
    if "cashier" in session:
        if session["cashier"]:
            return render_template("cashier.html")
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/pietanze", methods=["POST", "GET"])
def pietanze():
    if request.method == "POST":
        return render_template(
            "pietanze.html", 
            plates=utils.filter_plates(
                request.form["day"], 
                plates,
                request.form["ingredients"].split(" ") 
                if request.form["ingredients"] 
                else request.form["ingredients"]
            )
        )
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/scontrino", methods=["POST", "GET"])
def scontrino():
    if "cashier" in session:
        if session["cashier"] and request.method == "POST":
            session["day"] = request.form["day"]
            return render_template(
                "scontrino.html", 
                plates=utils.filter_plates(
                    request.form["day"],
                    plates
                )
            )
        
        flash("Failed to update ingredients selected")
        return render_template(
            "scontrino.html", 
            plates=utils.filter_plates(
                session["day"],
                plates
            )
        )
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/gen", methods=["POST", "GET"])
def gen():
    if "cashier" in session:
        if session["cashier"]:
            items = utils.get_requested_items(request.form, plates)
            total_cost = utils.get_total_cost(items)
            for item in items:
                esito = db.remove_ingredient(item[0], session["day"])
                if not esito:
                    return redirect(url_for("scontrino"))
            # utils.print_receipt(items, total_cost)
            return redirect(url_for("scontrino"))
    flash("Please log in first.")
    return redirect(url_for("login"))

@app.route("/storage", methods=["POST", "GET"])
def storage():
    if session["auth"]:
        ingredients = db.get_ingredients()
        return render_template(
            "storage.html", 
            ingredients=ingredients
        )
    return redirect(url_for("login"))

@app.route("/storage/<int:id>", methods=["POST", "GET"])
def storage_update(id):
    if session["auth"]:
        if request.method == "POST":
            db.update_ingredient(id, request.form["quantity"])
        return redirect(url_for("storage"))
    flash("Please log in first.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
