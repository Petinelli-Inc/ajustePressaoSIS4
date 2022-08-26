from eppy.modeleditor import IDF
from eppy.results import fasthtml
from eppy import modeleditor

import tkinter as tk
from tkinter import font
from tkinter import Tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.ttk import *
from tkinter import *
from tkinter import messagebox

import time
import os
import sys
import pprint
pp = pprint.PrettyPrinter()

# Variáveis utilizada no programa
version = ""
ver = ""
iddFile = ""
folder = ""
idfFile = ""
table = ""
epwFile = ""
newTable = ""
powerFansArray = []
pressureFansArray = []
fanMechEfficiency = 0.7
qtdepszhp = 0
pszhp = ""
idf = ""


# Função que realiza o primeiro ajuste de pressão e roda o arquivo para o segundo ajuste -----------------------------
def ajustePRESSAO(tableName):

    filehandle = open(tableName, 'r')
    fansOutput = fasthtml.tablebyname(filehandle, "Fans")
    fansOutputTable = fansOutput[1]

    # filehandle = open(table, 'r')
    # zoneCooling = fasthtml.tablebyname(filehandle, "Zone Sensible Cooling")
    # zoneCoolingTable = zoneCooling[1]

    for n in range(qtdepszhp):
        maxAirFlow = fansOutputTable[n+1][4]
        maxAirFlowCFM = round(maxAirFlow * 2118.88, 2)
        # filterMERV13 = round((zoneCoolingTable[13] * 21188.88) * 0.9, 5)
        bhp = (maxAirFlowCFM * 0.00094)

        if bhp <= 1.00:
            fanMotorEfficiency = 0.825
        if 1.00 < bhp <= 2.00:
            fanMotorEfficiency = 0.84
        if 2.00 < bhp <= 5.00:
            fanMotorEfficiency = 0.875
        if 5.00 < bhp <= 10:
            fanMotorEfficiency = 0.895
        if 10 < bhp <= 20:
            fanMotorEfficiency = 0.91
        if 20 < bhp <= 30:
            fanMotorEfficiency = 0.924
        if 30 < bhp <= 50:
            fanMotorEfficiency = 0.93
        if 50 < bhp <= 60:
            fanMotorEfficiency = 0.936
        if 60 < bhp <= 75:
            fanMotorEfficiency = 0.941
        if 75 < bhp <= 125:
            fanMotorEfficiency = 0.945
        if 125 < bhp <= 200:
            fanMotorEfficiency = 0.95

        powerfanWATT = round(bhp * (746 / fanMotorEfficiency), 8)
        newPressure = round(powerfanWATT * fanMechEfficiency / (maxAirFlow), 8)
        powerFansArray.append(powerfanWATT)
        pressureFansArray.append(newPressure)
        pszhp[n].Supply_Fan_Delta_Pressure = newPressure
        pszhp[n].Supply_Fan_Motor_Efficiency = fanMotorEfficiency

    idf.save()


# Função que realiza o segundo ajuste (regra de 3) a partir da simulação ----------------------------------------------
def segundoAjuste(tableName):
    global qtdepszhp, pszhp, powerFansArray, pressureFansArray

    filehandle = open(tableName, 'r')
    fansOutput = fasthtml.tablebyname(filehandle, "Fans")
    fansOutputTable = fansOutput[1]

    for n in range(qtdepszhp):
        newSecPressure = round((powerFansArray[n] * pressureFansArray[n]) / fansOutputTable[n+1][5], 8)
        pszhp[n].Supply_Fan_Delta_Pressure = newSecPressure
        labelPressure.insert(END, f"System Name: {fansOutputTable[n+1][0]} \n New Pressure: {round(newSecPressure, 4)} Pa\n\n")

    idf.saveas(folder + "\pressureAdjustedSIS4.idf")


# Função principal (Executa o código) ---------------------------------------------------------------------------------
def exacucaoCod():
    global idf, pszhp, qtdepszhp, folder, idfFile, epwFile, table, newTable, ver

    progress.place(x = WIDTH/2 - 160, rely = 0.4, width=200, height=20)
    infoLabel["text"] = "Iniciando. Aguarde..."
    
    #Progress------------
    progress['value'] = 5
    window.update_idletasks()
    window.update()
    time.sleep(1)

    idf = IDF(idfFile, epwFile)
    infoLabel["text"] = "Carregando dados."

    #Progress------------
    progress['value'] = 20
    window.update_idletasks()
    window.update()
    time.sleep(1)

    idf.idfobjects["SIMULATIONCONTROL"][0].Run_Simulation_for_Sizing_Periods = "Yes"
    idf.idfobjects["SIMULATIONCONTROL"][0].Run_Simulation_for_Weather_File_Run_Periods = "No"
    pszhp = idf.idfobjects['HVACTEMPLATE:SYSTEM:UNITARYHEATPUMP:AIRTOAIR']

    qtdepszhp = len(pszhp)

    #Progress------------
    progress['value'] = 40
    window.update_idletasks()
    window.update()
    time.sleep(1)
    infoLabel["text"] = "Ajustando simulação."
  
    ajustePRESSAO(table)

    #Progress------------
    progress['value'] = 60
    window.update_idletasks()
    window.update()
    time.sleep(1)
    infoLabel["text"] = "Simulação em Execução."

    idf.run(output_directory=f"{folder}")

    #Progress------------
    progress['value'] = 80
    window.update_idletasks()
    window.update()
    time.sleep(1)
    infoLabel["text"] = "Rodando Ajustes."

    segundoAjuste(newTable)
    infoLabel["text"] = "Salvando novo arquivo idf."
    
    #Progress------------
    progress['value'] = 100
    window.update_idletasks()
    window.update()
    time.sleep(1)

    infoLabel["text"] = "Ajuste Concluído."
    messagebox.showinfo("Aviso", f"Novo arquivo .idf salvo em:\n{folder}")
    buttonClose["state"] = "normal"


#-----------------------------------Funções de seleção de arquivos para a simulação -----------------------------------

# Função que seleciona o arquivo .idf ---------------------------------------------------------------------------------
def idfSelection():
    global idfFile, version, iddFile, ver
    idfFile = filedialog.askopenfilename(filetypes=[("EnergyPlus", ".idf")])

    try:
        if idfFile.lower().endswith(('.idf')):
            infoLabel["text"] = f"Arquivo IDF: {idfFile}"
            buttonEpw["state"] = "normal"

            try: 
                fo = open(idfFile, "r")
                for i, line in enumerate(fo):
                    if i == 3:
                        str = line
                fo.close()

                str = str.strip()
                version = str[0:3]
                ver = list(version)

                for n in range(len(ver)):
                    if ver[n] == '.':
                        ver[n] = '-'

                version = "V"+(''.join(ver))+"-0"
                iddfile = f"C:/EnergyPlus{version}/Energy+.idd"

                try:
                    IDF.setiddname(iddfile)
                except modeleditor.IDDAlreadySetError:
                    IDF.setiddname(iddfile)

                messagebox.showinfo("Versão", f"Versão do IDF: {version}")
            except:
                messagebox.showerror("Erro", "Problemas com o IDF. Reveja a sua versão.")
                sys.exit()

    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo não encontrado.")
    except FileExistsError: 
        messagebox.showerror("Erro", "Arquivo com problemas.")


# Função que seleciona o arquivo climático --------------------------------------------------------------------------
def epwSelection():
    global epwFile
    epwFile = filedialog.askopenfilename(filetypes=[("Energyplus Weather", "*.epw")])
    try:
        if epwFile.lower().endswith(('.epw')):
            infoLabel["text"] = f"Arquivo IDF: {idfFile}\nArquivo Climático: {epwFile}"
            buttonFolder["state"] = "normal"

    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo não encontrado.")
    except FileExistsError: 
        messagebox.showerror("Erro", "Arquivo com problemas.")


# Função que seleciona o diretório de destino -------------------------------------------------------------------------
def folderSelection():
    global folder, newTable
    folder = filedialog.asksaveasfilename(initialfile=f"baseline_Ajustado")

    infoLabel["text"] = f"Arquivo IDF: {idfFile}\nArquivo Climático: {epwFile}\nDiretório de destino: {folder}"
    newTable = f"{folder}\eplustbl.htm"
    buttonTable["state"] = "normal"


#Função que seleciona o table da simulação realizada direto no E+ ----------------------------------------------------
def tableSelection():
    global table
    table = filedialog.askopenfilename(filetypes=[("EnergyPlus", "*.html")])
    try:
        if table.lower().endswith(('.html')):
            infoLabel["text"] = f"Arquivo IDF: {idfFile}\nArquivo Climático: {epwFile}\nDiretório de destino: {folder}\nTable: {table}"
    
            buttonLimpa["state"] = "normal"
            buttonExec["state"] = "normal"

    except FileNotFoundError:
        messagebox.showerror("Erro", "Arquivo não encontrado.")
    except FileExistsError: 
        messagebox.showerror("Erro", "Arquivo com problemas.")

# Função que limpa os arquivos selecionados para uma nova simulação ---------------------------------------------------
def limpar():
    global idfFile, epwFile, version 
    idfFile = ""
    epwFile = ""

    buttonEpw["state"] = "disable"
    buttonFolder["state"] = "disable"
    buttonExec["state"] = "disable"
    buttonLimpa["state"] = "disable"

    infoLabel["text"] = ""

    progress.place(width=0, height=0)
    progress['value'] = 0

    messagebox.showwarning("Aviso", f"Dados de entrada limpos!\n\nVersão do EnergyPlus definida:\nVersão {version}.")
    messagebox.showwarning("Aviso", f"Se deseja alterar a versão, reinicie o aplicativo.")

# Função que fecha a janea do programa -------------------------------------------------------------------------------
def onClosing():
    window.destroy()

# Interface Gráfica ---------------------------------------------------------------------------------------------------
HEIGHT = 600
WIDTH = 800
window = tk.Tk()
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.title("Petinelli's Baseline Pressure Adjustment: System 4")
window.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, 2.25*w/9, h/11))
window.resizable(width=False, height=False)
window.configure(background="#1C4B73")

# Frame 1 ---------------------------------------------------------------------------------------------------------
frame1 = tk.Frame(window, bg = "#E82D3D", bd = 5)
frame1.place(relx = 0.5, rely = 0.025, relwidth = 0.8, relheight = 0.1, anchor = "n")

buttonIdf = tk.Button(frame1, bg = "#E1E0EA",  text="Carregar IDF", font = ("Roboto", 10), command=idfSelection, relief = RAISED)
buttonIdf.place(relx = 0, rely = 0.05, relheight = 0.9, relwidth = 0.3)

buttonEpw = tk.Button(frame1, bg = "#E1E0EA", text="Carregar Arquivo Climático", font = ("Roboto", 10), command=epwSelection, relief = RAISED)
buttonEpw.place(relx = 0.35, rely = 0.05, relheight = 0.9, relwidth = 0.3)
buttonEpw["state"] = "disable"

buttonFolder = tk.Button(frame1, bg = "#E1E0EA", text="Diretório de destino", font = ("Roboto", 10), command=folderSelection, relief = RAISED)
buttonFolder.place(relx = 0.7, rely = 0.05, relheight = 0.9, relwidth = 0.3)
buttonFolder["state"] = "disable"

# Frame 2 ---------------------------------------------------------------------------------------------------------
frame2 = tk.Frame(window, bg = "#E82D3D", bd = 5)
frame2.place(relx = 0.5, rely = 0.125, relwidth = 0.8, relheight = 0.1, anchor = "n")

buttonTable = tk.Button(frame2, bg = "#E1E0EA", text="Carregar Table", font = ("Roboto", 10), command=tableSelection, relief = RAISED)
buttonTable.place(relx = 0, rely = 0.05, relheight = 0.9, relwidth = 0.3)
buttonTable["state"] = "disable"

buttonLimpa = tk.Button(frame2, bg = "#E1E0EA", text="Limpar input", font = ("Roboto", 10), command=limpar, relief = RAISED)
buttonLimpa.place(relx = 0.35, rely = 0.05, relheight = 0.9, relwidth = 0.3)
buttonLimpa["state"] = "disable"

buttonExec = tk.Button(frame2, bg = "#E1E0EA", text="Executar", font = ("Roboto", 10), command=exacucaoCod, relief = RAISED)
buttonExec.place(relx = 0.7, rely = 0.05, relheight = 0.9, relwidth = 0.3)
buttonExec["state"] = "disable"

# Frame Info ---------------------------------------------------------------------------------------------------------
infoFrameAlt = tk.Frame(window, bg = "#E82D3D", bd = 5)
infoFrameAlt.place(relx = 0.5, rely = 0.225, relwidth = 0.9, relheight = 0.05, anchor = "n")

l = Label(infoFrameAlt, text = "Informações", font =("Roboto 11 bold"), bg= "#E82D3D", fg= "White")
l.pack()

infoFrame = tk.Frame(window, bg = "#E82D3D", bd = 5)
infoFrame.place(relx = 0.5, rely = 0.265, relwidth = 0.9, relheight = 0.135, anchor = "n")

infoLabel = tk.Label(infoFrame, font = ("Roboto", 10), anchor = "nw", justify = "left", bd = 4, bg = "#E1E0EA", wraplength=WIDTH)
infoLabel.place(relwidth = 1, relheight = 1)

progress = Progressbar(infoLabel, orient = HORIZONTAL, length = 300, mode = 'determinate')
progress.pack()
progress.place(width=0, height=0)

# Frame de resultados ---------------------------------------------------------------------
resultsFrame = tk.Frame(window, bg = "#E82D3D", bd = 5)
resultsFrame.place(relx = 0.5, rely = 0.41, relwidth = 0.9, relheight = 0.05, anchor = "n")

l = Label(resultsFrame, text = "Resultados", font =("Roboto 11 bold"), bg= "#E82D3D", fg= "White")
l.pack()

# Label para impressão ---------------------------------------------------------------------
lowerFrame = tk.Frame(window, bg = "#E82D3D", bd = 5)
lowerFrame.place(relx = 0.5, rely = 0.45, relwidth = 0.9, relheight = 0.48, anchor = "n")

labelPressure = tk.Text(lowerFrame, font = ("Roboto", 8), bd = 4, bg = "#E1E0EA", relief = FLAT)
labelPressure.place(relwidth = 0.995, relheight = 0.995)

scrollbar = ttk.Scrollbar(labelPressure, orient='vertical', command=labelPressure.yview)
scrollbar.pack(side=tk.RIGHT, fill = BOTH)

labelPressure.config(yscrollcommand=scrollbar.set)

# -------------------------------------------
frameClose = tk.Frame(window, bd = 5, bg = "#1C4B73")
frameClose.pack(side = BOTTOM)

buttonClose = tk.Button(frameClose, text="Fechar", font = ("Roboto", 10), command=onClosing, relief = RAISED)
buttonClose.pack(side = RIGHT)
buttonClose["state"] = "disable"


# Funções da Janela --------------------------------------------------------------------------------------------------

def ajuda_sobre():
    messagebox.showinfo("Sobre", "Versão 1.0 \n\nDesenvolvido por Petinelli Inc. \nSetembro de 2022\n\nPor Luis Henrique Alberti")

def orientacoes():
    messagebox.showinfo("Sobre", "Faça a primeira simulação direto no EnergyPlus, para gerar o primeiro table que será usado na execução do programa. \
                        \n\nSelecione, primeiro, o arquivo IDF expandido do baseline. \nApós isso, selecione o arquivo climático para simulação.\
                        \nDefina o diretório onde o IDF ajustado deverá ser salvo. Este diretório também será usado para salvar os arquivos geradaos na simulação. \
                        \n\nExecute a aplicação e aguarde a impressão dos parâmetros para validação. \
                        \nAo final do ajuste, o programa irá salvar um novo .idf na pasta selecionada.\
                        \n\nO tempo de execução dependerá da quantidade de sistemas e complexidade do projeto.")

def donothing():
   return

def reiniciar():
    import psutil
    import logging

    try:
        p = psutil.Process(os.getpid())
        try:
            for handler in p.get_open_files() + p.connections():
                os.close(handler.fd)
        except Exception:
            pass
    except Exception as e:
        logging.error(e)

    python = sys.executable
    os.execl(python, python, "\"{}\"".format(sys.argv[0]))

menubar = Menu(window)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_separator()
filemenu.add_command(label="Sair", command=window.quit)
filemenu.add_command(label="Reiniciar", command=reiniciar)
menubar.add_cascade(label="Opções", menu=filemenu)
menubar.add_cascade(label="Ajuda", command=orientacoes)
menubar.add_cascade(label="Sobre", command=ajuda_sobre)

window.config(menu=menubar)
window.mainloop()

