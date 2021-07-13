import matplotlib.pyplot as plt
import csv


def graficar_futuro(ticker):
    w = []
    x = []
    y = []
    z = []
    with open(f'tmp/{ticker}_futuro.csv', 'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            y.append(float(row[3]))
            w.append(float(row[2]))
            z.append(float(row[1]))
            x.append(str(row[0]))
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, label='Precio Cierre', marker="o")
    plt.plot(z, label='Precio Bajo', marker="o")
    plt.plot(w, label='Precio Alto', marker="o")
    plt.xlabel('Tiempo')
    plt.ylabel('Precio')
    plt.title(f'Proyección de precio\n{ticker}')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'img/{ticker}_tendencia.png')
