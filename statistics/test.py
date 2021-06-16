import pandas as pd
df = pd.DataFrame()
df["day"] = pd.date_range(start='1/1/2019', end='1/12/2019', freq='D')
print("original df",df)

print(type(df["day"][0]))
columns=  ["qnt_sold_white", "qnt_sold_wheat", "qnt_sold_glutenfree", "price_white", "price_wheat" ,"price_glutenfree"]

# for i in len(columns):

#     df[column[i]]= ""


print(df)

df['day_dt'] = pd.to_datetime(df['day'])
print("after datetime conversion")
print(df)
print(type(df["day_dt"][0]))
