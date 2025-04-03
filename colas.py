# Creación de una cola usando una lista
from collections import deque

queue = deque()

# Agregar elementos a la cola
queue.append(1)
queue.append(2)
queue.append(3)

# Eliminar y devolver el primer elemento
print(queue.popleft())  # 1

# Ver el primer elemento sin eliminarlo
print(queue[0] if queue else None)  # 2

# Verificar si la cola está vacía
print(len(queue) == 0)  # False

# para eliminar un elemento especifico de la cola
queue.remove(2)  # Esto eliminará el primer elemento que sea igual a 2
print(queue)  # deque([3])
# obtener el elemento que esta al frente de la cola
print(queue[0] if queue else None)  # 3
#borrar cola
queue.clear()
print(queue)  # deque([])

# verificar si la cola esta vacia
print(len(queue) == 0)  # True


# verificar si la cola esta llena
queue = deque(maxlen=5)  # Cola con capacidad máxima de 5 elementos

# Verificar si la cola está llena
def is_full(q):
    return len(q) == q.maxlen

# Agregar elementos
queue.extend([1, 2, 3, 4, 5])

# Comprobar si la cola está llena
print(is_full(queue))  # True

queue.popleft()  # Eliminar un elemento
print(is_full(queue))  # False

# verificar el tamaño de la cola
def tamaño_cola(q):
    return len(q)
queue = deque([1, 2, 3, 4, 5])
print(tamaño_cola(queue))  
# implementacion de nodos mediante listas enlazadas
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class Queue:
    def __init__(self):
        self.front = self.rear = None
        self.size = 0

    def is_empty(self):
        return self.front is None

    def enqueue(self, data):
        new_node = Node(data)
        if self.rear is None:
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        self.size += 1

    def dequeue(self):
        if self.is_empty():
            print("La cola está vacía. No hay elementos para eliminar.")
            return None
        temp = self.front
        self.front = temp.next
        if self.front is None:
            self.rear = None
        self.size -= 1
        return temp.data

    def peek(self):
        if self.is_empty():
            return None
        return self.front.data

    def get_size(self):
        return self.size

    def print_queue(self):
        if self.is_empty():
            print("La cola está vacía.")
            return
        
        current = self.front
        while current:
            print(current.data, end=" -> ")
            current = current.next
        print("None")  # Indica el final de la cola


# --- Menú interactivo ---
def main():
    q = Queue()

    while True:
        print("\n--- Menú de la Cola ---")
        print("1. Enqueue (Agregar nodo)")
        print("2. Dequeue (Eliminar nodo)")
        print("3. Peek (Ver primer elemento)")
        print("4. Obtener tamaño de la cola")
        print("5. Mostrar cola")
        print("6. Salir")
        
        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            valor = input("Introduce un valor para encolar: ")
            q.enqueue(valor)
            print("Elemento agregado.")
        elif opcion == "2":
            eliminado = q.dequeue()
            if eliminado is not None:
                print(f"Se eliminó: {eliminado}")
        elif opcion == "3":
            print(f"Primer elemento en la cola: {q.peek()}")
        elif opcion == "4":
            print(f"Tamaño actual de la cola: {q.get_size()}")
        elif opcion == "5":
            print("Cola actual:")
            q.print_queue()
        elif opcion == "6":
            print("Saliendo del programa.")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()


