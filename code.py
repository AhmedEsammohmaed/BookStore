import os
import json
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from PyPDF2 import PdfReader

# ---------------- Storage ----------------
BOOKS_DIR = Path("books")   # folder to store books
INDEX_FILE = BOOKS_DIR / "index.json"
BOOKS_DIR.mkdir(exist_ok=True)

def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)


# ---------------- Services ----------------
class ShippingService:
    @staticmethod
    def send(address: str) -> None:
        print(f"Quantum book store: shipping to {address}")


class MailService:
    @staticmethod
    def send(email: str) -> None:
        print(f"Quantum book store: sending email to {email}")


# ---------------- Abstract Base Class ----------------
class Book(ABC):
    def __init__(self, isbn: str, title: str, author: str, year: int, price: float) -> None:
        self._isbn = isbn
        self._title = title
        self._author = author
        self._year = year
        self._price = price

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def year(self) -> int:
        return self._year

    @property
    def price(self) -> float:
        return self._price

    @abstractmethod
    def is_for_sale(self) -> bool:
        ...

    @abstractmethod
    def buy(self, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        ...


# ---------------- Concrete Book Types ----------------
class PaperBook(Book):
    def __init__(self, isbn: str, title: str, author: str, year: int, price: float, stock: int) -> None:
        super().__init__(isbn, title, author, year, price)
        self._stock = stock

    def is_for_sale(self) -> bool:
        return True

    def buy(self, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        if quantity <= 0:
            raise ValueError("Quantum book store: You must enter a positive quantity")
        if self._stock < quantity:
            raise ValueError(f"Quantum book store: Not enough stock for ISBN: {self._isbn}")

        self._stock -= quantity
        if address:
            ShippingService.send(address)
        print(f"Quantum book store: shipping {quantity} copies of {self._title}")
        return self._price * quantity


class Ebook(Book):
    def __init__(self, isbn: str, title: str, author: str, year: int, price: float, filetype: str) -> None:
        super().__init__(isbn, title, author, year, price)
        self._filetype = filetype

    def is_for_sale(self) -> bool:
        return True

    def buy(self, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        if quantity <= 0:
            raise ValueError("Quantum book store: Quantity must be at least 1.")
        if quantity > 1:
            raise ValueError("Quantum book store: EBooks can only be bought one at a time.")
        if not email:
            raise ValueError("Quantum book store: Email required for Ebook delivery.")

        MailService.send(email)
        print(f"Quantum book store: Emailing EBook {self._title} to {email}")
        return self._price


class AudioBook(Book):
    def __init__(self, isbn: str, title: str, author: str, year: int, price: float, format_: str) -> None:
        super().__init__(isbn, title, author, year, price)
        self._format = format_

    def is_for_sale(self) -> bool:
        return True

    def buy(self, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        if quantity <= 0:
            raise ValueError("Quantum book store: Quantity must be positive.")
        if not email:
            raise ValueError("Quantum book store: Email is required to send AudioBook.")

        print(f"Quantum book store: Sending AudioBook {self._title} ({self._format}) to {email}")
        return self._price * quantity


@dataclass
class ShowcaseBook(Book):
    def __init__(self, isbn: str, title: str, author: str, year: int) -> None:
        super().__init__(isbn, title, author, year, price=0.0)

    def is_for_sale(self) -> bool:
        return False

    def buy(self, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        raise NotImplementedError("Quantum book store: Showcase books are not for sale.")

    def show(self) -> None:
        print("Quantum book store: SHOWCASE 📚")
        print(f"Title: {self._title}")
        print(f"Author: {self._author}")
        print(f"Year: {self._year}")
        print(f"ISBN: {self._isbn}")


# ---------------- Store ----------------
class QuantumBookStore:
    def __init__(self) -> None:
        self._inventory: Dict[str, Book] = {}
        self._load_books()

    def _load_books(self):
        """Load previously stored books from index.json."""
        index = load_index()
        for isbn, data in index.items():
            btype = data["type"]
            if btype == "PaperBook":
                self._inventory[isbn] = PaperBook(**data["args"])
            elif btype == "Ebook":
                self._inventory[isbn] = Ebook(**data["args"])
            elif btype == "AudioBook":
                self._inventory[isbn] = AudioBook(**data["args"])
            elif btype == "ShowcaseBook":
                self._inventory[isbn] = ShowcaseBook(**data["args"])

    def add_book(self, book: Book) -> None:
        self._inventory[book.isbn] = book
        print(f"Quantum book store: Book added -> {book.title}")

        # Save to index.json
        index = load_index()
        index[book.isbn] = {
            "type": type(book).__name__,
            "args": {
                "isbn": book.isbn,
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "price": book.price,
                **({"stock": book._stock} if isinstance(book, PaperBook) else {}),
                **({"filetype": book._filetype} if isinstance(book, Ebook) else {}),
                **({"format_": book._format} if isinstance(book, AudioBook) else {}),
            }
        }
        save_index(index)

    def list_books(self) -> None:
        if not self._inventory:
            print("📂 No books available in store.")
            return

        print("\n📚 Books in Quantum Book Store:")
        for isbn, book in self._inventory.items():
            status = "For Sale ✅" if book.is_for_sale() else "Showcase 🔒"
            print(f"- {book.title} by {book.author} ({book.year}) | ISBN: {isbn} | ${book.price:.2f} | {status}")

    def buy_book(self, isbn: str, quantity: int, email: Optional[str], address: Optional[str]) -> float:
        book = self._inventory.get(isbn)
        if not book:
            raise ValueError(f"Quantum book store: Book with ISBN not found: {isbn}")

        if not book.is_for_sale():
            if quantity == 0 and isinstance(book, ShowcaseBook):
                book.show()
                return 0.0
            else:
                raise ValueError(f"Quantum book store: Book is not for sale: {book.title}")

        return book.buy(quantity, email, address)


# ---------------- Interactive CLI ----------------
def main():
    store = QuantumBookStore()

    while True:
        print("\n📚 Quantum Book Store Menu:")
        print("1. Add PaperBook")
        print("2. Add Ebook")
        print("3. Add AudioBook")
        print("4. Add ShowcaseBook")
        print("5. Buy Book")
        print("6. List Books")
        print("7. Exit")

        choice = input("Enter your choice: ").strip()

        try:
            if choice == "1":
                isbn = input("ISBN: ")
                title = input("Title: ")
                author = input("Author: ")
                year = int(input("Year: "))
                price = float(input("Price: "))
                stock = int(input("Stock: "))
                store.add_book(PaperBook(isbn, title, author, year, price, stock))

            elif choice == "2":
                isbn = input("ISBN: ")
                title = input("Title: ")
                author = input("Author: ")
                year = int(input("Year: "))
                price = float(input("Price: "))
                filetype = input("Filetype (pdf, epub, etc.): ")
                store.add_book(Ebook(isbn, title, author, year, price, filetype))

            elif choice == "3":
                isbn = input("ISBN: ")
                title = input("Title: ")
                author = input("Author: ")
                year = int(input("Year: "))
                price = float(input("Price: "))
                format_ = input("Format (mp3, wav, etc.): ")
                store.add_book(AudioBook(isbn, title, author, year, price, format_))

            elif choice == "4":
                isbn = input("ISBN: ")
                title = input("Title: ")
                author = input("Author: ")
                year = int(input("Year: "))
                store.add_book(ShowcaseBook(isbn, title, author, year))

            elif choice == "5":
                isbn = input("Enter ISBN to buy: ")
                quantity = int(input("Quantity (0 if showcase): "))
                email = input("Email (press Enter if not needed): ").strip() or None
                address = input("Address (press Enter if not needed): ").strip() or None
                total = store.buy_book(isbn, quantity, email, address)
                print(f"✅ Purchase successful. Total: ${total:.2f}")

            elif choice == "6":
                store.list_books()

            elif choice == "7":
                print("👋 Exiting Quantum Book Store. Bye!")
                break

            else:
                print("❌ Invalid choice. Try again.")

        except Exception as e:
            print(f"⚠️ Error: {e}")


if __name__ == "__main__":
    main()
