import os
import pickle
import pandas as pd

PKL_DIR = os.path.join(os.path.dirname(__file__), '..', 'pkl')
CSV_DIR = os.path.join(os.path.dirname(__file__), '..', 'csv')

def convert_all_pkl_to_csv(pkl_dir=PKL_DIR, csv_dir=CSV_DIR):
    os.makedirs(csv_dir, exist_ok=True)
    for fname in os.listdir(pkl_dir):
        if fname.endswith('.pkl'):
            pkl_path = os.path.join(pkl_dir, fname)
            csv_path = os.path.join(csv_dir, fname.replace('.pkl', '.csv'))
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f)
            # data가 DataFrame이 아니면 변환 필요
            if isinstance(data, pd.DataFrame):
                data.to_csv(csv_path, index=False)
            else:
                # dict/list 등은 DataFrame으로 변환
                df = pd.DataFrame(data)
                df.to_csv(csv_path, index=False)
            print(f"Converted {fname} -> {os.path.basename(csv_path)}")

if __name__ == '__main__':
    convert_all_pkl_to_csv()