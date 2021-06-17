#!/usr/bin/env python3

# Název:            interpret.py
# Předmět:          Principy programovacích jazyků a OOP
# Instituce:        VUT FIT
# Autor:            Pavel Bobčík
# Login:            xbobci03
# vytvořeno:        29. březen 2021
# Kompatiliblita:   Python3 a vyšší


import sys
import re
import xml.etree.ElementTree as ET
import os

# Konstany chybových kódů
paramError = 10
openFileError = 11
xmlFormattingError = 31
otherXmlError = 32
semanticError = 52
wrongTypeError = 53
varDoesntExist = 54
frameDoesntExist = 55
missingValue = 56
wrongOperandValueError = 57
stringError = 58

# Globální proměnné
tmpSourceCreated = False
tmpInputCreated = False
sourceFile = None
inputFile = None
inputValue = []
actualInstractionIndex = 0

frameController = None
instructionConstroller = None

# Hlavní třída
# Vykoná kontrolu parametrů, vytvoří dočasnou složku (je-li to zapotřebí), 
# uloží názvy souborů ze vstupu a načte hodnotu input souboru.
# Dále se zda nachází hlavní běhová funkce, jenž volá funkce třídy pro kontrolu počáteční prvků XML,
# vytváří pořadí instrukcí a seznam lablů a poté se stará o volání třídy, 
# která slouží jako switch pro výběr sprévné instrukce.
class Main():
    # Funkce slouží ke kontrole vstupní argumentů a výpisu nápovědy.
    def checkArg(self):
        numOfParam = len(sys.argv)
        if(numOfParam < 2 or numOfParam > 3):
            CleanUp().exitCode(paramError, "Špatný počet parametrů.")
        if(numOfParam == 2 and sys.argv[1] == "--help"):
            print("Použití: python3.8 interpret.py [--source=file] [--input=file]\n" \
            " - Nutno uvést alespoň jeden přepínač.\n" \
            " - V případě udělení práv 'chmod +x interpret.py' lze spustit pomocí:\n"\
            "   o ./interpret.py [--source=file] [--input=file]")
            sys.exit(0)
        if(numOfParam == 2 and not ((re.search("^(--input=)", sys.argv[1]) and not re.search("^(--input=)$", sys.argv[1])) 
                        or (re.search("^(--source=)", sys.argv[1]) and not re.search("^(--source=)$", sys.argv[1])))):
            CleanUp().exitCode(paramError, "Chybný parametr.")
        if(numOfParam == 3 and not ((re.search("^(--input=)[^\s]", sys.argv[1]) and re.search("^(--source=)[^\s]", sys.argv[2])) 
                        or (re.search("^(--input=)[^\s]", sys.argv[2]) and re.search("^(--source=)[^\s]", sys.argv[1])))):
            CleanUp().exitCode(paramError, "Chybný parametr.")

    # Funkce pro vytvoření dočasné složky a nahrání dat ze standartního vstupu.
    # param name název dočasného souboru
    def creteTmpFile(self, name):
        tmpFile = open(name, "w")

        for line in sys.stdin:
            tmpFile.write(line)
        tmpFile.close()

        return name, True

    # Funkce pro uložení názvu souborů.
    def getFilesNameFromArgv(self):
        global tmpSourceCreated
        global tmpInputCreated
        global sourceFile
        global inputFile

        for i in range(1, len(sys.argv)):
            split = sys.argv[i].split("=")
            if(split[0] == "--input"):
                inputFile = split[1]
            else:
                sourceFile = split[1]

        if(sourceFile == None):
            sourceFile, tmpSourceCreated = self.creteTmpFile("_@tmp.xml")
        elif(inputFile == None):
            inputFile, tmpInputCreated = self.creteTmpFile("_@tmp.in")

    # Funkce pro načtení dat ze vstupního souboru.
    def loadInputValue(self):
        global inputValue
        global inputFile

        try:
            file = open(inputFile, "r")
        except FileNotFoundError:
            CleanUp().exitCode(openFileError, "Chyba při otvírání vstupního souboru.")
        inputValue = file.readlines()
        index = 0
        for line in inputValue:
            inputValue[index] = line.rstrip('\n')
            index += 1
        file.close()

    # Hlavní běhová funkce třídy
    def run(self):
        global inputFile
        global sourceFile
        global frameController
        global actualInstractionIndex
        global instructionConstroller

        self.checkArg()
        self.getFilesNameFromArgv()

        frameController = FrameController()
        instructionConstroller = InstructionStackController()

        xmlController = XmlController()
        instructionArr = xmlController.openAndLoadXML()
        orderNumArr, opcodeArr = xmlController.checkInstructionAndGetValues(instructionArr)
        xmlController.checkDuplicate(orderNumArr)

        self.loadInputValue()

        # Vytvoření seznamu labelů
        lookForLabel = 0
        while lookForLabel < len(instructionArr):
            if(opcodeArr[lookForLabel] == "LABEL"):
                instructionConstroller.insertIntoLabelStack(instructionArr[lookForLabel], lookForLabel)
            lookForLabel += 1
        
        while actualInstractionIndex < len(instructionArr):
            switch = Switcher()
            switch.callOpcode(opcodeArr[actualInstractionIndex], instructionArr[actualInstractionIndex])
            actualInstractionIndex += 1

        CleanUp().removeTmpFile()

# Třída slouží pro výpis chyby a úklid dočasných souborů.
class CleanUp():
    # Funkce pro smazání dočasných souborů
    def removeTmpFile(self):
        global tmpSourceCreated
        global tmpInputCreated
        global sourceFile
        global inputFile

        if(tmpSourceCreated):
            os.remove(sourceFile)
            tmpSourceCreated = False
        elif(tmpInputCreated):
            os.remove(inputFile)
            tmpInputCreated = False

    # Funkce pro výpis chyby a ukončení s chybou
    # param exitCode chybová hodnota
    # param exitMsg chybová zpráva
    def exitCode(self, exitCode, exitMsg):
        self.removeTmpFile()
        print(exitMsg, file=sys.stderr)
        sys.exit(exitCode)
    
    # Funkce pro ukončení bez výpisu chybového hlášení
    # param exitCode chybová hodnota
    def exitWithoutMsg(self, exitCode):
        self.removeTmpFile()
        sys.exit(exitCode)

# Třída pro obsluhu XML operací
class XmlController(Main):
    # Funkce slouží k získání pole order a opcode
    # param instructionArr pole instrukcí
    # return pole hodnot order a opcode
    def checkInstructionAndGetValues(self, instructionArr):
        global instructionConstroller
        global actualInstractionIndex
        orderNumArr = []
        opcodeArr = []
        for instruction in instructionArr:
            orderNum, opcode = self.checkSingleInstructionAndGetValues(instruction)
            orderNumArr.append(orderNum)
            opcodeArr.append(opcode)
        return orderNumArr, opcodeArr

    # Funkce slouží k získání hodnoty order a opcode a kontroly správnosti dané instrukce
    # param instruction instrukce k zpracování
    # return hodnotu order a opcode
    def checkSingleInstructionAndGetValues(self, instruction):
        hasOrder = False
        hasOpcode = False
        for key, value in instruction.attrib.items():
            if(key != "order" and key != "opcode"):
                CleanUp().exitCode(otherXmlError, "Element instruction obsahuje nepodporovaný atribut.")
            if(key == "order"):
                orderNum = (int(value))
                hasOrder = True
            else:
                opcode = value
                hasOpcode = True
        if(not hasOrder or not hasOpcode):
            CleanUp().exitCode(otherXmlError, "Element instruction neobsahuje atribut order či opcode.")
        return orderNum, opcode

    # Funkce slouží ke kontrole duplicitních hodnot order
    # param orderNumArr pole hodnot order
    def checkDuplicate(self, orderNumArr):
        for i in range(0, len(orderNumArr)):    
            for j in range(i+1, len(orderNumArr)):    
                if(orderNumArr[i] == orderNumArr[j]):    
                    CleanUp().exitCode(otherXmlError, "Duplicitní hodnota.")

    # Funkce vrací hodnotu order a kontroluje jeho validitu (slouží jako sort key)
    # param instruction instrukce k zpracování
    # return hodnotu order
    def getOrder(self, instruction):
        for key, value in instruction.attrib.items():
            if (key == "order"):
                try:
                    value = int(value)
                except ValueError:
                    CleanUp().exitCode(otherXmlError, "Neplatná hodnota order.")
                if (value < 1):
                    CleanUp().exitCode(otherXmlError, "Hodnota order je menší než 1.")
                return value
        CleanUp().exitCode(otherXmlError, "Element instruction neobsahuje atribut order.")

    # Funkce slouží k načtení XML souboru a provedení potřebných kontrol
    # return pole insturkcí
    def openAndLoadXML(self):
        global sourceFile
        instructionArr = []

        try:
            tree = ET.parse(sourceFile)
        except FileNotFoundError:
            CleanUp().exitCode(openFileError, "Chyba při otevření souboru s XML.")
        except ET.ParseError:
            CleanUp().exitCode(xmlFormattingError, "Chybné formátování XML souboru.")

        # Načtení stromu a kontrola kořenového elementu
        root = tree.getroot()
        if(root.tag == "program"):
            for key, languageVersion in root.attrib.items():
                if(key != "language"):
                    if(key != "name" and key != "description"):
                        CleanUp().exitCode(otherXmlError, "Chybný atribut elementu program.")
                else:
                    if(languageVersion != "IPPcode21"):
                        CleanUp().exitCode(otherXmlError, "Chybný atribut elementu program.")
                
        else:
            CleanUp().exitCode(otherXmlError, "Chybný či chybějící element program.")

        #Kontrola, že se nevyskytují jiné kořenové elementy než podporované a přidání instruction do pole
        for instruction in root:
            if(instruction.tag != "instruction"):
                CleanUp().exitCode(otherXmlError, "Nepodporovaný kořenový element.")
            if(instruction.tag == "instruction"):
                instructionArr.append(instruction)
        
        # Sestřídění pole instructionArr podle hodnoty order vzestupně
        instructionArr.sort(key = self.getOrder)

        return instructionArr 

    # Funkce slouží jako sort key pro arg
    # return vrací hodnotu arg
    def getSortKey(self, element):
        return element.tag

    # Funkce k seřazení elementů (arg) instrukce
    # return seřazené pole elementů (arg)
    def getSortedArrOfElement(self, element):
        elementArr = []
        for value in element:
            elementArr.append(value)
        elementArr.sort(key=self.getSortKey)
        return elementArr

    # Funce na získání hodnoty type z elementu
    # return hodnotu type
    def getTypeOfArg(self, attribute):
        attrib = None
        for key, value in attribute.items():
            if(key != "type"):
                CleanUp().exitCode(otherXmlError, "Element arg obsahuje nepodporovaný atribut.")
            attrib = value
        if(attrib == None):
            CleanUp().exitCode(otherXmlError, "Element arg neobsahuje atribut type.")
        return attrib

    # Funkce získá pole tagů (arg) a atributů (hodnoty type)
    # return pole tagů a atributů
    def getTagAndAttribute(self, element):
        tagArr = []
        attribArr = []
        for child in element:
            tagArr.append(child.tag)
            attribArr.append(self.getTypeOfArg(child.attrib))
        return tagArr, attribArr

    # Funkce kontroluje čísla arg a názvy atributů
    def checkAttribute(self, numberOfAttributes, nontermArray, tagArr, attribArr):
        if(len(tagArr) != numberOfAttributes):
            CleanUp().exitCode(otherXmlError, "Nesprávný počet neterminálů.")
        for i in range(0,numberOfAttributes):

            if(tagArr[i] != "arg"+str(i+1)):
                CleanUp().exitCode(otherXmlError, "Nesprávný element.")

            if(numberOfAttributes > 0):
                if(nontermArray[i] == "symb"):
                    if(not re.search("^(int|bool|string|nil)$", attribArr[i]) and not re.search("^var$", attribArr[i])):
                        CleanUp().exitCode(otherXmlError, "Nesprávný neterminál.")
                elif(nontermArray[i] == "label"):
                    if(not re.search("^label$", attribArr[i])):
                        CleanUp().exitCode(otherXmlError, "Nesprávný neterminál.")
                elif(nontermArray[i] == "type"):
                    if(not re.search("^type$", attribArr[i])):
                        CleanUp().exitCode(otherXmlError, "Nesprávný neterminál.")
                elif(nontermArray[i] == "var"):
                    if(not re.search("^var$", attribArr[i])):
                        CleanUp().exitCode(otherXmlError, "Nesprávný neterminál.")
                else:
                    CleanUp().exitCode(otherXmlError, "Nesprávný neterminál.")

# Pomocná třída pro matematické operace
class MathOperation():
    global frameController
    operationType = None
    attribArr = []
    elementArr = []
    leftValue = None
    rightValue = None
    leftVarType = None
    rightVarType = None

    # Konstruktor
    # param operationType název instrukce
    # param attribArr pole atributů (type) elementu
    # elementArr pole elementů instrukce
    def __init__(self, operationType, attribArr, elementArr):
        self.operationType = operationType
        self.attribArr = attribArr
        self.elementArr = elementArr

    # Funkce na kontrolu neterminálů
    # Volá funkci na získání typu a hodnoty a kontroluje správnost
    def typeControl(self):
        nTCtrl = NonTermController()

        for i in range(1,3):
            if(self.attribArr[i] == "var"):
                if(i == 1):
                    _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.leftVarType == None):
                        CleanUp().exitCode(missingValue, "Snaha o počítání s neinicializovanými hodnotami.")
                    if(self.leftVarType != "int"):
                        CleanUp().exitCode(wrongTypeError, "Operace "+self.operationType+" podporuje pouze celočíselné hodnoty (typu int).")
                else:
                    _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.rightVarType == None):
                        CleanUp().exitCode(missingValue, "Snaha o počítání s neinicializovanými hodnotami.")
                    if(self.rightVarType != "int"):
                        CleanUp().exitCode(wrongTypeError, "Operace "+self.operationType+" podporuje pouze celočíselné hodnoty (typu int).")
            else:
                if(self.attribArr[i] != "int"):
                    CleanUp().exitCode(wrongTypeError, "Operace "+self.operationType+" podporuje pouze celočíselné hodnoty (typu int).")
                elif(not re.search("^(-)?[0-9]+$", self.elementArr[i].text)):
                    CleanUp().exitCode(otherXmlError, "Operace "+self.operationType+" podporuje pouze celočíselné hodnoty.")
                if(i == 1):
                    self.leftValue = int(self.elementArr[1].text)
                else:
                    self.rightValue = int(self.elementArr[2].text)

    # Funkce na provedení výpočtu
    # return výsledek výpočtu
    def calculate(self):
        result = None
        if(self.operationType == "ADD"):
            result = self.leftValue + self.rightValue
        elif(self.operationType == "SUB"):
            result = self.leftValue - self.rightValue
        elif(self.operationType == "MUL"):
            result = self.leftValue * self.rightValue
        else:
            try:
                result = self.leftValue // self.rightValue
            except ZeroDivisionError:
                CleanUp().exitCode(wrongOperandValueError, "Nastala chyba při dělení nulou.")
        
        return result

# Pomocná třída pro relační operace
class Comparison():
    global frameController
    operationType = None
    attribArr = []
    elementArr = []
    leftValue = None
    rightValue = None
    leftVarType = None
    rightVarType = None

    # Konstruktor
    # param operationType název instrukce
    # param attribArr pole atributů (type) elementu
    # elementArr pole elementů instrukce
    def __init__(self, operationType, attribArr, elementArr):
        self.operationType = operationType
        self.attribArr = attribArr
        self.elementArr = elementArr

    # Funkce na kontrolu neterminálů
    # Volá funkci na získání typu a hodnoty a kontroluje správnost    
    def typeControl(self):
        nTCtrl = NonTermController()

        if(self.operationType == "EQ"):
            for i in range(1,3):
                if(self.attribArr[i] == "var"):
                    if(i == 1):
                        _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.leftVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o porovnání neinicializovaných hodnot.")
                    else:
                        _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.rightVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o porovnání neinicializovaných hodnot.")
                else:
                    if(i == 1):
                        self.leftValue, self.leftVarType = nTCtrl.convertValue(self.elementArr[i].text, self.attribArr[i], True)
                    else:
                        self.rightValue, self.rightVarType = nTCtrl.convertValue(self.elementArr[i].text, self.attribArr[i], True)
            if(self.leftVarType != self.rightVarType and (self.leftVarType != "nil" and self.rightVarType != "nil")):
                CleanUp().exitCode(wrongTypeError, "Nepovolená kombinace operandů u porovnání.")
        else:
            for i in range(1,3):
                if(self.attribArr[i] == "var"):
                    if(i == 1):
                        _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.leftVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o porovnání neinicializovaných hodnot.")
                    else:
                        _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.rightVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o porovnání neinicializovaných hodnot.")
                else:
                    if(i == 1):
                        self.leftValue, self.leftVarType = nTCtrl.convertValue(self.elementArr[i].text, self.attribArr[i], True)
                    else:
                        self.rightValue, self.rightVarType = nTCtrl.convertValue(self.elementArr[i].text, self.attribArr[i], True)
            if(self.leftVarType != self.rightVarType):
                CleanUp().exitCode(wrongTypeError, "Nepovolená kombinace operandů u porovnání.")
        if(self.leftVarType == "string"):
            self.leftValue = nTCtrl.unicodeDecoder(self.leftValue)
        if(self.rightVarType == "string"):
            self.rightValue = nTCtrl.unicodeDecoder(self.rightValue)

    # Funkce na porovnání LT
    # return boolean hodnotu
    def compareLT(self):
        if(self.leftVarType == "bool"):
            if(self.leftValue == True):
                self.leftValue = 1
            else:
                self.leftValue = 0
            if(self.rightValue == True):
                self.rightValue = 1
            else:
                self.rightValue = 0
            return self.leftValue < self.rightValue
        elif(self.leftVarType == "int"):
            return self.leftValue < self.rightValue
        elif(self.leftVarType == "string"):
            return self.leftValue < self.rightValue
        else:
            CleanUp().exitCode(wrongTypeError, "Nepovolená kombinace operandů u porovnání.")

    # Funkce na porovnání GT
    # return boolean hodnotu
    def compareGT(self):
        if(self.leftVarType == "bool"):
            if(self.leftValue == True):
                self.leftValue = 1
            else:
                self.leftValue = 0
            if(self.rightValue == True):
                self.rightValue = 1
            else:
                self.rightValue = 0
            return self.leftValue > self.rightValue
        elif(self.leftVarType == "int"):
            return self.leftValue > self.rightValue
        elif(self.leftVarType == "string"):
            return self.leftValue > self.rightValue
        else:
            CleanUp().exitCode(wrongTypeError, "Nepovolená kombinace operandů u porovnání.")

    # Funkce na porovnání EQ
    # return boolean hodnotu
    def compareEQ(self):
        if(self.rightVarType == "nil"):
            return self.leftValue == self.rightValue
        if(self.leftVarType == "bool"):
            if(self.leftValue == True):
                self.leftValue = 1
            else:
                self.leftValue = 0
            if(self.rightValue == True):
                self.rightValue = 1
            else:
                self.rightValue = 0
            return self.leftValue == self.rightValue
        elif(self.leftVarType == "int"):
            return self.leftValue == self.rightValue
        elif(self.leftVarType == "string"):
            return self.leftValue == self.rightValue
        else:
            return self.leftValue == self.rightValue

    # Funkce, jenž dle daného typu instrukce (operationType) vykoná odpovídající porovnání
    # return boolean hodnotu
    def compare(self):
        success = False
        if(self.leftValue == None):
            self.leftValue = self.elementArr[1].text
        if(self.rightValue == None):
            self.rightValue = self.elementArr[2].text   
        if(self.leftVarType == None):
            self.leftVarType = self.attribArr[1]
        if(self.operationType == "LT"):
            success = self.compareLT()
        elif(self.operationType == "GT"):
            success = self.compareGT()
        else:
            success = self.compareEQ()
        return success

# Pomocná třída pro logické operace
class LogicalOperations():
    global frameController
    attribArr = []
    elementArr = []
    operationType = None
    leftValue = None
    rightValue = None
    leftVarType = None
    rightVarType = None

    # Konstruktor
    # param operationType název instrukce
    # param attribArr pole atributů (type) elementu
    # elementArr pole elementů instrukce
    def __init__(self, operationType, attribArr, elementArr):
        self.attribArr = attribArr
        self.elementArr = elementArr
        self.operationType = operationType
    
    # Konvertuje konstantu bool na boolean hodnotu
    def convertConstant(self, value):
        if(value.lower() == "true"):
            value = True
        else:
            value = False
        return value

    # Funkce na kontrolu neterminálů
    # Volá funkci na získání typu a hodnoty a kontroluje správnost
    def typeControl(self):
        nTCtrl = NonTermController()

        if(self.operationType != "NOT"):
            for i in range(1,3):
                if(self.attribArr[i] == "var"):
                    if(i == 1):
                        _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.leftVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o logické operace s neinicializovanými hodnotami.")
                    else:
                        _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                        if(self.rightVarType == None):
                            CleanUp().exitCode(missingValue, "Snaha o logické operace s neinicializovanými hodnotami.")
                else:
                    if(i == 1):
                        self.leftValue, self.leftVarType = nTCtrl.getSymbIfConstant(self.convertConstant(self.elementArr[i].text), self.attribArr[i])
                    else:
                        self.rightValue, self.rightVarType = nTCtrl.getSymbIfConstant(self.convertConstant(self.elementArr[i].text), self.attribArr[i])
            if(self.leftVarType != "bool" or self.rightVarType != "bool"):
                    CleanUp().exitCode(wrongTypeError, "Špatná hodnota logické operace.")
        else:
            if(self.attribArr[1] == "var"):
                _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[1].text)
                if(self.leftVarType == None):
                    CleanUp().exitCode(missingValue, "Snaha o logické operace s neinicializovanými hodnotami.")
            else:
                self.leftValue, self.leftVarType = nTCtrl.getSymbIfConstant(self.convertConstant(self.elementArr[1].text), self.attribArr[1])
            if(self.leftVarType != "bool"):
                CleanUp().exitCode(wrongTypeError, "Špatná hodnota logické operace.")
    
    # Funkce provede operaci AND
    # return výsledek operace
    def andOperation(self):
        return self.leftValue and self.rightValue
    
    # Funkce provede operaci OR
    # return výsledek operace
    def orOperation(self):
        return self.leftValue or self.rightValue
    
    # Funkce provede operaci NOT
    # return výsledek operace
    def notOperation(self):
        return not self.leftValue

# Pomocní třída pro obshluhu neterminálů
class NonTermController():

    # Funkce na kontrolu syntaxe názvu proměnné
    # param name název proměnné
    def checkSyntaxVarName(self, name):
        if(name == None):
            CleanUp().exitCode(otherXmlError, "Chybějící název zásobníku.")
        if(not re.search("^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$", name)):
            CleanUp().exitCode(otherXmlError, "Nepodporovaný formát názvu zásobníku.")

    # Funkce na kontrolu syntaxe názvu návěští
    # param name název návěští
    def checkSyntaxLabelName(self, name):
        if(not re.search("^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$", name)):
            CleanUp().exitCode(otherXmlError, "Nepodporovaný formát názvu návěští.")

    # Kontrola typu operandu
    # param name název typu operandu
    def checkType(self, name):
        if(not re.search("^(int|string|bool)$", name)):
            CleanUp().exitCode(semanticError, "Špatný typ operandu.")

    # Funkce na rozdělení názvu proměnné a názvu framu
    # param name celý název proměnné
    def splitAndCheckVar(self, name):
        splitted = name.split("@")
        if(len(splitted) != 2):
            CleanUp().exitCode(otherXmlError, "Chyba při rozdělení názvu podle '@'.")
        return splitted

    # Funkce na získání objektu obsahující název, hodnotu a typ proměnné
    # param name název proměnné
    # return objekt obsahující název, hodnotu a typ proměnné
    def getSymbIfVar(self, name):
        global frameController

        self.checkSyntaxVarName(name)
        symbSplitted = self.splitAndCheckVar(name)
        return frameController.getVariable(symbSplitted[0], symbSplitted[1])
    
    # Funkce vrací hodnotu a typ konstanty
    # param value hodnota
    # param varType typ
    # return hodnotu a typ konstanty
    def getSymbIfConstant(self, value, varType):
        return value, varType
    
    # Funkce na konvertování hodnoty na odpovídající typ
    # param value hodnota ke konvertování
    # param varType typ, na který chceme konvertovat hodnotu
    # param errorToNil boolean hodnota, zda-li chceme chybnou konverzi uložit jako nil
    # return konvertovanou hodnotu a typ
    def convertValue(self, value, varType, errorToNil):
        convertedVarType = varType
        convertedValue = value
        if(value != None or (value == None and varType == "string")):
            if(varType == "int"):
                try: 
                    convertedValue = int(value)
                except ValueError:
                    if(errorToNil):
                        convertedVarType = "nil"
                        convertedValue = "nil"
                    else:
                        convertedVarType = None
                        convertedValue = None
            elif(varType == "string"):
                if(value == None):
                    convertedValue = ""
                else:
                    try: 
                        convertedValue = str(value)
                    except ValueError:
                        if(errorToNil):
                            convertedVarType = "nil"
                            convertedValue = "nil"
                        else:
                            convertedVarType = None
                            convertedValue = None
            elif(varType == "bool"):
                convertedVarType = varType
                if(value.lower() == "true"):
                    convertedValue = True
                else:
                    convertedValue = False
        return convertedValue, convertedVarType
    
    # Funkce na konvertování hodnoty na typ int
    # param value hodnota ke konvertování
    # return konvertovanou hodnotu nebo None
    def convertInt(self, value):
        if(value != None):
            try: 
                value = int(value)
            except ValueError:
                value = None
        return value

    # Funkce na konvertování hodnoty na typ int
    # param value hodnota ke konvertování
    # param type typ hodnoty
    # return konvertovanou hodnotu nebo None v případě, že se jedná o int, jinak původní
    def convertIntWithType(self, value, type):
        if(value != None):
            if(type == "int"):
                try: 
                    value = int(value)
                except ValueError:
                    value = None
        return value
    
    # Funkce na konvertování hodnoty na typ bool
    # param value hodnota ke konvertování
    # return boolean hodnotu
    def convertBoolean(self, value):
        if(value.lower() == "true"):
            return True
        else:
            return False

    # Funkce na typovou kontrolu a že jsme v rámci rozsahu řetězce
    # param leftValue hodnota operandu na levé straně operace
    # param leftVarType typ operandu na levé straně operace
    # param rightValue hodnota operandu na pravé straně operace
    # param rightVarType typ operandu na pravé straně operace
    # param název instrukce
    def checkTypesAndLength(self, leftValue, leftVarType, rightValue, rightVarType, instructionName):
        if(leftVarType != "string" or rightVarType != "int"):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce "+instructionName+".")

        if((len(leftValue)-1) < rightValue or rightValue < 0):
            CleanUp().exitCode(stringError, "Indexace mimo rozsah řetězce.")
    
    # Funkce na převod UNICODE na znak
    # return upravenou hodnotu
    def unicodeDecoder(self, toDecode):
        if(toDecode != None):
            pattern = re.compile(r"\\[0-9]{3}")
            escSeq = pattern.findall(toDecode)
            backslash = re.compile(r"\\")
            for decode in escSeq:
                toDecode = toDecode.replace(decode, chr(int(backslash.sub("", decode))))
        return toDecode
    
    # Funkce na převod hodnoty bool a nil na řetězec, případně dekódování UNICODE
    # param value hodnota k úpravě
    # param varType typ hodnoty
    # return upravenou či původní hodnotu
    def modifyOutPut(self, value, varType):
        if(varType == "bool"):
            if(value):
                value = "true"
            else:
                value = "false"
        elif(varType == "nil"):
            value = ""
        elif(varType == "string" and value != None):
            value = self.unicodeDecoder(value)
        elif(varType == "string" and value == None):
            value = ""
        return value

# Pomocná třída sloužící jako objekt pro ukládání do pole
class Variable():
    name = None
    value = None
    varType = None

    # Konstruktor třídy
    # param name název proměnné
    # param value hodnota proměnné
    # param varType typ proměnné
    def __init__(self, name, value, varType):
        self.name = name
        self.value = value
        self.varType = varType        

# Pomocná třída sloužící jako objekt pro ukládání do pole
class Frame():
    classification = None
    variable = [Variable]

    # Konstruktor třídy
    # param classification název rámce
    # param variable objekt obsahující proměnnou
    def __init__(self, classification, variable):
        self.classification = classification
        self.variable = variable

# Pomocní třída pro obshluhu rámců
class FrameController():
    gfFrame = []
    frameStack = []
    tfFrame = []
    tfFrameExists = False

    # Funkce vracející rámec dle daného typu frameType
    # param frameType typ rámce, jenž chceme získat
    # return odpovídající rámec nebo False v případě, že neexistuje
    def getFrame(self, frameType):
        if(frameType == "TF"):
            if(self.tfFrameExists):
                return self.tfFrame
            else:
                return False
        elif(frameType == "GF"):
            return self.gfFrame
        elif(frameType == "LF"):
            if(len(self.frameStack) > 0):
                return self.frameStack[len(self.frameStack) - 1]
            else:
                return False   

    # Funkce sloužící k vytvoření dočasného rámce
    def createTFFrame(self):
        self.tfFrame = []
        self.tfFrameExists = True
    
    # Funkce sloužící k přesunutí dočasného rámce na lokální rámec (dočasný rámec se stane neinializovaným)
    def pushTFFrameToFrameStack(self):
        if(self.tfFrameExists):
            self.frameStack.append(self.tfFrame)
            self.tfFrameExists = False
        else:
            CleanUp().exitCode(frameDoesntExist, "Dočasný rámec neexistuje.")

    # Funkce sloužící k uložení lokálního rámce na dočasný rámec
    def popToTFFrame(self):
        if(len(self.frameStack) > 0):
            self.tfFrame = self.frameStack.pop()
            self.tfFrameExists = True
        else:
            CleanUp().exitCode(frameDoesntExist, "Chybný přenus rámce, zásobník rámců je prázdný.")
    
    # Funkce sloužící k deklarování proměnné na uvedeném rámci
    # param frameType rámec, na kterém chceme deklarovat proměnnou
    # param varName název proměnné 
    def declarVariable(self, frameType, varName):
        frame = self.getFrame(frameType)
        if(frameType == "TF" and self.tfFrameExists == False):
            CleanUp().exitCode(frameDoesntExist, "Snaha o přístup k nedefinovanému zásobníku.")
        elif(frame == False):
            CleanUp().exitCode(frameDoesntExist, "Snaha o přístup k nedefinovanému zásobníku.")
        elif(any(var.name == varName for var in frame)):
            CleanUp().exitCode(semanticError, "Snaha o redefinici proměnné "+varName+" v zásobníku "+frameType+".")
        
        variable = Variable(varName, None, None)
        frame.append(variable)
        
    # Funkce sloužící k uložení hodnoty do uvedného rámce
    # param frameType typ rámce
    # param name název proměnné
    # param value hodnota proměnné
    # param varType typ proměnné
    def insertValue(self, frameType, varName, value, varType):
        frame = self.getFrame(frameType)
        if(frame == False):
            CleanUp().exitCode(frameDoesntExist, "Snaha o přístup k nedefinovanému zásobníku.")
        
        index = -1
        for index, item in enumerate(frame):
            if item.name == varName:
                break
            else:
                index = -1
        
        if(index == -1):
            CleanUp().exitCode(varDoesntExist, "Proměnná "+varName+" v zásobníku "+frameType+" neexistuje.")
        
        newVariable = Variable(varName, value, varType)
        frame[index] = newVariable

    # Funkce sloužící pro získání hodnot dané proměnné z daného rámce
    # param frameType typ rámce, z kterého má získat proměnnou
    # param varName název proměnné
    # return název proměnné, hodnotu a typ
    def getVariable(self, frameType, varName):
        frame = self.getFrame(frameType)
        if(frame == False):
            CleanUp().exitCode(frameDoesntExist, "Snaha o přístup k nedefinovanému zásobníku.")
        
        index = -1
        for index, item in enumerate(frame):
            if item.name == varName:
                break
            else:
                index = -1
        
        if(index == -1):
            CleanUp().exitCode(varDoesntExist, "Proměnná "+varName+" v zásobníku "+frameType+" neexistuje.")
        
        return frame[index].name, frame[index].value, frame[index].varType

# Pomocná třída sloužící jako objekt pro ukládání do pole
class LabelObject():
    name = None
    position = None

    # Konstruktor třídy
    # param name název návětší
    # param position pozice instrukce v programu
    def __init__(self, name, position):
        self.name = name
        self.position = position

# Pomocní třída pro obshluhu zásobníku instrukcí
class InstructionStackController():
    instructionStack = []
    labelStack = []
    xml = XmlController()

    # Funkce pro uložení pozice instrukce do zásobníku pozic instrukcí
    # param position pozice instrukce
    def insertInstractionToStack(self, position):
        self.instructionStack.append(position)

    # Funkce pro uložení názvu návěští do zásobníku návěští
    # param element element instrukce (LABEL)
    # param position pozice instrukce (LABEL)
    def insertIntoLabelStack(self, element, position):
        elementArr = self.xml.getSortedArrOfElement(element)
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxLabelName(elementArr[0].text)
        if(any(labelName.name == elementArr[0].text for labelName in self.labelStack)):
            CleanUp().exitCode(semanticError, "Duplicitní název návěští.")
        else:
            label = LabelObject(elementArr[0].text, position)
            self.labelStack.append(label)

    # Funkce vracející pozici instrukce návěští v programu
    # param name název návěští
    # return pozici nebo None v případě, že návěští z daným jménem neexistuje
    def getLabelPosition(self, name):
        for label in self.labelStack:
            if(label.name == name):
                return label.position
        return None
    
    # Funkce, jenž získá ze zásobníku pozic instrukcí posledně přidanou pozici
    def popInstruction(self):
        if(len(self.instructionStack) < 1):
            CleanUp().exitCode(56, "Snaha o návrat na nedefinovanou pozici.")
        return int(self.instructionStack.pop())

# Pomocní třída pro obshluhu datového zásobníku
class DataStackController():
    dataStack = []

    # Funkce pro přidání hodnoty a typu na zásobník
    # param value hodnota
    # param varType typ
    def insertIntoDataStack(self, value, varType):
        varS = Variable(None, value, varType)
        self.dataStack.append(varS)

    # Funkce na navrácení a odebrání posledně přidané proměnné z datováho zásobníku
    def popFromDataStack(self):
        if(len(self.dataStack) < 1):
            CleanUp().exitCode(missingValue, "Snaha o výpis z prázdného datového zásobníku.")
        return self.dataStack.pop()

class Move():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb"]
    numberOfNonterm = 2
    value = None
    varType = None

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)
        
        # Získání hodnoty a typu z symb
        if(self.attribArr[1] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[1].text)
            if(self.varType == None):
                CleanUp().exitCode(missingValue, "Snaha o přesun neinicializované hodnoty.")
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[1].text, self.attribArr[1])
            self.value, self.varType = nTCtrl.convertValue(self.value, self.varType, False)

        # Přidání hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], self.value, self.varType)

class CreateFrame():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = []
    numberOfNonterm = 0

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Vytvoření dočasného rámce
        frameController.createTFFrame()

class PushFrame():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = []
    numberOfNonterm = 0

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Přesunutí dočasného rámce do lokálního rámce
        frameController.pushTFFrameToFrameStack()

class PopFrame():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = []
    numberOfNonterm = 0

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Přesunutí posledního lokálního rámce na dočasný rámec
        frameController.popToTFFrame()

class Defvar():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var"]
    numberOfNonterm = 1

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Definice proměnné v určitém rámci
        frameController.declarVariable(varSplitted[0], varSplitted[1])

class Call():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["label"]
    numberOfNonterm = 1

    def __init__(self, element):
        global actualInstractionIndex
        global instructionConstroller

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola názvu label
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxLabelName(self.elementArr[0].text)
        
        # Jelikož po návratu z funkce RETURN dojde k iteraci, 
        # tak není třeba ukládat iterovanou hodnotu (potom bychom ji museli opět dekrementovat), tudiž uložíme aktuální
        instructionConstroller.insertInstractionToStack(actualInstractionIndex)
        # Získání pozice návětší v kódu, kontrola a skok na něj
        position = instructionConstroller.getLabelPosition(self.elementArr[0].text)
        if(position == None):
            CleanUp().exitCode(semanticError, "Nepodařilo se nalézt návěští instrukce CALL.")
        actualInstractionIndex = int(position)
        
class Return():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = []
    numberOfNonterm = 0

    def __init__(self, element):
        global actualInstractionIndex
        global instructionConstroller

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Získání a nastavení aktuální pozice ze zásobníku pozic
        actualInstractionIndex = instructionConstroller.popInstruction()

class Pushs():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["symb"]
    numberOfNonterm = 1
    value = None
    varType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Získání hodnoty a typu z symb
        nTCtrl = NonTermController()
        if(self.attribArr[0] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[0].text)
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[0].text, self.attribArr[0])
            nTCtrl.convertValue(self.value, self.varType, False)
        
        # Kontrola, že se jedná o inicializovanou hodnotu
        if(self.varType == None):
            CleanUp().exitCode(missingValue, "Snaha o uložení neinicializované hodnoty.")
        
        # Uložení hodnoty do datového zásobníku
        dataStackCtrl = DataStackController()
        dataStackCtrl.insertIntoDataStack(self.value, self.varType)

class Pops():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var"]
    numberOfNonterm = 1

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)
        
        # Získání objektu nesoucí hodnoty proměnné z datového zásobníku
        dataStackCtrl = DataStackController()
        dataObject = dataStackCtrl.popFromDataStack()

        # Uložení proměnné na zásobník
        frameController.insertValue(varSplitted[0], varSplitted[1], dataObject.value, dataObject.varType)

class Add():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení matematické operace a uložení hodnoty do proměnné
        math = MathOperation("ADD", self.attribArr, self.elementArr)
        math.typeControl()
        value = math.calculate()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "int")
           
class Sub():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení matematické operace a uložení hodnoty do proměnné
        math = MathOperation("SUB", self.attribArr, self.elementArr)
        math.typeControl()
        value = math.calculate()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "int")
        
class Mul():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení matematické operace a uložení hodnoty do proměnné
        math = MathOperation("MUL", self.attribArr, self.elementArr)
        math.typeControl()
        value = math.calculate()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "int")

class Idiv():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global frameController

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení matematické operace a uložení hodnoty do proměnné
        math = MathOperation("IDIV", self.attribArr, self.elementArr)
        math.typeControl()
        value = math.calculate()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "int")

class Lt():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení relační operace a uložení hodnoty do proměnné
        comp = Comparison("LT", self.attribArr, self.elementArr)
        comp.typeControl()
        value = comp.compare()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")

class Gt():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení relační operace a uložení hodnoty do proměnné
        comp = Comparison("GT", self.attribArr, self.elementArr)
        comp.typeControl()
        value = comp.compare()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")

class Eq():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení relační operace a uložení hodnoty do proměnné
        comp = Comparison("EQ", self.attribArr, self.elementArr)
        comp.typeControl()
        value = comp.compare()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")

class And():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení logické operace a uložení hodnoty do proměnné
        loper = LogicalOperations("AND", self.attribArr, self.elementArr)
        loper.typeControl()
        value = loper.andOperation()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")
        
class Or():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení logické operace a uložení hodnoty do proměnné
        loper = LogicalOperations("OR", self.attribArr, self.elementArr)
        loper.typeControl()
        value = loper.orOperation()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")

class Not():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb"]
    numberOfNonterm = 2

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Provedení logické operace a uložení hodnoty do proměnné
        loper = LogicalOperations("NOT", self.attribArr, self.elementArr)
        loper.typeControl()
        value = loper.notOperation()
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "bool")

class Int2Char():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb"]
    numberOfNonterm = 2
    value = None
    varType = None

    def __init__(self, element):
        global frameStack

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        if(self.attribArr[1] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[1].text)
            if(self.value == None):
                CleanUp().exitCode(missingValue, "Číselná hodnota instrukce int2char není inicializován.")
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(nTCtrl.convertInt(self.elementArr[1].text), self.attribArr[1])

        # Kontrola, že je hodnota inicializovaná a je typu int
        if(self.varType != "int" or self.value == None):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce INT2CHAR.")

        # Převedení typu na integer a dekédování UNICODE hodnoty na char
        try:
            self.value = int(self.value)
            self.value = chr(self.value)
        except ValueError:
            CleanUp().exitCode(stringError, "Chybná hodnotu v Unicode.")

        # Uložení hodnoty do proměnné
        frameController.insertValue(varSplitted[0], varSplitted[1], self.value, "string")

class Stri2Int():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3
    leftValue = None
    leftVarType = None
    rightValue = None
    rightVarType = None

    def __init__(self, element):
        global frameStack

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        for i in range(1,3):
            if(self.attribArr[i] == "var"):
                if(i == 1):
                    _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.leftValue == None):
                        CleanUp().exitCode(missingValue, "Řetězec instrukce stri2int není inicializován.")
                else:
                    _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.rightValue == None):
                        CleanUp().exitCode(missingValue, "Index instrukce stri2int není inicializován.")
            else:
                if(i == 1):
                    self.leftValue, self.leftVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "string"), self.attribArr[i])
                else:
                    self.rightValue, self.rightVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "int"), self.attribArr[i])
        
        # Kontrola, že jsou hodnoty inicializovány   
        if(self.leftValue == None or self.rightValue == None):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce STRI2INT.")

        # Kontrola typu a že je v rámci rozsahu řetězce
        nTCtrl.checkTypesAndLength(self.leftValue, self.leftVarType, self.rightValue, self.rightVarType, "STRI2INT")
        value = ord(self.leftValue[self.rightValue])

        # Uložení hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "int")

class Read():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "type"]
    numberOfNonterm = 2
    varType = None
    value = None

    def __init__(self, element):
        global frameController
        global inputValue

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkType(self.elementArr[1].text)
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Kontrola, že pole vstupního dat ze vstupního souboru stále obsahuje data, pokud ne, zapíše nil
        # Pokud ano, dojde ke konvertování hodnoty dle uvedeného typu
        if(len(inputValue) > 0):
            self.value, self.varType = nTCtrl.convertValue(inputValue[0], self.elementArr[1].text, True)
            _ = inputValue.pop(0)
        else:
            self.varType = "nil"
            self.value = "nil"
    
        # Uložení hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], self.value, self.varType)
            
class Write():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["symb"]
    numberOfNonterm = 1
    varType = None
    value = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)
        
        # Získání hodnoty a typu z symb
        nTCtrl = NonTermController()
        if(self.attribArr[0] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[0].text)
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[0].text, self.attribArr[0])
            if(self.varType == "bool"):
                self.value = nTCtrl.convertBoolean(self.value)
        
        # Zkontroluje, že se jedná o inicializovanou hodnotu
        if(self.varType == None):
            CleanUp().exitCode(missingValue, "Snaha o výpis neinicializované hodnoty.")

        # Zkonvertuje bool a nil na string a vypíše hodnotu na stdout
        self.value = nTCtrl.modifyOutPut(self.value, self.varType)
        print(self.value, end='', flush=True)

class Concat():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3
    leftValue = None
    leftVarType = None
    rightValue = None
    rightVarType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        for i in range(1,3):
            if(self.attribArr[i] == "var"):
                if(i == 1):
                    _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.leftVarType == None):
                        CleanUp().exitCode(missingValue, "Snaha o konkatenaci neinicializované hodnoty.")
                else:
                    _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.rightVarType == None):
                        CleanUp().exitCode(missingValue, "Snaha o konkatenaci neinicializované hodnoty.")
            else:
                if(i == 1):
                    self.leftValue, self.leftVarType = nTCtrl.getSymbIfConstant(self.elementArr[i].text, self.attribArr[i])
                else:
                    self.rightValue, self.rightVarType = nTCtrl.getSymbIfConstant(self.elementArr[i].text, self.attribArr[i])
        if(self.leftVarType != "string" or self.rightVarType != "string"):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce CONCAT.")
        
        # Pokud jsme načetli prázdnou konstanu, je uložena jako hodnota prázdného řetězce
        if(self.leftValue == None):
            self.leftValue = ""
        if(self.rightValue == None):
            self.rightValue = ""

        # Spojení řetězců
        value = self.leftValue + self.rightValue

        # Uložení hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "string")    

class Strlen():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb"]
    numberOfNonterm = 2
    value = None
    varType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        if(self.attribArr[1] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[1].text)
            if(self.value == None):
                CleanUp().exitCode(missingValue, "Řetězec instrukce strlen není inicializován.")
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[1].text, self.attribArr[1])
        if(self.varType != "string"):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce STRLEN.")

        # Pokud je hodnota prázdná, nastavíme délku na 0, jinak získáme její délku
        if(self.value == None):
            self.value = 0
        else:
            self.value = len(self.value)

        # Uložíme hodnotu do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], self.value, "int")

class Getchar():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3
    leftValue = None
    leftVarType = None
    rightValue = None
    rightVarType = None

    def __init__(self, element):
        global frameStack

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        for i in range(1,3):
            if(self.attribArr[i] == "var"):
                if(i == 1):
                    _, self.leftValue, self.leftVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.leftValue == None):
                        CleanUp().exitCode(missingValue, "Řetězec instrukce getchar není inicializován.")
                else:
                    _, self.rightValue, self.rightVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.rightValue == None):
                        CleanUp().exitCode(missingValue, "Index instrukce getchar není inicializován.")
            else:
                if(i == 1):
                    self.leftValue, self.leftVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "string"), self.attribArr[i])
                    if(self.leftValue == None):
                        CleanUp().exitCode(wrongTypeError, "Špatná hodnota řetězce instrukce getchar.")
                else:
                    self.rightValue, self.rightVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "int"), self.attribArr[i])
                    if(self.rightValue == None):
                        CleanUp().exitCode(wrongTypeError, "Špatná hodnota indexu instrukce getchar.")

        # Kontrola typu a že je v rámci rozsahu řetězce
        nTCtrl.checkTypesAndLength(self.leftValue, self.leftVarType, self.rightValue, self.rightVarType, "GETCHAR")
        value = self.leftValue[self.rightValue]

        # Uložení hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], value, "string")

class Setchar():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb", "symb"]
    numberOfNonterm = 3
    toChangeValue = None
    toChangeVarType = None
    posValue = None
    posVarType = None
    changeWithValue = None
    changeWithVarType = None

    def __init__(self, element):
        global frameStack
        
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        # Načtení hodnot ze získané proměnné z rámce
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)
        _, self.toChangeValue, self.toChangeVarType = frameController.getVariable(varSplitted[0], varSplitted[1])

        # Kontrola, že se jedná o inicializovanou proměnnou
        if(self.toChangeVarType == None):
            CleanUp().exitCode(missingValue, "Snaha o změnu v neinicializované hodnotě.")

        # Získání hodnoty a typu z symb
        for i in range(1,3):
            if(self.attribArr[i] == "var"):
                if(i == 1):
                    _, self.posValue, self.posVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.posValue == None):
                        CleanUp().exitCode(missingValue, "Index pozice setchar není neinicializován.")
                else:
                    _, self.changeWithValue, self.changeWithVarType = nTCtrl.getSymbIfVar(self.elementArr[i].text)
                    if(self.changeWithVarType == None):
                        CleanUp().exitCode(missingValue, "Snaha o změnu neinicializovanou hodnotou.")
            else:
                if(i == 1):
                    self.posValue, self.posVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "int"), self.attribArr[i])
                else:
                    self.changeWithValue, self.changeWithVarType = nTCtrl.getSymbIfConstant(nTCtrl.convertIntWithType(self.elementArr[i].text, "string"), self.attribArr[i])

        # Kontrola typů a inicializace hodnoty nesoucí index
        if(self.toChangeVarType != "string" or self.posVarType != "int" or self.changeWithVarType != "string" or self.posValue == None):
            CleanUp().exitCode(wrongTypeError, "Špatná hodnota instrukce SETCHAR.")

        # Kontrola, zda-li přistupujeme na index v rámci rozsahu řetězce
        if((len(self.toChangeValue)-1) < self.posValue or self.posValue < 0):
            CleanUp().exitCode(stringError, "Indexace mimo rozsah řetězce.")

        # Dekódování UNICODE hodnoty
        self.toChangeValue = self.modifyToChangeValue(nTCtrl)

        # Přidání hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], self.toChangeValue, "string")

    # Funkce kontroluje, že není řetězec prázdný a dekóduje UNICODE
    def modifyToChangeValue(self, nTCtrl):
        textToList = list(self.toChangeValue)
        if(self.changeWithValue == None):
            CleanUp().exitCode(stringError, "Řetězec nesoucí přepisující hodnotu je prázdný.")
        else:
            self.changeWithValue = nTCtrl.unicodeDecoder(self.changeWithValue)
            textToList[self.posValue] = self.changeWithValue[0]
        return "".join(textToList)

class Type():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["var", "symb"]
    numberOfNonterm = 2
    value = None
    varType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola a rozdělení proměnné na rámec a název
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxVarName(self.elementArr[0].text)
        varSplitted = nTCtrl.splitAndCheckVar(self.elementArr[0].text)

        # Získání hodnoty a typu z symb
        if(self.attribArr[1] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[1].text)
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[1].text, self.attribArr[1])
        
        # Převede neinicializovaný typ na prázdný řetězec
        if(self.varType == None):
            self.value = ""
        else:
            self.value = self.varType   

        # Přidání hodnoty do proměnné v rámci
        frameController.insertValue(varSplitted[0], varSplitted[1], self.value, "string")

class Label():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["label"]
    numberOfNonterm = 1

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

class Jump():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["label"]
    numberOfNonterm = 1

    def __init__(self, element):
        global actualInstractionIndex
        global instructionConstroller

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Kontrola názvu label
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxLabelName(self.elementArr[0].text)
        
        # Získání pozice návětší v kódu, kontrola a skok na něj
        position = instructionConstroller.getLabelPosition(self.elementArr[0].text)
        if(position == None):
            CleanUp().exitCode(semanticError, "Nepodařilo se nalézt návěští instrukce JUMP.")
        actualInstractionIndex = int(position)

class JumpIfEq():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["label", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global actualInstractionIndex
        global instructionConstroller

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Provedení relační operace
        comp = Comparison("EQ", self.attribArr, self.elementArr)
        comp.typeControl()
        value = comp.compare()

        # Kontrola názvu label
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxLabelName(self.elementArr[0].text)
        
        # Získání a kontrola pozice návětší v kódu
        position = instructionConstroller.getLabelPosition(self.elementArr[0].text)
        if(position == None):
            CleanUp().exitCode(semanticError, "Nepodařilo se nalézt návěští instrukce JUMPIFEQ.")

        # Skok na dané návěští
        if(value):
            actualInstractionIndex = int(position)

class JumpIfNEq():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["label", "symb", "symb"]
    numberOfNonterm = 3

    def __init__(self, element):
        global actualInstractionIndex
        global instructionConstroller

        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Provedení relační operace
        comp = Comparison("EQ", self.attribArr, self.elementArr)
        comp.typeControl()
        value = comp.compare()

        # Kontrola názvu label
        nTCtrl = NonTermController()
        nTCtrl.checkSyntaxLabelName(self.elementArr[0].text)
        
        # Získání a kontrola pozice návětší v kódu
        position = instructionConstroller.getLabelPosition(self.elementArr[0].text)
        if(position == None):
            CleanUp().exitCode(semanticError, "Nepodařilo se nalézt návěští instrukce JUMPIFNEQ.")

        # Skok na dané návěští
        if(not value):
            actualInstractionIndex = int(position)

class Exit():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["symb"]
    numberOfNonterm = 1
    value = None
    varType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        # Získání hodnoty a typu z symb
        nTCtrl = NonTermController()
        if(self.attribArr[0] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[0].text)
            if(self.varType == None):
                CleanUp().exitCode(missingValue, "Snaha o ukončení s neinicializovanou hodnotou.")
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[0].text, self.attribArr[0])
        
        # Konvertování hodnoty na int (v případě chyby vrací None)
        self.value = nTCtrl.convertInt(self.value)

        # Kontrola konverze a datového typu
        if(self.value == None or self.varType != "int"):
            CleanUp().exitCode(wrongTypeError, "Chybná hodnota instrukce EXIT.")

        # Kontrola rozsahu návratového kódu
        if(self.value < 0 or self.value > 49):
            CleanUp().exitCode(wrongOperandValueError, "Chybná celočíselná hodnota instrukce EXIT.")
        
        # Ukončení programu s návratovým kódem
        CleanUp().exitWithoutMsg(self.value)

class Dprint():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = ["symb"]
    numberOfNonterm = 1
    value = None
    varType = None

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

        nTCtrl = NonTermController()

        # Získání hodnoty a typu z symb
        if(self.attribArr[0] == "var"):
            _, self.value, self.varType = nTCtrl.getSymbIfVar(self.elementArr[0].text)
            if(self.varType == None):
                CleanUp().exitCode(missingValue, "Snaha o ukončení s neinicializovanou hodnotou.")
        else:
            self.value, self.varType = nTCtrl.getSymbIfConstant(self.elementArr[0].text, self.attribArr[0])
            if(self.varType == "bool"):
                self.value = nTCtrl.convertBoolean(self.value)
        
        # Zkonvertuje bool a nil na string a vypíše hodnotu na stderr
        self.value = nTCtrl.modifyOutPut(self.value, self.varType)
        print(self.value, file=sys.stderr)

class Break():
    elementArr = []
    tagArr = []
    attribArr = []
    nonterminalsArr = []
    numberOfNonterm = 0

    def __init__(self, element):
        # Načtení a kontrola elementů instrukce 
        xml = XmlController()
        self.elementArr = xml.getSortedArrOfElement(element)
        self.tagArr, self.attribArr = xml.getTagAndAttribute(self.elementArr)
        xml.checkAttribute(self.numberOfNonterm, self.nonterminalsArr, self.tagArr, self.attribArr)

# Třída sloužící jako switch pro výběr třídy odpovídající prováděné instrukce
class Switcher(object):
    def callOpcode(self, argument, element):
        methodName = str(argument)
        methodName = methodName.upper()
        method = getattr(self, methodName, lambda x: CleanUp().exitCode(otherXmlError, "Neplatný opcode."))
        return method(element)
 
    def MOVE(self, element):
        Move(element)
 
    def CREATEFRAME(self, element):
        CreateFrame(element)
 
    def PUSHFRAME(self, element):
        PushFrame(element)

    def POPFRAME(self, element):
        PopFrame(element)

    def DEFVAR(self, element):
        Defvar(element)

    def CALL(self, element):
        Call(element)

    def RETURN(self, element):
        Return(element)

    def PUSHS(self, element):
        Pushs(element)

    def POPS(self, element):
        Pops(element)

    def ADD(self, element):
        Add(element)

    def SUB(self, element):
        Sub(element)
    
    def MUL(self, element):
        Mul(element)

    def IDIV(self, element):
        Idiv(element)

    def LT(self, element):
        Lt(element)
    
    def GT(self, element):
        Gt(element)

    def EQ(self, element):
        Eq(element)

    def AND(self, element):
        And(element)

    def OR(self, element):
        Or(element)

    def NOT(self, element):
        Not(element)

    def INT2CHAR(self, element):
        Int2Char(element)

    def STRI2INT(self, element):
        Stri2Int(element)

    def READ(self, element):
        Read(element)

    def WRITE(self, element):
        Write(element)

    def CONCAT(self, element):
        Concat(element)

    def STRLEN(self, element):
        Strlen(element)

    def GETCHAR(self, element):
        Getchar(element)

    def SETCHAR(self, element):
        Setchar(element)

    def TYPE(self, element):
        Type(element)

    def LABEL(self, element):
        Label(element)

    def JUMP(self, element):
        Jump(element)

    def JUMPIFEQ(self, element):
        JumpIfEq(element)

    def JUMPIFNEQ(self, element):
        JumpIfNEq(element)

    def EXIT(self, element):
        Exit(element)

    def DPRINT(self, element):
        Dprint(element)

    def BREAK(self, element):
        Break(element)

if __name__ == "__main__":
    Main().run()