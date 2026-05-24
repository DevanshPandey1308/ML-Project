import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

df = pd.read_csv('Notebook/data/stud.csv')

os.makedirs("static/images", exist_ok=True)

# Maths Score Distribution

plt.figure(figsize=(8,5))
sns.histplot(df['math score'], kde=True)
plt.title("Math Score Distribution")
plt.savefig("static/images/math_distribution.png")
plt.close()


# Reading vs Maths

plt.figure(figsize=(8,5))
sns.scatterplot(x='reading score', y='math score', data=df)
plt.title("Reading Score vs Math Score")
plt.savefig("static/images/reading_vs_math.png")
plt.close()


# Writing vs Maths

plt.figure(figsize=(8,5))
sns.scatterplot(x='writing score', y='math score', data=df)
plt.title("Writing Score vs Math Score")
plt.savefig("static/images/writing_vs_math.png")
plt.close()


# Correlation Heatmap

plt.figure(figsize=(8,5))
sns.heatmap(df.corr(numeric_only=True), annot=True, cmap='Blues')
plt.title("Correlation Heatmap")
plt.savefig("static/images/correlation_heatmap.png")
plt.close()

print("EDA graphs generated successfully")