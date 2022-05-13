def filter_plates(day, plates, ingredients=None):
    if ingredients:
        #-> lista di piatti con gli ingredienti specificati disponibili nel giorno indicato
        return [plate for plate in plates if day in plate and [ing for ing in ingredients if ing in [ingredienti[0] for ingredienti in plate[4]]] or plate[0] == "everyday" and [ing for ing in ingredients if ing in [ingredienti[0] for ingredienti in plate[4]]]]
    else:
        #-> lista di piatti disponibili nel giorno indicato
        return [plate for plate in plates if day in plate or plate[0] == "everyday"]

def get_price(name, plates):
    return [plate[5] for plate in plates if plate[2] == name][0]
#-> costo

def get_requested_items(form, plates):
    return [(name, int(value), get_price(name, plates), int(value)*get_price(name, plates)) for name, value in form.items() if f"{name}_check" in form and int(value)]
#-> lista di tuple (nome, quantita, costo x unità, costo totale)

def load_plates(file):
    from json import load
    l = []
    with open(file, "r") as f:
        days:dict = load(f)
        for day, contents in days.items():
            for category, component in contents.items():
                for nome, elem in component.items():
                    l.append((day, category, nome, elem["description"], [(ing_name, ing_q) for ing_name, ing_q in elem["ingredients"].items()], elem["cost"]))
    return l
#-> lista di tuple (giorno, categoria, nome, descrizione, [(nome_ingrediente, quantità_ingrediente)], costo)

def get_total_cost(items):
    return sum(item[3] for item in items)
#-> costo totale

template = '''
       Opensagra

--- Bassano del Grappa ---

       RIEPILOGO

(non valido per il ritiro)

--------------------------
'''

endspace = '''





'''

def print_receipt(items, total_cost):
    import os

    with open("receipt.txt", "w") as f:
        f.write(template)

        for item in items:
            f.write(f"{item[0]}:\n{item[1]} x {item[2]} = {item[3]}\n\n")
        
        f.write("---------------------------\n\n")
        f.write(f"TOTALE        {total_cost}")
        f.write(endspace)

    os.system("lpr -P scontrini receipt.txt")
    print("Scontrino stampato")
    os.system("rm receipt.txt")