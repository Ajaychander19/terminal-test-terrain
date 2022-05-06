import tkinter as tk
import sys
import re
from tkinter import font
from tkinter import messagebox, Canvas, BOTH


class AppliCanevas(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.size = 1800
        self.colors=["black","MidnightBlue","Navy","DarkBlue", "MediumBlue","blue","RoyalBlue","DodgerBlue","DeepSkyBlue","LightSkyBlue", "Cyan", "PaleTurquoise","aquamarine","lightgreen","mediumaquamarine","GreenYellow","Lime","chartreuse","yellow","Gold", "orange","DarkOrange", "Coral", "Tomato","Crimson"]#["black", "red", "green", "blue", "yellow", "magenta","cyan", "white", "purple"]
        self.creer_widgets()

    def creer_widgets(self):
        # création canevas
        self.canv = tk.Canvas(self, bg="light gray", height=100,
                              width=self.size)
        self.canv.pack(side=tk.LEFT)
        # boutons
        self.bouton_cercles = tk.Button(self, text="Colors",
                                        command=self.showS_Colors)
        self.bouton_cercles.pack(side=tk.TOP)
       
        self.bouton_quitter = tk.Button(self, text="Close",
                                        command=self.quit)
        self.bouton_quitter.pack(side=tk.BOTTOM)

    def getColor(self,index):
        gap=int(96/(len(self.colors)))
        
        for i in range(0,len(self.colors)-1):
           if (index < (i+1)*(96/(len(self.colors)-1))) and (index >= i*(96/(len(self.colors)-1))) :
                
                return self.colors[i+1]
           elif (index==96):
                return self.colors[len(self.colors)-1]
    

    def show_Colors(self):
        y=18;
        for i in range(0,96):
            diameter = 100 
            self.canv.create_rectangle(0+i*y, 50, (i+1)*y,0,fill=self.getColor(i))
            if self.checkModulo(i) ==True:  
                self.canv.create_text(8+i*y, 60,font=("Purisa", 12), text=str(i))
    def checkModulo(self,i):
        if i%4 ==0:
            return True
        else :
            return False
      


if __name__ == "__main__":
    app = AppliCanevas()
    app.title("colors")
    app.mainloop()
