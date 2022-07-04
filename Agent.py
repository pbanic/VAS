import time as t
import random as r
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from argparse import ArgumentParser
from spade import quit_spade

idIgrac = ""
agentIgrac = ""   
mojZnak = ""

ploca = []

# pravila za pobjedu
def stanje_ploca(ploca):
    # redovi
    if ploca[0] == ploca[1] and ploca[1] == ploca[2] and ploca[0] != " ":
        return ploca[0]
    elif ploca[3] == ploca[4] and ploca[4] == ploca[5] and ploca[3] != " ":
        return ploca[4]
    elif ploca[6] == ploca[7] and ploca[7] == ploca[8] and ploca[6] != " ":
        return ploca[6]

    # stupci
    if ploca[0] == ploca[3] and ploca[3] == ploca[6] and ploca[0] != " ":
        return ploca[0]
    elif ploca[1] == ploca[4] and ploca[4] == ploca[7] and ploca[1] != " ":
        return ploca[1]
    elif ploca[2] == ploca[5] and ploca[5] == ploca[8] and ploca[2] != " ":
        return ploca[2]

    # diagonale
    if ploca[0] == ploca[4] and ploca[4] == ploca[8] and ploca[0] != " ":
        return ploca[0]
    elif ploca[2] == ploca[4] and ploca[4] == ploca[6] and ploca[2] != " ":
        return ploca[2]

    for i in range(0, 9):
        if ploca[i] == " ":
            return None

    # ne riješeno
    return 'D'

def max(ploca):
    # inicijalna vrijednost gora od najgore moguće a to je -1
    max_vrijednost = -3

    pozicija_X = None

    rezultat = stanje_ploca(ploca)

    if rezultat == 'X':
        return (-1, 0)
    elif rezultat == 'O':
        return (1, 0)
    elif rezultat == 'D':
        return (0, 0)

    for i in range(0, 9):
        if ploca[i] == ' ':
            ploca[i] = 'X'
            (m, _) = min(ploca)
            if m > max_vrijednost:
                max_vrijednost = m
                pozicija_X = i
            ploca[i] = ' '

    return (max_vrijednost, pozicija_X)
                        
def min(ploca):
    # inicijalna vrijednost gora od najgore moguće a to je 1
    min_vrijednost = 3

    pozicija_O = None

    rezultat = stanje_ploca(ploca)

    if rezultat == 'X':
        return (-1, 0)
    elif rezultat == 'O':
        return (1, 0)
    elif rezultat == 'D':
        return (0, 0)

    for i in range(0, 9):
        if ploca[i] == ' ':
            ploca[i] = 'O'
            (m, _) = max(ploca)
            if m < min_vrijednost:
                min_vrijednost = m
                pozicija_O = i
            ploca[i] = ' '

    return (min_vrijednost, pozicija_O)    

class AgentIgrac(Agent):

    class PonasanjeAgentaIgraca(FSMBehaviour):

        async def on_start(self):
            print(f"|{idIgrac}| Zapocinjem ponašanje!")

        async def on_end(self):
            print(f"|{idIgrac}| Završavam ponašanje!")
            await self.agent.stop()
            
    class UkljuciSe(State):
        async def run(self):
            poruka = Message(to="server@localhost")
            poruka.body = agentIgrac 
            await self.send(poruka)
            self.set_next_state("CekajNaOdgovor")
            
    class CekajNaOdgovor(State):
        async def run(self):
            global ploca
            global mojZnak
            poruka = await self.receive(timeout = 60)
            if (poruka):
                msg = poruka.body
                sadrzaj = eval(msg)
                mojZnak = sadrzaj["znak"]   
                print(mojZnak)             
                poruka = await self.receive(timeout = 60)
                if (poruka):
                    msg = poruka.body
                    sadrzaj = eval(msg)
                    ploca = sadrzaj["ploca"]   
                    self.set_next_state("Igra")         
                else:
                    self.set_next_state("CekajNaOdgovor")
            else:
                self.set_next_state("CekajNaOdgovor")
                
    class Igra(State):
        async def run(self):
            global ploca
            global mojZnak
            poruka = await self.receive(timeout = 60)
            if (poruka):
                msg = poruka.body
                sadrzaj = eval(msg)
                tip = sadrzaj["tip"]
                if tip == "ploca":
                    ploca = sadrzaj["ploca"]
                elif tip == "igras": 
                    if mojZnak == "X":
                        (_, poz) = max(ploca)
                        b = {
                          "pozicija" : poz, 
                          "znak" : mojZnak
                        }
                        poruka = Message(to="server@localhost")
                        poruka.body = str(b) 
                        await self.send(poruka)
                        
                    else: 
                        (_, poz) = min(ploca)
                        b = {
                          "pozicija" : poz, 
                          "znak" : mojZnak
                        }                 
                        poruka = Message(to="server@localhost")
                        poruka.body = str(b) 
                        await self.send(poruka)      
                self.set_next_state("Igra")   
            else:
                self.set_next_state("Igra")            
   
                    
        
    async def setup(self):

        print(f"|{idIgrac}| Pokrecem se!")
        
        fsm = self.PonasanjeAgentaIgraca()
        
        fsm.add_state(name="UkljuciSe", state=self.UkljuciSe(), initial=True)
        fsm.add_state(name="CekajNaOdgovor", state=self.CekajNaOdgovor())
        fsm.add_state(name="Igra", state=self.Igra())

        fsm.add_transition(source="UkljuciSe", dest="CekajNaOdgovor")
        fsm.add_transition(source="CekajNaOdgovor", dest="Igra")
        fsm.add_transition(source="CekajNaOdgovor", dest="CekajNaOdgovor")
        fsm.add_transition(source="Igra", dest="Igra")

        self.add_behaviour(fsm)

if __name__ == '__main__':

    parser = ArgumentParser() 
    parser.add_argument("-id", type = str)
    args = parser.parse_args()
    idIgrac = args.id
    agentIgrac = f"{idIgrac}@localhost"

    agent = AgentIgrac(agentIgrac, "password")
    start = agent.start()
    start.result()
      
    while agent.is_alive():
       try:
           t.sleep(1)
       except KeyboardInterrupt:
           print("Zatvaram program...")
           break
           
    agent.stop()
    
    quit_spade()

        
