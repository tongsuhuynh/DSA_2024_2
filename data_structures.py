class DynamicArray:
    def __init__(self):
        self.capacity = 2
        self.size = 0
        self.data = [None] * self.capacity
        self.shrink_factor = 0.25  # Shrink when utilization is below 25%

    def append(self, value):
        if self.size == self.capacity:
            self._resize()
        self.data[self.size] = value
        self.size += 1

    def _resize(self):
        if self.size == self.capacity:
            # Double capacity when full
            self.capacity *= 2
            new_data = [None] * self.capacity
            for i in range(self.size):
                new_data[i] = self.data[i]
            self.data = new_data
        elif self.size < self.capacity * self.shrink_factor and self.capacity > 2:
            # Shrink when utilization is low
            self.capacity = max(2, self.capacity // 2)
            new_data = [None] * self.capacity
            for i in range(self.size):
                new_data[i] = self.data[i]
            self.data = new_data

    def get(self, index):
        if 0 <= index < self.size:
            return self.data[index]
        raise IndexError('Index out of range')

    def set(self, index, value):
        if 0 <= index < self.size:
            self.data[index] = value
        else:
            raise IndexError('Index out of range')

    def remove(self, value):
        for i in range(self.size):
            if self.data[i] == value:
                # Shift elements to fill the gap
                for j in range(i, self.size - 1):
                    self.data[j] = self.data[j + 1]
                self.data[self.size - 1] = None
                self.size -= 1
                self._resize()  # Check if we need to shrink
                return True
        return False

    def clear(self):
        """Clear all elements from the array"""
        self.size = 0
        self.capacity = 2
        self.data = [None] * self.capacity

    def __len__(self):
        return self.size

    def __iter__(self):
        for i in range(self.size):
            yield self.data[i]

    def __str__(self):
        return str([self.data[i] for i in range(self.size)])

class LinkedListNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, value):
        new_node = LinkedListNode(value)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.size += 1

    def remove(self, value):
        prev = None
        curr = self.head
        while curr:
            if curr.data == value:
                if prev:
                    prev.next = curr.next
                else:
                    self.head = curr.next
                if curr == self.tail:
                    self.tail = prev
                self.size -= 1
                return True
            prev = curr
            curr = curr.next
        return False

    def contains(self, value):
        curr = self.head
        while curr:
            if curr.data == value:
                return True
            curr = curr.next
        return False

    def __len__(self):
        return self.size

    def __iter__(self):
        curr = self.head
        while curr:
            yield curr.data
            curr = curr.next

class HashNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    def __init__(self, initial_capacity=53):
        self.capacity = initial_capacity
        self.size = 0
        self.buckets = [None] * self.capacity
        self.load_factor = 0.75
        self.DELETED = object()
        self.min_capacity = 11  # Minimum capacity to prevent too frequent resizing

    def _hash(self, key):
        if isinstance(key, str):
            key = key.encode('utf-8')
        hash_value = 0x811c9dc5
        for byte in key:
            hash_value ^= byte
            hash_value *= 0x01000193
            hash_value &= 0xFFFFFFFF  # Keep it 32-bit
        return hash_value % self.capacity

    def _probe(self, key, index):
        i = 1
        while True:
            new_index = (index + i * i) % self.capacity
            if self.buckets[new_index] is None or self.buckets[new_index] is self.DELETED:
                return new_index
            i += 1
            if i > self.capacity:  # Prevent infinite loop
                return None

    def put(self, key, value):
        if self.size / self.capacity >= self.load_factor:
            self._resize()
        
        index = self._hash(key)
        if self.buckets[index] is not None and self.buckets[index] is not self.DELETED:
            index = self._probe(key, index)
            if index is None:  # Table is full
                self._resize()
                return self.put(key, value)
        
        self.buckets[index] = (key, value)
        self.size += 1

    def get(self, key):
        index = self._hash(key)
        original_index = index
        i = 0 # Counter for probing

        while self.buckets[index] is not None:
            # Found a non-deleted element
            if self.buckets[index] is not self.DELETED and self.buckets[index][0] == key:
                return self.buckets[index][1]

            # Probe to the next index using quadratic probing
            i += 1
            index = (original_index + i * i) % self.capacity

            # Prevent infinite loop if probing covers all slots without finding the key
            # (This check might need refinement based on proper quadratic probing analysis)
            if i > self.capacity:
                 break

        # Key not found after probing
        return None

    def remove(self, key):
        index = self._hash(key)
        original_index = index
        i = 0 # Counter for probing

        while self.buckets[index] is not None:
            # Found a non-deleted element that matches the key
            if self.buckets[index] is not self.DELETED and self.buckets[index][0] == key:
                self.buckets[index] = self.DELETED
                self.size -= 1
                # Consider shrinking if load factor is too low after removal
                if self.size / self.capacity < self.load_factor / 4 and self.capacity > self.min_capacity:
                     self._resize() # Resize will rehash active elements
                return True # Successfully removed

            # Probe to the next index using quadratic probing
            i += 1
            index = (original_index + i * i) % self.capacity
            
            # Prevent infinite loop
            if i > self.capacity:
                 break

        # Key not found after probing
        return False # Key not found to remove

    def _resize(self):
        old_buckets = self.buckets
        old_capacity = self.capacity
        
        # Calculate new capacity
        if self.size / self.capacity >= self.load_factor:
            self.capacity = max(self.min_capacity, self.capacity * 2)
        else:
            self.capacity = max(self.min_capacity, self.capacity // 2)
            
        self.buckets = [None] * self.capacity
        self.size = 0
        
        for bucket in old_buckets:
            if bucket is not None and bucket is not self.DELETED:
                self.put(bucket[0], bucket[1])

    def clear(self):
        """Clear all elements from the hash table"""
        self.capacity = self.min_capacity
        self.size = 0
        self.buckets = [None] * self.capacity

    def __iter__(self):
        for bucket in self.buckets:
            if bucket is not None and bucket is not self.DELETED:
                yield bucket[1]

    def items(self):
        for bucket in self.buckets:
            if bucket is not None and bucket is not self.DELETED:
                yield bucket[0], bucket[1]

    def __len__(self):
        return self.size

    def __str__(self):
        return str({k: v for k, v in self.items()})

# === BST và Tree cho quản lý sách, tìm kiếm tiêu đề ===
class AVLNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1

class BST:
    def __init__(self):
        self.root = None
        self.size = 0

    def _height(self, node):
        if not node:
            return 0
        return node.height

    def _balance(self, node):
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _update_height(self, node):
        if not node:
            return
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _rotate_right(self, y):
        x = y.left
        T2 = x.right

        x.right = y
        y.left = T2

        self._update_height(y)
        self._update_height(x)

        return x

    def _rotate_left(self, x):
        y = x.right
        T2 = y.left

        y.left = x
        x.right = T2

        self._update_height(x)
        self._update_height(y)

        return y

    def insert(self, key, value):
        self.root = self._insert(self.root, key, value)
        self.size += 1

    def _insert(self, node, key, value):
        if not node:
            return AVLNode(key, value)

        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            node.value = value
            self.size -= 1  # Don't count replacement as new insertion
            return node

        self._update_height(node)
        balance = self._balance(node)

        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)

        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)

        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, node, key):
        if not node or node.key == key:
            return node.value if node else None

        if key < node.key:
            return self._search(node.left, key)
        return self._search(node.right, key)

    def delete(self, key):
        self.root = self._delete(self.root, key)
        self.size -= 1

    def _delete(self, node, key):
        if not node:
            self.size += 1  # Compensate for the decrement in delete()
            return node

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left

            temp = self._min_value_node(node.right)
            node.key = temp.key
            node.value = temp.value
            node.right = self._delete(node.right, temp.key)

        if not node:
            return node

        self._update_height(node)
        balance = self._balance(node)

        # Left Left Case
        if balance > 1 and self._balance(node.left) >= 0:
            return self._rotate_right(node)

        # Left Right Case
        if balance > 1 and self._balance(node.left) < 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Right Right Case
        if balance < -1 and self._balance(node.right) <= 0:
            return self._rotate_left(node)

        # Right Left Case
        if balance < -1 and self._balance(node.right) > 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def clear(self):
        """Clear all elements from the tree"""
        self.root = None
        self.size = 0

    def get_all_values(self):
        """Get all values in the tree in-order"""
        values = []
        self._inorder_traversal(self.root, values)
        return values

    def _inorder_traversal(self, node, values):
        if node:
            self._inorder_traversal(node.left, values)
            values.append(node.value)
            self._inorder_traversal(node.right, values)

    def __len__(self):
        return self.size

    def __str__(self):
        return str(self.get_all_values())

class TreeNode:
    def __init__(self):
        self.children = DynamicArray()
        self.is_end_of_word = False
        self.books = DynamicArray()
        self.word_count = 0

class Tree:
    def __init__(self):
        self.root = TreeNode()
        self.size = 0

    def insert(self, word, book):
        node = self.root
        for char in word.lower():
            found = False
            for i in range(len(node.children)):
                child = node.children.get(i)
                if child.char == char:
                    node = child
                    found = True
                    break
            
            if not found:
                new_node = TreeNode()
                new_node.char = char
                node.children.append(new_node)
                node = new_node
                
        if not node.is_end_of_word:
            self.size += 1
        node.is_end_of_word = True
        node.word_count += 1
        node.books.append(book)

    def search(self, prefix):
        node = self.root
        for char in prefix.lower():
            found = False
            for i in range(len(node.children)):
                child = node.children.get(i)
                if child.char == char:
                    node = child
                    found = True
                    break
            
            if not found:
                return DynamicArray()
                
        return self._get_all_books(node)

    def _get_all_books(self, node):
        books = DynamicArray()
        if node.is_end_of_word:
            for i in range(len(node.books)):
                books.append(node.books.get(i))
        for i in range(len(node.children)):
            child = node.children.get(i)
            child_books = self._get_all_books(child)
            for j in range(len(child_books)):
                books.append(child_books.get(j))
        return books

    def remove(self, word, book):
        node = self.root
        for char in word.lower():
            found = False
            for i in range(len(node.children)):
                child = node.children.get(i)
                if child.char == char:
                    node = child
                    found = True
                    break
            
            if not found:
                return False
                
        if node.is_end_of_word:
            for i in range(len(node.books)):
                if node.books.get(i) == book:
                    node.books.remove(book)
                    break
            node.word_count -= 1
            if node.word_count == 0:
                node.is_end_of_word = False
                self.size -= 1
            return True
        return False

    def clear(self):
        """Clear all elements from the trie"""
        self.root = TreeNode()
        self.size = 0

    def get_all_words(self):
        """Get all words in the trie"""
        words = []
        self._get_words(self.root, "", words)
        return words

    def _get_words(self, node, prefix, words):
        if node.is_end_of_word:
            words.append(prefix)
        for i in range(len(node.children)):
            child = node.children.get(i)
            self._get_words(child, prefix + child.char, words)

    def __len__(self):
        return self.size

    def __str__(self):
        return str(self.get_all_words())

class PriorityQueue:
    """
    A simple FIFO queue implemented using a LinkedList for book reservations.
    """
    def __init__(self):
        self._list = LinkedList()

    def enqueue(self, reader_id):
        """Adds a reader to the end of the reservation queue."""
        self._list.append(reader_id)

    def dequeue(self):
        """Removes and returns the reader at the front of the queue."""
        if not self._list.head:
            return None
        # LinkedList does not have a direct pop_front, so we'll manually remove head
        reader_id = self._list.head.data
        self._list.head = self._list.head.next
        if not self._list.head:
            self._list.tail = None
        self._list.size -= 1
        return reader_id

    def peek(self):
        """Returns the reader at the front of the queue without removing them."""
        if not self._list.head:
            return None
        return self._list.head.data

    def contains(self, reader_id):
        """Checks if a reader is in the reservation queue."""
        return self._list.contains(reader_id)

    def remove(self, reader_id):
        """Removes a specific reader from the queue."""
        return self._list.remove(reader_id)

    def is_empty(self):
        """Returns True if the queue is empty, False otherwise."""
        return self._list.head is None

    def __len__(self):
        """Returns the number of readers in the queue."""
        return len(self._list)

    def __iter__(self):
        """Iterates over the readers in the queue."""
        return iter(self._list)