#linkedList.py
#created 4/17/07
#by Alex Miller and Derek Groenendyk

from Node import * 

class LinkedList:
    def __init__(self):
        self.head = None
        self.listLength = 0

    def isEmpty(self):
        return self.head == None

    def add(self,item,location):
        if self.duplicate(item):            
            self.listLength += 1
            temp = Node(item, 1)
            temp.setNext(self.head)
            temp.setLocation(location)
            self.head = temp
            current = self.head
            while current.getNext() != None:
                position = current.getPosition()
                current = current.getNext()
                current.setPosition(position+1)
        
    def selfHead(self):
        return self.head

    def betterLength(self):
        return self.listLength

    def search(self,item):
        current = self.head
        while current != None:
            if current.getFileName() == item:
                return current
            else:
                current = current.getNext()
        return None

    def duplicate(self, item):
        current = self.head
        while current != None and current.getFileName() != item:
            current = current.getNext()
        if current != None and current.getFileName() == item:
            return False
        else:
            return True     

    def remove(self,item):
        current = self.head
        previous = None
        while current.getFileName() != item:
            previous = current
            current = current.getNext()
        if previous == None:
            self.head = current.getNext()
        else:
            previous.setNext(current.getNext())

    def insertAfter(self, itemInList, itemToAdd):
        next = None
        current = self.head
        while not current.getFileName() == itemInList and current.getData() != None:
            current = current.getNext()
        next = current.getNext()
        temp = Node(itemToAdd)
        current.setNext(temp.getFileName())
        temp.setNext(next)

    def move(self, itemToMove, itemInList):
        next = None
        current = self.head
        while current.getFileName() != itemInList and current.getNext() != None:
            current = current.getNext()
        next = current.getNext()
        item = self.search(itemToMove)
        self.remove(itemToMove)
        current.setNext(item)
        item.setNext(next)
        
##        while item != None:
##            oldItem = item
##            position = oldItem.getPosition()
##            oldItem.setPosition(position+1)
##            oldItem.getNext()
        

##        position = current.getPosition()
##        while current.getData() != None:
##            current.setPosition(position+1)
##            position = current.getPosition()
##            current = current.getNext()
##

        
        
            

