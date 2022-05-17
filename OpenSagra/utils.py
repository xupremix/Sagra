#classe di metodi generali utili

#filtraggio dei piatti in base ad un determinato giorno e una lista di ingredienti che possono comporlo
#per questo abbiamo utilizzato una list comprehension, che permette di tradurre un ciclo in una lista, dati dei criteri
def filter_plates(day, plates, ingredients=None):
    if ingredients:
        #-> lista di piatti con gli ingredienti specificati disponibili nel giorno indicato
        return [plate for plate in plates if day in plate and [ing for ing in ingredients if ing in [ingredienti[0] for ingredienti in plate[4]]] or plate[0] == "everyday" and [ing for ing in ingredients if ing in [ingredienti[0] for ingredienti in plate[4]]]]
    else:
        #-> lista di piatti disponibili nel giorno indicato
        return [plate for plate in plates if day in plate or plate[0] == "everyday"]

#funzione per l'ottenimento del prezzo di un piatto
def get_price(name, plates):
    return [plate[5] for plate in plates if plate[2] == name][0]
#-> costo

#funzione che ritorna una lista di piatti selezionati precedentemente dall'utente dal form
def get_requested_items(form, plates):
    return [(name, int(value), get_price(name, plates), int(value)*get_price(name, plates)) for name, value in form.items() if f"{name}_check" in form and int(value)]
#-> lista di tuple (nome, quantita, costo x unità, costo totale)

#caricamento di una lista di piatti disponibili con le varie informazioni
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

#funzione per il calcolo del costo di una lista di piatti
def get_total_cost(items):
    return sum(item[3] for item in items)
#-> costo totale

#creazione lista di piatti associati alla postazione di ritiro per la stampa dello scontrino
def locate(items, db):
    return [(item[0], item[1], item[2], item[3], db.get_location(item[0])) for item in items]

#funzione per il raggruppamento dei piatti
def group_items(items, db):
    new_items = locate(items, db)
    locations = []
    for item in new_items:
        if item[4] not in locations:
            locations.append(item[4])
    grouped_items = []
    for location in locations:
        grouped_items.append([])
        for item in new_items:
            if item[4] == location:
                grouped_items[-1].append(item)
    return grouped_items

#templates per la stampa dello scontrino
template = '''
       Opensagra

--- Bassano del Grappa ---

       RIEPILOGO

'''

endspace = '''





'''

def print_receipt(items, location, day, time):
    import os
    #apertura file temporaneo per la stampa
    with open("receipt.txt", "w") as f:
        f.write(template)
        
        f.write(f"  {day} - {time}\n\n")
        f.write("--------------------------\n\n")

        for item in items:
            f.write(f"{item[0]}:\n{item[1]} x {item[2]} = {item[3]}\n\n")
        
        f.write("---------------------------\n\n")
        f.write(f"Ritiro:   {location}\n\n")
        f.write(f"TOTALE        {get_total_cost(items)} Euro")
        f.write(endspace)

    #invio dello scontrino alla stampante
    os.system("lpr -P scontrini receipt.txt")
    print("Scontrino stampato")
    #rimozione del file temporaneo
    os.system("rm receipt.txt")