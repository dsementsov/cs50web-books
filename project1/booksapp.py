import requests



def run():
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "98Q83fyMcWF418clkugQ", "isbns": "9781632168146"})
    print(res.json())


if __name__ == "__main__":
    run()