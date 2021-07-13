import sys
import os
from fpdf import FPDF
from datetime import datetime
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from graficarfuturo import graficar_futuro

path_img = "img"
path_report = "reportes"
accion = "normal"

if len(sys.argv) >= 3:
    accion = sys.argv[1]
    LOOKUP_STEP = sys.argv[1]

now = datetime.now()
fecha_hora_now = now.strftime('%d/%m/%Y - %I:%M%p')
fecha_rep = now.strftime('%d%m%Y%I%M%p')

if os.path.exists("tmp/archivo.csv"):
    os.system("rm tmp/archivo.csv")

if not os.path.isdir("tmp"):
    os.mkdir("tmp")


class Symbols:
    # listado = ['AUDCAD=X', 'AUDCHF=X', 'AUDNZD=X', 'AUDUSD=X', 'CHFJPY=X', 'EURCAD=X', 'EURUSD=X', 'EURGBP=X',
    #            'EURJPY=X', 'EURCHF=X', 'USDCAD=X', 'USDCHF=X', 'USDJPY=X', 'GBPAUD=X', 'GBPUSD=X', 'GBPJPY=X',
    #            'NZDCAD=X', 'NZDUSD=X', 'NZDJPY=X']
    listado = ['EURUSD=X', 'USDJPY=X']
    # listado = ['EURUSD=X']


def ejecutar():
    limite = len(Symbols.listado)

    veces = 4
    for a in range(limite):
        for i in range(veces):
            os.system(f"python train.py {Symbols.listado[a]} {int(i)}")
            os.system(f"python test.py {Symbols.listado[a]} {int(i)}")
        graficar_futuro(Symbols.listado[a])


def leercsv():
    with open('tmp/archivo.csv', newline='') as f:
        reader = csv.reader(f)
        data = list(reader)
    # print(data[0])
    return data


def crearpdf(titulo, tipo):
    pdf = FPDF(orientation='L', format='Legal')
    num_a = 0
    for image in Symbols.listado:
        datos = str(leercsv()[num_a]).split(',')
        fecha_exec = datos[0]
        symbol = datos[1]
        fecha_rango = datos[2]
        min = datos[3]
        max = datos[4]
        cierre = datos[5]
        # print(data[int(num_a)])
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(100, 5, f'{titulo} {symbol} {fecha_exec}', 0, 2, 'J')
        pdf.set_font('Arial', 'I', 14)
        pdf.cell(100, 4, f'Datos analizados en el rango {fecha_rango}', 0, 2, 'J')
        # pdf.cell(100, 6, f'Minimo {min}$', 0, 2, 'J')
        # pdf.cell(100, 7, f'Maximo {max}$', 0, 2, 'J')
        # pdf.cell(100, 8, f'Cierre {cierre}$', 0, 2, 'J')
        pdf.image(f'{path_img}/{image}_{tipo}.png', y=40, x=10)
        num_a = num_a + 1
    pdf.output(f"reporte_{tipo}_{fecha_rep}.pdf", "F")


def email(tipo):
    mail_content = f"Reporte Generado {fecha_hora_now}"
    # The mail addresses and password
    sender_address = 'franklin.arias89@gmail.com'
    sender_pass = 'mortdihaqlfpdyiw'
    receiver_address = 'franklin.arias89@gmail.com'
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = f'Analisis de pares {tipo}'  # The subject line
    # The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    # attach_file_name = f'reporte_{tipo}_{fecha_rep}.pdf'
    attach_file_name = f'reporte_{tipo}_{fecha_rep}.pdf'
    attach_file = open(attach_file_name, 'rb')  # Open the file as binary mode
    payload = MIMEBase('application', 'octate-stream')
    payload.set_payload((attach_file).read())
    encoders.encode_base64(payload)  # encode the attachment
    # add payload header with filename
    payload.add_header('Content-Disposition', 'attachment', filename=attach_file_name)
    message.attach(payload)
    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    session.starttls()  # enable security
    session.login(sender_address, sender_pass)  # login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail Sent')


ejecutar()
crearpdf(titulo='Backtesting', tipo='backtesting')
crearpdf(titulo='Tendencia', tipo='tendencia')
email(tipo='backtesting')
email(tipo='tendencia')
# os.system("rm -rf data logs img csv-results *.pdf tmp results")
