####
#
# D&D Tools
#
# A suite of tools for differnt D&D related tasks. This portion implements 3:
#   -A die parser and roller that converts arbitrary strings, like 2d8+14d6-3d12+6d9-12+156d19 into sequences of
#       rolls
#   -A minor magic item generator, derived from a collection of properties collected from cantrips, minor properties
#       in the DMG, and internet generators, as well as a few novel ones
#   -A background generator which is derived from the tables in the PHB, augmented with the ones from XGE, converted
#       to parseable tables (the included in the attached .txts) and then sequentially rolled and processed into a
#       coherent output (like not having a career based on your parents' if they're absent). Does some NLP stuff to
#       stitch all that together.
#
####

#Standards
import math,time,random

#Only for saving result history file with a unique name
from datetime import datetime

#Internet things
import asyncio,websockets
import webbrowser
from urllib.parse import unquote
from html.parser import HTMLParser

#Base HTML for formatting saved results files
saveHTMLbase1 = '''<!DOCTYPE html><html><head><style>.columns {max-width:1080px;width: 100%;padding: 20px 0 0 10px;}.columnLeft {width: 50%;vertical-align: top;}.columnRight {width: 50%;vertical-align: top;padding: 0 0 0 20px;}.simpleBorder {border:1px solid #000000;}.combatant{border:4px solid gold;width: 250px;margin-bottom: 5px;}.combatantout{border:4px solid red;width: 250px;margin-bottom: 5px;}</style></head><body><table class="columns" id='mainContent'><tr><td class="columnLeft"></td><td class="columnRight"><div id="outputText">'''
saveHTMLbase2 = '''</div><br/></td></tr></body></html></table>'''

#Read in properties from txt tables:
item_prop_minor = open("minor.txt",'r') #Minor magic properties
item_prop_mat_typ = open("mat_typ.txt",'r') #Typical materials
item_prop_atyp_mat = open("atyp_mat.txt",'r') #Unusual materials
item_prop_maker = open("maker.txt",'r') #Makers of items and descriptions
item_prop_quirk = open("quirk.txt",'r') #Magic quirks
item_prop_base = open("base.txt",encoding='utf-8-sig') #base forms for items with variable <tags>
backstory_tables = open("backstory_tables.txt",encoding='utf-8-sig') #All the backstory tables from DMG and XGE, woof.

###
#Make Backstory dictionaries
###

#Read in the backstory txt
bs_lines = backstory_tables.read().splitlines()

#Variables for table reads
current_table = [] #Table being written
current_label = None #Label being examined
current_dice = None #Die roll template for current label

#Root table dictionary
bs_tables = {}

#Loop over lines in the backstory table
for lne in bs_lines:
    if lne == "": ##Ignore empty lines
        pass
    elif lne[0] == "&": #& marks table start
        if current_label != None: #For the first table
            bs_tables[current_label] = [current_dice,current_table] #Load in the new key with the previously made table
        current_label = lne.split("|")[0][1:] #Split line to get label and die separately
        current_dice = lne.split("|")[1]
        current_table = [] #reset table for new read set
    else: #If not starting a new table
        lne_range = lne.split(" ")[0] #Split the line and grab first element for range
        lne_cont = lne[len(lne_range)+1:] #Grab line content
        lne_range = (int(lne_range.split(":")[0]),int(lne_range.split(":")[1])) #Grab the die ranges
        current_table = current_table + [(lne_range,lne_cont)] #Update the currently building table
bs_tables[current_label] = [current_dice,current_table] #Load the last table in, since there's not next new table to tell it to do so

###
#Populate lists for magic item maker:
###

bases = [] #Item bases list
text = item_prop_base.read().splitlines() #Read in the item bases by line
for i in range(len(text)): #Going over the list
    if text[i] != "": #If not empty line
        bases = bases + [text[i]] #Add it to the actual list
    else: #otherwise
        pass #do nothing

makers = [] #Object makers list
text = item_prop_maker.read().splitlines() #read in lines
lab_desc = 0 #label/description toggle
tar = [] #maker w/ probabilty list
s_incident = 0 #Incidence probability string
for i in range(len(text)): #Looping over the whole file
    if text[i] != "": #If not an empty line
        if lab_desc == 0: #if on the label part
            s_incident = s_incident + int(text[i].split(" ")[-1]) #grab the incident probability
            tar = [text[i].split(" ")[0].replace("_"," "),s_incident] #Make [maker/prob] set
            lab_desc = 1 #toggle to description
        elif lab_desc == 1: #If getting description
            tar = tar + [text[i]] #add the description to the list
            makers = makers + [tar] #Add the list to the makers list
            tar = [] #reset to the next maker values list
            lab_desc = 0 #set toggle to label
    else: #Pass on empty lines
        pass

minor = [] #Minor properties list
text = item_prop_minor.read().splitlines() #Read the txt
lab_desc = 0 #label toggle
tar = [] #values list
for i in range(len(text)):
    if text[i] != "":
        if lab_desc == 0:
            tar = [text[i]] #get property name
            lab_desc = 1 #toggle label
        elif lab_desc == 1:
            tar = tar + [text[i]] #get property text
            minor = minor + [tar]
            tar = []
            lab_desc = 0
    else:
        pass

amat = [] #Atypical materials list
text = item_prop_atyp_mat.read().splitlines()
tar = []
for i in range(len(text)): #add them all in, no special format- same list structure as above, thought
    if text[i] != "":
        tar = tar + [text[i]]
        amat = amat + [tar]
        tar = []
    else:
        pass

quirk = [] #Quirks list
text = item_prop_quirk.read().splitlines()
lab_desc = 0 #label/description toggle
tar = []
for i in range(len(text)): #Loop- toggle label/desc, but no other properties
    if text[i] != "":
        if lab_desc == 0:
            tar = [text[i]]
            lab_desc = 1
        elif lab_desc == 1:
            tar = tar + [text[i]]
            quirk = quirk + [tar]
            tar = []
            lab_desc = 0
    else:
        pass

tmat = [] #typical materials lise
text = item_prop_mat_typ.read().splitlines()
tar = []
for i in range(len(text)): #Just a list of materials
    if text[i] != "":
        tar = tar + [text[i]]
        tmat = tmat + [tar]
        tar = []
    else:
        pass


###
# Lists of additional properties, for randomly filling in <stuff> tags in item bases
###
colors = ["red","orange","yellow","green","blue","purple","gold","grey","white","black"]
vowels = ["A","E","I","O","U","a","e","i","o","u"]
beasts = ['ape','badger','bear','boar','bull','deer','eagel','elephant','goat','hare','hawk','horse','lion','owl','tiger','fox','panther','dog','cat','rat','raven','lizard','snake','wolf']
creatures = ['dragon','unicorn','gryphon','centaur','mermaid','oni','demon','pheonix','minotaur','fairy','hydra','pegasus','werewolf']
liquids = ["water","sweat","blood","tears","urine","beer","mead","wine","saltwater","acid","spirits","mud","bile","tea","coffee","milk","juice"]
letters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
vowel_letters = ["A","E","F","H","I","L","M","N","O","R","S","X"]
utensils = ['fork','knife','spoon','dagger','lockpick','rod','spatula','spade','bowl','plate','cup','goblet','belt buckle']
smallobjects = ['teeth','coins','feathers','ball bearings','buttons','pins','nails','hooks','kernels']
sensations = ['warm','cold','hot','cool','wet','dry','slimy','sticky','tacky','rough','smooth']

def roll_table(name):
    #Function to roll on a table, by the name of the table (which is the key in the dict)
    if not(name in bs_tables): #If the name is wrong, return nothing
        return False
    tab = bs_tables[name] #Grab the table entry
    die = tab[0] #Grab what die is rolled for the table
    val,rolls,_,_ = die_parser(die) #Roll that die set
    lne_pick = None #line holder
    for lne in tab[1]: #Loop over the lines
        if (val >= lne[0][0]) and (val <= lne[0][1]): #If the roll is between the targets
            lne_pick = lne #grab the line
        else: #otherwise pass
            pass

    if lne_pick == None: #if not found, report so we can go find and fix it
        print(val,die,name)

    #Otherwise return the selected line
    return lne_pick

class person:
    #Class to hold a generic 'person' relative to main character

    def __init__(self,personage):
        #Make up the basics

        #Race, alignment, occupation (can be a class- see below)
        self.race = roll_table("Race")[1]
        self.alignment = roll_table("Alignment")[1]
        self.occupation = roll_table("Occupation")[1]

        #holder for background, if generated, and death flag
        self.background = None
        self.is_dead = False

        #Make a class for an 'adventurer'
        if self.occupation == "Adventurer":
            self.occupation = roll_table("Class")[1]
            self.background = roll_table("Background")[1]
        self.rel_age = roll_table("Birth Order")[1] #Grab relative age, since might be a sibling
        while self.rel_age == "Twin":
            self.rel_age = roll_table("Birth Order")[1]

        #Grab the death state
        self.status = roll_table("Status")[1]
        if self.status == "Dead (roll on the Cause of Death table)":
            self.is_dead = True
            #Grab the cause of death and format for output
            S_death = roll_table("Cause of Death")
            if S_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                self.status = "were " + S_death[1]
            if S_death[0] in [(4,4),(5,5)]:
                self.status = "had an " + S_death[1]
            if S_death[0] in [(6,7),(8,8),(12,12)]:
                self.status = "died by " + S_death[1]
            if S_death[0] in [(1,1)]:
                self.status = "perished under unknown circumstances"

        #Personage is the type of person relative to main character
        self.personage = personage
        self.relationship = None #Empty relationship flag for now

    def print_person(self):
        #Function to output person's information pretty for handling elsewhere
        if self.is_dead:
            S = "You had a"
            if self.personage[0] in ['A','E','I','O','U']: #This shows up a lot to make grammar do
                S = S + "n"
            S = S + " " + self.personage + " "
            S = S + "who was a " + self.alignment + " " + self.occupation + ". "
            if self.background != None:
                S = S + "They had been a " + self.background + " before becoming a " + self.occupation + ". "
            S = S + "They " + self.status + ". "
        else:
            S = "You have a"    
            if self.personage[0] in ['A','E','I','O','U']:
                S = S + "n"
            S = S + " " + self.personage + " "
            S = S + "who is a " + self.alignment + " " + self.occupation + ". "
            if self.background != None:
                S = S + "They were a " + self.background + " before becoming a " + self.occupation + ". "
            S = S + "They are " + self.rel_age + " than you, and they are " + self.status + ". "
            if self.relationship != None:
                S = S + "They are currently " + self.relationship + " to you. "
        return S

class family_member:
    #Class specifically to hold a family member of the main character

    def __init__(self,_sib):
        #Initialize all properties empty
        self.occupation = None
        self.alignment = None
        self.rel_age = None
        self.relationship = None
        self.status = None

        self.is_sib = _sib #put in whether a sibling on create
        self.parentage = None
        self.is_dead = False

    def print_fam(self):
        #Function to pretty prent the family member for output
        S = ""
        if self.parentage == None and not(self.is_dead):
            if self.rel_age[0] == "O":
                S = "An " + self.rel_age + " sibling who is a "
            else:
                S = "A " + self.rel_age + " sibling who is a "
            S = S + self.alignment + " " + self.occupation +  " "
            S = S + "with whom you are " + self.relationship + " "
            S = S + "and who is " + self.status
        if self.parentage == None and self.is_dead:
            if self.rel_age[0] == "O":
                S = "An " + self.rel_age + " sibling who " + self.status
            else:
                S = "A " + self.rel_age + " sibling who " + self.status
        if self.parentage != None and not(self.is_dead):
            S = "Your " + self.parentage + " who is a "
            S = S + self.alignment + " " + self.occupation +  " "
            S = S + "with whom you are " + self.relationship + " "
            S = S + "and who is " + self.status
        if self.parentage != None and self.is_dead:
            S = "Your " + self.parentage + " who " + self.status
        return S

    def get_occupation(self):
        #Make an occupation for this family member
        self.occupation = roll_table("Occupation")[1]
        if self.occupation == "Adventurer":
            self.occupation = roll_table("Class")[1]

    def get_alignment(self):
        #Make an alignment
        self.alignment = roll_table("Alignment")[1]

    def get_status(self):
        #Get their current status
        self.status = roll_table("Status")[1]

        #Update if dead
        if self.is_sib and self.status == "Dead (roll on the Cause of Death table)":
            self.is_dead = True
            S_death = roll_table("Cause of Death")
            if S_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                self.status = "Was " + S_death[1]
            if S_death[0] in [(4,4),(5,5)]:
                self.status = "Had an " + S_death[1]
            if S_death[0] in [(6,7),(8,8),(12,12)]:
                self.status = "Died by " + S_death[1]
            if S_death[0] in [(1,1)]:
                self.status = "Perished under unknown circumstances"

    def get_relationship(self):
        #Get state of relationship
        self.relationship = roll_table("Relationship")[1]

    def get_rel_age(self):
        #Get relative age (for siblings)
        self.rel_age = roll_table("Birth Order")[1]

    def make(self):
        #Root basic make for all relatives
        self.get_occupation()
        self.get_alignment()
        self.get_status()
        self.get_relationship()
        if self.is_sib:
            self.get_rel_age()
        else:
            pass
        return True
        
class backstory:
    #Backstory class- for building and maintaining all the consistency of elements
    # across the many, many tables that make a backstory

    def __init__(self):
        #Initialization

        self.cha_mod = 0 #cha modifier used in some tables- set later

        #Make basics
        self.age = None
        self.race = None
        self.background = None
        self.Class = None
        self.alignment = None

        #Core consistency flags
        self.know_parents = None 
        self.birthplace = None #birth location
        self.family = None #whether family
        self.num_sib = None
        self.parents = [] #list of arrents
        self.absent_mother = None
        self.absent_father = None
        self.sibs = [] #list of siblings
        self.nonhuman_parents = None #if nonhuman parents

        #Life variables
        self.lifestyle_mod = None #Lifestyle quality
        self.family_lifestyle = None
        self.childhood_home = None #where you lived
        self.childhood_memories = None #how it went

        self.why_bkg = None #background reason (by background)
        self.why_Class = None #class reason

        self.num_life_events = None #number of events rolled
        self.life_events_list = None #list of those

        self.other_people = [] #Additional non-relatives
        self.num_children = 0 #how many kids?

    def make_story(self): 
        #to build up the whole background
        self.get_choices() #core choices
        self.get_family() #family
        self.get_events() #life events

    def print_story(self):
        #pretty-printed everything
        S = self.print_choices() + "\n \n"
        S = S + self.print_family() + "\n \n"
        S = S + self.print_events()
        return S         

    def set_char_traits(self,age=None,CHA=None,background=None,Class=None,race=None,alignment=None):
        #Function to set basics used for consistency, if you want to assign them manually
        if age != None:
            self.age = age
        if CHA != None:
            self.cha_mod = math.floor((CHA-10)/2) #calc mod from CHA
        if background != None:
            self.background = background
        if Class != None:
            self.Class = Class
        if race != None:
            self.race = race
        if alignment != None:
            self.alignment = alignment

    def get_choices(self):
        #Making the life choices sections
        if self.race == None:
            self.race = roll_table("Race")[1] #Assume choices made by fate, okay?
        if self.alignment == None:
            self.alignment = roll_table("Alignment")[1]
        if self.background == None:
            self.background = roll_table("Background")[1]
        self.why_bkg = roll_table(self.background)[1]
        if self.Class == None:
            self.Class = roll_table("Class")[1]
        self.why_Class = roll_table(self.Class)[1]

    def print_choices(self):
        #Pretty print the 'choices'
        S = "You are a " + self.alignment + " " + self.race + " " + self.Class + " "
        S = S + "who began your career as a " + self.background + " "
        S = S + "because " + self.why_bkg + " "
        S = S + "You became a " + self.Class + " because "
        S = S + self.why_Class
        return S

    def get_family(self):
        #Make family- this is the big one
        self.family = roll_table("Family") #initial, key roll

        if self.family == "None": #if no family
            self.num_sib = 0 #no siblings
            self.parents = [] #no parents
            self.know_parents = "You do not know who your parents are or were"
            ls = ["Wretched (-40)","Squalid (-20)","Poor (-10)"," Modest (+0)"] #limited life affluency
            r = random.randint(1,len(ls))
            self.family_lifestyle = ls[r] #lifestyle from limited set
            ls = ["On the streets","Rundown shack","No permanent residence; you moved around a lot","Encampment or village in the wilderness"]
            r = random.randint(1,len(ls)) #pick limited homes
            self.childhood_home = ls[r]

        elif self.family == "Institution, such as an asylum":
            self.family_lifestyle = "Poor (-10)" #Automatic choices here
            self.childhood_home = "Institute"
            pass

        elif self.family == "Temple":
            ls = ["Poor (-10)","Modest (+0)","Comfortable (+10)"]
            r = random.randint(1,len(ls)) #Limited affluency
            self.family_lifestyle = ls[r]
            self.childhood_home = "Temple" #fixed home
            pass

        elif self.family == "Orphanage":
            ls = ["Wretched (-40)","Squalid (-20)","Poor (-10)"," Modest (+0)"]
            r = random.randint(1,len(ls)) #limited affluency
            self.family_lifestyle = ls[r]
            self.childhood_home = "Orphanage" #known home
            self.parents = []
            self.know_parents = "You do not know who your parents are or were" #unknown parents

        elif self.family == "Guardian": #No extra flag limits
            pass

        #extended family means you know parents
        elif self.family == "Paternal or maternal aunt, uncle, or both; or extended family such as a tribe or clan":
            self.know_parents = "You know who your parents are or were"
            self.absent_mother = True
            self.absent_father = True

        #same as above
        elif self.family == "Paternal or maternal grandparent(s)":
            self.know_parents = "You know who your parents are or were"
            self.absent_mother = True
            self.absent_father = True

        #no additional flags
        elif self.family == "Adoptive family (same or different race)":
            pass

        #know mom is absent
        elif self.family == "Single father or stepfather":
            self.know_parents = "You know who your parents are or were"
            self.absent_mother = True

        #know dad is absent
        elif self.family == "Single mother or stepmother":
            self.absent_father = True
            self.know_parents = "You know who your parents are or were"

        #Know you know your parents
        elif self.family == "Mother and father":
            self.know_parents = "You know who your parents are or were"

        #Otherwise, find out ig you know them
        if self.know_parents == None:
            self.know_parents = roll_table("Parents")[1]

        #if you know them
        if self.know_parents != "You do not know who your parents are or were":
            #Make mother and father
            mother = family_member(False)
            mother.make()
            mother.parentage = "Mother"
            father = family_member(False)
            father.make()
            father.parentage = "Father"
            self.parents = [mother,father]
        else: #otherwise, you don't have facts about them
            self.parents = []

        #For absent mother
        if self.absent_mother != None:
            self.absent_mother = roll_table("Absent Parent")[1] #roll why
            #If dead, mark flag and grab reason
            if self.absent_mother == "Your parent died (roll on the Cause of Death supplemental table).":
                M_death = roll_table("Cause of Death")
                if M_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                    self.absent_mother = "Your mother was " + M_death[1]
                elif M_death[0] in [(4,4),(5,5)]:
                    self.absent_mother = "Your mother had an " + M_death[1]
                elif M_death[0] in [(6,7),(8,8),(12,12)]:
                    self.absent_mother = "Your mother died by " + M_death[1]
                else:
                    self.absent_mother = "Your mother perished under unknown circumstances"

        #Same for father
        if self.absent_father != None:
            self.absent_father = roll_table("Absent Parent")[1]
            if self.absent_father == "Your parent died (roll on the Cause of Death supplemental table).":
                F_death = roll_table("Cause of Death")
                if F_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                    self.absent_father = "Your father was " + M_death[1]
                elif F_death[0] in [(4,4),(5,5)]: 
                    self.absent_father = "Your father had an " + M_death[1]
                elif F_death[0] in [(6,7),(8,8),(12,12)]:
                    self.absent_father = "Your father died by " + M_death[1]
                else:
                    self.absent_father = "Your father perished under unknown circumstances"

        #If you know them, roll up nonhuman parents features
        if self.know_parents != "You do not know who your parents are or were":
            if self.race == "Half-elf":
                self.nonhuman_parents = roll_table("Half-Elf Parents")
            if self.race == "Half-orc":
                self.nonhuman_parents = roll_table("Half-Orc Parents")
            if self.race == "Tiefling":
                self.nonhuman_parents = roll_table("Tiefling Parents")

        #Without siblings picked yet
        if self.num_sib == None:
            sib_dice = roll_table("Number of Siblings")[1] #roll up how-many range
            if sib_dice != "None": #if some of them
                self.num_sib = die_parser(sib_dice)[0]#roll how many actually
            else:
                self.num_sib = 0 #else, just none
        else: #if already picked, leave that number in
            pass

        #for how many siblings you have
        for s in range(self.num_sib):
            sib_s = family_member(True) #create a sibling family member
            sib_s.make() #make the sibling proper
            self.sibs = self.sibs + [sib_s] #add to list

        if self.family_lifestyle == None: #if not set lifestyle already
            self.family_lifestyle = roll_table("Family Lifestyle")[1] #roll it up
            self.lifestyle_mod = int(self.family_lifestyle.split("(")[1][1:-1]) #select modifier (for leter)

        if self.childhood_home == None: #make home if not already set, based on lifestyle mod
            bs_tables["Childhood Home"][0] = bs_tables["Childhood Home"][0].split("+")[0]+"+"+str(self.lifestyle_mod)
            self.childhood_home = roll_table("Childhood Home")[1]

        if self.childhood_memories == None: #make memories, based on charisma mod, if set
            bs_tables["Childhood Memories"][0] = bs_tables["Childhood Memories"][0].split("+")[0]+"+"+str(self.cha_mod)
            self.childhood_memories = roll_table("Childhood Memories")[1]

    def print_family(self):
        #pretty print family for use elsewhere
        if self.family[1] == "None": #special for 'no family'
            S = "You had no family"
            if self.childhood_home == "On the streets":
                S = S + " and you lived " + self.childhood_home + "."
            if self.childhood_home == "Rundown shack":
                S = S + " and you lived in a " + self.family_lifestyle[1].split(" ")[0] + " " + self.childhood_home + "."
            if self.childhood_home == "No permanent residence; you moved around a lot":
                S = S + " and you had " + self.childhood_home + "."
            if self.childhood_home == "Encampment or village in the wilderness":
                S = S + " and you lived in an " + self.childhood_home + "."
            return S

        #formatting for parents
        if self.know_parents == "You know who your parents are or were":
            S = "Your family consists of: \n"
            if self.absent_mother == None:
                S = S + self.parents[0].print_fam() + ".\n"
            else:
                S = S + self.absent_mother + ".\n"

            if self.absent_father == None:
                S = S + self.parents[1].print_fam() + ".\n"
            else:
                S = S + self.absent_father + ".\n"
        else:
            S = self.know_parents + ", "

        #Special for no siblings
        if self.num_sib == 0:
            if self.know_parents == "You know who your parents are or were":
                S = S + "You have no siblings. \n"
            else:
                S = S + "and you have no siblings. \n"
        else: #if siblings
            if self.know_parents == "You know who your parents are or were":
                if self.num_sib > 1:
                    S = S + "Additionally, you have " + str(self.num_sib) + " siblings: \n"
                if self.num_sib == 1:
                    S = S + "Additionally, you have " + str(self.num_sib) + " sibling: \n"
            else:
                S = S + "but you have " + str(self.num_sib) + " siblings: \n"

            #Listing out siblings
            i = 1
            for sib in self.sibs: #putting each one in list off their pretty print
                if len(self.sibs) > 1 and i == len(self.sibs)-1:
                    S = S + sib.print_fam() + "; and \n"
                else:
                    S = S + sib.print_fam() + "; \n"
                i+=1
            S = S[:-3]+".\n"

        #For history growing up
        if self.family[1] != 'None':
            S = S + "You grew up "

            #Formatting for different homes
            if self.family[1] in ["Institution, such as an asylum", "Orphanage"]:
                S = S + "in an " + self.family[1] + " in " +self.family_lifestyle.split(" ")[0] + " conditions. "
            if self.family[1] in ["Temple"]:
                S = S + "in a " + self.family_lifestyle.split(" ")[0] + " " + self.family[1] + ". "
            if self.family[1] in ["Guardian","Single father or stepfather","Single mother or stepmother"]:
                S = S + "with a " + self.family[1] + ". "
            if self.family[1] in ["Paternal or maternal aunt, uncle, or both; or extended family such as a tribe or clan","Paternal or maternal grandparent(s)","Mother and father"]:
                S = S + "with your " + self.family[1] + ". "
            if self.family[1] in ["Adoptive family (same or different race)"]:
                S = S + "with an " + self.family[1] + ". "

            #Formatting for living with family
            if self.family[1] in ["Guardian","Single father or stepfather","Single mother or stepmother"]+["Paternal or maternal aunt, uncle, or both; or extended family such as a tribe or clan","Paternal or maternal grandparent(s)","Mother and father"]+["Adoptive family (same or different race)"]:
                #Affluency descriptors
                S = S + "You "
                if self.family_lifestyle in ["Wretched (-40)","Squalid (-20)","Poor (-10)"]:
                    S = S + "were impoverished, "
                if self.family_lifestyle in ["Modest (+0)","Comfortable (+10)"]:
                    S = S + "had enough to get by, "
                if self.family_lifestyle in ["Wealthy (+20)","Aristocratic (+40)"]:
                    S = S + "were well off, "

                #Standard residences
                if not(self.childhood_home in ["On the streets","No permanent residence; you moved around a lot"]):
                    S = S + "and you resided in "
                    if self.family_lifestyle != "Aristocratic (+40)":
                        S = S + "a "
                    else:
                        S = S + "an "
                    S = S + self.family_lifestyle.split(" ")[0] + " " + self.childhood_home + ". "
                #transients
                else:
                    if self.childhood_home == "On the streets":
                        S = S + "and you lived " + self.childhood_home[1] + ". "
                    if self.childhood_home == "No permanent residence; you moved around a lot":
                        S = S + "and you had " + self.childhood_home[1] + ". "

            #Adding in memories of growing up
            S = S + "Growing up, "
            if self.childhood_memories == "I am still haunted by my childhood, when I was treated badly by my peers.":
                S = S + "your childhood was awful and your peers mistreated you. You are still haunted by the memories of it. "
            if self.childhood_memories == "I spent most of my childhood alone, with no close friends.":
                S = S + "you spent most of your childhood alone, and had no close friends. "
            if self.childhood_memories == "Others saw me as being diiferent or strange, and so I had few companions.":
                S = S + "others saw you as different or strange, and you had few companions. "
            if self.childhood_memories == "I had a few close friends and lived an ordinary childhood.":
                S = S + "you had a few close friends and a fairly ordinary childhood. "
            if self.childhood_memories == "I had several friends, and my childhood was generally a happy one.":
                S = S + "you had several friends, and your childhood was generally happy. "
            if self.childhood_memories == "I always found it easy to make Friends, and I loved being around people.":
                S = S + "you always found it easy to make friends, and loved being around people. "
            if self.childhood_memories == "Everyone knew who I was, and I had friends everywhere I went.":
                S = S + "everyone knew who you were, and you made friends everywhere you went. "

        #Woof, finally!
        return S

    def print_events(self):
        #pretty print for life events

        #Formatting for entry point
        if len(self.life_events_list) > 1:
            S = "Throughout your life before now, you experienced some notable things:"
        else:
            S = "Throughout your life, only one notable thing has happened to you so far:"

        #Add in each event
        for event in self.life_events_list:
            S = S + event + "\n"

        #Add in the additional people
        S = S + "\n"
        if len(self.other_people) > 0: #If some people:

            #format entry point
            if len(self.other_people) > 1:
                S = S + "You also have a few notable individuals in your life:"
            if len(self.other_people) == 1:
                S = S + "You also have one particularly notable person in your life:"

            #Add in each person by their pretty print
            for per in self.other_people:
                S = S + per.print_person()+"\n"

        #Last, add in the kids, if any
        if self.num_children > 0:
            if self.num_children > 1:
                S = S + "You also have "+str(self.num_children)+" children. "
            if self.num_children == 1:
                S = S + "You also have "+str(self.num_children)+" child. "
        return S

    def get_events(self):
        #Function to build life events
        # this is another big one

        self.life_events_list = [] #List of events
        event_locks = {} #Dictionary to prevent double-use

        #If an age is defined
        if self.age != None:

            #Set number by age
            if self.age <= 20:
                self.num_life_events = 1
            elif self.age <= 30:
                self.num_life_events = die_parser("1d4+1")[0]
            elif self.age <= 40:
                self.num_life_events = die_parser("1d6+1d4+1")[0]
            elif self.age <= 40:
                self.num_life_events = die_parser("1d8+1d6+1d4")[0]
            elif self.age <= 60:
                self.num_life_events = die_parser("1d10+1d8+1d6")[0]
            else:
                self.num_life_events = die_parser("ld12+1d10+1d8")[0]

        #Otherwise, roll on events by age table
        else:
            self.num_life_events = die_parser(roll_table("Life Events by Age")[1].split(" ")[-1])[0]

        #Event counter
        e_ctr = self.num_life_events
        while e_ctr > 0: #Until you get them all
            event = roll_table("Events") #Roll up an event type

            ###
            #Each event has different required formatting, and some require supplemental rolls.
            #   the length of these sections is handling all that- most are fundamentally the same
            #   notes therefor only remark on unique handling
            #   if `cont =`  is in there, the content text is modified, otherwise the table text is fine
            #   There's a complicated set of event locks, so non-repeatable ones aren't used over
            #       Sometimes duplicates are re-rolled, other times some subsets are re-rolled
            ###

            #Tragedies
            if event[0] == (1,10):
                if not((1,10) in event_locks):
                    event_locks[(1,10)] = [] #Make a lock list for tragedies

                #if you haven't used up all tragedies
                if len(event_locks[(1,10)]) < 11:
                    es = roll_table("Tragedies") #roll one

                    while es in event_locks[(1,10)]: #re-roll duplicates
                        es = roll_table("Tragedies")

                    #lock the newly selected one
                    event_locks[(1,10)] = event_locks[(1,10)] + [es]

                    cont = es[1] #Grab the event content

                    if es[0] == (1,2):
                        cont = "A family member or close friend died. "
                        S_death = roll_table("Cause of Death") #get reason
                        if S_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                            cause = "They were " + S_death[1]
                        if S_death[0] in [(4,4),(5,5)]:
                            cause = "They had an " + S_death[1]
                        if S_death[0] in [(6,7),(8,8),(12,12)]:
                            cause = "They died by " + S_death[1]
                        if S_death[0] in [(1,1)]:
                            cause = "They perished under unknown circumstances"                        
                        cont = cont + cause
                    elif es[0] == (5,5):
                        cont = "You were imprisoned for a crime you didn't commit and spent "+str(roll(1,6)[0])+" years at hard labor or in jail."
                    elif es[0] == (9,9): #Update family relations for this one
                        ls = ['hostile','indifferent']
                        for sib in self.sibs:
                            sib.relationship = ls[random.randint(0,1)]
                        for par in self.parents:
                            par.relationship = ls[random.randint(0,1)]
                    elif es[0] == (11,11):#update known people with an ex-romantic relation person
                        r = random.randint(0,1)
                        if r == 0:
                            cont = "A romantic relationship ended amicably"
                            part = person("Former Lover")
                            ls = ["indifferent","friendly"]
                            part.relationship = ls[random.randint(0,1)]
                            self.other_people = self.other_people + [part]
                        if r == 1:
                            cont = "A romantic relationship ended belligerantly"
                            part = person("Former Lover")
                            ls = ["indifferent","hostile"]
                            part.relationship = ls[random.randint(0,1)]
                            self.other_people = self.other_people + [part]
                    elif es[0] == (12,12):#update known persons with a deceased romantic partner 
                        S_death = roll_table("Cause of Death")
                        if S_death[0] in [(2,2),(3,3),(9,9),(10,10),(11,11)]:
                            cause = "They were " + S_death[1]
                        if S_death[0] in [(4,4),(5,5)]:
                            cause = "They had an " + S_death[1]
                        if S_death[0] in [(6,7),(8,8),(12,12)]:
                            cause = "They died by " + S_death[1]
                        if S_death[0] in [(1,1)]:
                            cause = "They perished under unknown circumstances"                        
                        cont = "A romantic partner died. "+ cause + ". "
                        if S_death[0] == (2,2) and random.randint(1,12)==12:
                            cont = cont + "You were responsible. "
                        part = person("Romantic Partner")
                        part.is_dead = True
                        part.status = cause
                        self.other_people = self.other_people + [part]
                    self.life_events_list = self.life_events_list + [cont] #Add content to events list
                    e_ctr-=1
                else:
                    pass

            #Boons
            if event[0] == (11,20):
                if not((11,20) in event_locks):
                    event_locks[(11,20)] = [] #make boons lock

                if len(event_locks[(11,20)]) < 10: #If you haven't used all the boons
                    es = roll_table("Boons") #roll it up
                    while es in event_locks[(11,20)]:
                        es = roll_table("Boons")
                    event_locks[(11,20)] = event_locks[(11,20)] + [es]

                    cont = es[1]
                    if es[0] == (2,2): #Add a retainer person with attitude for this one
                        ret = person("Retainer")
                        ret.relationship = "Friendly"
                        ret.occupation = "Laborer"
                        self.other_people = self.other_people + [ret]
                    if es[0] == (4,4): #You found some gold!
                        cont = "You found "+str(roll(1,20)[0])+" gp"
                    if es[0] == (10,10): #Reformatting w/ rolled amount
                        cont = "A distant relative left you a stipend that enables you to live at the comfortable lifestyle for "+str(roll(1,20)[0])+" years. If you choose to live at a higher lifestyle, you reduce the price of the lifestyle by 2 gp during that time period."
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1

            #Fell in love or got married
            if event[0] == (21,30):

                #Lock to keep consistent, but on first one you get a current spouse, and subsequent ones add kids
                if not((21,30) in event_locks):
                    event_locks[(21,30)] = []

                if event_locks[(21,30)] == []: #Add a spouse for this one
                    cont = "You fell in love and got married. "
                    event_locks[(21,30)] = event_locks[(21,30)] + [cont]
                    part = person("Spouse")
                    part.relationship = "Friendly"
                    self.other_people = self.other_people + [part]
                else: #Add a kid for this one
                    cont = "You had a child"
                    self.num_children+=1
                    event_locks[(21,30)] = event_locks[(21,30)] + [cont]
                self.life_events_list = self.life_events_list + [cont]
                e_ctr-=1

            #Made an enemy
            if event[0] == (31,40):
                if not((31,40) in event_locks):
                    event_locks[(31,40)] = [] #Directly set an enemy person for this one
                    enem = person("Enemy")
                    enem.relationship = "Hostile"
                    self.other_people = self.other_people + [enem]
                    cont = "You made an enemy. "
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Made a friend of an adventurer
            if event[0] == (41,50):
                if not((41,50) in event_locks):
                    event_locks[(41,50)] = [] #Add an adventurer friend with class and background
                    adv = person("Adventurer Friend")
                    adv.relationship = "Friendly"
                    adv.occupation = roll_table("Class")[1]
                    adv.background = roll_table("Background")[1]
                    self.other_people = self.other_people + [adv]
                    cont = "You made friends with another adventurer. "
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass
                
            #Spent time working a job
            if event[0] == (51,70):
                if not((51,70) in event_locks):
                    event_locks[(51,70)] = [] #Edit to note it's related to your background
                    cont = "You spent some time working a job related to your background as a " + self.background + ". "
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Met someone imporant
            if event[0] == (71,75):
                imp = person("Important Acquaintance") #Add an important person to known people
                ls = ["indifferent","friendly"]
                imp.relationship = ls[random.randint(0,1)]
                ls = ["Academic","Adventurer","Aristocrat","Aristocrat","Entertainer","Merchant","Politician or bureaucrat","Priest"] #Limited occupations
                occ = ls[random.randint(0,len(ls)-1)]
                if occ == "Adventurer":
                    imp.background = roll_table("Background")[1]
                    imp.occupation = roll_table("Class")[1]
                else:
                    imp.occupation = occ
                cont = "You met an important "+imp.occupation +". "
                self.other_people = self.other_people + [imp]

            #Went on an adventure
            if event[0] == (76,80):
                if not((76,80) in event_locks):
                    event_locks[(76,80)] = []
                    if len(event_locks[(76,80)]) < 11:
                        es = roll_table("Adventures") #Roll additional adventures
                    while es in event_locks[(76,80)]:
                        es = roll_table("Adventures")
                    event_locks[(76,80)] = event_locks[(76,80)] + [es] #add up adventure locks
                    cont = es[1]
                    #Adventure results needing modified
                    if es[0] == (1,10):
                        cont = "You nearly died. You have nasty scars on your body, and you are missing an ear, "+str(roll(1,3)[0])+" fingers and "+str(roll(1,4)[0])+" toes."
                    if es[0] == (81,90):
                        cont = "You found some treasure on your adventure. You have "+str(roll(2,6)[0])+" gp left from your share of it."
                    if es[0] == (81,90):
                        cont = "You found a considerable amount of treasure on your adventure. You have "+str(roll(1,20)[0]+50)+" gp left from your share of it."
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1

                else:
                    pass

            #Supernatural experience
            if event[0] == (81,85):
                if not((81,85) in event_locks):
                    event_locks[(81,85)] = []
                if len(event_locks[(81,85)]) < 15:
                    es = roll_table("Supernatural Events") #Roll up the event type
                    while es in event_locks[(81,85)]:
                        es = roll_table("Supernatural Events")
                    event_locks[(81,85)] = event_locks[(81,85)] + [es] #no repeats here
                    cont = es[1]
                    #Ones needing modification:
                    if es[0] == (1,5):
                        cont = "You were ensorcelled by a fey and enslaved for "+str(roll(1,6)[0])+" years before you escaped."
                    if es[0] == (11,15):
                        cont = "A devil tempted you. Make a DC 10 Wisdom saving throw. On a failed save, your alignment shifts one step toward evil (ifit‘s not evil already), and you start the game with an additional "+str(roll(1,20)[0]+50)+" gp."
                    if es[0] == (71,75):
                        ls = ["a celestial", "a devil", "a demon", "a fey", "an elemental", "an undead"]
                        cont = "You were briefly possessed by "+ls[roll(1,6)[0]-1]+". "
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Fought in a battle
            if event[0] == (86,90):
                if not((86,90) in event_locks):
                    event_locks[(86,90)] = []
                    if len(event_locks[(86,90)]) < 7:
                        es = roll_table("War")
                    while es in event_locks[(86,90)]:
                        es = roll_table("War")
                    event_locks[(86,90)] = event_locks[(86,90)] + [es] #No repeats, and none need mods
                    cont = es[1]
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Committed a crime
            if event[0] == (91,95):

                if not((91,95) in event_locks):
                    event_locks[(91,95)] = []
                if len(event_locks[(91,95)]) < 8:
                    es = roll_table("Crime") #Roll up the crime committed
                    while es in event_locks[(91,95)]:
                        es = roll_table("Crime") #No repeats
                    event_locks[(91,95)] = event_locks[(91,95)] + [es]
                    cont = "You were were accused of "+es[1]+". " #formatting, just one compatibility mod
                    resol = roll_table("Punishment")
                    if resol[0] == (9,12):
                        cont = cont + "You were caught and convicted. You spent time in jail, chained to an oar, or performing hard labor. You served a sentence of "+str(roll(1,4)[0])+" years or succeeded in escaping after that much time."
                    else:
                        cont = cont + resol[1] + " "
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Arcane Matters
            if event[0] == (96,99):
                if not((96,99) in event_locks):
                    event_locks[(96,99)] = []
                if len(event_locks[(96,99)]) < 10:
                    es = roll_table("Arcane Matters")
                    while es in event_locks[(96,99)]:
                        es = roll_table("Arcane Matters") #No re-rolls, no mods
                    event_locks[(96,99)] = event_locks[(96,99)] + [es]
                    cont = es[1]
                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass

            #Weird Stuff
            if event[0] == (100,100):

                if not((100,100) in event_locks):
                    event_locks[(100,100)] = []

                if len(event_locks[(100,100)]) < 12:
                    es = roll_table("Weird Stuff")
                    while es in event_locks[(100,100)]:
                        es = roll_table("Weird Stuff") #no repeats
                    event_locks[(100,100)] = event_locks[(100,100)] + [es]

                    cont = es[1] #A few re-formats and mods
                    if es[0] == (1,1):
                        cont = "You were turned into a toad and remained in that form for "+str(roll(1,4)[0])+" weeks."
                    if es[0] == (3,3):
                        cont = "You were enslaved by a hag, a satyr, or some other being and lived in that creature’s thrall for "+str(roll(1,6)[0])+" years."
                    if es[0] == (4,4):
                        cont = "A dragon held you as a prisoner for "+str(roll(1,4)[0])+" months until adventurers killed it."
                    if es[0] == (6,6):
                        adv = person("Former Employer")
                        adv.background = roll_table("Background")[1]
                        adv.occupation = roll_table("Class")[1]
                        adv.relationship = "Friendly"
                        self.other_people = self.other_people + [adv]
                        cont = "You served a powerful adventurer as a hireling. You have only recently left that service."
                    if es[0] == (7,7):
                        cont = "You went insane for "+str(roll(1,6)[0])+" years and recently regained your sanity. A tic or some other bit of odd behavior might linger."

                    self.life_events_list = self.life_events_list + [cont]
                    e_ctr-=1
                else:
                    pass
        #Woof, finally done!

    def makeWebData(self):
        #A function to make up the browser-friendly chunks for later html formatting

        #Core things about your personhood
        P1 = "A " + self.alignment + " " + self.race + " " + self.Class
        P2 = "You began your career as a " + self.background + " because " + self.why_bkg
        P3 = "You became a " + self.Class + " because " + self.why_Class

        #Variables for remaining life settings
        parents = []
        siblings = []
        home = ""
        condition = ""
        memories = []

        if self.family[1] == "None": #unique for no family
            parents = []
            siblings = []
            home = ""

            if self.childhood_home == "On the streets":
                home = "You lived " + self.childhood_home + "."
            if self.childhood_home == "Rundown shack":
                home = "You lived in a " + self.family_lifestyle[1].split(" ")[0] + " " + self.childhood_home + "."
            if self.childhood_home == "No permanent residence; you moved around a lot":
                home = "You had " + self.childhood_home + "."
            if self.childhood_home == "Encampment or village in the wilderness":
                home = "You lived in an " + self.childhood_home + "."

        else:
            #Parents
            if self.know_parents == "You know who your parents are or were":
                parents = ["Your family consists of:"]
                if self.absent_mother == None:
                    parents = parents + [self.parents[0].print_fam() + ".\n"]
                else:
                    parents = parents + [self.absent_mother + ".\n"]

                if self.absent_father == None:
                    parents = parents + [self.parents[1].print_fam() + ".\n"]
                else:
                    parents = parents + [self.absent_father + ".\n"]
            else:
                parents = [self.know_parents + ". "]

            #Siblings
            if self.num_sib == 0:
                    siblings = []
            else:
                for sib in self.sibs:
                    siblings = siblings + [sib.print_fam()]

            #Home
            if self.family[1] in ["Institution, such as an asylum", "Orphanage"]:
                home = "You lived in an " + self.family[1] + " in " +self.family_lifestyle.split(" ")[0] + " conditions. "
            if self.family[1] in ["Temple"]:
                home = "You lived in a " + self.family_lifestyle.split(" ")[0] + " " + self.family[1] + ". "
            if self.family[1] in ["Guardian","Single father or stepfather","Single mother or stepmother"]:
                home = "You lived with a " + self.family[1] + ". "
            if self.family[1] in ["Paternal or maternal aunt, uncle, or both; or extended family such as a tribe or clan","Paternal or maternal grandparent(s)","Mother and father"]:
                home = "You lived with your " + self.family[1] + ". "
            if self.family[1] in ["Adoptive family (same or different race)"]:
                home = "You lived with an " + self.family[1] + ". "

            #Condition
            if self.family[1] in ["Guardian","Single father or stepfather","Single mother or stepmother"]+["Paternal or maternal aunt, uncle, or both; or extended family such as a tribe or clan","Paternal or maternal grandparent(s)","Mother and father"]+["Adoptive family (same or different race)"]:
                condition = "You "
                if self.family_lifestyle in ["Wretched (-40)","Squalid (-20)","Poor (-10)"]:
                    condition = condition + "were impoverished. "
                if self.family_lifestyle in ["Modest (+0)","Comfortable (+10)"]:
                    condition = condition + "had enough to get by. "
                if self.family_lifestyle in ["Wealthy (+20)","Aristocratic (+40)"]:
                    condition = condition + "were well off. "

                if not(self.childhood_home in ["On the streets","No permanent residence; you moved around a lot"]):
                    home = "You lived in "
                    if self.family_lifestyle != "Aristocratic (+40)":
                        home = home + "a "
                    else:
                        home = home + "an "
                    home = home + self.family_lifestyle.split(" ")[0] + " " + self.childhood_home + ". "
                else:
                    if self.childhood_home == "On the streets":
                        home = "You lived " + self.childhood_home + ". "
                    if self.childhood_home == "No permanent residence; you moved around a lot":
                        home = "You had " + self.childhood_home + ". "

        #Memories
        memories = ""
        if self.childhood_memories == "I am still haunted by my childhood, when I was treated badly by my peers.":
            memories = memories + "your childhood was awful and your peers mistreated you. You are still haunted by the memories of it. "
        if self.childhood_memories == "I spent most of my childhood alone, with no close friends.":
            memories = memories + "you spent most of your childhood alone, and had no close friends. "
        if self.childhood_memories == "Others saw me as being diiferent or strange, and so I had few companions.":
            memories = memories + "others saw you as different or strange, and you had few companions. "
        if self.childhood_memories == "I had a few close friends and lived an ordinary childhood.":
            memories = memories + "you had a few close friends and a fairly ordinary childhood. "
        if self.childhood_memories == "I had several friends, and my childhood was generally a happy one.":
            memories = memories + "you had several friends, and your childhood was generally happy. "
        if self.childhood_memories == "I always found it easy to make Friends, and I loved being around people.":
            memories = memories + "you always found it easy to make friends, and loved being around people. "
        if self.childhood_memories == "Everyone knew who I was, and I had friends everywhere I went.":
            memories = memories + "everyone knew who you were, and you made friends everywhere you went. "

        #Events
        events = []
        if len(self.life_events_list) > 1:
            events = events + ["Throughout your life before adventuring, you experienced some notable things:"]
        else:
            events = events + ["In your life, only one notable thing has happened to you so far:"]

        for event in self.life_events_list:
           events = events + [event]

        #People
        people = []
        if len(self.other_people) > 0:
            if len(self.other_people) > 1:
                people = people + ["You also have a few notable individuals in your life:"]
            if len(self.other_people) == 1:
                people = people + ["You also have one particularly notable person in your life:"]
            for per in self.other_people:
                people = people + [per.print_person()]

        #Children
        children = ''
        if self.num_children > 0:
            if self.num_children > 1:
                children = "you have "+str(self.num_children)+" children. "
            if self.num_children == 1:
                children = "you have one child. "

        #Output all the chunks
        return P1,P2,P3,parents,siblings,condition,home,memories,events,people,children

def fixCases(s):
    #A function to fix the casing and punctuation of a string
    # A lot of the loaded in files have weird casing and punctuation from source copy things
    # being lazy, we fix them here rather than editing the docs. Plus is that you can add freely
    # without messing this up
    s = s.lower() #Convert all to lower case
    s_sp = s.split(".") #split by periods
    if (s_sp[-1] in ['',' ','\n']): #For any whitespace at end
        s_sp = s_sp[:-1] #truncate
    s_sp = [a.strip() for a in s_sp] #Strip other whitespace on edges of partitions
    s_sp = [a[0].upper()+a[1:] for a in s_sp] #Make first character uppercase on all parts
    s = "" #new output string
    for a in s_sp: #for each fixed fragment
        if not(a[-1] in [':']): #if not a colon trailing
            s = s + a + ". " #add snip and a period
        else:
            s = s + a #otherwise just add the snip
    return s #return processed string
    

def makeWebPrint(P1,P2,P3,parents,siblings,condition,home,memories,events,people,children):
    #Function to take in the segments of a made character background and put them into the HTML formatting we want

    #Load in all the fixed segments which are single strings
    P1 = fixCases(P1)
    P2 = fixCases(P2)
    P3 = fixCases(P3)
    condition = fixCases(condition)
    home = fixCases(home)
    memories = fixCases(memories)
    children = fixCases(children)

    #Make all lists of strings into lists of fixed strings
    parents = [fixCases(a) for a in parents]
    siblings = [fixCases(a) for a in siblings]
    events = [fixCases(a) for a in events]
    people = [fixCases(a) for a in people]

    ###
    #The response itself is the html we want to see on page- the JS side grabs it and puts it right in the display div
    ###

    #Start off with header and content div with known style
    resp = '<h2>'+P1[:-2]+"</h2><hr><div style='float:left;padding-left:30px;padding-top:10px;padding-bottom:10px;'>"
    resp = resp + P2 + "<br/>" + P3 + "<br/>"

    #Add the 'childhood' section
    resp = resp + '<h3><u>Growing up:</u></h3>'

    #If no parents or siblings, custom formatting
    if (parents == []) and (siblings == []):
        resp = resp + "<div style='padding-left:10px;'>"
        resp = resp + "You have no known family." + "<br/>"
        resp = resp + home + "<br/>"
        resp = resp + memories + "<br/>"
        resp = resp + "</div>"
    else: #otherwise
        resp = resp + "<div style='padding-left:10px;'>" #div for indented text

        #Add in growing up sections
        resp = resp + home + "<br/>"
        resp = resp + condition + "<br/>"
        resp = resp + memories + "<br/><br/>"

        #Add in family sections
        resp = resp + parents[0]
        resp = resp + "<ul>"
        for p in parents[1:]: #List parents
            resp = resp + "<li>" + p + "</li>"
        resp = resp + "</ul>"

        if len(siblings)>0: #list siblings
            resp = resp + "You have "+str(len(siblings))+" sibling"+"s"*(len(siblings)>1) + ":"
            resp = resp + "<ul>"
            for s in siblings:
                resp = resp + "<li>" + s + "</li>"
            resp = resp + "</ul><br/>"
        else:
            resp = resp + "You have no known siblings. <br/>"

        resp = resp + "</div>" #end indent div

    #Life events section
    resp = resp + "<h3>" + events[0] + "</h3>"

    #List life events
    resp = resp + "<ul>"
    for e in events[1:]:
        resp = resp + "<li>" + e + "</li>"
    resp = resp + "</ul>"

    #list people known
    if (len(people)>0):
        resp = resp + people[0]
        resp = resp + "<ul>"
        for pe in people[1:]:
            resp = resp + "<li>" + pe + "</li>"
        resp = resp + "</ul>"

    #List number of kids
    if (children != ''):
        resp = resp + "Finally, " + children

    #End content div and add bar for separation
    resp = resp + "</div><hr>"

    #Return the html response
    return resp

def print_table(name):
    #Utility function to print out a table
    if not(name in bs_tables):
        return False #do nothing if not a real table
    tab = bs_tables[name] #grab table otherwise
    print(name,"  ",tab[0]) #print title and header
    for lne in tab[1]: #print each line with the die roll ranges
        r1 = lne[0][0]
        r2 = lne[0][1]
        cont = lne[1]
        print(str(r1)+"-"+str(r2),"  ",cont)
    return True

def die_parser(dies):
    #function to parse a die roll string and roll it

    dies = dies.strip() #remove whitespace
    pos_curr = 0 #current pointer position
    pos_look = 0 #lookahead positon
    rolls = [] #list of rolls to do
    val = 0 #result value

    dies_list = [] #list of die rolls individually
    interp_string = "" #string of interpreted string

    #loop over all positions in string
    while pos_look < len(dies):

        #Looping over non add or subtract values before the end
        while not(dies[pos_look] in ['+','-']) and (pos_look < len(dies)-1):
            if (pos_look < len(dies)-1): #if not at the end, increment
                pos_look+=1
        if pos_look == len(dies)-1: #At the end, increment look-ahead once more
            pos_look = pos_look+1

        #current segment is from the base positon to the lookahead
        seg = dies[pos_curr:pos_look]

        #If no +/-, at start or empty space, interpret as +
        if not(seg[0] in ['+','-']):
            seg = "+"+seg

        #grab the number of dies and die size around the 'd'
        nd = seg[1:].split('d')
        if len(nd) == 1: #if only one element, it's a constant
            if seg[0] == '+': #if adding
                val = val + int(nd[0]) #add integer value to the value
                interp_string = interp_string + "+" + nd[0] #and to interpreted string
            if seg[0] == '-': #flop to subtract for -
                val = val - int(nd[0])
                interp_string = interp_string + "-" + nd[0]
        else: #if not a constant
            if (nd[0] == ''): #if just 'dK', assume 1dK
                nd[0] = "1" 
            v,rl = roll(int(nd[0]),int(nd[1])) #do the die roll
            dies_list = dies_list + [nd[1]] #add results to list
            if seg[0] == '+': #if adding, add to interpret string and value
                interp_string = interp_string + "+" + nd[0] + "d" + nd[1]
                val = val + v
            if seg[0] == '-': #subtract for -
                interp_string = interp_string + "-" + nd[0] + "d" + nd[1]
                val = val - v
            rolls = rolls + [rl] #add up results to rolled die
        pos_curr = pos_look #set start position to end of frame
        pos_look+=1 #increment look-ahead

    #return the full roll result, the rolled dies, the list of die rolled, and the string actually executed
    return val,rolls,dies_list,interp_string

def make_minor_magic_items(N,pQ,pAmat):
    #Function to make some minor magic items

    items = []#items list

    for i in range(N): #For the number to make

        #bases,makers,minor,tmat,amat,quirk
        base = bases[random.randint(0,len(bases)-1)] #Grab a base item

        #Make up a maker of the item
        r = random.randint(0,makers[-1][1]-1)
        i = 0
        while makers[i][1] < r:
            i+=1
        maker = makers[i]

        #Grab properties
        prop = minor[random.randint(0,len(minor)-1)]
        if prop[0] == 'Dual-Featured': #if 'dual feartured property
            prop = [minor[random.randint(0,len(minor)-3)] for a in range(2)] #roll again twice without the multi-property options
        elif prop[0] == 'Triple-Featured': #same for triple except 3 times
            prop = [minor[random.randint(0,len(minor)-3)] for a in range(3)]
        else:
            prop = [prop] #otherwise, single property list

        #Calculate the chance for atypical materials
        r = random.random()
        if r > pAmat: #traditional materials if over that chance
            mat = [tmat[random.randint(0,len(tmat)-1)][0],tmat[random.randint(0,len(tmat)-1)][0]]
        elif r <= pAmat: #atypical ones otherwise
            mat = [amat[random.randint(0,len(tmat)-1)][0],tmat[random.randint(0,len(tmat)-1)][0]]

        #Check quirk probabiltity
        r = random.random()
        if r > pQ:
            quirks = []
        elif r <= pQ:
            quirks = [quirk[random.randint(0,len(quirk)-1)]] #add a quirk if under that chance

        #Make up a cost- totally random, in the range of those for minor items in the DMG
        cost = random.randint(1,6)*10 + random.randint(1,9)

        #make an item list of all those factors above and add to the list
        item = [base,maker,prop,mat,quirks,cost]
        items = items + [item]

    #Return the list of items
    return items

def print_items(items):
    #Function to pretty print an item
    for item in items:
        print("Item: ",item[0],"  Cost: ",item[5], "gp")
        print("Made by: ",item[1][0])
        print("        ",item[1][2])
        print("Properties: ")
        for p in item[2]:
            print("    ",p[0])
            print("            ",p[1])
        print("Materials: ")
        print("    ",item[3][0])
        print("    ",item[3][1])
        print("Quirks: ")
        if item[4] != []:
            print("    ",item[4][0][0])
            print("        ",item[4][0][1])
        else:
            print("    ","No quirks")
        print("--------")

def roll(n,d):
    #core roll function- roll n d-sided dies, return the sum and individual rolls
    rolls = [random.randint(1,d) for a in range(n)]
    return sum(rolls),rolls

def empowered(rolls,mod,d):
    #Function to roll and empowering check
    # given a set of rolls, a die type d, and a limit modifier
    # up to mod many d dies can be re-rolled, if they're less than the expectation value for that roll

    #Sort the rolls in ascending order
    rolls.sort()

    rolls_l = rolls[:mod] #lowest rolls that can be re-rolled
    rolls_h = rolls[mod:] #rolls that can't be re-rolled
    rolls_l_new = [] #new rolls set

    #for all the low rolls that can be re-rolled
    for r in rolls_l:
        if r < (d+1)/2: #if less than expectation, re-roll
            rolls_l_new = rolls_l_new + [roll(1,d)[1][0]]
        else: #otherwise leave alone
            rolls_l_new = rolls_l_new + [r]

    #make new rolls from re-rolled and originals
    rolls = rolls_l_new + rolls_h

    #return new value and rolls
    return sum(rolls),rolls

def run_trial(dies,N):
    #Function to run a trial on (possibly empowered) rolls to see net effect, averaged over N trials
    # dies is formatted as := [(n,d,E,m)]
    #   n and d define n many d-sided rolls
    #   E is whether to empower this roll set, m is the empower modifier for this set, if applicable

    results = [] #results- holds totals for each die set

    #loop over the number of trials
    for n in range(N):
        total = 0 #summation

        #looping over all the die roll sets
        for die in dies:
            if die[2] == True: #if set to empower this set
                if (die[0] == ''): #if no number of dice specified, assume 1
                    die[0] = '1'
                v,rs = roll(die[0],die[1]) #do the initial roll
                v,rs = empowered(rs,die[3],die[1]) #apply the empowering check
            else: #otherwise
                if (die[0] == ''): #same as aobve- no dice specified means '1'
                    die[0] = '1'
                v,rs = roll(die[0],die[1]) #standeard roll
            total = total + v #add result to total summation
        results = results + [total] #update results for that die set to results

    #Find the total average over all results
    average = sum(results)/len(results)

    #Return calculates average
    return average

def make_chars(n):
    #Function to make up n many character backstories
    s = "" #output string

    for a in range(n): #loop over all n
        ch = backstory() #make the object
        ch.make_story() #call the full story method
        s = s + ch.print_story() + "--------\n" #pretty print the result

    #return the output string
    return s

def make_magic(N,Q,M):
    #Wrapper function to make magic items and print them
    it = make_minor_magic_items(N,Q,M)
    print_items(it) #print the results

async def handle_client(websocket):
    #Function to handle client requests

    try: #mostly for checking open connection

        #For all the received messages
        async for message in websocket:
            print("received:",message) #Report the message- diagnostic

            #We use § delimiter character to denote the message type
            message = message.split('§')

            resp = '' #Start off with nothing to respond, it will be the HTML to display

            #if the client is asking for an empowered roll trial
            if message[0]=="trial":

                #Process dies from message string
                dies = message[1].split(";") #Separate into individual trial types
                dies = dies[:-1] #Remove trailing ''
                dies = [s.split(',') for s in dies] #split dies by comma
                dies = [[int(a) for a in s] for s in dies] #Turn n, d, and mod to integers
                dies = [a[:-1]+[1]+[a[-1]] for a in dies] #Add in the E parameter, since we always use it

                #Run a 10000 trial test to get the average result
                res = run_trial(dies,10000)

                #Build the string for the kind of roll checked
                interpStr = ''
                for d in dies: #Format: ndK(mod)
                    interpStr = interpStr + str(d[0])+"d"+str(d[1]) + "("+str(d[3])+") + "
                interpStr = interpStr[:-3]

                #Start building html results
                resp = "Empower Trial: <span style='color:green;'>" + interpStr + "</span><hr>"
                resp = resp + "&nbsp;&nbsp;<u>Result:</u> <span style='color:blue'>" + str(res) + "</span>" + "<br/>"

                #Display results, along with dies by type and highlighting numbers that might be replaced
                resp = resp + "<div style='padding-left:30px;padding-top:5px;max-width:512;'>"
                for i in range(len(dies)): #for each die
                    resp = resp + "<b>d"+str(dies[i][1])+":</b> " #list what type
                    for j in range(dies[i][1]):
                        if (j<dies[i][3]):
                            resp = resp + "<span style='color:green;'>"+str(j+1)+"</span> "
                        else:
                            resp = resp + "<span style='color:purple;'>"+str(j+1)+"</span> "
                    resp = resp + "<br/>"
                resp = resp + "</div>" #close the indented div

            #If the client is asking us to save results
            if message[0] == "save":
                txt = message[1] #the message is the html to save

                dt = datetime.now() #grab the date and time for unique file name
                tme = str(dt.year)+"-"+str(dt.month)+"-"+str(dt.day) + " " + str(dt.hour) + ":" + str(dt.minute) + ":" + str(dt.second)
                fle = "DnDTools "+tme

                #open the file
                f = open("saves/"+fle+".html",mode='w')

                #write the sent html in between the bases needed to make it a full visible formatted page
                f.write(saveHTMLbase1 + txt + saveHTMLbase2)
                f.close() #close the file before something happens to it

                #result to add to results- notice that the file is saved
                resp = "<center style='color:DarkGreen;'><i>History Saved!</i></center><hr>"

            #If doing a die roll
            if message[0] == "die":
                rollString = message[1] #message is the die string to parse
                rollString = rollString.replace(" ","") #take out all spaces, they're annoying

                #parse the string, and grab the results
                res,rolls,dies,interp = die_parser(rollString)

                #process the interpret string so the user knows what was actually rolled
                interpStr = interp[1:]
                interpStr = interpStr.replace("+"," + ") #space out + and - so the text wrap works
                interpStr = interpStr.replace("-"," - ")

                #Start the response with a note of what actually got rolled
                resp = "Rolling: <span style='color:green;'>" + interpStr + "</span><hr>"

                #Add the actual summed result to the response
                extra = "<i style='color:purple;'> <u>Nice</u></i>"#snrk.
                resp = resp + "&nbsp;&nbsp;<u>Result:</u> <span id='rollRes' style='color:blue'>" + str(res) + "</span>"+ extra*(res==69) + "<br/>"

                #add a formatted div to tab over and hold the rolled dies and their results
                resp = resp + "<div style='float:left;padding-left:30px;padding-top:5px;max-width:512;'>"
                for i in range(len(dies)): #for each die
                    resp = resp + "<b>d"+dies[i]+":</b> " #list what type
                    rs = rolls[i] #grab individual rolls
                    rs.sort() #sort in order for ease of reading
                    for r in rs: #add each roll to the row
                        resp = resp + str(r) + ", "
                    resp = resp[:-2] + "<br/>" #strip trailing comma and add line break
                resp = resp + "</div><br/>" #close the indented div

            #If doing magic items
            if message[0] == "magicitem":
                itemString = message[1] #message content is the generator parameters
                itemsProps = [int(a) for a in itemString.split(",")] #split params by ',' and make to ints

                #call function to make items list, with percents converted to floats against 100.0
                items = make_minor_magic_items(itemsProps[0],itemsProps[1]/100.0,itemsProps[2]/100.0)

                #Sort the items by their cost to buy
                items.sort(key=lambda x: x[-1])

                itemNumber = 1 #item number label
                resp = "" #start the response

                for item in items: #for each item
                    item_sp = item[0].split(" ") #split item base by ' '
                    item[0] = "" #clear old base to handle <stuff> tags

                    ###
                    #For each word in the item base, check if it's a tag to replace and replace it from the appropriate random table
                    #   each one handles a/an grammar with the 'vowels' list, with an oddball one for the letters (a C, an F, an O, a U, etc.)
                    ###
                    for a in item_sp:
                        if "<race>" in a or "<maker>" in a:
                            race = roll_table("Race")[1]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(race[0] in vowels)
                            item[0] = item[0] + " " + race
                        elif "<color>" in a:
                            clr = colors[random.randint(0,len(colors)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(clr[0] in vowels)
                            item[0] = item[0] + " " + clr
                        elif "<material>" in a:
                            mater = tmat[random.randint(0,len(tmat)-1)][0]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(mater[0] in vowels)
                            item[0] = item[0] + " " + mater
                        elif "<weirdmaterial>" in a:
                            mater = amat[random.randint(0,len(amat)-1)][0]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(mater[0] in vowels)
                            item[0] = item[0] + " " + mater
                        elif "<beast's>" in a:
                            beast = beasts[random.randint(0,len(beasts)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(beast[0] in vowels)
                            item[0] = item[0] + " " + beast + "'s"
                        elif "<beast>" in a:
                            beast = beasts[random.randint(0,len(beasts)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(beast[0] in vowels)
                            item[0] = item[0] + " " + beast
                        elif "<creature's>" in a:
                            creature = creatures[random.randint(0,len(creatures)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(creature[0] in vowels)
                            item[0] = item[0] + " " + creature + "'s"
                        elif "<creature>" in a:
                            creature = creatures[random.randint(0,len(creatures)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(creature[0] in vowels)
                            item[0] = item[0] + " " + creature
                        elif "<liquid>" in a:
                            liquid = liquids[random.randint(0,len(liquids)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(liquid[0] in vowels)
                            item[0] = item[0] + " " + liquid
                        elif "<utensil>" in a:
                            utensil = utensils[random.randint(0,len(utensils)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(utensil[0] in vowels)
                            item[0] = item[0] + " " + utensil
                        elif "<letter>" in a:
                            letter = letters[random.randint(0,len(letters)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(letter in vowel_letters)
                            item[0] = item[0] + " " + letter
                        elif "<smallobjects>" in a:
                            smallobject = smallobjects[random.randint(0,len(smallobjects)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(smallobject[0] in vowels)
                            item[0] = item[0] + " " + smallobject
                        elif "<sensation>" in a:
                            sense = sensations[random.randint(0,len(sensations)-1)]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(sense[0] in vowels)
                            item[0] = item[0] + " " + sense
                        elif "<race-crafted>" in a:
                            race = roll_table("Race")[1]
                            item[0] = item[0] + "n"*(item[0][-1]=='a')*(race[0] in vowels)
                            item[0] = item[0] + " " + race + "-stylized"
                        elif ("<" in a) and (">" in a): #Another kind of tag, could be either an <ndK> dice roll or an unhandled tag
                            dTry = a[1:-1] #peel <> to try a die roll
                            try:
                                v = die_parser(a[1:-1])[0] #roll the die
                                item[0] = " " + str(v) #add the numeric value if it works
                            except: #otherwise note that it's unhandled so we can fix it
                                print("UNHANDLED:",a)
                                item[0] = " " + "UNHANDLED:("+a[1:-1] + ")" #put in 'unhandled' in the tag to note it client side, too
                        else: #otherwise
                            if item[0] == "": #if empty string, add first value w/o ' '
                                item[0] = a
                            else: #if not first, add with ' '
                                item[0] = item[0] + " " + a

                    #format the item label header- Item N:... and the div for the properties to follow indented
                    resp = resp + "<b>Item "+str(itemNumber)+"</b>: "+item[0]+"<hr><div style='float:left;padding-left:30px;padding-top:10px;padding-bottom:10px;'>"

                    #Add the maker formatting and content
                    resp = resp + "<u>Provenance: "+item[1][0]+"</u><br/>"
                    resp = resp + "<div style='padding-left:10px;'>" + item[1][2] + "</div><br/>"

                    #Format the materials content, remove duplicates (gold and gold => gold)
                    mats = item[3]
                    matString = mats[0]
                    if not(mats[1] in matString):
                        matString = matString + " and " + mats[1]

                    #Add arcane materials formatting and content
                    resp = resp + "<u>Arcane material"+"s"*('and' in matString)+":</u><br/> <div style='padding-left:10px;'>"
                    resp = resp + matString
                    resp = resp + "</div><br/>"

                    #Add properties formatting and content- properties as a list
                    resp = resp + "<u>Properties:</u> <ul>"
                    for prop in item[2]:
                        resp = resp + "<li>" + prop[0] + ": " + prop[1] + "</li>"
                    resp = resp + "</ul>"

                    #Add quirks, if present, as a list
                    if len(item[4]) > 0:
                        resp = resp + "<u>Quirks:</u> <ul>"
                        for quirk in item[4]:
                            resp = resp + "<li>" + quirk[0] + ": "+ quirk[1] + "</li>"
                        resp = resp + "</ul>"

                    #Add in the cost
                    resp = resp + "<u>Cost:</u> "+str(item[5])+"gp"

                    #Finish with closing the div and a separator line
                    resp = resp + "</div><hr>"

                    #Increment item index
                    itemNumber+=1

            #if requesting a background
            if message[0] == 'background':
                char = backstory() #Make the background object
                char.make_story() #build the whole story
                P1,P2,P3,parents,siblings,condition,home,memories,events,people,children = char.makeWebData() #grab the output chunks
                resp = makeWebPrint(P1,P2,P3,parents,siblings,condition,home,memories,events,people,children) #format chunks into HTML as response

            #Send along the response once it's made
            await websocket.send(resp) #Send the html

    except websockets.exceptions.ConnectionClosed:
        #If it's closed, oh well!
        print("CONNECTION CLOSED")
        pass


#Running server on localhost 
HOST = "127.0.0.1"
PORT = 8080

async def main():

    #Fire up the server
    server = await websockets.serve(handle_client, HOST, PORT)

    webbrowser.open("D&D Dice.html") #Open the html/js side in the browser

    await server.wait_closed() #Spin indefinitely

if __name__ == '__main__':
    #do thing
    asyncio.run(main())    
    
