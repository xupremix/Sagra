from flaskext.mysql import MySQL

#database manager
class dbManager(object):
    def __init__(self, app):
        '''
        Creates an instance of a class that manages the database connected to the app\n
        a list of the functions available are:\n
            1- load_list(self, plates)\n
            2- load_from_file(filename)\n
            3- add_default_admin()\n
            4- get_by_username_role_password(username, role, password)\n
            5- get_by_role(role)\n
            6- insert_admin(username, role, password)\n
            7- delete_from_admin(id, session_username)\n
            8- get_ingredients()\n
            9- update_ingredient(id, quantity)\n
            10- remove_ingredient(name, day)\n
            11- get_location(name)\n
        '''
        self.mysql = MySQL()
        self.mysql.init_app(app)
        self.conn = self.mysql.connect()
        self.cursor = self.conn.cursor()
    
    #caricamento posizione
    def load_json(self, filename):
        self.cursor.execute(
            '''
                SELECT * FROM location;
            '''
        )

        if self.cursor.fetchall(): return

        from json import load
        with open(filename, "r") as f:
            elems:dict = load(f)
            for key, value in elems.items():
                self.cursor.execute(
                    f'''
                        INSERT INTO location (name, type) VALUES
                            ("{value}", "{key}");
                    '''
                )
            self.conn.commit()

    def load_list(self, plates):
        #caricamento piatti
        self.cursor.execute(
            f'''
                SELECT * FROM dish;
            '''
        )

        if self.cursor.fetchall(): return

        for plate in plates:
            self.cursor.execute(
                f'''
                    SELECT id
                    FROM location
                    WHERE   type = "{plate[1]}";
                '''
            )
            location = self.cursor.fetchone()[0]
            self.cursor.execute(
                f'''
                    INSERT INTO dish (name, description, price, day, location) VALUES
                        ("{plate[2]}", "{plate[3]}" , "{plate[5]}", "{plate[0]}", "{location}");
                '''
            )

            #popolazione tabella composizione con riferimenti esterni
            for ing in plate[4]:
                self.cursor.execute(
                    f'''
                        SELECT id
                        FROM ingredient
                        WHERE   name = "{ing[0]}";
                    '''
                )
                id_ing = self.cursor.fetchone()[0]
                self.cursor.execute(
                    f'''
                        SELECT id
                        FROM dish
                        WHERE   name = "{plate[2]}";
                    '''
                )
                id_dish = self.cursor.fetchone()[0]
                self.cursor.execute(
                    f'''
                        INSERT INTO composition (idDish, idIngredient, day, quantity) VALUES
                            ("{id_dish}", "{id_ing}", "{plate[0]}", "{ing[1]}");
                    '''
                )
                self.conn.commit()

    #caricamento ingredienti
    def load_ingredients(self, filename):
        self.cursor.execute(
            '''
                SELECT * FROM ingredient;
            '''
        )

        if self.cursor.fetchall(): return

        from json import load
        with open(filename, "r") as f:
            ingredients:dict = load(f)
            for name, availability in ingredients.items():
                self.cursor.execute(
                    f'''
                        INSERT INTO ingredient (name, availability) VALUES
                            ("{name}", "{availability}");
                    '''
                )
            self.conn.commit()

    #caricamento configurazione base del db
    def load_from_file(self, filename):
        with open(filename, 'r') as f:
            data = f.read().split("\n\n")
            for elem in data:
                self.cursor.execute(
                    f'''
                        {elem}
                    '''
                )
                self.conn.commit()
    
    #aggiunta grezza degli utenti bases
    def add_default_admin(self):
        if not self.get_by_role("admin"):
            self.insert_admin("admin", "admin", "semprelasolita")
            self.insert_admin("cashier", "cashier", "semprelasolita")
    
    
    #ottenimento utente in base al nome utente, ruolo e password (già eseguito l'md5)
    def get_by_username_role_password(self, username, role, password):
        self.cursor.execute(
            f'''
                SELECT *
                FROM admin
                WHERE   username = "{username}" AND
                        password = "{password}" AND
                        role = "{role}";
            '''
        )
        return self.cursor.fetchone()
    
    #ottenimento utente in base al ruolo
    def get_by_role(self, role):
        self.cursor.execute(
            f'''
                SELECT id, username 
                FROM admin
                WHERE  role = "{role}";
            '''
        )
        return self.cursor.fetchall()
    
    #inserimento nella tabella admin di un utente
    def insert_admin(self, username, role, password):
        self.cursor.execute(
            f'''
                INSERT INTO admin (username, role, password) VALUES
                    ("{username}", "{role}", MD5("{password}"));
            '''
        )
        self.conn.commit()
    
    #rimozione dalla tabella admin di un utente 
    def delete_from_admin(self, id, session_username):
        self.cursor.execute(
            f'''
                DELETE FROM admin
                WHERE   id = {id} AND 
                        username <> "admin" AND
                        username <> "{session_username}";
            '''
        )
        self.conn.commit()
    
    #ottenimento ingredienti
    def get_ingredients(self):
        self.cursor.execute(
            '''
                SELECT *
                FROM ingredient; 
            '''
        )
        return self.cursor.fetchall()

    #aggiornamento quantità di un ingrediente nel db
    def update_ingredient(self, id, quantity):
        self.cursor.execute(
            f'''
                UPDATE ingredient
                SET    availability = availability + {quantity}
                WHERE  id = {id};
            '''
        )
        self.conn.commit()

    #rimozione di un determinato ingrediente
    def remove_ingredient(self, name, quantity, day):
        self.cursor.execute(
            f'''
                SELECT ingredient.id, composition.quantity
                FROM dish JOIN composition ON 
                    dish.id = composition.idDish AND
                    dish.name = "{name}" AND (
                        composition.day = "{day}" OR
                        composition.day = "everyday"
                    )
                    JOIN ingredient ON
                        composition.idIngredient = ingredient.id;
            '''
        )
        ingredients = self.cursor.fetchall()
        for ingredient in ingredients:
            self.cursor.execute(
                f'''
                    SELECT availability
                    FROM ingredient
                    WHERE  id = {ingredient[0]};
                '''
            )
            
            availability = self.cursor.fetchone()[0]
            
            #controllo che la rimozione sia fattibile
            if availability < ingredient[1]*quantity:
                return False
            
            self.update_ingredient(ingredient[0], -ingredient[1]*quantity)
        return True
    
    #ottentimento posizione in base al nome pre-assegnato
    def get_location(self, name):
        self.cursor.execute(
            f'''
                SELECT location.name
                FROM dish JOIN location ON
                    dish.location = location.id AND
                    dish.name = "{name}";
            '''
        )
        return self.cursor.fetchone()[0]