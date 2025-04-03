#implementar colas mediante vectores

class Queue:
    def __init__(self):
        self.queue = []  # Usamos una lista como base de la cola

    def is_empty(self):
        return len(self.queue) == 0  # Devuelve True si la cola está vacía

    def enqueue(self, data):
        self.queue.append(data)  # Agrega un elemento al final de la cola
        print(f"Elemento {data} agregado.")

    def dequeue(self):
        if self.is_empty():
            print("La cola está vacía. No hay elementos para eliminar.")
            return None
        return self.queue.pop(0)  # Elimina y devuelve el primer elemento

    def peek(self):
        if self.is_empty():
            return None
        return self.queue[0]  # Devuelve el primer elemento sin eliminarlo

    def get_size(self):
        return len(self.queue)  # Devuelve el número de elementos en la cola

    def print_queue(self):
        if self.is_empty():
            print("La cola está vacía.")
        else:
            print(" -> ".join(map(str, self.queue)) + " -> None")  # Imprime la cola

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