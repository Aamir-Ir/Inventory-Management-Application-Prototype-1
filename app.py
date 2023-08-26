from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import functools
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = 'REENA_INV'

'''
    Class Declaration For 3 Objects:

    1) rawMaterials object describes the attributes name, cost, units, quantity, and code. All this is important information that will be an instance of the rawMaterials object. One thing 
    note the code will hold all finished product codes that are associated with the raw material instance. 

    2) packagingMaterials object is very similar to the object described above it has attributes for name, cost, quantity, and code. All this is important information that will be an instance
    of the rawMaterials object. One thing to note is that the code will hold all finished product codes that are associated with the packaging material instance.

    3) Finished Products = products object which will have attributes code, productName, cost, unit, quantity, and price. These attributes consist of the information of each specific product.
    Two other attributes of interest are rawMaterials, and packagingMaterials. These two are lists, think of these lists containing the requred raw material objects and packaging material objects 
    these two lists together consists of the formula of the finished product.
'''

# rawMaterials class.

class rawMaterials:
     
     # Constructor method initalizes the object with the given parameters.

     def __init__(self, name, cost, units, quantity, code):
        self.name = name
        self.cost = cost
        self.units = units
        self.quantity = quantity
        self.code = code

# packagingMaterials class.

class packagingMaterials:
     
     # Constructor method initalizes the object with the given parameters.

     def __init__(self, name, cost, quantity, code):
        self.name = name
        self.cost = cost
        self.quantity = quantity
        self.code = code

# products class.

class products:

    # Constructor method initalizes the object with the given parameters.

    def __init__(self, code, productName, cost, unit, quantity, price, rawMaterials=None, packagingMaterials=None):
        self.code = code
        self.name = productName
        self.cost = cost
        self.unit = unit
        self.quantity = quantity
        self.price = price
        if rawMaterials:
            self.rawMaterials = rawMaterials
        else:
            self.rawMaterials = []
        if packagingMaterials:
            self.packagingMaterials = packagingMaterials
        else:
            self.packagingMaterials = []


def createAllTables(restartDataBase):

    '''
        The createAllTables() function will be used to generally create an intial data base consisting of the tables described below. The restartDataBase will decide if the database should 
        be deleted or not to start over or continue.
    '''

    # Remove existing database file if it exists and if restartDataBase is true.

    if (restartDataBase == True):
        if os.path.exists('mydatabase.db'):
            os.remove('mydatabase.db')
            print("Database Deleted. Creating New One...\n")

    # Create a connection to the SQLite database.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # Create the FinishedProduct table (Used to hold information for finished products). Products object will hold relavent information from here.
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS FinishedProduct (
            code TEXT PRIMARY KEY,
            productName TEXT UNIQUE,
            cost REAL,
            unit TEXT,
            quantity INTEGER,
            price REAL
        )
    ''')

    # Create the RawMaterials table (Used to hold information for raw materials). RawMaterials object will hold relavent information from here.

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RawMaterials (
            materialID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            cost REAL,
            units TEXT,
            quantity INTEGER,
            associated_codes TEXT
        )
    ''')

    # Create the PackagingMaterials table (Used to hold information for packaging materials). packagingMaterials object will hold relavent information from here.

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PackagingMaterials (
            materialID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            cost REAL,
            quantity INTEGER,
            associated_codes TEXT
        )
    ''')

    # Create the ProductMaterialAssociation table (Used for many-to-many relationships between Product and materials, this is used so that mateirals can be associated with multiple product codes).
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProductMaterialAssociation (
            associationID INTEGER PRIMARY KEY,
            materialID INTEGER,
            materialType TEXT,
            code TEXT,
            FOREIGN KEY (materialID, materialType) REFERENCES Materials (materialID, materialType),
            FOREIGN KEY (code) REFERENCES FinishedProduct (code)
        )
    ''')

    # Create the Users table, this will store the information of all the users that have access to the app.

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT UNIQUE
        )
    ''')
    
    # Commit the changes and close the connection.

    conn.commit()
    conn.close()


def insert_data_with_pre_filled_inputs():

    '''
        This insert_data_with_pre_filled_inputs() function is used for inserting values into the tables so that the database is pre-filled with cases. This function was only used for testing
        will not be used in production (can remove).
    '''

    try:

        # Create a connection to the SQLite database + add a cursor to edit.

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        # Insert test data into the FinishedProduct table.

        cursor.execute('''
            INSERT INTO FinishedProduct (code, productName, cost, unit, quantity, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("FP001", "Cake", 10.99, "g", 100, 20.99))

        # Insert test data into the RawMaterials table.

        cursor.execute('''
            INSERT INTO RawMaterials (name, cost, units, quantity, associated_codes)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Sugar", 2.99, "g", 50, "FP001"))

        # Insert test data into the PackagingMaterials table.

        cursor.execute('''
            INSERT INTO PackagingMaterials (name, cost, quantity, associated_codes)
            VALUES (?, ?, ?, ?)
        ''', ("Sugar Box", 2.99, 200, "FP001"))

        # Insert associations between materials and finished products into ProductMaterialAssociation table.

        cursor.execute('''
            INSERT INTO ProductMaterialAssociation (materialID, materialType, code)
            VALUES (?, ?, ?)
        ''', (1, 'RawMaterials', "FP001")) # MaterialID 1 corresponds to the "Sugar" raw material.

        cursor.execute('''
            INSERT INTO ProductMaterialAssociation (materialID, materialType, code)
            VALUES (?, ?, ?)
        ''', (1, 'PackagingMaterials', "FP001")) # MaterialID 1 corresponds to the "Sugar Box" packaging material.
        
        conn.commit()

    # Errors + close connection.

    except sqlite3.Error:
        conn.rollback()
        print("Failed to insert data. Please try again.")
    finally:
        conn.close()


def inventory():

    '''
        Inventory is the basic function that is used to drive the program as it will consist of the interaction with the user through input and output. Greet and run the program which
        will genrally allow the user to Recive, Use, Adjust and View the database. Now you can perform more advanced operations by adding/removing products and/or materials, and lastly
        you can update associations allowing you to add connections between products and materials that are needed so that you can understand what products are associated with which 
        materials and if the system is updating everything correctly this was added for ease for the user.
    '''

    # Greet user and let them know their options + collect user input.

    print("Welcome to the Inventory page.\n")
    print("1. Recive.\n")
    print("2. Use.\n")
    print("3. Adjust.\n")
    print("4. View Database.\n")
    print("5. Add Entries.\n")
    print("6. Delete Entires.\n")
    print("7. Update Associations.\n")
    print("8. Quit (Type 0).\n")

    decision = int(input())
    
    # In the While loop use the input condition 0 to exit, otherwise continue the inventory logic.

    while (decision != 0):

        # Case 1: If the user is in the correct range of input, run the function they have selected.

        if (decision >= 0 and decision < 8):

            # Case 1; Subcase 1: Run the Recive function.

            if (decision == 1):
                recive()
            
            # Case 1; Subcase 2: Run the Use function.

            elif (decision == 2):
                use()
            
             # Case 1; Subcase 3: Run the adjust function.

            elif (decision == 3):
                adjust()
            
            # Case 1; Subcase 4: Run the Viewdata base function.

            elif (decision == 4):

                # Few ways to view the database.

                print("How do you want to view the database.\n")

                # 1) View the database by picking a specfic table or all of them and view each entry in the table.

                print("1) Table View (Can view each entry for 1 or all tables).\n")

                # 2) View in a list format each raw material, packaging material, and finished product. This view will give a better understanding of which materials are associated with which product.
                
                print("2) List a summary of all Raw Materials, Packaging Materials, and Finsihed Products, with their associations.\n")
                viewType = int(input())

                # Case 1; Subcase 4; subsubcase 1: run view_database, this will give the user the tables view of the database.

                if (viewType == 1):
                    view_database()

                # Case 1; Subcase 4; subsubcase 2: create objects with the entries from all the tables, this will help the user see the assciations better.

                elif (viewType == 2):

                    # Call create_objects_from_tables function to create objects (rawMaterials, packagingMaterials, products) of each entry in the tables with respect to the type of table the data is stored in.

                    raw_materials, packaging_materials, products = create_objects_from_tables()

                    # Print the objects for the user to see. Starting with Raw Material.

                    print("\nList of Raw Materials (Table Format: Name, Cost, Units, Quantity, Associated Product Codes):\n")
                    for rm in raw_materials:
                        print(rm.name, rm.cost, rm.units, rm.quantity, rm.code)

                    # Print all the Packaging Materials.

                    print("\nList of Packaging Materials (Table Format: Name, Cost, Quantity, Associated Product Codes):\n")
                    for pm in packaging_materials:
                        print(pm.name, pm.cost, pm.quantity, pm.code)

                    # Print all the Finished Products with materials that associate with the product.

                    print("\nList of Products (Table Format: Code, Name, Cost, Units, Quantity, Price) Also associated product materials list after:\n")
                    for product in products:
                        print(product.code, product.name, product.cost, product.unit, product.quantity, product.price)

                        # Print all the associated materials with the product.

                        print("\nRaw Materials associated wih this product:")
                        for rm in product.rawMaterials:
                            print(rm.code, rm.name, rm.cost, rm.units, rm.quantity)

                        print("\nPackaging Materials associated wih this product:")
                        for pm in product.packagingMaterials:
                            print(pm.code, pm.name, pm.cost, pm.quantity)
                        print()

            # Case 1; Subcase 5: Add a new entry to one of the tables.

            elif (decision == 5):
                add_entry()
            
            # Case 1; Subcase 6: Remove an entry from one of the tables.

            elif (decision == 6):
                delete_entry()

            # Case 1; Subcase 7: Update the assocations between products and materials.

            elif (decision == 7):
                update_associations_menu()

            # After a successful run of the expected operations, ask for the next operation.

            print("\nNext Operation.\n")
            print("1. Recive.\n")
            print("2. Use.\n")
            print("3. Adjust.\n")
            print("4. View Database.\n")
            print("5. Add Entries.\n")
            print("6. Delete Entires.\n")
            print("7. Update Associations.\n")
            print("8. Quit (Type 0).\n")
            decision = int(input())
            
        else:
            print("\nInvalid Input.\n")
            print("1. Recive.\n")
            print("2. Use.\n")
            print("3. Adjust.\n")
            print("4. View Database.\n")
            print("5. Add Entries.\n")
            print("6. Delete Entires.\n")
            print("7. Update Associations.\n")
            print("8. Quit (Type 0).\n")
            decision = int(input("Invalid Input, Try Again: "))
    return


def update_quantity(table_name, name, quantity, operation):

    '''
        The update_quantity() function is used in conjunction with both use() and receive() funcitons to update the value depending on the type of operation determined by the previous functions.
    '''

    # Connect to the database + create a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Error check to confirm if an update actually took place.

    try:

        # Distinguish the table types Case 1 is specific to add into the Finsihed Products table as it will look for the product code, while Case 2 will add to the material tables by identifying a name.

        if table_name == 'FinishedProduct':

            # Will result in a product FinishedProduct table with only the quantity column where the code of the product matches, this will result in only 1 match as codes should be unique.

            cursor.execute(f"SELECT quantity FROM {table_name} WHERE code = ?", (name,))

        else:

            # Will result in a material specified from table name with only the quantity column where the name of the product matches, this will result in only 1 match as names should be unique.

            cursor.execute(f"SELECT quantity FROM {table_name} WHERE name = ?", (name,))
        
        # Fetchone function here collects one row entry from the table that matches the name in a list, the only thing that should be seen is the quantity column and the first entry should be the desired quantity the user wished to change.

        current_quantity = cursor.fetchone()[0]
        
        # Case 1: Chech for subtraction, check if the current quantity is enough to perform the operation.

        if operation == 'subtract' and current_quantity < quantity:
            raise ValueError(f"Insufficient quantity of {name} in {table_name}. Cannot perform the operation.")
        
        # Case 2: Perform the update operation, watch out for table types.

        if table_name == 'FinishedProduct':

            # Add or Subtract into FinsihedProduct table call will be determined by recive or use function.

            if operation == 'add':
                cursor.execute(f"UPDATE {table_name} SET quantity = quantity + ? WHERE code = ?", (quantity, name))
            elif operation == 'subtract':
                cursor.execute(f"UPDATE {table_name} SET quantity = quantity - ? WHERE code = ?", (quantity, name))
        else:

            # Add or Subtract into any of the materials table call will be determined by recive or use function.

            if operation == 'add':
                cursor.execute(f"UPDATE {table_name} SET quantity = quantity + ? WHERE name = ?", (quantity, name))
            elif operation == 'subtract':
                cursor.execute(f"UPDATE {table_name} SET quantity = quantity - ? WHERE name = ?", (quantity, name))
        
        # Check if any rows were affected by the update operation. This is to ensure if something was actually changed in the database this is added to ensure if there was a change.
        
        if cursor.rowcount == 0:
            raise sqlite3.Error("Item not found in the table.")
        
        # Commit changes + confrim with user what took place.

        conn.commit()
        print(f"Quantity for {name} in {table_name} updated successfully.")

    # Errors: Let the user know if something went wrong + close connection.

    except sqlite3.Error as e: 
        conn.rollback()
        print(f"Failed to update quantity for {name} in {table_name}. Error: {e}")
    except ValueError as e:
        conn.rollback()
        print(e)
    finally:
        conn.close()


def recive():

    '''
        The recive() function is used to receive items (raw materials, packaging materials, and finished products), It will update the quantity field in any of the tables in the database not
        the objects as the objects will be used to print information.
    '''

    # Greet the user + get input.

    print("\nWelcome to the recive function. Here you can add what you have received. This includes Raw Materials, Packaging Materials, and Finished Products.")
    print("What did you recive today:\n")
    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    recive = int(input())

    # While user is not done receiving items, keep the program running.

    while (run == True):

        # Case 1: Add Raw Materials.

        if (recive == 1):
            name = input("Enter the name of the raw material: ")
            quantity = int(input("How many did you receive: "))
            update_quantity('RawMaterials', name, quantity, 'add')
            run = False

        # Case 2: Add Packaging Materials.

        elif (recive == 2):
            name = input("Enter the name of the packaging material: ")
            quantity = int(input("How many did you receive: "))
            update_quantity('PackagingMaterials', name, quantity, 'add')
            run = False

        # Case 3: Add Products.

        elif (recive == 3):
            name = input("Enter the product code of the finished product: ")
            quantity = int(input("How many did you receive: "))
            update_quantity('FinishedProduct', name, quantity, 'add')
            run = False

        # Case 4: Invalid Input.

        else:
            recive = int(input("Invalid Input, Try Again: "))


def use():

    '''
        The use() function is used to use items (raw materials, packaging materials, and finished products). It will update the tables in the database, not the objects.
    '''

    # Greet the user + get input.

    print("\nWelcome to the use function. Here you can remove what has already been used. This includes Raw Materials, Packaging Materials, and Finished Products.")
    print("\nWhat do you want to use today:\n")
    
    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    use = int(input())

    # While the user does not insert a useful value, keep asking.

    while (run == True):

        # Case 1: Use Raw Materials.

        if (use == 1):
            name = input("Enter the name of the raw material: ")
            quantity = int(input("How many did you use: "))
            update_quantity('RawMaterials', name, quantity, 'subtract')
            run = False

        # Case 2: Use Packaging Materials.

        elif (use == 2):
            name = input("Enter the name of the packaging material: ")
            quantity = int(input("How many did you use: "))
            update_quantity('PackagingMaterials', name, quantity, 'subtract')
            run = False

        # Case 3: Use Finished Products.
        
        elif (use == 3):
            name = input("Enter the product code of the finished product: ")
            quantity = int(input("How many did you use: "))
            update_quantity('FinishedProduct', name, quantity, 'subtract')
            run = False

        # Case 4: Invalid Input.

        else:
            use = int(input("Invalid Input, Try Again: "))


def adjust_quantity(table_name, name, new_quantity):

    '''
        The adjust_quantity() function is used in conjunction with the adjust function to change the quantity of the items in the respective tables (raw materials, packaging materials, and finished products). It will update the tables in the database.
    '''

    # Connect to database + add cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Try-except block added to see if data was properly adjusted.

    try:

        # Check if the new quantity is negative, if so, raise an error.

        if new_quantity < 0:
            raise ValueError("Quantity cannot be set to a negative value.")
        
        # Update depending on the table.

        if table_name == 'FinishedProduct':
            cursor.execute(f"UPDATE {table_name} SET quantity = ? WHERE code = ?", (new_quantity, name))
        else:
            cursor.execute(f"UPDATE {table_name} SET quantity = ? WHERE name = ?", (new_quantity, name))

        # Check if any rows were affected by the update operation.

        if cursor.rowcount == 0:
            raise sqlite3.Error("Item not found in the table.")
        
        # Commit changes and let the user know of the chnages.

        conn.commit()
        print(f"Quantity for {name} in {table_name} adjusted successfully.")

    # All special cases are checked for + close connection.

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Failed to adjust quantity for {name} in {table_name}. Error: {e}")
    except ValueError as e:
        conn.rollback()
        print(e)
    finally:
        conn.close()


def adjust():

    '''
        The adjust function is used to adjust the value of the items completely (raw materials, packaging materials, and finished products), It will update the tables in the database not the
        objects.
    '''
    
    # Greet user + collect the user input.

    print("\nWelcome to the adjust function. Here you can update the value of Raw Materials, Packaging Materials, and Finished Products to a fixed value. Use this function for corrections of values if you simply wish to take use or receive use the other functions.")
    print("\nWhat do you want to adjust today: \n")

    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    adjustment = int(input())

    # While the user does not provide a valid number loop.

    while (run == True):

        # Case 1: Adjust the Raw Materials.

        if (adjustment == 1):
            name = input("Enter the name of the raw material: ")
            quantity = int(input("Adjust the value: "))
            adjust_quantity('RawMaterials', name, quantity)
            run = False

        # Case 2: Adjust the Packaging Materials.

        elif (adjustment == 2):
            name = input("Enter the name of the packaging material: ")
            quantity = int(input("Adjust the value: "))
            adjust_quantity('PackagingMaterials', name, quantity)
            run = False

        # Case 3: Adjust the Finished Products.

        elif (adjustment == 3):
            name = input("Enter the product code of the finished product: ")
            quantity = int(input("Adjust the value: "))
            adjust_quantity('FinishedProduct', name, quantity)
            run = False

        # Case 4: Invalid Input.

        else:
            adjustment = int(input("Invalid Input, Try Again: "))


def print_finished_products():

    '''
        The print_finished_products() function is used to print all entries in the FinishedProducts table.
    '''
    
    # Connect to database + add cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Used a try-except block just incase of error when reteriving table.

    try:

        # Get all the FinsishedProducts entries through rows in a tuple.

        cursor.execute('SELECT * FROM FinishedProduct')
        finished_products = cursor.fetchall()

        # Case 1: Let user know if there are no products.

        if not finished_products:
            print("No finished products found.")

        # Case 2: Print each of the finished products.

        else:
            print("Finished Products:")
            for product in finished_products:

                # product is one entry a 1D tuple unpacking is used here to collect all the indivisual information which will be told to the user.

                code, product_name, cost, unit, quantity, price = product
                print(f"Code: {code}, Name: {product_name}, Cost: {cost}, Unit: {unit}, Quantity: {quantity}, Price: {price}")
    
    # Errors + close connection.

    except sqlite3.Error as e:
        print(f"Failed to retrieve finished products. Error: {e}")
    finally:
        conn.close()


def print_raw_materials():

    '''
        The print_raw_materials() function is used to print all the information in the RawMaterials table.
    '''
    
    # Connect to database + add cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Used a try-except block just incase of error when reteriving table.

    try:

        # Get all the RawMateirals entries through rows in a tuple.

        cursor.execute('SELECT * FROM RawMaterials')
        raw_materials = cursor.fetchall()

        # Case 1: Nothing in the table.

        if not raw_materials:
            print("No raw materials found.")

        # Case 2: Print all the entries.

        else:

            # Material is one entry a 1D tuple unpacking is used here to collect all the indivisual information which will be told to the user.

            print("Raw Materials:")
            for material in raw_materials:
                material_id, name, cost, units, quantity, associated_codes = material
                print(f"ID: {material_id}, Name: {name}, Cost: {cost}, Units: {units}, Quantity: {quantity}, Associated Codes: {associated_codes}")

    # Errors + close connection.

    except sqlite3.Error as e:
        print(f"Failed to retrieve raw materials. Error: {e}")
    finally:
        conn.close()


def print_packaging_materials():

    '''
        The print_packaging_materials() function is used to print all the information in the PackagingMaterials table.
    '''

    # Connect to database + add cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Used a try-except block just incase of error when reteriving table.

    try:

        # Get all the PackagingMaterials entries through rows in a tuple.

        cursor.execute('SELECT * FROM PackagingMaterials')
        packaging_materials = cursor.fetchall()

        # Case 1: Nothing in the table.

        if not packaging_materials:
            print("No packaging materials found.")

        # Case 2: Print all the entries.

        else:
            print("Packaging Materials:")
            for material in packaging_materials:
                
                # material is one entry a 1D tuple unpacking is used here to collect all the indivisual information which will be told to the user.

                material_id, name, cost, quantity, associated_codes = material
                print(f"ID: {material_id}, Name: {name}, Cost: {cost}, Quantity: {quantity}, Associated Codes: {associated_codes}")

    # Errors + close connection.

    except sqlite3.Error as e:
        print(f"Failed to retrieve packaging materials. Error: {e}")
    finally:
        conn.close()


def view_database():

    '''
        The view_database function is used to view the 3 tables for Finsihed Products, Raw Materials, and Packaging Maaterials.        
    '''

    # Greet user + collect the user input.

    print("\nWelcome to the view database function. Here you can view the information from a certain table (Finsihed Products, Raw Materials, and Packing Maaterials).\n")
    print("Which table(s) do you want to view: \n")

    print("1) Finished Products.\n")
    print("2) Raw Material.\n")
    print("3) Packaging Material.\n")
    print("4) Print All.\n")
    run = True
    view = int(input())   
    
    # While the user does not provide a valid number loop.
   
    while (run == True):
        
        # Case 1: Print the Finished Products.

        if (view == 1):
            print_finished_products()
            run = False
                    
        # Case 2: Print the Raw Materials.

        elif (view == 2):
            print_raw_materials()
            run = False
        
        # Case 3: Print the Packaging Materials.

        elif (view == 3):
            print_packaging_materials()
            run = False
        
        # Case 4: Print all tables.

        elif (view == 4):
            print_finished_products()
            print_raw_materials()
            print_packaging_materials()
            run = False
                    
        # Case 5: Invalid Input.

        else:
            view = int(input("Invalid Input, Try Again: "))


def create_objects_from_tables():
    
    '''
        The create_objects_from_tables() function is used to create objects (RawMaterials, PackagingMaterials, and Products) from their respective tables.
    '''

    # Create a connection to the SQLite database + cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Add a try-except block to ensure error checks.

    try:

        # Retrieve data from RawMaterials table, each index holds a row (2D tuple).

        cursor.execute("SELECT name, cost, units, quantity, associated_codes FROM RawMaterials")
        raw_material_rows = cursor.fetchall()

        # Create RawMaterial objects from the rows and store them in a list.
        
        raw_material_objects = []
        
        for row in raw_material_rows:

            # row 4 holds the codes. Get them all in a list otherwise keep the list empty if no associations. Then create an object.

            associated_codes = row[4].split(',') if row[4] else []
            raw_material_objects.append(rawMaterials(row[0], row[1], row[2], row[3], associated_codes))

        # Retrieve data from PackagingMaterials table, each index holds a row (2D tuple).

        cursor.execute("SELECT name, cost, quantity, associated_codes FROM PackagingMaterials")
        packaging_material_rows = cursor.fetchall()

        # Create PackagingMaterial objects from the rows and store them in a list.

        packaging_material_objects = []

        for row in packaging_material_rows:

            # row 3 holds the codes. Get them all in a list otherwise keep the list empty if no associations. Then create an object.

            associated_codes = row[3].split(',') if row[3] else []
            packaging_material_objects.append(packagingMaterials(row[0], row[1], row[2], associated_codes))
        
        # Retrieve data from FinishedProduct table.

        cursor.execute("SELECT code, productName, cost, unit, quantity, price FROM FinishedProduct")
        product_rows = cursor.fetchall()

        # Create Product objects from the rows and store them in a list.

        product_objects = []
        for row in product_rows:
            product_objects.append(products(row[0], row[1], row[2], row[3], row[4], row[5]))

        # Close the connection.

        conn.close()

        # Associate rawMaterials and packagingMaterials with the Product objects.

        for product in product_objects:
            
            # For each Raw Material, run through raw mateiral objects and if the code matches product code it should be appended to the rawMateirals list in the products object.

            associated_raw_materials = [rm for rm in raw_material_objects if product.code in rm.code]
            
            # For each Packaging Material, run through packaging mateiral objects and if the code matches product code it should be appended to the packagingMateirals list in the products object.
            
            associated_packaging_materials = [pm for pm in packaging_material_objects if product.code in pm.code]
            
            # Extend the lists to the correct attributes.

            product.rawMaterials.extend(associated_raw_materials)
            product.packagingMaterials.extend(associated_packaging_materials)

        # Return the lists of objects.

        return raw_material_objects, packaging_material_objects, product_objects
    
    # Errors.

    except sqlite3.Error as e:
        conn.close()
        raise sqlite3.Error(f"Failed to create objects from tables. Error: {e}")


def add_raw_mats(name, cost, units, quantity, associated_codes_input):
    
    '''
        The add_raw_material() function is used to add a new entry into the raw materials table. Also update the association for the new material.
    '''
    
    # Connect to the database + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Try-except block ensurs error check. We are trying to insert raw mateirals or packaging materials into the DB with associations if nessary.

    try:
        
        associated_codes_test = associated_codes_input.split(',')

        for code in associated_codes_test:
            if code.strip():  # Skip check if code is blank
                cursor.execute('SELECT * FROM FinishedProduct WHERE code = ?', (code.strip(),))
                checkExist = cursor.fetchone()
                if not checkExist:
                    return False  # Return False if code does not exist
            
        # Insert an entry into the RawMateirals table with the input.

        cursor.execute('INSERT INTO RawMaterials (name, cost, units, quantity, associated_codes) VALUES (?, ?, ?, ?, ?)',
                       (name, cost, units, quantity, associated_codes_input))
        material_id = cursor.lastrowid

        # Collect the associated codes in list format then update the ProductMaterialAssociation for the many-to-many relationship.

        if associated_codes_input.strip():
            associated_codes = associated_codes_input.split(',')

            for code in associated_codes:
                cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                               (material_id, 'RawMaterials', code.strip()))
                
        # Fetch existing associated codes for the raw material.

        cursor.execute('SELECT associated_codes FROM RawMaterials WHERE materialID = ?', (material_id,))
        existing_associated_codes = cursor.fetchone()[0]

        # Combine the existing and new associated codes, removing duplicates
        
        if existing_associated_codes:
            existing_codes_set = set(existing_associated_codes.split(','))
            new_codes_set = set(associated_codes)
            combined_codes_set = existing_codes_set.union(new_codes_set)
            all_associated_codes = ','.join(combined_codes_set)
        else:
            all_associated_codes = associated_codes_input

        # Update the associated codes.

        cursor.execute('UPDATE RawMaterials SET associated_codes = ? WHERE materialID = ?', (all_associated_codes, material_id))

        # Commit changes and let the user know.

        conn.commit()
        print("Raw material added successfully.")

    # Errors + close connection.

    except sqlite3.Error:
        conn.rollback()
        print("Failed to add raw material. Please try again.")
    finally:
        conn.close()
    
    return True


def add_packaging_mats(name, cost, quantity, associated_codes_input):

    '''
        The add_packaging_material() function is used for adding new packaing materials to the correct table, as well as updating all association for the new material.
    '''

    # Connect to the database + connect a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Add a try-except block used for error check.

    try:

        associated_codes_test = associated_codes_input.split(',')

        for code in associated_codes_test:
            if code.strip():  # Skip check if code is blank
                cursor.execute('SELECT * FROM FinishedProduct WHERE code = ?', (code.strip(),))
                checkExist = cursor.fetchone()
                if not checkExist:
                    return False  # Return False if code does not exist
                
        # Insert an entry into the PackagingMaterials table with the input.

        cursor.execute('INSERT INTO PackagingMaterials (name, cost, quantity, associated_codes) VALUES (?, ?, ?, ?)',
                       (name, cost, quantity, associated_codes_input))
        material_id = cursor.lastrowid

        # Collect the associated codes in list format then update the ProductMaterialAssociation for the many-to-many relationship.

        if associated_codes_input.strip():
            associated_codes = associated_codes_input.split(',')

            for code in associated_codes:
                cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                               (material_id, 'PackagingMaterials', code.strip()))
        
        # Fetch existing associated codes for the packaging material.

        cursor.execute('SELECT associated_codes FROM PackagingMaterials WHERE materialID = ?', (material_id,))
        existing_associated_codes = cursor.fetchone()[0]
        
        # Combine the existing and new associated codes, removing duplicates.

        if existing_associated_codes:
            existing_codes_set = set(existing_associated_codes.split(','))
            new_codes_set = set(associated_codes)
            combined_codes_set = existing_codes_set.union(new_codes_set)
            all_associated_codes = ','.join(combined_codes_set)
        else:
            all_associated_codes = associated_codes_input

        # Update the associated codes.

        cursor.execute('UPDATE PackagingMaterials SET associated_codes = ? WHERE materialID = ?', (all_associated_codes, material_id))
        
        # Commit changes and let the user know.

        conn.commit()
        print("Packaging material added successfully.")

    # Errors + close connection.
    
    except sqlite3.Error:
        conn.rollback()
        print("Failed to add packaging material. Please try again.")
    finally:
        conn.close()
    return True

def add_finished_prod(code, product_name, cost, unit, quantity, price, associated_materials_input):
    
    '''
        The add_finished_product() function is used for adding new products to the correct table, as well as updating all the materials that are associated to the the new product.
    '''
    
    # Connect to the database + connect a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # print(associated_materials_input)

    # Add a try-except block used for error check. We will try to insert all the information for a finishedproduct.

    try:

        # Insert an entry into the FinishedProduct table with the input.

        cursor.execute('INSERT INTO FinishedProduct (code, productName, cost, unit, quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                       (code, product_name, cost, unit, quantity, price))
        
        # Ask the user if they want to associate existing materials with the finished product.

        #associate_existing = input("Do you want to associate existing materials with this finished product? (yes/no): ").lower() don't need but keep just incase.

        if len(associated_materials_input) > 0:     #associate_existing == 'yes':

            # Collect associated_materials in a list by spliting incoming array of associated_materials_input.

            associated_materials = associated_materials_input.split(',')

            # For each material in associated materials make sure to properly associate the materials to the product in the DB by altering 3 tables, the respective material, product, and ProductMaterialAssociation tables.

            for material_name in associated_materials:

                # Check if the associated material name is for raw materials or packaging materials using the LIKE statement.
                
                cursor.execute('SELECT * FROM RawMaterials WHERE name LIKE ?', ('%' + material_name + '%',))
                raw_material = cursor.fetchone()

                # Case 1: If a raw_material was found associate it to the new product.

                if raw_material:

                    # Associate the material with the finished product in the ProductMaterialAssociation table.
                    
                    cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                                   (raw_material[0], 'RawMaterials', code))
                    
                    # Update the associated_codes in the RawMaterials table.
                    
                    associated_codes = raw_material[5]

                    # Add the new code to the associated_codes in RawMaterial table, regardless of how many codes exist.

                    if associated_codes:
                        associated_codes += ',' + code
                    else:
                        associated_codes = code

                    # Update the table with the new code.

                    cursor.execute('UPDATE RawMaterials SET associated_codes = ? WHERE materialID = ?', (associated_codes, raw_material[0]))

                # Case 2: No raw_material then that means a packaging material was found associate it to the new product.
                
                else:

                    # Find packaging material.

                    cursor.execute('SELECT * FROM PackagingMaterials WHERE name LIKE ?', ('%' + material_name + '%',))
                    packaging_material = cursor.fetchone()

                    # Case 2; Subcase 1: Append assocaiting codes.

                    if packaging_material:

                        # Associate the material with the finished product in the ProductMaterialAssociation table.
                        
                        cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                                       (packaging_material[0], 'PackagingMaterials', code))
                        
                        # Update the associated_codes in the PackagingMaterials table.
                        associated_codes = packaging_material[4]
                        if associated_codes:
                            associated_codes += ',' + code
                        else:
                            associated_codes = code
                        cursor.execute('UPDATE PackagingMaterials SET associated_codes = ? WHERE materialID = ?', (associated_codes, packaging_material[0]))
                    
                    # Case 2; Subcase 2: Material Not Found.

                    else:
                        print(f"Material with name '{material_name}' not found.")
                        return False

        # Save Changes and let user know of the changes.

        conn.commit()
        print("Finished product added successfully.")

    # Errors + close connection.

    except sqlite3.Error:
        conn.rollback()
        print("Failed to add finished product. Please try again.")
    finally:
        conn.close()
    return True

def add_entry():

    '''
        The add_entry function is used to add entries in the tables (raw materials, packaging materials, and finished products), It will update the tables in the database not the objects.
    '''
    
    # Greet user + collect the user input.

    print("\nWelcome to the add entry function. Here you can insert a new entry for Raw Materials, Packaging Materials, and Finished Products. Use this function for adding new entries.\n")
    print("What do you want to add today: \n")

    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    add_item = int(input())

    # While the user does not provide a valid number loop.

    while run:

        # Case 1: Add new entry for the Raw Materials.
    
        if add_item == 1:
            add_raw_mats()
            run = False

        # Case 2: Add new entry for the Packaging Materials.

        elif add_item == 2:
            add_packaging_mats()
            run = False

        # Case 3: Add new entry for the Finished Products.

        elif add_item == 3:
            add_finished_prod()
            run = False

        # Case 4: Invalid Input.

        else:
            add_item = int(input("Invalid Input, Try Again: "))


def remove_data(table_name, key_value):

    '''
        The remove_data() function is being used to delete entries in the respective table and then also updating the ProductMaterialAssociation to remove the association of the deleted entry.
    '''
    
    # Connect to the database + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Add a try-except block that will ensure error check.

    try:

        # Case 1: Remove a FinsihedProduct.

        if table_name == 'FinishedProduct':

            # Delete Product from FinishedProduct table.

            cursor.execute('DELETE FROM FinishedProduct WHERE code = ?', (key_value,))

            # Delete from ProductMaterialAssociation table each an every association with that key value.
            
            cursor.execute('DELETE FROM ProductMaterialAssociation WHERE code = ?', (key_value,))

            # Update associated_codes in RawMaterials table to remove the product codes from each material that contains that product code.
            
            cursor.execute('UPDATE RawMaterials SET associated_codes = REPLACE(associated_codes, ?, "") WHERE associated_codes LIKE ?', (key_value, f'%{key_value}%'))

            # Update associated_codes in PackagingMaterials table to remove the product codes from each material that contains that product code.
            
            cursor.execute('UPDATE PackagingMaterials SET associated_codes = REPLACE(associated_codes, ?, "") WHERE associated_codes LIKE ?', (key_value, f'%{key_value}%'))
            conn.commit()

            # Let user know operation successful.

            print(f"Finished product with code '{key_value}' has been removed along with its associations.")

        # Case 2: Remove a PackagingMaterials.

        elif table_name == 'PackagingMaterials':

            # Fetch materialID for the packaging material.

            cursor.execute('SELECT materialID FROM PackagingMaterials WHERE name = ?', (key_value,))
            packaging_material_id = cursor.fetchone()[0]

            # Delete from PackagingMaterials table.

            cursor.execute('DELETE FROM PackagingMaterials WHERE name = ?', (key_value,))

            # Delete all associations from ProductMaterialAssociation table where the packaging material matches the materialID. Essentialy removes all associations of packaging material with the product code.

            cursor.execute('DELETE FROM ProductMaterialAssociation WHERE materialType = ? AND materialID = ?', ('PackagingMaterials', packaging_material_id))

            # Remove any associations from ProductMaterialAssociation table where the packaging material is in the associated_codes column.

            cursor.execute('DELETE FROM ProductMaterialAssociation WHERE materialType = ? AND code = ?', ('PackagingMaterials', key_value))

            # Let user know operation successful.

            conn.commit()
            print(f"Packaging material with name '{key_value}' has been removed and its associations have been removed.")
        
        # Case 3: Remove a RawMaterials.

        elif table_name == 'RawMaterials':

            # Fetch materialID for the raw material.

            cursor.execute('SELECT materialID FROM RawMaterials WHERE name = ?', (key_value,))
            raw_material_id = cursor.fetchone()[0]

            # Delete from RawMaterials table.

            cursor.execute('DELETE FROM RawMaterials WHERE name = ?', (key_value,))

            # Delete all associations from ProductMaterialAssociation table where the raw material matches the materialID.

            cursor.execute('DELETE FROM ProductMaterialAssociation WHERE materialType = ? AND materialID = ?', ('RawMaterials', raw_material_id))

            # Remove any associations from ProductMaterialAssociation table where the raw material is in the associated_codes column.

            cursor.execute('DELETE FROM ProductMaterialAssociation WHERE materialType = ? AND code = ?', ('RawMaterials', key_value))

            # Let user know operation successful.

            conn.commit()
            print(f"Raw material with name '{key_value}' has been removed and its associations have been removed.")
        
        # Case 4: Let user no the correct table was not picked. (In Theory this will never occur since we currently hardcode these values but I added it if the implementation changes in the future)

        else:
            print("Invalid table name. Please provide a valid table name: 'FinishedProduct', 'PackagingMaterials', or 'RawMaterials'.")

    # Errors + close connection. 

    except sqlite3.Error:
        conn.rollback()
        print(f"Failed to remove {key_value} from {table_name}. Please try again.")
    finally:
        conn.close()


def delete_entry():

    '''
        The delete_entry function is used to delete entries from the tables that are not needed. Then it also removes that material or product code from being associated with anything as it
        will be gone.
    '''

    # Greet user + collect the user input.

    print("Welcome to the delete entry function. Here you can delete a specific entry of Raw Materials, Packaging Materials, and Finished Products to a fixed value. Use this function for corrections of values if you simply wish to take use or receive use the other functions.\n")
    print("What do you want to delete today: ")
    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    delete = int(input())

    # While the user does not provide a valid number loop.

    while (run == True):

        # Case 1: Delete a Raw Material.

        if (delete == 1):
            name = input("Enter the name of the raw material: ")
            remove_data('RawMaterials', name)
            run = False

        # Case 2: Delete a Packaging Material.

        elif (delete == 2):
            name = input("Enter the name of the packaging material: ")
            remove_data('PackagingMaterials', name)
            run = False

        # Case 3: Delete a Finished Products.

        elif (delete == 3):
            code = input("Enter the product code of the finished product: ")
            remove_data('FinishedProduct', code)
            run = False

        # Case 4: Invalid Input.

        else:
            delete = int(input("Invalid Input, Try Again: "))


def create_associations(material_type):

    '''
        The create_associations function is used to associate a given mateiral with all the product codes that will be listed by the user.
    '''
    
    # Create a DB connection and cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Add a try-except block used for attempting to create the associations between the mateiral and all the givne product codes.

    try:

        # Define a dictionary to map material types to the respective table and column names in ProductMaterialAssociation.

        material_mapping = {
            'RawMaterials': {'table': 'RawMaterials', 'column': 'associated_codes'},
            'PackagingMaterials': {'table': 'PackagingMaterials', 'column': 'associated_codes'}
        }

        # Get the material name from the user.

        material_name = input(f"Enter the name of the {material_type}: ")

        # Check if the material exists in the respective table.

        cursor.execute(f'SELECT * FROM {material_type} WHERE name = ?', (material_name,))
        material = cursor.fetchone()
        
        # If the material does not exist let the user know.

        if not material:
            print(f"{material_type.capitalize()} with name '{material_name}' not found.")
            return
        
        # Get the list of finished product codes from the user.

        product_codes_input = input("Enter comma-separated product codes to associate with the material: ")

        # If there is nothing entered let the user know and let him try again.

        if not product_codes_input:
            print("No product codes entered. Associations not updated.")
            return
        
        # If there are codes get them in a list by spliting the string every time there is a comma.

        product_codes = product_codes_input.split(',')


        # Find the existing associated codes for the material type with the name in the correct column.

        cursor.execute(f'SELECT {material_mapping[material_type]["column"]} FROM {material_mapping[material_type]["table"]} WHERE name = ?', (material_name,))
        existing_associated_codes = cursor.fetchone()[0]
        
        # Case 1: If the exisiting codes exist you have to append the new codes in order to update what codes are associated to that material.

        if existing_associated_codes:

            # Simply collect the existing codes in an array and combine the 2 arrays then collect them all in a string.

            existing_codes_set = set(existing_associated_codes.split(','))
            new_codes_set = set(product_codes)
            combined_codes_set = existing_codes_set.union(new_codes_set)
            all_associated_codes = ','.join(combined_codes_set)
        
        # Case 2: If there are no existing codes only append the list of codes given by the user.

        else:
            all_associated_codes = product_codes_input
        
        # Update the column with the new values.

        cursor.execute(f'UPDATE {material_mapping[material_type]["table"]} SET {material_mapping[material_type]["column"]} = ? WHERE name = ?', (all_associated_codes, material_name))
        
        # For each code in the product codes list insert a new association with the materialID, and the code.

        for code in product_codes:
            cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                           (material[0], material_type, code.strip()))
            
        # Commit changes and let the user know.

        conn.commit()
        print(f"Associations of {material_type.capitalize()} '{material_name}' with product codes '{product_codes_input}' created successfully.")
    
    # Errors + close DB connection.

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Failed to create associations. Error: {e}")
    finally:
        conn.close()


def associate_materials_with_product(product_code, material_names_input):

    '''
        The associate_materials_with_product is simialr to the create_associations function however the difference is that this time the user will be asked a product code they wish to update
        associations for and then add a list of materials to be associated with that code.
    '''

    # Connect to the database + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Add a try-except block to ensure error checks. Goal here is to achive what the function is expected to do.
    
    try:
    
        # Get the product from the FinishedProduct table.

        cursor.execute('SELECT * FROM FinishedProduct WHERE code = ?', (product_code,))
        product = cursor.fetchone()

        # Check if product exists.

        if not product:
            print(f"Finished product with code '{product_code}' not found.")
            return 10
        
        # Ask the user for the names of materials to associate with the product.
        #material_names_input = input("Enter comma-separated names of the materials to associate with the product: ")

        # Let the user know if they added no materials to associate the product with.

        if not material_names_input:
            print("No material names entered. Associations not updated.")
            return 20
        
        # Collect the material names in a list.

        material_names = material_names_input.split(',')

        # Check if the material names exist in either the RawMaterials or PackagingMaterials table.

        for material_name in material_names:

            # Check RawMaterials table for the material name and collect that entry.

            cursor.execute('SELECT * FROM RawMaterials WHERE name = ?', (material_name,))
            raw_material = cursor.fetchone()

            # Case 1: Found the material in RawMaterials table.

            if raw_material:

                # Update the associated_codes column in the RawMaterials table.

                # Find the associated codes for the raw material.

                cursor.execute('SELECT associated_codes FROM RawMaterials WHERE name = ?', (material_name,))
                existing_associated_codes = cursor.fetchone()[0]

                # Subcase 1: If the exisiting codes exist you have to append the new codes in order to update what codes are associated to that material.

                if existing_associated_codes:
                    existing_codes_set = set(existing_associated_codes.split(','))
                    new_codes_set = {product_code}
                    combined_codes_set = existing_codes_set.union(new_codes_set)
                    all_associated_codes = ','.join(combined_codes_set)

                # Subcase 2: If there are no existing codes only append the list of codes given by the user.

                else:
                    all_associated_codes = product_code

                # Update the codes to hold the new values.

                cursor.execute('UPDATE RawMaterials SET associated_codes = ? WHERE name = ?', (all_associated_codes, material_name))
                
                # Insert the new associations in the ProductMaterialAssociation table.

                cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                               (raw_material[0], 'RawMaterials', product_code))
                
            # Case 2: Found the material in PackagingMaterials table.

            else:

                # Check PackagingMaterials table for the material name and collect that entry.

                cursor.execute('SELECT * FROM PackagingMaterials WHERE name = ?', (material_name,))
                packaging_material = cursor.fetchone()

                # Check if packaging meterial exixts otherwise let user know it does not exist.

                if packaging_material:

                    # Update the associated_codes column in the PackagingMaterials table.
                    
                    # First collect all the associated codes for that packaging material.

                    cursor.execute('SELECT associated_codes FROM PackagingMaterials WHERE name = ?', (material_name,))
                    existing_associated_codes = cursor.fetchone()[0]
                    
                    # Sub Case 1: Add the new code with all the other existing codes.

                    if existing_associated_codes:
                        existing_codes_set = set(existing_associated_codes.split(','))
                        new_codes_set = {product_code}
                        combined_codes_set = existing_codes_set.union(new_codes_set)
                        all_associated_codes = ','.join(combined_codes_set)

                    # Sub Case 2: Add the new code as the first entry.

                    else:
                        all_associated_codes = product_code

                    # Update the packaging materials and set the new code into the associated_codes column. Also update the ProductMaterialAssociation table for every packaging material.

                    cursor.execute('UPDATE PackagingMaterials SET associated_codes = ? WHERE name = ?', (all_associated_codes, material_name))
                    cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                                   (packaging_material[0], 'PackagingMaterials', product_code))
                    
                # Case 3: Not Found.

                else:
                    print(f"Material with name '{material_name}' not found.")
                    return 30

        # Commit the changes and let the user know they were successful.

        conn.commit()
        print(f"Associations of product with code '{product_code}' with materials '{material_names_input}' created successfully.")
    
    # Errors + close the DB connection.

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Failed to create associations. Error: {e}")
    finally:
        conn.close()


def update_associations_menu():

    '''
        The update_associations_menu function is used in conjunction with other 2 other functions (create_associations, associate_materials_with_product) in order to update the associations of
        materials and products. This is used when the user wants to add relationships between finsihed products and materials after their creation incase they don't know what objects need
        to be connected.
    '''

    # Greet the user + user input.

    print("\nWelcome to the update associations function. Here you can update the connections between products and materials.\n")
    print("Pick which material or product needs a new association:\n")
    
    print("1) Raw Material.\n")
    print("2) Packaging Material.\n")
    print("3) Finished Products.\n")
    run = True
    update = int(input())

    # While the user does not input a valid number keep asking again.

    while (run == True):

        # Case 1: Create associations for a Raw Mateiral to a Finished Product Code.

        if (update == 1):
            create_associations("RawMaterials")
            run = False

        # Case 2: Create associations for a Packaging Mateiral to a Finished Product Code.

        elif (update == 2):
            create_associations("PackagingMaterials")
            run = False
        
        # Case 3: Create associations for a Finished Products by listing Mateirals.
        
        elif (update == 3):
            code = input("What is the product code you wish to add mateirals to? ")
            associate_materials_with_product(code)
            run = False

        # Case 4: Ask user agian to re-input.
        else:
            update = int(input("Invalid Input, Try Again: "))


def hash_password(password):

    '''
        The hash_password function is used to run the sha256 algorithm on the passwords so that there is a strong password stored in the database, this function will be used to create 
        passwords as well as check if the user has entered the correct password.
    '''
    
    # Hash the password using hashlib's sha256 and return it.
     
    salt = b'simplicity'  # Change this to a random salt
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return password_hash

def add_user(username, password):
    
    '''
        add_user function is used to add a new user so that they can have access to the site.
    '''
    
    # Connect to the database + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # Try-except block used to create a new user as expected with error check. 

    try:

        # Hash the password.

        hashed_password = hash_password(password)
        
        # Create the user by inserting the new user's information.

        cursor.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (username, hashed_password))
        
        # Commit the changes and let the use know of the success.

        conn.commit()
        print(f"User '{username}' added successfully.")

    # Errors + close the DB connection.

    except sqlite3.IntegrityError:
        conn.rollback()
        print(f"User '{username}' already exists.")
    finally:
        conn.close()


def remove_user(username, password):
    
    '''
        The remove_user function is used to remove a user from the database, which will no longer provie access to that user.
    '''
    
    # Connect to the DB + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # Find the instance of the specified user and password.

    hashed = hash_password(password)
    cursor.execute('SELECT * FROM Users WHERE username = ? AND password = ?', (username, hashed))
    user = cursor.fetchone()
    
    # Case 1: If the user exists delete them let the admin know about the success.

    if user:
        cursor.execute('DELETE FROM Users WHERE id = ?', (user[0],))
        conn.commit()
        print(f"User '{username}' removed successfully.")

    # Case 2: If the user does not exist let the admin know nothing was deleted.

    else:
        print(f"User '{username}' not found or incorrect password was inserted.")
    
    conn.close()


# HOME PAGE CODE IN index.html (endpoints) [Keep in case] 
'''
@app.route('/')
def index():
    return render_template('index.html')
'''

'''
    Each and every route is contained here for the app.
'''


@app.route('/')
def index():

    '''
        For route('/') call the index function which will render index.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''
    
    # Case 1: If the user is logged in render the home page.

    if 'username' in session:
        return render_template('index.html')  # Render the index.html template.
    
    # Case 2: If the use is not logged in render the login page.

    else:
        return redirect(url_for('login'))


@app.route('/receive')
def receive():

    '''
        For route('/recive') call the recive function which will render recive.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in
    
    return render_template('receive.html')


@app.route('/use')
def use():

    '''
        For route('/use') call the use function which will render use.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.

    return render_template('use.html')


@app.route('/adjust')
def adjust():

    '''
        For route('/adjust') call the adjust function which will render adjust.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('adjust.html')


@app.route('/choose_view')
def choose_view():
    
    '''
        For route('/choose_view') call the choose_view function which will render choose_view.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('choose_view.html')


@app.route('/view_table')
def view_table():

    '''
        For route('/view_table') call the view_table function which will render view_table.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('view_table.html')


@app.route('/view_rm_table')
def view_rm_table():

    '''
        For route('/view_rm_table') call the view_rm_table function which will render view_rm_table.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('view_rm_table.html')


@app.route('/view_pm_table')
def view_pm_table():

    '''
        For route('/view_pm_table') call the view_pm_table function which will render view_pm_table.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('view_pm_table.html')


@app.route('/view_fp_table')
def view_fp_table():

    '''
        For route('/view_fp_table') call the view_fp_table function which will render view_fp_table.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('view_fp_table.html')


@app.route('/view_all_table')
def view_all_table():

    '''
        For route('/view_all_table') call the view_all_table function which will render view_all_table.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('view_all_table.html')


@app.route('/summary_view')
def summary_view():

    '''
        For route('/summary_view') call the summary_view function which will render summary_view.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template('summary_view.html')


@app.route("/add_entry")
def add_entry():

    '''
        For route('/add_entry') call the add_entry function which will render add_entry.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("add_entry.html")


@app.route("/add_raw_material")
def add_raw_material():

    '''
        For route('/add_raw_material') call the add_raw_material function which will render add_raw_material.html if the user is logged in otherwise it will ask them to be redirected to 
        the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("add_raw_material.html")


@app.route("/add_packaging_material")
def add_packaging_material():

    '''
        For route('/add_packaging_material') call the add_packaging_material function which will render add_packaging_material.html if the user is logged in otherwise it will ask them to be 
        redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    return render_template("add_packaging_material.html")


@app.route("/add_finished_product")
def add_finished_product():
    
    '''
        For route('/add_finished_product') call the add_finished_product function which will render add_finished_product.html if the user is logged in otherwise it will ask them to be 
        redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.
    
    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    return render_template("add_finished_product.html")


@app.route("/delete_entries")
def delete_entries():

    '''
        For route('/delete_entries') call the delete_entries function which will render delete_entries.html if the user is logged in otherwise it will ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.
    
    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("delete_entries.html")


@app.route("/update_association", methods=["GET"])
def update_association():

    '''
        For route('/update_association') call the update_association function which will render update_association.html if the user is logged in otherwise it will ask them to be redirected to
        the login page.
    '''

    # If the user is not logged in make them, else render the correct page.
    
    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("update_association.html")


@app.route("/update_material_association", methods=["GET"])
def update_material_association():

    '''
        For route('/update_material_association') call the update_material_association function which will render update_material_association.html if the user is logged in otherwise it will
        ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("update_material_association.html")


@app.route("/update_product_association", methods=["GET"])
def update_product_association():
    
    '''
        For route('/update_product_association') call the update_product_association function which will render update_product_association.html if the user is logged in otherwise it will
        ask them to be redirected to the login page.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.
    
    return render_template("update_product_association.html")


@app.route('/logout')
def logout():

    '''
        For route('/logout') call the logout function which will logout the user and then render the login page (login.html)
    '''
    
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route("/submit_receive_form", methods=["POST"])
def submit_receive_form():

    '''
        The submit_receive_form() function is a flask endpoint that will be called in the JS of the recive.html template in order to use the values recived from the user from the frontend.
    '''
    
    # Try-except block is used to achieve the purpose of the function along with handling the error check. 

    try:

        # Connect to the database + add a cursor.

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        # Access the form data from the backend using JavaScript Object Notation (JSON).
        
        table_name = request.json.get("table_name")
        name = request.json.get("name")
        quantity = int(request.json.get("quantity"))

        # Error checking: Ensure the quantity is a positive integer.

        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        # Error checking: Ensure that all the fields have an entry.

        if not table_name or not name or not quantity:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400
    
        # Check if the name exists in the correct table by finding how many of the products/materials exist. (It should always be 1).

        if table_name == 'FinishedProduct':
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE code = ?", (name,))
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE name = ?", (name,))
        count = cursor.fetchone()[0]

        # Error checking: Let the user know what they entered does not exist.

        if count == 0:
            return jsonify({"error": f"Item '{name}' not found in the table '{table_name}'."}), 400

        # Perform the 'receive' operation using the provided data.

        update_quantity(table_name, name, quantity, 'add')

        # Return a success message

        response = {"message": "Receive operation successful!"}
        return jsonify(response), 200
    
    # Errors + Handling.

    except ValueError as ve:
        
        # Handle errors related to invalid quantity or other issues.
        
        response = {"error": str(ve)}
        return jsonify(response), 400
    except sqlite3.Error as e:
        
        # Handle errors related to database access.
        
        response = {"error": "Failed to perform the receive operation. Please try again."}
        return jsonify(response), 500
    except Exception as e:
        
        # Handle other unexpected errors.
        
        response = {"error": "Failed to perform the receive operation. Please try again."}
        return jsonify(response), 500


@app.route("/submit_use_form", methods=["POST"])
def submit_use_form():

    '''
        The submit_use_form() function is a flask endpoint that will be called in the JS of the use.html template in order to use the values recived from the user from the frontend.
    '''
    
    # Try-except block is used to achieve the purpose of the function along with handling the error check. 

    try:

        # Connect to the DB + Add a cursor.

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        # Access the form data from the backend using JavaScript Object Notation (JSON).
        
        table_name = request.json.get("table_name")
        name = request.json.get("name")
        quantity = int(request.json.get("quantity"))

        # Error checking: Ensure the quantity is a positive integer.

        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        # Error checking: Ensure that all the fields have an entry.

        if not table_name or not name or not quantity:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400
    
        # Check if the name exists in the correct table by finding how many of the products/materials exist. (It should always be 1).

        if table_name == 'FinishedProduct':
            cursor.execute(f"SELECT quantity FROM {table_name} WHERE code = ?", (name,))
        else:
            cursor.execute(f"SELECT quantity FROM {table_name} WHERE name = ?", (name,))
        fetched_quantity = cursor.fetchone()

        # Error checking: Let the user know what they entered does not exist.

        if fetched_quantity is None:
            response = {"error": f"Item '{name}' not found in the table '{table_name}'."}
            return jsonify(response), 400

        # Error checking: Let the user know what they entered is to large to subtract from the DB.

        current_quantity = fetched_quantity[0]
        if current_quantity < quantity:
            raise ValueError(f"Insufficient quantity of {name} in {table_name}. Cannot perform the operation.")

        # Perform the 'use' operation using the provided data.

        update_quantity(table_name, name, quantity, 'subtract')

        # Return a success message

        response = {"message": "Use operation successful!"}
        return jsonify(response), 200
    
    # Errors + Handling.

    except ValueError as ve:
        
        # Handle errors related to invalid quantity or other issues.
        
        response = {"error": str(ve)}
        return jsonify(response), 400
    except sqlite3.Error as e:
        
        # Handle errors related to database access.
        
        response = {"error": "Failed to perform the use operation. Please try again."}
        return jsonify(response), 500
    except Exception as e:
        
        # Handle other unexpected errors.
        
        response = {"error": "Failed to perform the use operation. Please try again."}
        return jsonify(response), 500


@app.route("/submit_adjust_form", methods=["POST"])
def submit_adjust_form():

    '''
        The submit_adjust_form() function is a flask endpoint that will be called in the JS of the adjust.html template in order to use the values recived from the user from the frontend.
    '''
    
    # Try-except block is used to achieve the purpose of the function along with handling the error check. 

    try:

        # Connect to the DB + Add a cursor.

        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        # Access the form data from the backend using JavaScript Object Notation (JSON).
        
        table_name = request.json.get("table_name")
        name = request.json.get("name")
        new_quantity = int(request.json.get("quantity"))

        # Error checking: Ensure the new_quantity is a non-negative integer.
        
        if new_quantity < 0:
            raise ValueError("New quantity cannot be set to a negative value.")

        # Error checking: Ensure that all the fields have an entry.

        if not table_name or not name or not new_quantity:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400

        # Check if the name exists in the correct table by finding how many of the products/materials exist. (It should always be 1).

        if table_name == 'FinishedProduct':
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE code = ?", (name,))
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE name = ?", (name,))
        count = cursor.fetchone()[0]

        # Error checking: Let the user know what they entered does not exist.

        if count == 0:
            return jsonify({"error": f"Item '{name}' not found in the table '{table_name}'."}), 400

        # Perform the 'adjust' operation using the provided data.

        adjust_quantity(table_name, name, new_quantity)

        # Return a success message.

        response = {"message": "Adjustment successful!"}
        return jsonify(response), 200
    
    # Errors + Handling.

    except ValueError as ve:
        
        # Handle errors related to invalid new_quantity.
        
        response = {"error": str(ve)}
        return jsonify(response), 400
    except sqlite3.Error as e:
        
        # Handle errors related to database access.
        
        response = {"error": "Failed to perform the adjustment. Please try again."}
        return jsonify(response), 500
    except Exception as e:
        
        # Handle other unexpected errors.
        
        response = {"error": "Failed to perform the adjustment. Please try again."}
        return jsonify(response), 500


@app.route("/submit_choose_view_form", methods=["POST"])
def submit_choose_view_form():

    '''
        The submit_choose_view_form() function is a flask endpoint that will be called in the JS of the choose_view.html template in order to use the values recived from the user from the
        frontend.
    '''
    
    # Try-except block is used to achieve the purpose of the function along with handling the error check. 

    try:

        # Get the user's selection on the type of view they wish to see.

        view_type = request.json.get("view_type")

        # Case 1: Table view will help the user see all the products in the table.

        if view_type == "table":

            # Redirect to the view_table endpoint
            
            return redirect("/view_table")

        # Case 2: Summary View will help the user see all the products in the table.
        
        elif view_type == "summary":
            # Retrieve the data for summary view and pass it to the summary_view.html template
            raw_materials, packaging_materials, products = create_objects_from_tables()
            return render_template("summary_view.html", raw_materials=raw_materials,
                                   packaging_materials=packaging_materials, products=products)
        else:
            return "Invalid view type.", 400

    except sqlite3.Error as e:
        return "Failed to view the database. Please try again.", 500


@app.route("/submit_view_form", methods=["POST"])
def submit_view_form():
    try:
        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()

        view_type = request.json.get("view_type")

        if view_type == "RawMaterials":
            data = fetch_table_data(cursor, "RawMaterials")
            print(data)
            return render_template("view_rm_table.html", table_data=data)
        elif view_type == "PackagingMaterials":
            data = fetch_table_data(cursor, "PackagingMaterials")
            print(data)
            return render_template("view_pm_table.html", table_data=data)
        elif view_type == "FinishedProduct":
            data = fetch_table_data(cursor, "FinishedProduct")
            print(data)
            return render_template("view_fp_table.html", table_data=data)
        elif view_type == "all":
            raw_materials = fetch_table_data(cursor, "RawMaterials")
            packaging_materials = fetch_table_data(cursor, "PackagingMaterials")
            finished_products = fetch_table_data(cursor, "FinishedProduct")
            print(raw_materials)
            print(packaging_materials)
            print(finished_products)
            return render_template("view_all_table.html",
                                   raw_materials=raw_materials,
                                   packaging_materials=packaging_materials,
                                   finished_products=finished_products)
        else:
            return "Invalid view type.", 400

    except sqlite3.Error as e:
        return "Failed to view the database. Please try again.", 500
    finally:
        conn.close()


def fetch_table_data(cursor, table_name):
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return {"columns": columns, "data": rows}


@app.route("/submit_choose_entry_form", methods=["POST"])
def submit_choose_entry_form():

    '''
        The submit_choose_entry_form is used to decide which table will have an additional entry added into it.
    '''
    
    # Try-except block is used to ensure that the functions performs as expected along with error handling.

    try:

        # Get the form data from the Javascript code using JSON.

        entry_type = request.json.get("entry_type")

        # Depending on the entry the user will be redirected to a new page where they can use functions to add a specifice mateial or product.

        if entry_type == "raw_material":
            return redirect("/add_raw_material")
        elif entry_type == "packaging_material":
            return redirect("/add_packaging_material")
        elif entry_type == "finished_product":
            return redirect("/add_finished_product")
        else:
            return "Invalid entry type.", 400

    except Exception as e:
        return "Failed to proceed with the selected entry type. Please try again.", 500

#Endpoint for add raw materials.

@app.route("/submit_add_raw_material_form", methods=["POST"])
def submit_add_raw_material_form():

    '''
        The submit_add_raw_material_form function is used as a flask endpoint to add new raw materials to the DB by collecting data from the frontend. 
    '''
    
    # Try-except block is used for achiving the purpose of the function + handling error checks.

    try:

        # Access the form data from the frontend.
        
        name = request.json.get("name")
        cost = float(request.json.get("cost"))
        units = request.json.get("units")
        quantity = int(request.json.get("quantity"))
        associated_codes_input = request.json.get("associated_codes")

        # Error checking: Ensure the quantity is a positive integer.

        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        
        # Error checking: Ensure the cost is a positive value.

        if cost <= 0:
            raise ValueError("Cost must be a positive value.")

        # Error checking: Ensure that all the fields are entered in.

        if not name or not cost or not units or not quantity:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400
        
        #print(name, cost, units, quantity, associated_codes_input)

        # Perform the 'add raw material' operation using the provided data + let the user know of the success.

        status = add_raw_mats(name, cost, units, quantity, associated_codes_input)

        #print(status)
        if (status == True):
            response_data = {"message": "Raw material added successfully"}
            return jsonify(response_data), 200
        else:
            response_data = {"message": "Failed to add a new Raw material due to an invalid product code given in list. (confirm product codes)"}
            return jsonify(response_data), 400

    # Error Handling.

    except ValueError as ve:
        
        # Handle errors related to invalid quantity or other issues.
        
        response = {"error": str(ve)}
        return jsonify(response), 400
    
    except Exception as e:
    
        # Handle other unexpected errors.
    
        response_data = {"error": "Failed to add raw material. Please try again."}
        return jsonify(response_data), 500


@app.route("/submit_add_packaging_material_form", methods=["POST"])
def submit_add_packaging_material_form():

    '''
        The submit_add_packaging_material_form function is used as a flask endpoint to add new packaging materials to the DB by collecting data from the frontend. 
    '''
    
    # Try-except block is used for achieving the purpose of the function + handling error checks.

    try:

        # Access the form data from the frontend.
        
        name = request.json.get("name")
        cost = float(request.json.get("cost"))
        quantity = int(request.json.get("quantity"))
        associated_codes_input = request.json.get("associated_codes")

        # Error checking: Ensure the quantity is a positive integer.
        
        if quantity <= 0:
            return jsonify({"error": "Quantity must be a positive integer."}), 400

        # Error checking: Ensure the cost is a positive value.

        if cost <= 0:
            return jsonify({"error": "Cost must be a positive value."}), 400
        
        # Error checking: Ensure that all fields are filled in.
        
        if not name or not cost or not quantity:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400
        
        # Perform the 'add packaging material' operation using the provided data.

        status = add_packaging_mats(name, cost, quantity, associated_codes_input)
        print(status)
        if (status == True):
            response_data = {"message": "Packaging material added successfully"}
            return jsonify(response_data), 200
        else:
            response_data = {"message": "Failed to add a new Packaging Material due to an invalid product code given in list. (confirm product codes)"}
            return jsonify(response_data), 400
        
        # if (status == True):
        #     response_data = {"message": "Raw material added successfully"}
        #     return jsonify(response_data), 200
        # else:
        #     response_data = {"message": "Raw material failed to add due to an invalid product code in given list. (confirm code exists)"}
        #     return jsonify(response_data), 400
        
    # Error handling.

    except ValueError as ve:
    
        # Handle errors related to invalid quantity or other issues
    
        response = {"error": str(ve)}
        return jsonify(response), 400
    
    except Exception as e:
    
        # Handle other unexpected errors
    
        response_data = {"error": "Failed to add packaging material. Please try again."}
        return jsonify(response_data), 500


@app.route("/submit_add_finished_product_form", methods=["POST"])
def submit_add_finished_product_form():

    '''
        The submit_add_finished_product_form function is used for adding new entries of finished products to the database by collecting all the information about it from the frontend.
    '''
    
    # Try-except block is used to perform the normal procedures of the function + error check.

    try:
    
        # Access the form data from the frontend using JSON.
    
        code = request.json.get("code")
        product_name = request.json.get("product_name")
        cost = float(request.json.get("cost"))
        unit = request.json.get("unit")
        quantity = int(request.json.get("quantity"))
        price = float(request.json.get("price"))
        associated_materials_input = request.json.get("associated_materials")

        # Error checking: Ensure the quantity is a positive integer.

        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        # Error checking: Ensure the cost is a positive value.

        if cost <= 0:
            return jsonify({"error": "Cost must be a positive value."}), 400
        
        # Error checking: Ensure the price is a positive value.

        if price <= 0:
            return jsonify({"error": "Price must be a positive value."}), 400
        
        # Error checking: Ensure that all fields are entered in.

        if not code or not product_name or not cost or not unit or not quantity or not price:
            return jsonify({"error": "Invalid form data. Please fill all the fields."}), 400

        # Perform the 'add finished product' operation using the provided data and let the user know it was successful.

        status = add_finished_prod(code, product_name, cost, unit, quantity, price, associated_materials_input)
        response_data = {"message": "Finished product added successfully"}

        if (status == True):
            response_data = {"message": "Finished product added successfully"}
            return jsonify(response_data), 200
        else:
            response_data = {"error": "Failed to add a new Finished Product due to an invalid Material given in list. (confirm names of material)"}
            return jsonify(response_data), 400
        
    # Error Handling.

    except ValueError as ve:

        # Handle errors related to invalid quantity or other issues
        
        response = {"error": str(ve)}
        return jsonify(response), 400
    
    except Exception as e:
    
        # Handle other unexpected errors
    
        response_data = {"error": "Failed to add finished product. Please try again."}
        return jsonify(response_data), 500


@app.route("/delete_entry", methods=["POST"])
def delete_entry():

    '''
        The delete_entry function is used to delete entries in the database which is specified from the frontend by the user.
    '''
    
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Try-except block is used to ensure normal procedure of the function and handling error checks.

    try:

        # Collect the information from the frontend.

        table_name = request.form.get("table_name")
        key_value = request.form.get("key_value")

        if (table_name == 'FinishedProduct'):
            cursor.execute(f"SELECT * FROM '{table_name}' WHERE code = ?", (key_value,))
            check = cursor.fetchone()
            if (not check):
                return jsonify({"message": f"Failed to remove {key_value} from {table_name} as it does not exist."}), 400
        else:
            cursor.execute(f"SELECT * FROM '{table_name}' WHERE name = ?", (key_value,))
            check = cursor.fetchone()
            if (not check):
                return jsonify({"message": f"Failed to remove {key_value} from {table_name} as it does not exist."}), 400

        # Remove the requested data from the database, and also let the user know of the success.

        remove_data(table_name, key_value)
        response_message = f"Successfully removed {key_value} from {table_name}."

        return jsonify({"message": response_message}), 200
    
    # Error Handling.

    except Exception as e:
        response_data = {"error": f"Failed to delete entry: {str(e)}"}
        return jsonify(response_data), 500


@app.route("/update_associations", methods=["POST"])
def update_associations():

    '''
        This function should not be in use.
    '''

    update_type = request.form.get("update_type")

    if update_type == "materials":
        # Handle updating materials associations
        # Implement your logic here
        response = "Updating materials associations..."
    elif update_type == "products":
        # Handle updating products associations
        # Implement your logic here
        response = "Updating products associations..."
    else:
        response = "Invalid update type."

    return jsonify(message=response)


@app.route("/update_material_associations", methods=["POST"])
def update_material_associations():

    '''
        The update_material_associations function is used for updating the relationship between materials to existing product codes.
    '''
    
    # Collect the user input from the frontend usign JSON.

    material_type = request.form.get("material_type")
    material_name = request.form.get("material_name")
    product_codes_input = request.form.get("product_codes")
    product_codes = product_codes_input.split(',')

    if not material_name:
            return "Please provide material name.", 400
        
    if not product_codes_input:
        return "Please provide product codes associated with this material.", 400
    
    # Connect to the DB + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()

    # Check if each code exists.

    for code in product_codes:
            if code.strip():  # Skip check if code is blank
                cursor.execute('SELECT * FROM FinishedProduct WHERE code = ?', (code.strip(),))
                checkExist = cursor.fetchone()
                if not checkExist:
                    return "A given Product Code does not exist.", 400  # Return False if code does not exist

    # Try-except block is used to achieve the purpose of the function + error handling. 

    try:

        # Dictionary used to map the material type with column names, #, and associated codes.

        material_mapping = {
            'RawMaterials': {'table': 'RawMaterials', 'column': 'associated_codes'},
            'PackagingMaterials': {'table': 'PackagingMaterials', 'column': 'associated_codes'}
        }
         
        # Collect the material.

        cursor.execute(f'SELECT * FROM {material_type} WHERE name = ?', (material_name,))
        material = cursor.fetchone()

        # Case 1: If the material does not exist let the user know.

        if not material:
            return f"{material_type.capitalize()} with name '{material_name}' not found.", 404

        # Case 2: Update the relationship of the material with each of the product codes.

        else:

            # Find the material and its existing codes.

            cursor.execute(f'SELECT {material_mapping[material_type]["column"]} FROM {material_mapping[material_type]["table"]} WHERE name = ?', (material_name,))
            existing_associated_codes = cursor.fetchone()[0]
            
            # If the existing_associated_codes exist add the new one on top.

            if existing_associated_codes:
                existing_codes_set = set(existing_associated_codes.split(','))
                new_codes_set = set(product_codes)
                combined_codes_set = existing_codes_set.union(new_codes_set)
                all_associated_codes = ','.join(combined_codes_set)

            # Otherwise make the first entry.

            else:
                all_associated_codes = product_codes_input

            # Update the correct table and add all the associated_codes in the correct column.

            cursor.execute(f'UPDATE {material_mapping[material_type]["table"]} SET {material_mapping[material_type]["column"]} = ? WHERE name = ?', (all_associated_codes, material_name))
            
            # Also update the ProductMaterialAssociation table with each of the new codes addedd to the material.

            for code in product_codes:
                cursor.execute('INSERT INTO ProductMaterialAssociation (materialID, materialType, code) VALUES (?, ?, ?)',
                               (material[0], material_type, code.strip()))
            
            # Commit and let the user know it was successful.

            conn.commit()
            response = f"Associations of {material_type.capitalize()} '{material_name}' with product codes '{product_codes_input}' updated successfully."
    
    # Errors + close connection.
    
    except sqlite3.Error as e:
        conn.rollback()
        response = f"Failed to update associations. Error: {e}"
    finally:
        conn.close()

    #return jsonify(message=response)
    return response, 200


@app.route("/update_product_associations", methods=["GET", "POST"])
def update_product_associations():

    '''
        The update_product_associations function is used to update the relationship between products and materials, by listing a product code and then listing each material name.
    '''

    # If the user is not logged in make them, else render the correct page.

    if "username" not in session:
        return redirect(url_for("login"))  # Redirect to the login page if user is not logged in.

    if request.method == "POST":
    
        # Collect the code + all the materials to be associated with that code from the frontend.

        product_code = request.form.get("product_code")
        material_names_input = request.form.get("material_names")
        
        # Error check: Let the user know they have to enter something.

        if not product_code:
            return "Please provide product code.", 400
        
        if not material_names_input:
            return "Please provide material names.", 400
        
        #material_names = material_names_input.split(',')

        # Call the function associate_materials_with_product to update the association.
        
        status = associate_materials_with_product(product_code, material_names_input)

        # If the function failed let the user know.

        if (status == 10):
            return f"Finished product with code '{product_code}' not found.", 400
    
        if (status == 30):
            return "One of the materials listed was not found.", 400

        # Return success message

        return f"Associations of product with code '{product_code}' with materials '{material_names_input}' created successfully."
    
    return render_template("update_product_association.html")


def authenticate_user(username, password):

    '''
        The authenticate_user function is used to authenticate the user when they login to ensure the username and password they are entering is correct.
    '''

    # Connect a DB + add a cursor.

    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    # Find the username entry if it exists.

    cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    # If user exists move on to the password check.

    if user:
    
        # Check if the password they entered is correct by checking if the hashed password match.

        stored_password_hash = user[2]  # Assuming the hashed password is in the second column
        hashed_password = hash_password(password)  # Hash the provided password

        if stored_password_hash == hashed_password:
            conn.close()
            return user
    
    # Close the connection and end.

    conn.close()
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():

    '''
        The login function is used for the login process for the user.
    '''

    if request.method == 'POST':

        # Request the user to insert the fields.

        username = request.form['username']
        password = request.form['password']
        
        # Authenticate the user.

        user = authenticate_user(username, password)
        
        # Case 1: If the user is autenticated add them in a session so they have access.

        if user:
            session['username'] = user[1]  # Store username in session
            return redirect(url_for('index'))
        
        # Case 2: Ask them to login in again.

        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

''' No longer need but keep in case.
@app.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))
'''

if __name__ == "__main__":

    '''
        INSTRUCTIONS.

        1) RUNNING FOR THE FIRST TIME:

        When Running for the first time set restartDataBase to True and then add all users below who will have access using add_user() function. Then stop the server and set
        restartDataBase to False what this will do is allow for the creation of an empty database, and give access to users who will be allowed to login to the site (this is achived
        through the add user function which inserts new users)

        2) RESTARTING DATABASE:

        If you ever want to restart your database for whatever reason set restartDataBase to True and follow the instructions above for RUNNING FOR THE FIRST TIME.

        3) DELETING USERS:

        If you want to delete users use delete_user() function, use it after you create all the users.

        4) ADDITIONAL NOTES

        As you read the main below there are helper comments.
    '''
    
    restartDataBase = False

    # Create all the tables, depending on restartDataBase if True will reset the DB or else it will just create the table if they do not exist.

    createAllTables(restartDataBase)        # Keep this line only change restartDataBase depending on application.
    
    # Add all users who will have access.

    #FORM: add_user("USERNAME", "PASSWORD")     - Will give success/fail message.
    
    ''' 
        NOtE: There is no need to worry you can keep re running the server and keep adding the same user over and over. In fact you should keep them listed one by one below to ensure 
        they will have access as the database can be reset, also it will help you keep track of who has access without viewing the database. 
    '''

    add_user("user1", "123")

    
    # Remove all users who no longer need access.

    #remove_user("USERNAME", "PASSWORD")    - Will give success/fail message.

    ''' 
        NOtE: For every user in order you should get either a success message saying they were removed or a failure message go through and make sure for each one that failed if you entered the
        username and password correctly.

        Best practice should be to remove the line of code after you have deleted the user. However in theory you can keep it you will just get a message on the console saying the user does not exist.
    '''

    app.run(debug=True)