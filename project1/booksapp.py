import requests

def import_books():
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "98Q83fyMcWF418clkugQ", "isbns": "9781632168146"})


if __name__ == "__main__":
    import_books()


def get_book(isbn):
    goodreads_data = requests.get(f"https://www.goodreads.com/book/review_counts.json", params={"key": "98Q83fyMcWF418clkugQ", "isbns": isbn}).json()
    return goodreads_data['books'][0]
