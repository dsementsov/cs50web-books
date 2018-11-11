import pandas as pd 
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

csv = pd.read_csv('books.csv')

enginne = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=enginne))


for index, row in csv.iterrows():
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
                    {"isbn": row["isbn"], "title":row["title"], "author":row["author"], "year":row["year"]})
    db.commit()




