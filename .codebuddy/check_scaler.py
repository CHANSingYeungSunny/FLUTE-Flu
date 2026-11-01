import pandas as pd, numpy as np, json

df = pd.read_csv(r'c:\Users\Asus\Desktop\FYP code\MLFlu\recovery\author_repo\dataset\illness\national_illness_orig.csv')
print('Columns:', list(df.columns))
print('Shape:', df.shape)
n = len(df)
num_train = int(n * 0.7)
print(f'Total rows: {n}, train: {num_train}')

train_data = df.iloc[:num_train, 1:]
means = train_data.mean()
stds = train_data.std(ddof=0)
print()
print('Author StandardScaler (fit on 70% train):')
for i, col in enumerate(train_data.columns):
    print(f'  feat {i} ({col}): mean={means.iloc[i]:.4f}, std={stds.iloc[i]:.4f}')

with open(r'c:\Users\Asus\Desktop\FYP code\MLFlu\data\scaler_miflu_author966.json') as f:
    sc = json.load(f)
print()
print('Our scaler keys:', list(sc.keys()))
print(json.dumps(sc, indent=2, default=str)[:2000])
