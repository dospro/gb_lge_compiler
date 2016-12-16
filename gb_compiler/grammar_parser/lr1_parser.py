#!/usr/bin/env python

# Grammar Parser v 1
# Este programa lee una gramática BNF
# y genera un arbol de sintaxis.
# El arbol es guardado en un formato
# que puede ser leido mas facilmente.

import optparse
import re

# The key is the token text and the value Boolean
# True - is terminal
# False - is no terminal
tokensSet = {}
firstsList = {}


class Token(object):
    def __init__(self):
        self.isTerminal = False
        self.text = ""

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class LRItem(object):
    def __init__(self):
        self.leftHand = None
        self.rightHand = None
        self.dot = 0
        self.lookAhead = ''

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        if self.leftHand is None:
            return "Empty LR(1) item"
        text = self.leftHand
        text += " -> "
        for tokens in self.rightHand[:self.dot]:
            text += ' ' + tokens.text
        text += ' .'
        for tokens in self.rightHand[self.dot:]:
            text += ' ' + tokens.text

        text += ' ||' + self.lookAhead
        return text


automata = re.compile(r'<(?P<left>\w+)>\s*::=\s*(?P<right>.+)\s*')
right_matcher = re.compile(r'<(?P<non_terminal>[^>\n]+)>|"(?P<terminal>[^"\n]+)"')


def transform_to_dict(string):
    """Takes a string representing a line of the BNF file
    and returns a dict with the left hand as the key and
    a list of right hands as value"""
    rules = automata.finditer(string)
    grammar_dict = {}
    for rule in rules:
        right_side = rule.group("right")
        left_side = rule.group("left")
        right_hand = right_matcher.finditer(right_side)

        tokens = []
        for token in right_hand:
            terminal = token.group("terminal")
            non_terminal = token.group("non_terminal")
            if terminal:
                tokens.append({"terminal": terminal})
            elif non_terminal:
                tokens.append({"non_terminal": non_terminal})

        if left_side in grammar_dict:
            grammar_dict[left_side].append(tokens)
        else:
            grammar_dict[left_side] = [tokens]

    return grammar_dict


def read_bnf_file(bnf_filename):
    """Opens a BNF file and creates a python dict representing the grammar.
    The dict keys are the right hands and the values are lists containing
    dicts with keys "terminal" or "no_terminal".
    """

    grammar_table = {}
    line_number = 0

    with open(bnf_filename) as bnf_file:
        for line in bnf_file:
            result = transform_to_dict(line)
            for key in result:
                if key in grammar_table:
                    for i in result[key]:
                        grammar_table[key].append(i)
                else:
                    grammar_table[key] = result[key]
            line_number += 1

    print(grammar_table)


def firstSet(grammar, noTerminal):
    fList = []
    toDoList = [noTerminal]
    doneList = []
    if noTerminal.isTerminal:
        print("Error: No hay primeros para terminales")
        return None

    while len(toDoList) > 0:
        nt = toDoList.pop(0)
        if nt.text in firstsList:
            fList.extend(firstsList[nt.text])
            continue
        for rule in grammar[nt.text]:
            nextToken = rule[0]
            if nextToken.isTerminal:
                if nextToken not in fList:
                    fList.append(nextToken)
            else:
                if nextToken not in toDoList and nextToken not in doneList:
                    toDoList.append(nextToken)
        doneList.append(nt)

    if noTerminal.text not in firstsList:
        firstsList[noTerminal.text] = fList
    # print("FIRST(%s) = [" % noTerminal.text, end="")
    # for i in fList:
    #    print(" %s " % i.text, end="")
    # print("]")
    return fList


def getLookAheads(grammar, lrItem):
    oldLookAhead = lrItem.lookAhead
    newLookAheads = set()

    # If the dot is at the far right, return current lookAhead
    if lrItem.dot + 1 >= len(lrItem.rightHand):
        return [oldLookAhead]

    # If token next to the symbol to the right of the dot is a terminal
    # add it to the list.
    elif lrItem.rightHand[lrItem.dot + 1].isTerminal:
        la = lrItem.rightHand[lrItem.dot + 1].text
        return [la]

    terminals = firstSet(grammar, lrItem.rightHand[lrItem.dot + 1])
    if not terminals:
        print("Error: No se pudo encontrar primeros de %s." %
              lrItem.rightHand[lrItem.dot + 1].text)
        return None

    for i in terminals:
        newLookAheads.add(i.text)

    return list(newLookAheads)


def closure(grammar, lrItems):
    itemsList = []
    toDoItems = lrItems
    toDoNoTerminals = []
    doneNoTerminals = []

    # while there are pendent lritems
    while len(toDoItems) > 0:
        # Analize the first item of the list and pop it out
        currentItem = toDoItems.pop(0)
        itemsList.append(currentItem)

        if currentItem.dot >= len(currentItem.rightHand):
            continue
        # Get token next to the dot
        noTerminal = currentItem.rightHand[currentItem.dot]

        # If there is a terminal or nothing, nothing to be done.
        if tokensSet[noTerminal.text]:
            continue

        # We have a no terminal. We must get the rules of that no terminal.
        # print("Searching rules for noterminal %s" % noTerminal.text)
        # Search for the rules with noterminal as lefthand

        if noTerminal.text not in grammar:
            print("Can't find production")
            continue
        for rule in grammar[noTerminal.text]:
            lookAheads = getLookAheads(grammar, currentItem)
            for la in lookAheads:
                newItem = LRItem()
                newItem.leftHand = noTerminal.text
                newItem.rightHand = rule
                newItem.dot = 0
                newItem.lookAhead = la
                if newItem not in toDoItems and newItem not in itemsList:
                    toDoItems.append(newItem)
    return itemsList


def goto(grammar, itemsList, grammarSymbol):
    newState = []
    for item in itemsList:
        if item.dot < len(item.rightHand):
            if grammarSymbol == item.rightHand[item.dot].text:
                newItem = LRItem()
                newItem.leftHand = item.leftHand
                newItem.rightHand = item.rightHand
                newItem.dot = item.dot + 1
                newItem.lookAhead = item.lookAhead
                if newItem not in newState:
                    newState.append(newItem)
    return closure(grammar, newState)


def buildActionTable(grammar, collection, gotoTable):
    actionTable = {}
    currentState = 0
    print("\nBuilding action table...", end="")
    for state in collection:
        for item in state:
            if item.dot >= len(item.rightHand):
                # If the dot is at the far right, we have a reduce
                keyTuple = (currentState, item.lookAhead)
                if keyTuple in actionTable:
                    print("Reduce-shift conflict: ", item)
                if item.leftHand == "Goal" and item.lookAhead == "$":
                    actionTable[keyTuple] = ('a', 0)
                else:
                    grammarRule = (item.leftHand, item.rightHand)
                    actionTable[keyTuple] = ('r', grammarRule)
            else:
                # If the dot is somewhere else, we have a shift
                symbol = item.rightHand[item.dot]
                if not symbol.isTerminal:
                    # If the token to the right is a no terminal
                    # there is nothing to shift.
                    continue
                keyTuple = (currentState, symbol.text)
                if keyTuple in gotoTable:
                    nextStateNumber = gotoTable[keyTuple]
                    if keyTuple in actionTable:
                        action = actionTable[keyTuple]
                        if action != ('s', nextStateNumber):
                            print("Shift reduce conflict: ",
                                  symbol.text, item, action[1])
                    actionTable[keyTuple] = ('s', nextStateNumber)
        currentState += 1

    print("Done")
    return actionTable


def build_tables(input_filename, output_filename):
    """Opens the grammar file and builds actions table and goto table.
    Then it saves the grammar, the tokens list and the tables in
    the output file."""

    goto_table = {}
    e_table = {}

    # Read the grammar bnf file to create a list of productions
    print("Reading bnf file...", end="")
    grammar_table = read_bnf_file(input_filename)
    print("Done")

    # The first LR(1) item must be the goal production
    # this the dot at the far left and EOF as look ahead
    # EOF is represented by '$'
    lritem = LRItem()
    lritem.leftHand = "Goal"
    lritem.rightHand = grammar_table["Goal"][0]
    lritem.dot = 0
    lritem.lookAhead = '$'

    # The cannonical collection(CC) is a list of lists of LR items
    can_collection = []

    # The first set comes from the clousure of the first LR item
    print("Building state 0...", end="")
    can_collection.append(closure(grammar_table, [lritem]))
    print("Done")

    # counter will hold the state number in CC
    counter = 0
    newState = 0
    print("Building cannonical collection...", end="")
    for state in can_collection:
        for symbol in tokensSet:
            # Get a new state from current state and symbol
            cc = goto(grammar_table, state, symbol)
            # If the new state is not empty
            if cc:
                # If the new state is not already in the CC add it
                if cc not in can_collection:
                    can_collection.append(cc)
                    newState += 1
                    # Record this transition to create the action_table
                    e_table[(counter, symbol)] = newState
                else:
                    index = can_collection.index(cc)
                    e_table[(counter, symbol)] = index
                # If the symbol is a terminal, record the goto transition
                if not tokensSet[symbol]:
                    goto_table[(counter, symbol)] = e_table[(counter, symbol)]
        counter += 1
    print("Done")

    action_table = buildActionTable(grammar_table, can_collection, e_table)

    counter = 0
    '''for i in can_collection:
        print("\nState ", counter)
        for j in i:
            print("State ", counter, ": ", j)
        counter += 1


    print("\nAction Table")
    for i in action_table:
        print(i, action_table[i][0], action_table[i][1])
    print("Goto Table")
    for i in goto_table:
        print(i, goto_table[i])'''

    saveGPF(grammar_table, action_table, goto_table, output_filename)


def saveGPF(grammar, actionTable, gotoTable, outFilename):
    grammarTable = []

    for ruleList in grammar:
        for rule in grammar[ruleList]:
            tempList = [ruleList]
            tempList.extend(rule)
            grammarTable.append(tempList)

    outFile = open(outFilename, "w")
    outFile.write(str(len(grammarTable)) + "\n")
    print("Saving %d rules..." % len(grammarTable), end="")
    for rule in grammarTable:
        outFile.write(str(len(rule)) + " ")
        outFile.write(rule[0] + " ")
        for x in rule[1:]:
            if x.isTerminal:
                outFile.write("0 ")
            else:
                outFile.write("1 ")
            outFile.write(x.text + " ")
        outFile.write("\n")

    print("Done")
    outFile.write(str(len(tokensSet)) + "\n")
    print("Saving %d tokens..." % len(tokensSet), end="")
    for item in tokensSet:
        if tokensSet[item]:
            outFile.write("0 ")
        else:
            outFile.write("1 ")
        outFile.write(item + "\n")

    print("Done")
    outFile.write(str(len(actionTable)) + "\n")
    print("Saving %d entries in actionTable..." % len(actionTable), end="")
    for key in actionTable:
        if actionTable[key][0] == 'r':
            tempRule = [actionTable[key][1][0]]
            tempRule.extend(actionTable[key][1][1])
            tempText = "{0} {1} {2} {3}\n".format(key[0], key[1],
                                                  actionTable[key][0], str(grammarTable.index(tempRule)))
            outFile.write(tempText)
        else:
            tempText = "{0} {1} {2} {3}\n".format(key[0], key[1],
                                                  actionTable[key][0], actionTable[key][1])
            outFile.write(tempText)

    print("Done")
    outFile.write(str(len(gotoTable)) + "\n")
    print("Saving %d entries in gotoTable..." % len(gotoTable), end="")
    for key in gotoTable:
        tempText = "{0} {1} {2}\n".format(key[0], key[1], gotoTable[key])
        outFile.write(tempText)

    outFile.close()
    print("Done")


if __name__ == "__main__":
    oparser = optparse.OptionParser()

    oparser.add_option("-o", action="store", dest="outfile")
    opts, args = oparser.parse_args()

    print("Grammar Parser")
    if not args:
        print("Usage: lr1_parser.py [options]")
        raise SystemExit

    if not opts.outfile:
        opts.outfile = "out.gpf"

    canCollection = build_tables(args[0], opts.outfile)

    print("Done")
