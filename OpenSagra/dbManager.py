from flaskext.mysql import MySQL

class dbManager(object):
    def __init__(self, app):
        '''
        Creates an instance of a class that manages the database connected to the app\n
        a list of the functions available are:\n
            1- load_list(self, plates)
            2- load_from_file(filename)\n
            3- add_default_admin()\n
            4- get_by_username_role_password(username, role, password)\n
            5- get_by_role(role)\n
            6- insert_admin(username, role, password)\n
            7- delete_from_admin(id, session_username)\n
        '''
        self.mysql = MySQL()
        self.mysql.init_app(app)
        self.conn = self.mysql.connect()
        self.cursor = self.conn.cursor()
    
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
                
    def add_default_admin(self):
        if not self.get_by_role("admin"):
            self.insert_admin("admin", "admin", "semprelasolita")
            self.insert_admin("cashier", "cashier", "semprelasolita")
    
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
    
    def get_by_role(self, role):
        self.cursor.execute(
            f'''
                SELECT id, username 
                FROM admin
                WHERE  role = "{role}";
            '''
        )
        return self.cursor.fetchall()
    
    def insert_admin(self, username, role, password):
        self.cursor.execute(
            f'''
                INSERT INTO admin (username, role, password) VALUES
                    ("{username}", "{role}", MD5("{password}"));
            '''
        )
        self.conn.commit()
    
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
    
    def get_ingredients(self):
        self.cursor.execute(
            '''
                SELECT *
                FROM ingredient; 
            '''
        )
        return self.cursor.fetchall()

    def update_ingredient(self, id, quantity):
        self.cursor.execute(
            f'''
                UPDATE ingredient
                SET    availability = availability + {quantity}
                WHERE  id = {id};
            '''
        )
        self.conn.commit()

    def remove_ingredient(self, name, day):
        #serve il giorno
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
            if availability < ingredient[1]:
                return False
            
            self.update_ingredient(ingredient[0], -ingredient[1])
        return True