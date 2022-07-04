import time as t
import random as r
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
from spade import quit_spade

agenti = []

naRedu = ""

ploca = [" ", " ", " ", " ", " ", " ", " ", " ", " "]

def ispis_ploca(ploca):
    print(' {} | {} | {}'.format(ploca[0], ploca[1], ploca[2]))
    print('---:---:---')
    print(' {} | {} | {}'.format(ploca[3], ploca[4], ploca[5]))
    print('---:---:---')
    print(' {} | {} | {}\n\n'.format(ploca[6], ploca[7], ploca[8]))
    
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

class Server(Agent):

    class TicTacToe(FSMBehaviour):

        async def on_start(self):
            print("|S| Zapocinjem ponasanje!")

        async def on_end(self):
            print("|S| Zavrsavam ponasanje!")
            await self.agent.stop()
            
    class Priprema(State):
    
        async def run(self):
            global naRedu
            print("|S| U pripremi...")
            poruka = await self.receive(timeout = 60)
            if (poruka):
                msg = poruka.body
                agenti.append(msg)
                if (len(agenti) == 2):
                    print(f"|S| Oba igraca su tu: {agenti}")
                    naRedu = r.randint(0, 1) 
                    if naRedu == 0:
                        porukaX = Message(to = agenti[0])
                        b = {
                          "igras" : 1,
                          "znak" : 'X'
                        }
                        porukaX.body = str(b)
                        await self.send(porukaX)
                        porukaO = Message(to = agenti[1])
                        b = {
                          "igras" : 2,
                          "znak" : 'O'
                        }
                        porukaO.body = str(b)
                        await self.send(porukaO)
                        self.set_next_state("Igra")
                    else: 
                        porukaO = Message(to = agenti[0])
                        b = {
                          "igras" : 2,
                          "znak" : 'O'
                        }
                        porukaO.body = str(b)
                        await self.send(porukaO)
                        porukaX = Message(to = agenti[1])
                        b = {
                          "igras" : 1,
                          "znak" : 'X'
                        }
                        porukaX.body = str(b)
                        await self.send(porukaX)
                        self.set_next_state("Igra")
                else:
                  self.set_next_state("Priprema")
            else:
              self.set_next_state("Priprema")   
                
    class Igra(State):

       async def run(self):
           print(f"|S| Igra može započeti! ")
           ispis_ploca(ploca)         
           for agent in agenti: 
              b = {
                "ploca" : ploca
              }
              poruka = Message(to = agent)
              poruka.body = str(b)
              await self.send(poruka)
              self.set_next_state("PoteziIgraca") 
                
    class PoteziIgraca(State):
        async def run(self):
            global agenti
            global ploca
            global naRedu
            b = {
              "ploca" : ploca,
              "tip": "igras"
            }
            poruka = Message(to = agenti[naRedu])
            if naRedu == 0:
                naRedu = 1
            else:
                naRedu = 0
            poruka.body = str(b)
            await self.send(poruka) 
            self.set_next_state("OdgovorIgraca")
            
    class OdgovorIgraca(State):
        async def run(self):
            global agenti
            global ploca
            poruka = await self.receive(timeout = 60)
            if (poruka):
                msg = poruka.body
                poruka = eval(msg)
                pozicija = int(poruka["pozicija"])
                znak = poruka["znak"]
                ploca[pozicija] = znak
                for agent in agenti:
                    b = {
                      "tip" : "ploca", 
                      "ploca" : ploca
                    }
                    poruka = Message(to = agent)
                    poruka.body = str(b)
                    await self.send(poruka)   
                self.set_next_state("ProvjeriPobjedu")
            else:
                self.set_next_state("OdgovorIgraca")
      
    class ProvjeriPobjedu(State):   
       async def run(self):
        
           global agenti
           global ploca
           ispis_ploca(ploca) 
           rezultat = stanje_ploca(ploca)
           # ako je igra gotova:
           if rezultat != None: 
               if rezultat == 'X':
                   print('|S| Pobjednik je X!')
               elif rezultat == 'O':
                   print('|S| Pobjednik je O!')
               elif rezultat == 'D':
                   print("|S| Ne riješeno je!")
               self.set_next_state("KrajIgre")
           else: 
              self.set_next_state("PoteziIgraca")
              
    class KrajIgre(State):   
       async def run(self):               
           print("|S| Igra je gotova.")
     
    async def setup(self):

        print("|S| Pokrečem se!")
        
        fsm = self.TicTacToe()

        fsm.add_state(name="Priprema", state=self.Priprema(), initial=True)
        fsm.add_state(name="Igra", state=self.Igra())
        fsm.add_state(name="PoteziIgraca", state=self.PoteziIgraca())
        fsm.add_state(name="OdgovorIgraca", state=self.OdgovorIgraca())
        fsm.add_state(name="ProvjeriPobjedu", state=self.ProvjeriPobjedu())
        fsm.add_state(name="KrajIgre", state=self.KrajIgre())
        
        fsm.add_transition(source="Priprema", dest="Priprema")
        fsm.add_transition(source="Priprema", dest="Igra")
        fsm.add_transition(source="Igra", dest="PoteziIgraca")
        fsm.add_transition(source="PoteziIgraca", dest="OdgovorIgraca")
        fsm.add_transition(source="OdgovorIgraca", dest="OdgovorIgraca")
        fsm.add_transition(source="OdgovorIgraca", dest="ProvjeriPobjedu")
        fsm.add_transition(source="ProvjeriPobjedu", dest="PoteziIgraca")
        fsm.add_transition(source="ProvjeriPobjedu", dest="KrajIgre")
        self.add_behaviour(fsm)
        
if __name__ == '__main__':

    server = Server("server@localhost", "password")
    start = server.start()
    start.result()
    
    while server.is_alive():
           try:
               t.sleep(1)
           except KeyboardInterrupt:
               print("Zatvaram program...")
               break
              
    server.stop()
    
    quit_spade()
