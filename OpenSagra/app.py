#lettura dal file di configurazione
from configparser import ConfigParser
config = ConfigParser()
config.read("settings/config.ini")
dbconfig = config["DATABASE"]

#caricamento piatti disponibili da file json
import utils
plates = utils.load_plates("settings/plates.json")

#ottenimento giorno per mostrare i piatti disponibili
from datetime import date, timedelta, datetime
import calendar
my_date = date.today()

#Flask
from flask import Flask, flash, url_for, render_template, redirect, request, session

#creazione e configurazione app e database
app = Flask(__name__)
app.secret_key = config["APP"]["SECRET_KEY"]
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=int(config["APP"]["PERMANENT_SESSION_LIFETIME"]))
app.config["MYSQL_DATABASE_HOST"] = dbconfig["MYSQL_DATABASE_HOST"]
app.config["MYSQL_DATABASE_PORT"] = int(dbconfig["MYSQL_DATABASE_PORT"])
app.config["MYSQL_DATABASE_USER"] = dbconfig["MYSQL_DATABASE_USER"]
app.config["MYSQL_DATABASE_PASSWORD"] = dbconfig["MYSQL_DATABASE_PASSWORD"]
app.config["MYSQL_DATABASE_DB"] = dbconfig["MYSQL_DATABASE_DB"]

#per la connessione al database sarà utilizzata una classe personalizzata
from dbManager import dbManager
from hashlib import md5

#creazione istanza del manager
db = dbManager(app)
#caricamento file sql con impostazioni
db.load_from_file("database.sql")
#aggiunta admin di default per la prima installazione
db.add_default_admin()
#caricamento impostazioni predefinite per le posizioni e ingredienti
db.load_json("settings/location.json")
db.load_ingredients("settings/ingredients.json")
db.load_list(plates)

#pagina index
@app.route("/")
def index():
    return render_template(
        "index.html",
        #passo i piatti disponibili nel giorno corrente(aggiornato dinamicamente)
        plates=utils.filter_plates(
            calendar.day_name[my_date.weekday()].lower(),
            plates
        )
    )

#login
@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

#pagina admin
@app.route("/admin", methods=["POST", "GET"])
def admin():
    #se con post controllo credenziali
    if request.method == "POST":
        username = request.form["username"]
        password = md5(request.form["password"].encode()).hexdigest()
        #controllo password sul db con md5 (admin)
        if db.get_by_username_role_password(username, "admin", password):
            session["username"] = username
            session["auth"] = True
            session.permanent = True
        #controllo password sul db con md5 (cassiere)
        elif db.get_by_username_role_password(username, "cashier", password):
            session["username"] = username
            session["cashier"] = True
            session.permanent = True
            return redirect(url_for("cashier"))
        else:
            #errore di inserimento dati di login con messaggio flash
            flash("Invalid username or password.")
            return redirect(url_for("login"))
    #se loggato carico dati per popolare la tabella degli utenti
    if "auth" in session:
        args = (
            db.get_by_role("admin"), 
            db.get_by_role("cashier")
        )
        return render_template("admin.html", args=args)
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#aggiunta utente dal pannello admin
@app.route("/admin/add", methods=["POST", "GET"])
def admin_addadmin():
    #controllo metodo
    if request.method == "POST":
        if request.form["password_check"] == request.form["password"]:
            #inserimento utente nel db
            db.insert_admin(request.form["username"], request.form["role"], request.form["password"])
        else:
            #errore password di controllo
            flash("Passwords did not match.")
        return redirect(url_for("admin"))
    #esclusione accesso non autorizzato
    return redirect(url_for("index"))

#rimozione utente dal pannello admin
@app.route("/admin/remove/<int:id>", methods=["POST", "GET"])
def admin_remove(id):
    #controllo autenticazione
    if session["auth"]:
        #rimozione dal database
        db.delete_from_admin(id, session["username"])
        return redirect(url_for("admin"))
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#pagina per il cassiere
@app.route("/cashier")
def cashier():
    #controllo sessione per il login
    if "cashier" in session:
        if session["cashier"]:
            return render_template("cashier.html")
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#pagina per mostrare i piatti disponibili in base al giorno selezionato e ingredienti
@app.route("/pietanze", methods=["POST", "GET"])
def pietanze():
    if request.method == "POST":
        return render_template(
            "pietanze.html",
            #funzione per il filtraggio dei piatti
            plates=utils.filter_plates(
                request.form["day"], 
                plates,
                request.form["ingredients"].split(" ") 
                if request.form["ingredients"] 
                else request.form["ingredients"]
            )
        )
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#pagina per la creazione di uno scontrino
@app.route("/scontrino", methods=["POST", "GET"])
def scontrino():
    #controllo sessione
    if "cashier" in session:
        if session["cashier"] and request.method == "POST":
            session["day"] = request.form["day"]
            return render_template(
                "scontrino.html",
                #filtraggio piatti in base al giorno selezionato dal cassiere
                plates=utils.filter_plates(
                    request.form["day"],
                    plates
                )
            )
        
        return render_template(
            "scontrino.html", 
            plates=utils.filter_plates(
                session["day"],
                plates
            )
        )
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#pagina temporanea per la generazione dello scontrino fisico
@app.route("/gen", methods=["POST", "GET"])
def gen():
    if "cashier" in session:
        if session["cashier"]:
            #ottenimento piatti selezionai dal cassiere
            items = utils.get_requested_items(request.form, plates)
            for item in items:
                #rimozione dal db degli ingredienti richiesti
                esito = db.remove_ingredient(item[0], item[1], session["day"])
                #in caso manchino ingredienti torneremo un alert
                if not esito:
                    flash("Failed to update ingredients selected")
                    return redirect(url_for("scontrino"))
            #per la stampa dello scontrino come richiesto i piatti verranno raggruppati in base al posto di ritiro es. ("Cucina" per un panino, "Bar" per una birra)
            grouped_items = utils.group_items(items, db)
            for item in grouped_items:
                #stampa dello scontrino
                utils.print_receipt(
                    item,
                    item[0][4], 
                    session["day"],
                    datetime.now().strftime("%H:%M:%S")
                )
            return redirect(url_for("scontrino"))
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

#pagina per mostrare gli ingredienti rimanenti in magazzino
@app.route("/storage", methods=["POST", "GET"])
def storage():
    if session["auth"]:
        #ottenimento ingredienti
        ingredients = db.get_ingredients()
        return render_template(
            "storage.html", 
            ingredients=ingredients
        )
    return redirect(url_for("login"))

#aggiornamento quantità ingrediente in magazzino
@app.route("/storage/<int:id>", methods=["POST", "GET"])
def storage_update(id):
    if session["auth"]:
        if request.method == "POST":
            #aggiornamento
            db.update_ingredient(id, request.form["quantity"])
        return redirect(url_for("storage"))
    #rimane il caso in cui l'utente non è loggato
    flash("Please log in first.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
