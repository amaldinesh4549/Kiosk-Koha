from flask import Flask, jsonify
import pymysql
import datetime
from escpos import printer

# Initialising the printer
# Printer Configurations
p = printer.Usb(0x0456, 0x0808, 4, 0x81, 0x03)

app = Flask(__name__)

tasks = {'login': False}
time = {'start':'' , 'end':''}

# Apis
@app.route('/login', methods=['POST'])
def login():
    tasks = {
        'login': True
    }
    print (tasks)
    time['start']= datetime.datetime.today().replace(microsecond=0)
    print (time)
    return jsonify({'task': tasks}), 201

@app.route('/logout', methods=['POST'])
def logout():
    tasks = {
        'login': False
    }
    print (tasks)
    time['end'] =  datetime.datetime.today().replace(microsecond=0)
    x = datetime.datetime.now()
    
    # database connection
    db=pymysql.connect("localhost","root","a123456789","koha_library")
    cursor=db.cursor()

    # # get rows of logged in user
    cursor.execute("SELECT * FROM statistics WHERE datetime BETWEEN %s AND %s",(time['start'],time['end']))
    records=cursor.fetchall()
    
    # # find count of return
    returned_book_count=0
    for row in records: 
        if row[3]=='return':
            returned_book_count=returned_book_count+1

    # FETCHING REQUIRED DATA
    # Fetching borrowers data
    borrowersid=str(records[0][8])
    cursor.execute("SELECT cardnumber,firstname,surname FROM borrowers WHERE borrowernumber=%s",(borrowersid))
    borrower_details=cursor.fetchall()
    print (borrower_details)

    # Fetching book details
    # These arrays contain book title and barcode as array of arrays
    return_books = []
    renew_books = []
    issue_books = []
    for row in records:
        if row[3]=='return':
            item_number=str(row[5])
            cursor.execute("SELECT biblionumber,barcode FROM items WHERE itemnumber=%s",(item_number))
            barcode=cursor.fetchall()
            biblio_number=str(barcode[0][0])
            cursor.execute("SELECT title FROM biblio WHERE biblionumber=%s",(biblio_number))
            book_title=cursor.fetchall()
            return_books.append([book_title[0][0],barcode[0][1]])

        elif row[3]=='renew':
            item_number=str(row[5])
            cursor.execute("SELECT biblionumber,barcode FROM items WHERE itemnumber=%s",(item_number))
            barcode=cursor.fetchall()
            biblio_number=str(barcode[0][0])
            cursor.execute("SELECT title FROM biblio WHERE biblionumber=%s",(biblio_number))
            book_title=cursor.fetchall()
            renew_books.append([book_title[0][0],barcode[0][1]])

        elif row[3]=='issue':
            item_number=str(row[5])
            cursor.execute("SELECT biblionumber,barcode FROM items WHERE itemnumber=%s",(item_number))
            barcode=cursor.fetchall()
            biblio_number=str(barcode[0][0])
            cursor.execute("SELECT title FROM biblio WHERE biblionumber=%s",(biblio_number))
            book_title=cursor.fetchall()
            issue_books.append([book_title[0][0],barcode[0][1]])
    
    print (return_books)
    print (renew_books)
    print (issue_books)

    # Checking the Count of return

    
    
    # PRINTING

    # Fixed items in receipt
    p.set(align='center', font='a', height=2)
    p.text("Alethea Library\n")
    p.set(align='center', font='a', width=1, height=1)
    p.text("RSET\n\n")
    
    p.set(align='left', font='a', width=1, height=1)
    p.text("Date:" + (x.strftime("%d")) + "/" + (x.strftime("%m")) + "/" + (x.strftime("%Y")))
    p.set(align='left', font='a', width=1, height=1)
    p.text("   Time:" + (x.strftime("%I")) + ":" + (x.strftime("%M")) + " " + (x.strftime("%p")))
    p.text("\n\n")

    p.set(align='center', font='a', width=1, height=1)
    p.text(borrower_details[0][1] + " " + borrower_details[0][2])
    p.text("\n")
    p.text(borrower_details[0][0])
    p.text("\n\n")

    # Variable book details
    # For checkout or issue
    if (len(issue_books) != 0):
        p.set(align='center', text_type="B", font='a', width=1, height=1)
        p.text("CHECKOUT\n")
        for item in issue_books:
            p.set(align='left', font='a', width=1, height=1)
            p.text(item[0] + " (" + str(item[1]) + ")\n")
        p.text("\n")

    # For renew
    if (len(renew_books) != 0):
        p.set(align='center', text_type="B", font='a', width=1, height=1)
        p.text("RENEW\n")
        for item in renew_books:
            p.set(align='left', font='a', width=1, height=1)
            p.text(item[0] + " (" + str(item[1]) + ")\n")
        p.text("\n")

    # For checkin or return
    if (len(return_books) != 0):
        p.set(align='center', text_type="B", font='a', width=1, height=1)
        p.text("CHECKIN\n")
        for item in return_books:
            p.set(align='left', font='a', width=1, height=1)
            p.text(item[0] + " (" + str(item[1]) + ")\n")
        p.text("\n")

    # Closing database connection
    db.close()

    p.set(align='center', height=2)
    p.text("Thank You!\n\n\n\n")
    p.cut()

    return jsonify({'task': tasks}), 201


if __name__ == '__main__':
    app.run(debug=True)
